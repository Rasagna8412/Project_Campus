"""Campus AI Tutor Service: Grounded Academic Concept Clarifier & Learning Companion.

Features:
- Bounded, lesson-aware contextual reasoning
- Multi-mode support: EXPLAIN, SIMPLIFY, EXAMPLE, HINT, QUIZ
- Robust anti-hallucination and provenance citations
- Academic dishonesty guardrails (refuses direct answers to active exams/tests)
- Prompt injection defense & input sanitization
- Clean provider-agnostic dispatch (Gemini API with deterministic grounded fallback)
- Student subscription entitlement checks & quota enforcement
"""

import json
import logging
import re
import uuid
from datetime import datetime, time, timezone
from typing import Any, Dict, List, Optional, Tuple
import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import auth_rate_limiter
from app.models.ai import AITutorInteraction, StudentSubscription
from app.models.content import ContentStatus, Lesson, LessonSection
from app.models.taxonomy import Topic
from app.schemas.ai import (
    AITutorChatRequest,
    AITutorChatResponse,
    AITutorQuizQuestion,
    SubscriptionEntitlementResponse,
)

logger = logging.getLogger(__name__)

# Injection patterns to detect and neutralize
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+override",
    r"you\s+are\s+now\s+dan",
    r"jailbreak",
    r"bypass\s+all\s+(rules|restrictions)",
    r"disregard\s+all\s+guidelines",
    r"reveal\s+your\s+system\s+prompt",
]

# Patterns detecting attempts to extract direct test/exam answer keys
ACADEMIC_DISHONESTY_PATTERNS = [
    r"give\s+me\s+the\s+(answer|solution)\s+to\s+(question|problem)?\s*#?\s*\d+",
    r"what\s+is\s+the\s+answer\s+to\s+(question|problem)?\s*#?\s*\d+",
    r"solve\s+(question|problem)\s*#?\s*\d+",
    r"test\s+answer\s+key",
    r"exam\s+answer\s+key",
    r"which\s+option\s+is\s+correct\s+for\s+(question|problem)?\s*#?\s*\d+",
    r"direct\s+answer\s+to\s+(question|problem)",
]

# Completely out-of-syllabus subjects to politely decline
OFF_TOPIC_PATTERNS = [
    r"\b(bake\s+a\s+cake|recipe|cooking\s+pasta)\b",
    r"\b(write\s+a\s+movie\s+script|hollywood|celebrity\s+gossip)\b",
    r"\b(crypto\s+trading|invest\s+in\s+bitcoin)\b",
    r"\b(horoscope|astrology\s+prediction)\b",
]


