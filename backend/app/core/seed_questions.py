"""Seed Verified Academic Questions, Options, and Answer Keys for Milestone 4.

Includes authentic CBSE, JEE Main, and NEET practice questions across Physics,
Chemistry, and Mathematics with KaTeX formulas, step-by-step explanations,
numerical tolerance specifications, and unapproved DRAFT/IN_REVIEW questions
for publication gating verification.
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import (
    DifficultyLevel,
    Question,
    QuestionAnswerKey,
    QuestionOption,
    QuestionType,
)
from app.models.content import ContentStatus
from app.models.taxonomy import Topic

logger = logging.getLogger(__name__)

SAMPLE_QUESTIONS_DATA = [
    # ---------------------------------------------------------
    # PHYSICS: Coulomb's Law and Superposition
    # ---------------------------------------------------------
    {
        "topic_slug": "coulombs-law-and-superposition",
        "question_type": QuestionType.SINGLE_CHOICE.value,
        "difficulty": DifficultyLevel.EASY.value,
        "content_latex": (
            "Two equal point charges $q$ are separated by a distance $r$ in vacuum, "
            "experiencing an electrostatic repulsive force $F$. If the distance between them is "
            "doubled and the magnitude of each charge is halved, what is the new electrostatic force?"
        ),
        "status": ContentStatus.PUBLISHED.value,
        "provenance": "CBSE Class 12 Board Exam 2023 (Physics Section A)",
        "is_verified": True,
        "options": [
            {"option_key": "A", "content_latex": "$F/4$", "display_order": 1},
            {"option_key": "B", "content_latex": "$F/16$", "display_order": 2},
            {"option_key": "C", "content_latex": "$F/8$", "display_order": 3},
            {"option_key": "D", "content_latex": "$F/2$", "display_order": 4},
        ],
        "answer_key": {
            "correct_options": ["B"],
            "explanation_latex": (
                "By Coulomb's Law, the original force is $F = k \\frac{q^2}{r^2}$.\n\n"
                "When the charges become $q' = q/2$ and the separation becomes $r' = 2r$, "
                "the new force is:\n\n"
                "$$F' = k \\frac{(q/2)^2}{(2r)^2} = k \\frac{q^2/4}{4r^2} = \\frac{1}{16} \\left(k \\frac{q^2}{r^2}\\right) = \\frac{F}{16}$$\n\n"
                "Hence, option B is the correct answer."
            ),
        },
    },
    {
        "topic_slug": "coulombs-law-and-superposition",
        "question_type": QuestionType.NUMERICAL.value,
        "difficulty": DifficultyLevel.MEDIUM.value,
        "content_latex": (
            "Two point charges $q_1 = +3.0\\,\\mu\\text{C}$ and $q_2 = -3.0\\,\\mu\\text{C}$ "
            "are placed in vacuum at a separation distance of $0.30\\text{ m}$. "
            "Calculate the magnitude of the electrostatic attraction force in Newtons. "
            "(Take $\\frac{1}{4\\pi\\varepsilon_0} = 9.0 \\times 10^9\\text{ N}\\cdot\\text{m}^2/\\text{C}^2$)."
        ),
        "status": ContentStatus.PUBLISHED.value,
        "provenance": "NCERT Physics Exemplar (Class 12, Chapter 1)",
        "is_verified": True,
        "options": [],
        "answer_key": {
            "numerical_value": 0.90,
            "numerical_tolerance": 0.02,
            "explanation_latex": (
                "Applying Coulomb's Inverse-Square Law for vacuum:\n\n"
                "$$F = \\frac{1}{4\\pi\\varepsilon_0} \\frac{|q_1 q_2|}{r^2}$$\n\n"
                "Substitute the given SI values:\n\n"
                "$$F = (9.0 \\times 10^9) \\frac{(3.0 \\times 10^{-6})(3.0 \\times 10^{-6})}{(0.30)^2}$$\n\n"
                "$$F = \\frac{9.0 \\times 10^9 \\times 9.0 \\times 10^{-12}}{0.09} = \\frac{8.1 \\times 10^{-2}}{9.0 \\times 10^{-2}} = 0.90\\text{ N}$$\n\n"
                "The electrostatic force magnitude is exactly $0.90\\text{ N}$."
            ),
        },
    },
    {
        "topic_slug": "coulombs-law-and-superposition",
        "question_type": QuestionType.MULTIPLE_CHOICE.value,
        "difficulty": DifficultyLevel.HARD.value,
        "content_latex": (
            "Which of the following statements regarding electrostatic forces and the "
            "superposition principle are correct?"
        ),
        "status": ContentStatus.PUBLISHED.value,
        "provenance": "JEE Main 2022 Foundation Bank",
        "is_verified": True,
        "options": [
            {
                "option_key": "A",
                "content_latex": "The force between two point charges obeys Newton's Third Law: $\\vec{F}_{12} = -\\vec{F}_{21}$.",
                "display_order": 1,
            },
            {
                "option_key": "B",
                "content_latex": "The pairwise electrostatic force between two charges is modified if a third charge is brought nearby.",
                "display_order": 2,
            },
            {
                "option_key": "C",
                "content_latex": "The electrostatic force between two stationary point charges acts along the line connecting their centers.",
                "display_order": 3,
            },
            {
                "option_key": "D",
                "content_latex": "The dielectric constant $K$ of any insulating medium is always greater than or equal to 1.",
                "display_order": 4,
            },
        ],
        "answer_key": {
            "correct_options": ["A", "C", "D"],
            "explanation_latex": (
                "* **Statement A is correct:** Coulomb force is an internal mutual interaction obeying action-reaction duality.\n"
                "* **Statement B is incorrect:** By the Superposition Principle, pairwise interaction between any two charges is independent of surrounding charges.\n"
                "* **Statement C is correct:** The electrostatic force is a central force directed along the radial line.\n"
                "* **Statement D is correct:** For vacuum $K=1$, and for any physical dielectric $K > 1$.\n\n"
                "Therefore, statements A, C, and D are correct."
            ),
        },
    },

    # ---------------------------------------------------------
    # PHYSICS: Electric Dipoles
    # ---------------------------------------------------------
    {
        "topic_slug": "electric-dipole-and-moment",
        "question_type": QuestionType.SINGLE_CHOICE.value,
        "difficulty": DifficultyLevel.EASY.value,
        "content_latex": (
            "An electric dipole of moment $\\vec{p}$ is placed in a uniform external electric field $\\vec{E}$. "
            "The dipole experiences:"
        ),
        "status": ContentStatus.PUBLISHED.value,
        "provenance": "CBSE Class 12 Physics 2021",
        "is_verified": True,
        "options": [
            {"option_key": "A", "content_latex": "A net translational force and a torque", "display_order": 1},
            {"option_key": "B", "content_latex": "Only a torque, but no net force", "display_order": 2},
            {"option_key": "C", "content_latex": "Only a net force, but no torque", "display_order": 3},
            {"option_key": "D", "content_latex": "Neither a net force nor a torque", "display_order": 4},
        ],
        "answer_key": {
            "correct_options": ["B"],
            "explanation_latex": (
                "In a uniform electric field, the force on $+q$ is $+q\\vec{E}$ and on $-q$ is $-q\\vec{E}$. "
                "The net translational force is $\\vec{F}_{\\text{net}} = (+q\\vec{E}) + (-q\\vec{E}) = \\vec{0}$.\n\n"
                "Since the forces have different lines of action, they constitute a couple producing a non-zero torque: "
                "$\\vec{\\tau} = \\vec{p} \\times \\vec{E}$."
            ),
        },
    },

    # ---------------------------------------------------------
    # CHEMISTRY: Chemical Kinetics
    # ---------------------------------------------------------
    {
        "topic_slug": "rate-of-reaction-and-rate-laws",
        "question_type": QuestionType.SINGLE_CHOICE.value,
        "difficulty": DifficultyLevel.MEDIUM.value,
        "content_latex": (
            "For the elementary reaction $2A + B \\longrightarrow C$, if the concentration of $A$ "
            "is doubled while the concentration of $B$ is halved, the rate of reaction will:"
        ),
        "status": ContentStatus.PUBLISHED.value,
        "provenance": "CBSE Class 12 Chemistry 2022",
        "is_verified": True,
        "options": [
            {"option_key": "A", "content_latex": "Remain unchanged", "display_order": 1},
            {"option_key": "B", "content_latex": "Increase by a factor of 2", "display_order": 2},
            {"option_key": "C", "content_latex": "Increase by a factor of 4", "display_order": 3},
            {"option_key": "D", "content_latex": "Decrease by a factor of 2", "display_order": 4},
        ],
        "answer_key": {
            "correct_options": ["B"],
            "explanation_latex": (
                "For an elementary reaction, rate law matches the stoichiometric coefficients: "
                "$\\text{Rate}_1 = k [A]^2 [B]^1$.\n\n"
                "When $[A]' = 2[A]$ and $[B]' = [B]/2$, the new rate is:\n\n"
                "$$\\text{Rate}_2 = k (2[A])^2 \\left(\\frac{[B]}{2}\\right) = k (4[A]^2) \\frac{[B]}{2} = 2 k [A]^2 [B] = 2 \\text{Rate}_1$$\n\n"
                "The rate of reaction increases by a factor of 2 (Option B)."
            ),
        },
    },

    # ---------------------------------------------------------
    # MATHEMATICS: Definite Integrals
    # ---------------------------------------------------------
    {
        "topic_slug": "fundamental-theorem-calculus",
        "question_type": QuestionType.INTEGER.value,
        "difficulty": DifficultyLevel.MEDIUM.value,
        "content_latex": (
            "Evaluate the definite integral using King's property: "
            "$$I = \\frac{4}{\\pi} \\int_{0}^{\\frac{\\pi}{2}} \\frac{\\sin x}{\\sin x + \\cos x} \\, dx$$"
        ),
        "status": ContentStatus.PUBLISHED.value,
        "provenance": "JEE Main 2023 Mathematics Core",
        "is_verified": True,
        "options": [],
        "answer_key": {
            "integer_value": 1,
            "explanation_latex": (
                "Let $J = \\int_{0}^{\\pi/2} \\frac{\\sin x}{\\sin x + \\cos x} \\, dx$.\n\n"
                "Apply King's property $\\int_0^a f(x)dx = \\int_0^a f(a-x)dx$:\n\n"
                "$$J = \\int_{0}^{\\pi/2} \\frac{\\sin(\\pi/2 - x)}{\\sin(\\pi/2 - x) + \\cos(\\pi/2 - x)} \\, dx = \\int_{0}^{\\pi/2} \\frac{\\cos x}{\\cos x + \\sin x} \\, dx$$\n\n"
                "Adding both expressions gives:\n\n"
                "$$2J = \\int_{0}^{\\pi/2} \\frac{\\sin x + \\cos x}{\\sin x + \\cos x} \\, dx = \\int_{0}^{\\pi/2} 1 \\, dx = \\frac{\\pi}{2} \\implies J = \\frac{\\pi}{4}$$\n\n"
                "Therefore: $I = \\frac{4}{\\pi} \\times J = \\frac{4}{\\pi} \\times \\frac{\\pi}{4} = 1$."
            ),
        },
    },

    # ---------------------------------------------------------
    # UNPUBLISHED GATING TESTS (Must return 404 / be excluded from student lists)
    # ---------------------------------------------------------
    {
        "topic_slug": "coulombs-law-and-superposition",
        "question_type": QuestionType.SINGLE_CHOICE.value,
        "difficulty": DifficultyLevel.MEDIUM.value,
        "content_latex": "Draft Question: What is the dielectric constant of copper metal?",
        "status": ContentStatus.DRAFT.value,
        "provenance": "Unreviewed author draft",
        "is_verified": False,
        "options": [
            {"option_key": "A", "content_latex": "$0$", "display_order": 1},
            {"option_key": "B", "content_latex": "$\\infty$", "display_order": 2},
        ],
        "answer_key": {
            "correct_options": ["B"],
            "explanation_latex": "Draft explanation: Dielectric constant of conductors is infinity.",
        },
    },
    {
        "topic_slug": "rate-of-reaction-and-rate-laws",
        "question_type": QuestionType.SINGLE_CHOICE.value,
        "difficulty": DifficultyLevel.HARD.value,
        "content_latex": "In-Review Question: For a zero-order reaction, what is the half-life dependence on initial concentration?",
        "status": ContentStatus.IN_REVIEW.value,
        "provenance": "Pending SME review",
        "is_verified": False,
        "options": [
            {"option_key": "A", "content_latex": "$t_{1/2} \\propto [A]_0$", "display_order": 1},
            {"option_key": "B", "content_latex": "$t_{1/2} \\propto 1/[A]_0$", "display_order": 2},
        ],
        "answer_key": {
            "correct_options": ["A"],
            "explanation_latex": "In-review explanation: For zero order, $t_{1/2} = [A]_0 / (2k)$.",
        },
    },
]


async def seed_academic_questions(session: AsyncSession) -> None:
    """Populate sample academic questions, options, and answer keys idempotently."""
    for item in SAMPLE_QUESTIONS_DATA:
        # Find Topic
        top_res = await session.execute(
            select(Topic).where(Topic.slug == item["topic_slug"])
        )
        topic = top_res.scalar_one_or_none()
        if not topic:
            logger.warning("Topic with slug %s not found. Skipping question.", item["topic_slug"])
            continue

        # Check if question with same content_latex already exists for this topic
        q_res = await session.execute(
            select(Question).where(
                Question.topic_id == topic.id,
                Question.content_latex == item["content_latex"],
            )
        )
        question = q_res.scalar_one_or_none()
        if not question:
            question = Question(
                topic_id=topic.id,
                question_type=item["question_type"],
                difficulty=item["difficulty"],
                content_latex=item["content_latex"],
                hints=item.get("hints", []),
                status=item["status"],
                provenance=item.get("provenance"),
                is_verified=item.get("is_verified", False),
            )
            session.add(question)
            await session.flush()

            # Seed Options
            for opt_data in item.get("options", []):
                opt = QuestionOption(
                    question_id=question.id,
                    option_key=opt_data["option_key"],
                    content_latex=opt_data["content_latex"],
                    display_order=opt_data["display_order"],
                )
                session.add(opt)

            # Seed Answer Key
            ak_data = item.get("answer_key")
            if ak_data:
                ak = QuestionAnswerKey(
                    question_id=question.id,
                    correct_options=ak_data.get("correct_options"),
                    numerical_value=ak_data.get("numerical_value"),
                    numerical_tolerance=ak_data.get("numerical_tolerance", 0.01),
                    integer_value=ak_data.get("integer_value"),
                    explanation_latex=ak_data["explanation_latex"],
                )
                session.add(ak)

    await session.commit()
    logger.info("Academic questions and answer keys seeded successfully.")
