"""Tests for Curriculum Content, Lessons, and Section Delivery."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.content import ContentStatus, Lesson, LessonSection, SectionType
from app.models.taxonomy import GradeStage, Subject, Topic, Chapter


@pytest.mark.asyncio
async def test_get_curricula_includes_subjects(client: AsyncClient):
    """Verify that curricula listing returns boards, grades, and subjects."""
    response = await client.get("/api/v1/curricula/")
    assert response.status_code == 200
    boards = response.json()
    assert len(boards) > 0

    cbse = next((b for b in boards if b["code"] == "CBSE"), None)
    assert cbse is not None
    class_12 = next((g for g in cbse["grades"] if g["code"] == "CLASS_12"), None)
    assert class_12 is not None
    subject_codes = [s["code"] for s in class_12["subjects"]]
    assert "PHYSICS" in subject_codes
    assert "CHEMISTRY" in subject_codes
    assert "MATHEMATICS" in subject_codes


@pytest.mark.asyncio
async def test_get_subject_chapters_and_topics(client: AsyncClient, db_session):
    """Verify retrieval of chapters and topics with published lesson counts."""
    stmt = (
        select(Subject)
        .join(GradeStage)
        .where(
            GradeStage.code == "CLASS_12",
            Subject.code == "PHYSICS",
        )
    )
    res = await db_session.execute(stmt)
    physics = res.scalars().first()
    assert physics is not None

    response = await client.get(f"/api/v1/curricula/subjects/{physics.id}/chapters")
    assert response.status_code == 200
    chapters = response.json()
    assert len(chapters) >= 1

    first_ch = chapters[0]
    assert first_ch["chapter_number"] == 1
    assert "topics" in first_ch
    assert len(first_ch["topics"]) >= 1

    topic = first_ch["topics"][0]
    assert "published_lessons_count" in topic
    assert topic["published_lessons_count"] >= 1


@pytest.mark.asyncio
async def test_get_subject_chapters_not_found(client: AsyncClient):
    """Verify 404 response for nonexistent subject ID."""
    random_id = uuid.uuid4()
    response = await client.get(f"/api/v1/curricula/subjects/{random_id}/chapters")
    assert response.status_code == 404
    assert response.json()["detail"] == "Subject not found"


@pytest.mark.asyncio
async def test_get_chapter_topics(client: AsyncClient, db_session):
    """Verify retrieval of topics for a specific chapter."""
    stmt = select(Chapter).limit(1)
    res = await db_session.execute(stmt)
    chapter = res.scalar_one_or_none()
    assert chapter is not None

    response = await client.get(f"/api/v1/curricula/chapters/{chapter.id}/topics")
    assert response.status_code == 200
    topics = response.json()
    assert len(topics) >= 1
    assert topics[0]["chapter_id"] == str(chapter.id)
    assert "published_lessons_count" in topics[0]


@pytest.mark.asyncio
async def test_get_chapter_topics_not_found(client: AsyncClient):
    """Verify 404 response for nonexistent chapter ID."""
    random_id = uuid.uuid4()
    response = await client.get(f"/api/v1/curricula/chapters/{random_id}/topics")
    assert response.status_code == 404
    assert response.json()["detail"] == "Chapter not found"


@pytest.mark.asyncio
async def test_get_topic_lessons_only_published(client: AsyncClient, db_session):
    """Verify that topic lessons listing only returns published content."""
    stmt = select(Topic).where(Topic.slug == "coulombs-law-and-superposition")
    res = await db_session.execute(stmt)
    topic = res.scalar_one_or_none()
    assert topic is not None

    response = await client.get(f"/api/v1/curricula/topics/{topic.id}/lessons")
    assert response.status_code == 200
    lessons = response.json()
    assert len(lessons) >= 1

    for l in lessons:
        assert l["status"] == ContentStatus.PUBLISHED.value
        assert l["topic_id"] == str(topic.id)
        assert "learning_objectives" in l
        assert len(l["learning_objectives"]) > 0


@pytest.mark.asyncio
async def test_draft_lessons_excluded_from_topic_listing(client: AsyncClient, db_session):
    """Verify that draft and in-review lessons are excluded from student-facing topic lesson lists."""
    stmt = select(Topic).where(Topic.slug == "coulombs-law-and-superposition")
    res = await db_session.execute(stmt)
    topic = res.scalar_one_or_none()
    assert topic is not None

    # Verify directly in DB that PUBLISHED, DRAFT, and IN_REVIEW lessons exist for this topic
    stmt_lessons = select(Lesson).where(Lesson.topic_id == topic.id)
    all_lessons = (await db_session.execute(stmt_lessons)).scalars().all()
    statuses = {l.status for l in all_lessons}
    assert ContentStatus.PUBLISHED.value in statuses
    assert ContentStatus.DRAFT.value in statuses
    assert ContentStatus.IN_REVIEW.value in statuses

    # Now verify via API endpoint: strictly only PUBLISHED lessons are returned
    response = await client.get(f"/api/v1/curricula/topics/{topic.id}/lessons")
    assert response.status_code == 200
    public_lessons = response.json()

    assert len(public_lessons) >= 1
    for pub_l in public_lessons:
        assert pub_l["status"] == ContentStatus.PUBLISHED.value
        assert "Draft" not in pub_l["title"]
        assert "In Review" not in pub_l["title"]


@pytest.mark.asyncio
async def test_get_lesson_detail_with_ordered_sections(client: AsyncClient, db_session):
    """Verify detailed view of a published lesson with properly ordered sections."""
    stmt = select(Lesson).where(
        Lesson.slug == "coulombs-law-and-superposition-principle",
        Lesson.status == ContentStatus.PUBLISHED.value,
    )
    res = await db_session.execute(stmt)
    lesson = res.scalar_one_or_none()
    assert lesson is not None

    response = await client.get(f"/api/v1/curricula/lessons/{lesson.id}")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(lesson.id)
    assert data["title"] == lesson.title
    assert data["status"] == ContentStatus.PUBLISHED.value
    assert len(data["sections"]) >= 4

    # Verify sections are in ascending order
    orders = [s["display_order"] for s in data["sections"]]
    assert orders == sorted(orders)

    # Verify section types include required types
    sec_types = [s["section_type"] for s in data["sections"]]
    assert SectionType.CONCEPT.value in sec_types
    assert SectionType.KEY_FORMULA.value in sec_types
    assert SectionType.WORKED_EXAMPLE.value in sec_types

    # Verify LaTeX math is preserved in section content
    formula_sec = next(s for s in data["sections"] if s["section_type"] == SectionType.KEY_FORMULA.value)
    assert "\\vec{F}" in formula_sec["content_markdown"] or "q_1" in formula_sec["content_markdown"]


@pytest.mark.asyncio
async def test_draft_lesson_detail_returns_404(client: AsyncClient, db_session):
    """Verify that attempting to fetch a DRAFT lesson detail strictly returns 404."""
    stmt = select(Lesson).where(Lesson.status == ContentStatus.DRAFT.value)
    res = await db_session.execute(stmt)
    draft_lesson = res.scalar_one_or_none()
    assert draft_lesson is not None

    response = await client.get(f"/api/v1/curricula/lessons/{draft_lesson.id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_in_review_lesson_detail_returns_404(client: AsyncClient, db_session):
    """Verify that attempting to fetch an IN_REVIEW lesson detail strictly returns 404."""
    stmt = select(Lesson).where(Lesson.status == ContentStatus.IN_REVIEW.value)
    res = await db_session.execute(stmt)
    in_review_lesson = res.scalar_one_or_none()
    assert in_review_lesson is not None

    response = await client.get(f"/api/v1/curricula/lessons/{in_review_lesson.id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_nonexistent_lesson_detail_returns_404(client: AsyncClient):
    """Verify 404 for completely random lesson ID."""
    random_id = uuid.uuid4()
    response = await client.get(f"/api/v1/curricula/lessons/{random_id}")
    assert response.status_code == 404