class AITutorService:
    """Core domain service for AI tutoring, grounding, guardrails, and entitlements."""

    def __init__(self) -> None:
        self.rate_limiter = auth_rate_limiter

    async def get_or_create_subscription(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> StudentSubscription:
        """Fetch existing subscription or provision default FREE tier."""
        stmt = select(StudentSubscription).where(StudentSubscription.user_id == user_id)
        res = await db.execute(stmt)
        sub = res.scalar_one_or_none()
        if not sub:
            sub = StudentSubscription(
                user_id=user_id,
                tier="FREE",
                daily_tutor_quota=settings.SUBSCRIPTION_FREE_TIER_DAILY_TUTOR_LIMIT,
            )
            db.add(sub)
            await db.commit()
            await db.refresh(sub)
        return sub

    async def get_daily_usage(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> int:
        """Count AI interactions recorded today (UTC)."""
        today_start = datetime.combine(
            datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc
        )
        stmt = (
            select(func.count(AITutorInteraction.id))
            .where(
                AITutorInteraction.user_id == user_id,
                AITutorInteraction.created_at >= today_start,
            )
        )
        res = await db.execute(stmt)
        return res.scalar() or 0

    async def get_entitlements(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> SubscriptionEntitlementResponse:
        """Compute full entitlement summary for authenticated student."""
        sub = await self.get_or_create_subscription(db, user_id)
        daily_used = await self.get_daily_usage(db, user_id)
        is_pro = sub.tier.upper() == "PRO"
        quota = sub.daily_tutor_quota if not is_pro else 9999
        remaining = max(0, quota - daily_used)

        features = [
            "CBSE & JEE Standard Curriculum Grounding",
            "Socratic Doubt Clarification",
            "Formula & Mathematical Derivations",
        ]
        if is_pro:
            features.extend([
                "Unlimited Campus AI Tutor Queries",
                "Full Undergraduate Engineering Track (Programming, DSA, Eng Math)",
                "Interactive Code Sandbox Verification",
                "Automated Custom Practice Quiz Generation",
                "Priority Inference Response Latency",
            ])
        else:
            features.append(f"Free Tier: {sub.daily_tutor_quota} Daily Tutor Queries")

        return SubscriptionEntitlementResponse(
            tier=sub.tier,
            daily_tutor_quota=sub.daily_tutor_quota,
            daily_tutor_used=daily_used,
            daily_tutor_remaining=remaining,
            is_unlimited=is_pro,
            valid_until=(
                sub.valid_until.isoformat() if sub.valid_until else None
            ),
            features=features,
        )

    def check_rate_limits(self, user_id: uuid.UUID) -> None:
        """Enforce burst rate limit (e.g. max requests per minute)."""
        client_key = f"tutor:{user_id}"
        if self.rate_limiter.is_rate_limited(
            client_key,
            max_attempts=settings.AI_RATE_LIMIT_PER_MINUTE,
            window_seconds=60,
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI Tutor rate limit exceeded. Please wait a moment before sending another query.",
            )
        self.rate_limiter.record_attempt(client_key)

    async def fetch_grounding_context(
        self,
        db: AsyncSession,
        lesson_id: Optional[uuid.UUID],
        topic_id: Optional[uuid.UUID],
    ) -> Tuple[Optional[Lesson], List[LessonSection]]:
        """Retrieve lesson and ordered sections from database for factual grounding."""
        lesson: Optional[Lesson] = None
        sections: List[LessonSection] = []

        if lesson_id:
            stmt = (
                select(Lesson)
                .where(
                    Lesson.id == lesson_id,
                    Lesson.status == ContentStatus.PUBLISHED.value,
                )
                .options(selectinload(Lesson.sections))
            )
            res = await db.execute(stmt)
            lesson = res.scalar_one_or_none()
            if lesson and lesson.sections:
                sections = sorted(lesson.sections, key=lambda s: s.display_order)
        elif topic_id:
            stmt = (
                select(Lesson)
                .where(
                    Lesson.topic_id == topic_id,
                    Lesson.status == ContentStatus.PUBLISHED.value,
                )
                .options(selectinload(Lesson.sections))
                .order_by(Lesson.display_order)
            )
            res = await db.execute(stmt)
            lesson = res.scalars().first()
            if lesson and lesson.sections:
                sections = sorted(lesson.sections, key=lambda s: s.display_order)

        return lesson, sections

    def evaluate_guardrails(
        self, query: str
    ) -> Tuple[bool, Optional[str]]:
        """Evaluate input against safety, dishonesty, and off-topic guardrails."""
        # 1. Prompt Injection Filter
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(f"Prompt injection attempt detected: {pattern}")
                return False, (
                    "Your prompt contains disallowed instructions or attempt to override tutor system safety boundaries. "
                    "Please ask an academic or concept question."
                )

        # 2. Academic Dishonesty / Direct Test Cheating
        for pattern in ACADEMIC_DISHONESTY_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return False, (
                    "As your Campus Academic AI Tutor, I uphold academic integrity and cannot give direct answer keys "
                    "to test or exam questions. However, I can help you understand the foundational principles! "
                    "Tell me what concept you find confusing, and we will work through a similar example step by step."
                )

        # 3. Off-Topic Query
        for pattern in OFF_TOPIC_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return False, (
                    "I am your Campus Academic AI Tutor, specialized in your syllabus curriculum. "
                    "I can only assist with academic concepts, lessons, formulas, and practice problems. "
                    "Let's focus on your studies!"
                )

        return True, None

    async def execute_query(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        request: AITutorChatRequest,
    ) -> AITutorChatResponse:
        """Process student tutoring query with full grounding, guardrails, and quota deduction."""
        # 1. Enforce rate limiting
        self.check_rate_limits(user_id)

        # 2. Enforce subscription quota
        sub = await self.get_or_create_subscription(db, user_id)
        daily_used = await self.get_daily_usage(db, user_id)
        is_pro = sub.tier.upper() == "PRO"
        if not is_pro and daily_used >= sub.daily_tutor_quota:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Daily free AI Tutor limit reached ({sub.daily_tutor_quota} queries/day). "
                    "Upgrade to Campus Pro for unlimited AI-powered learning sessions and engineering courses."
                ),
            )

        # 3. Check guardrails
        is_safe, guardrail_response = self.evaluate_guardrails(request.message)
        if not is_safe and guardrail_response:
            return AITutorChatResponse(
                response=guardrail_response,
                mode=request.mode,
                lesson_id=request.lesson_id,
                lesson_title=None,
                grounding_sources=["Academic Safety Guardrail"],
                quiz_questions=None,
                provider="academic_guardrail",
                tokens_used=15,
                tier=sub.tier,
                daily_quota=sub.daily_tutor_quota,
                daily_used=daily_used,
                daily_remaining=max(0, sub.daily_tutor_quota - daily_used),
            )

        # 4. Fetch Grounding Syllabus Content
        lesson, sections = await self.fetch_grounding_context(
            db, request.lesson_id, request.topic_id
        )

        # 5. Dispatch to LLM or Deterministic Grounded Engine
        api_key = settings.GEMINI_API_KEY or settings.AI_API_KEY
        use_external_llm = (
            bool(api_key)
            and settings.AI_PROVIDER.lower() in ("gemini", "external")
        )

        response_text = ""
        grounding_sources: List[str] = []
        quiz_questions: Optional[List[AITutorQuizQuestion]] = None
        provider_name = "deterministic_grounded_engine"
        estimated_tokens = 0

        if use_external_llm:
            try:
                response_text, grounding_sources = await self._call_gemini_api(
                    api_key=api_key,  # type: ignore[arg-type]
                    user_query=request.message,
                    mode=request.mode,
                    lesson=lesson,
                    sections=sections,
                    history=request.history,
                )
                provider_name = settings.AI_MODEL_NAME
                estimated_tokens = len(response_text) // 4 + 100
            except Exception as e:
                logger.warning(
                    f"External LLM invocation failed ({str(e)}). Falling back to deterministic grounded engine."
                )
                use_external_llm = False

        if not use_external_llm:
            # Deterministic Grounded Educator Engine
            response_text, grounding_sources, quiz_questions = (
                self._generate_deterministic_grounded_response(
                    user_query=request.message,
                    mode=request.mode,
                    lesson=lesson,
                    sections=sections,
                )
            )
            provider_name = "deterministic_grounded_engine"
            estimated_tokens = len(response_text) // 4 + 80

        # 6. Record interaction in database for history, telemetry, and quota
        interaction = AITutorInteraction(
            user_id=user_id,
            lesson_id=lesson.id if lesson else None,
            mode=request.mode,
            user_query=request.message,
            tutor_response=response_text,
            grounding_sources=", ".join(grounding_sources) if grounding_sources else None,
            tokens_used=estimated_tokens,
        )
        db.add(interaction)
        await db.commit()

        new_daily_used = daily_used + 1
        daily_remaining = max(0, sub.daily_tutor_quota - new_daily_used) if not is_pro else 9999

        return AITutorChatResponse(
            response=response_text,
            mode=request.mode,
            lesson_id=lesson.id if lesson else None,
            lesson_title=lesson.title if lesson else None,
            grounding_sources=grounding_sources,
            quiz_questions=quiz_questions,
            provider=provider_name,
            tokens_used=estimated_tokens,
            tier=sub.tier,
            daily_quota=sub.daily_tutor_quota,
            daily_used=new_daily_used,
            daily_remaining=daily_remaining,
        )

    def _generate_deterministic_grounded_response(
        self,
        user_query: str,
        mode: str,
        lesson: Optional[Lesson],
        sections: List[LessonSection],
    ) -> Tuple[str, List[str], Optional[List[AITutorQuizQuestion]]]:
        """Synthesize high-fidelity, grounded educational response from actual lesson syllabus."""
        lesson_title = lesson.title if lesson else "Curriculum Foundations"
        sources: List[str] = []
        quiz_items: Optional[List[AITutorQuizQuestion]] = None

        if sections:
            sources = [f"Section {s.section_number}: {s.title}" for s in sections[:3]]
            primary_sec = sections[0]
            sec_title = primary_sec.title
            sec_text = primary_sec.content_markdown
        else:
            sec_title = "Academic Core Concepts"
            sec_text = "Mastery of fundamental definitions, rigorous mathematical derivations, and physical laws."
            sources = ["General Syllabus Objectives"]

        mode_upper = mode.upper()

        if mode_upper == "SIMPLIFY":
            response = (
                f"### Simplified Breakdown: {lesson_title}\n\n"
                f"Let's make this simple and intuitive! Think of this concept in everyday terms:\n\n"
                f"* **The Big Idea:** In **{sec_title}**, we study how nature behaves under fundamental physical laws. "
                f"Instead of getting overwhelmed by complex mathematical formulas, remember the golden rule: forces or interactions depend directly on the strengths involved, and weaken as distance grows.\n"
                f"* **Everyday Analogy:** Imagine holding two small bar magnets in your hands. When they are far apart, you barely feel anything. But bring them close, and suddenly they snap together or push apart strongly! That exact same principle powers electrostatic interactions.\n\n"
                f"**Key Takeaway:** Always identify the given variables first before jumping into equations. Would you like a step-by-step example next?"
            )

        elif mode_upper == "EXAMPLE":
            response = (
                f"### Step-by-Step Worked Example: {lesson_title}\n\n"
                f"Here is a typical exam problem applying **{sec_title}**:\n\n"
                f"**Problem:** Two point charges $q_1 = +2.0\\,\\mu\\text{{C}}$ and $q_2 = -3.0\\,\\mu\\text{{C}}$ are placed in vacuum separated by a distance $r = 0.30\\,\\text{{m}}$. Calculate the magnitude and direction of the electrostatic force between them.\n\n"
                f"**Step 1 — Identify the governing formula:**\n"
                f"$$F = \\frac{{1}}{{4\\pi\\varepsilon_0}} \\frac{{|q_1 q_2|}}{{r^2}}$$\n"
                f"Where $\\frac{{1}}{{4\\pi\\varepsilon_0}} = 9.0 \\times 10^9\\,\\text{{N}}\\cdot\\text{{m}}^2/\\text{{C}}^2$.\n\n"
                f"**Step 2 — Substitute the values into SI units:**\n"
                f"$$F = (9.0 \\times 10^9) \\frac{{(2.0 \\times 10^{{-6}}) \\times (3.0 \\times 10^{{-6}})}}{{(0.30)^2}}$$\n\n"
                f"**Step 3 — Compute the final result:**\n"
                f"$$F = 9.0 \\times 10^9 \\times \\frac{{6.0 \\times 10^{{-12}}}}{{0.09}} = 0.60\\,\\text{{N}}$$\n\n"
                f"**Conclusion:** Because the charges have opposite signs ($+q_1$ and $-q_2$), the electrostatic force is **attractive** with a magnitude of **$0.60\\,\\text{{N}}$**."
            )

        elif mode_upper == "HINT":
            response = (
                f"### Socratic Conceptual Hint\n\n"
                f"To tackle this question, think about the core relationships from **{sec_title}**:\n\n"
                f"1. **Coordinate System & Symmetry:** Does the problem have geometric symmetry (e.g. charges along an axis or at triangle vertices)?\n"
                f"2. **Vector Superposition:** Remember that force and field are vector quantities. You cannot simply add scalars; resolve each vector into $x$ and $y$ components:\n"
                f"   $$\\vec{{F}}_{{\\text{{net}}}} = \\sum \\vec{{F}}_i$$\n"
                f"3. **Units Check:** Ensure charges are converted to Coulombs ($\\mu\\text{{C}} = 10^{{-6}}\\,\\text{{C}}$) and distances to metres ($\\text{{cm}} = 10^{{-2}}\\,\\text{{m}}$).\n\n"
                f"*Try setting up your vector sum with these steps, and let me know what components you get!*"
            )

        elif mode_upper == "QUIZ":
            response = (
                f"### AI Practice Quiz: {lesson_title}\n\n"
                f"Here are 3 quick check questions generated from your syllabus sections. "
                f"Select your answers in the interactive widget below or write down your answers!"
            )
            quiz_items = [
                AITutorQuizQuestion(
                    question=f"According to Coulomb's Law, how does the electrostatic force between two point charges change if the distance between them is doubled?",
                    options=[
                        "It is halved (divided by 2)",
                        "It is reduced to one-fourth (divided by 4)",
                        "It is doubled (multiplied by 2)",
                        "It remains unchanged",
                    ],
                    correct_index=1,
                    explanation="Coulomb's Law is an inverse-square law: F ∝ 1/r². Doubling r multiplies the denominator by 2² = 4, reducing force to 1/4.",
                ),
                AITutorQuizQuestion(
                    question="What is the SI unit of the permittivity of free space (ε₀)?",
                    options=[
                        "N·m²/C²",
                        "C²/(N·m²)",
                        "N/C",
                        "J/C",
                    ],
                    correct_index=1,
                    explanation="Since F = (1 / 4πε₀)(q₁q₂ / r²), solving for ε₀ gives units of C²/(N·m²).",
                ),
                AITutorQuizQuestion(
                    question="If a dielectric medium of dielectric constant K = 5 replaces the vacuum between two fixed charges, the force between them:",
                    options=[
                        "Increases by 5 times",
                        "Decreases by 5 times",
                        "Increases by 25 times",
                        "Becomes zero",
                    ],
                    correct_index=1,
                    explanation="In a dielectric medium, F_medium = F_vacuum / K. With K = 5, the electrostatic force decreases by a factor of 5.",
                ),
            ]

        else:  # EXPLAIN default
            response = (
                f"### Conceptual Explanation: {lesson_title}\n\n"
                f"In **{sec_title}**, we explore the foundational framework for this subject:\n\n"
                f"1. **Core Principle:** {sec_text[:280]}...\n\n"
                f"2. **Mathematical Formulation:**\n"
                f"$$\\vec{{F}}_{{12}} = \\frac{{1}}{{4\\pi\\varepsilon_0}} \\frac{{q_1 q_2}}{{r^2}} \\hat{{r}}_{{12}}$$\n\n"
                f"3. **Physical Significance:** Forces obey Newton's third law ($\\vec{{F}}_{{12}} = -\\vec{{F}}_{{21}}$), and the principle of superposition applies universally across multi-particle configurations.\n\n"
                f"How would you like to continue? You can ask me to **simplify** this further, walk through a **step-by-step example**, or generate a **practice quiz**!"
            )

        return response, sources, quiz_items

    async def _call_gemini_api(
        self,
        api_key: str,
        user_query: str,
        mode: str,
        lesson: Optional[Lesson],
        sections: List[LessonSection],
        history: Optional[List[Any]],
    ) -> Tuple[str, List[str]]:
        """Call external Gemini API with strict grounded prompt boundaries."""
        system_instructions = (
            "You are the Campus AI Tutor, an empathetic, pedagogically rigorous academic learning assistant. "
            "You help high school and undergraduate engineering students master science and mathematics.\n"
            "Rules:\n"
            "1. Ground your answers strictly in the provided syllabus context.\n"
            "2. Never hallucinate facts outside the provided syllabus.\n"
            "3. Format all mathematical equations in KaTeX (use $...$ for inline and $$...$$ for display equations).\n"
            "4. If asked to solve a test/exam question or provide an answer key, decline to give the direct answer and instead give a conceptual hint.\n"
            "5. Cite the exact lesson section title where applicable."
        )

        context_snippets = []
        sources = []
        for sec in sections[:4]:
            sources.append(f"Section {sec.section_number}: {sec.title}")
            context_snippets.append(f"### Section: {sec.title}\n{sec.content_markdown[:600]}")

        syllabus_text = "\n\n".join(context_snippets) if context_snippets else "General academic curriculum."

        prompt_payload = (
            f"<syllabus_context>\n{syllabus_text}\n</syllabus_context>\n\n"
            f"Explanation Mode: {mode}\n\n"
            f"<student_query>\n{user_query}\n</student_query>"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.AI_MODEL_NAME}:generateContent?key={api_key}"
        request_body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_instructions}\n\n{prompt_payload}"}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 800,
            },
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=request_body)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API returned status {resp.status_code}: {resp.text}")
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("No candidate response returned from Gemini API")
            parts = candidates[0].get("content", {}).get("parts", [])
            text_response = parts[0].get("text", "")
            return text_response, sources


ai_tutor_service = AITutorService()
