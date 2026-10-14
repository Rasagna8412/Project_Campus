"""Idempotent database seeding for roles and foundational curriculum taxonomy."""

import logging
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Role
from app.models.taxonomy import BoardCurriculum, GradeStage, Subject

logger = logging.getLogger(__name__)

INITIAL_ROLES: List[Tuple[str, str]] = [
    ("STUDENT", "Student learner with access to practice and personal analytics"),
    ("EDUCATOR", "Academic author with rights to draft educational content"),
    ("REVIEWER", "Senior educator with pedagogical content approval privileges"),
    ("ADMIN", "System administrator with platform and user management access"),
]

# Minimal approved seed taxonomy for Milestone 2 onboarding
SEED_CURRICULA = [
    {
        "code": "CBSE",
        "name": "Central Board of Secondary Education",
        "country_code": "IND",
        "description": "Indian National Secondary & Higher Secondary Board",
        "grades": [
            {
                "code": "CLASS_11",
                "name": "Class 11 (+1)",
                "display_order": 1,
                "subjects": [
                    ("PHYSICS", "Physics", 1),
                    ("CHEMISTRY", "Chemistry", 2),
                    ("MATHEMATICS", "Mathematics", 3),
                    ("BIOLOGY", "Biology", 4),
                ],
            },
            {
                "code": "CLASS_12",
                "name": "Class 12 (+2)",
                "display_order": 2,
                "subjects": [
                    ("PHYSICS", "Physics", 1),
                    ("CHEMISTRY", "Chemistry", 2),
                    ("MATHEMATICS", "Mathematics", 3),
                    ("BIOLOGY", "Biology", 4),
                ],
            },
        ],
    },
    {
        "code": "JEE_MAIN",
        "name": "JEE Main (Engineering Entrance)",
        "country_code": "IND",
        "description": "National Testing Agency Engineering Examination",
        "grades": [
            {
                "code": "CLASS_11",
                "name": "Class 11 (Foundation)",
                "display_order": 1,
                "subjects": [
                    ("PHYSICS", "Physics", 1),
                    ("CHEMISTRY", "Chemistry", 2),
                    ("MATHEMATICS", "Mathematics", 3),
                ],
            },
            {
                "code": "CLASS_12",
                "name": "Class 12 (Target)",
                "display_order": 2,
                "subjects": [
                    ("PHYSICS", "Physics", 1),
                    ("CHEMISTRY", "Chemistry", 2),
                    ("MATHEMATICS", "Mathematics", 3),
                ],
            },
        ],
    },
    {
        "code": "NEET",
        "name": "NEET UG (Medical Entrance)",
        "country_code": "IND",
        "description": "National Eligibility cum Entrance Test for Medical Programs",
        "grades": [
            {
                "code": "CLASS_11",
                "name": "Class 11 (Foundation)",
                "display_order": 1,
                "subjects": [
                    ("PHYSICS", "Physics", 1),
                    ("CHEMISTRY", "Chemistry", 2),
                    ("BIOLOGY", "Biology", 3),
                ],
            },
            {
                "code": "CLASS_12",
                "name": "Class 12 (Target)",
                "display_order": 2,
                "subjects": [
                    ("PHYSICS", "Physics", 1),
                    ("CHEMISTRY", "Chemistry", 2),
                    ("BIOLOGY", "Biology", 3),
                ],
            },
        ],
    },
]


async def seed_initial_data(session: AsyncSession) -> None:
    """Populate initial roles and curriculum taxonomy idempotently."""
    # 1. Seed Roles
    for role_name, role_desc in INITIAL_ROLES:
        existing = await session.execute(
            select(Role).where(Role.name == role_name)
        )
        if not existing.scalar_one_or_none():
            session.add(Role(name=role_name, description=role_desc))

    await session.flush()

    # 2. Seed Curricula, Grades, and Subjects
    for curr_data in SEED_CURRICULA:
        curr_res = await session.execute(
            select(BoardCurriculum).where(BoardCurriculum.code == curr_data["code"])
        )
        board = curr_res.scalar_one_or_none()
        if not board:
            board = BoardCurriculum(
                code=curr_data["code"],
                name=curr_data["name"],
                country_code=curr_data["country_code"],
                description=curr_data["description"],
            )
            session.add(board)
            await session.flush()

        for grade_data in curr_data["grades"]:
            grade_res = await session.execute(
                select(GradeStage).where(
                    GradeStage.board_id == board.id,
                    GradeStage.code == grade_data["code"],
                )
            )
            grade = grade_res.scalar_one_or_none()
            if not grade:
                grade = GradeStage(
                    board_id=board.id,
                    code=grade_data["code"],
                    name=grade_data["name"],
                    display_order=grade_data["display_order"],
                )
                session.add(grade)
                await session.flush()

            for sub_code, sub_name, sub_order in grade_data["subjects"]:
                sub_res = await session.execute(
                    select(Subject).where(
                        Subject.grade_stage_id == grade.id,
                        Subject.code == sub_code,
                    )
                )
                if not sub_res.scalar_one_or_none():
                    subject = Subject(
                        grade_stage_id=grade.id,
                        code=sub_code,
                        name=sub_name,
                        display_order=sub_order,
                    )
                    session.add(subject)

    await session.commit()
    logger.info("Foundational database seed completed successfully.")
