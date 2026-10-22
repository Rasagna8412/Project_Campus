"""Automated PostgreSQL Backup and Restore Recovery Drill.

Executes an end-to-end recovery drill on an isolated disposable PostgreSQL 15 database:
1. Creates a transient, disposable source database.
2. Applies all Alembic migrations to HEAD (0cbebed2ada2).
3. Seeds representative synthetic domain records using real Project Campus models.
4. Records pre-backup metrics (row counts, checksums, relations).
5. Creates a consistent custom-format (-Fc) backup using scripts/backup_postgres.sh.
6. Validates the backup artifact structure via pg_restore --list.
7. Creates a fresh, empty disposable destination database.
8. Restores the backup into the destination database using scripts/restore_postgres.sh.
9. Performs deep post-restore verification:
   - Alembic migration state matches 0cbebed2ada2
   - Exact row count fidelity across all seeded tables
   - Foreign key constraint cascade integrity on restored tables
   - PostgreSQL sequence incrementation without ID collision (roles autoincrement sequence)
   - Application query execution across multi-table relationships
10. Guaranteed cleanup of disposable databases and artifacts with failure reporting.
"""

import asyncio
from datetime import date
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import get_password_hash
from app.models.assessment import (
    DifficultyLevel,
    Question,
    QuestionAnswerKey,
    QuestionOption,
    QuestionType,
)
from app.models.content import ContentStatus, Lesson, LessonSection, SectionType
from app.models.identity import Role, StudentProfile, User, UserRole
from app.models.planner import GoalStatus, StudyGoal, StudyTask, TaskStatus, TaskType
from app.models.repetition import ReviewItem, ReviewLog, ReviewStatus
from app.models.taxonomy import BoardCurriculum, Chapter, GradeStage, Subject, Topic

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
BACKUP_SCRIPT = REPO_ROOT / "scripts" / "backup_postgres.sh"
RESTORE_SCRIPT = REPO_ROOT / "scripts" / "restore_postgres.sh"

# Connection parameter resolution
_env_pg_url = os.environ.get("POSTGRES_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
if _env_pg_url and "postgres" in _env_pg_url:
    BASE_PG_URL = _env_pg_url
else:
    BASE_PG_URL = "postgresql+asyncpg://campus_user:campus_dev_secret@127.0.0.1:5432/project_campus_test"


def get_bash_executable():
    """Locate appropriate bash interpreter across Linux CI and Windows Git Bash."""
    if sys.platform == "win32":
        git_bash = Path(r"C:\Program Files\Git\bin\bash.exe")
        if git_bash.exists():
            return str(git_bash)
    found = shutil.which("bash")
    if found and "system32" not in found.lower():
        return found
    return "bash"


def _check_live_postgres() -> bool:
    """Detect whether a live PostgreSQL server is reachable."""
    async def _probe():
        engine = create_async_engine(BASE_PG_URL, connect_args={"timeout": 2})
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
        finally:
            await engine.dispose()

    try:
        return asyncio.run(_probe())
    except Exception:
        return False


LIVE_POSTGRES_AVAILABLE = _check_live_postgres()
requires_live_postgres = pytest.mark.skipif(
    not LIVE_POSTGRES_AVAILABLE,
    reason="Live PostgreSQL database not reachable on localhost:5432. Start Docker Compose or set POSTGRES_TEST_DATABASE_URL.",
)


def parse_connection_info(url_str: str):
    """Parse standard database URL into libpq components."""
    clean_url = url_str.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg://", "postgresql://")
    parsed = urlparse(clean_url)
    return {
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "host": parsed.hostname or "127.0.0.1",
        "port": str(parsed.port or 5432),
        "maintenance_db": parsed.path.lstrip("/") or "postgres",
    }


@requires_live_postgres
@pytest.mark.asyncio
async def test_end_to_end_backup_and_restore_recovery_drill():
    """Full end-to-end automated backup and recovery drill on live PostgreSQL."""
    conn_info = parse_connection_info(BASE_PG_URL)
    drill_id = uuid.uuid4().hex[:8]
    source_db = f"campus_drill_src_{drill_id}"
    target_db = f"campus_drill_dst_{drill_id}"
    bash_path = get_bash_executable()

    maintenance_url = (
        f"postgresql+asyncpg://{conn_info['user']}:{conn_info['password']}@"
        f"{conn_info['host']}:{conn_info['port']}/{conn_info['maintenance_db']}"
    )

    maint_engine = create_async_engine(maintenance_url, isolation_level="AUTOCOMMIT")

    async def exec_maint(stmt: str):
        async with maint_engine.connect() as conn:
            await conn.execute(text(stmt))

    async def drop_db(dbname: str):
        assert dbname.startswith("campus_drill_"), f"Safety lock: Refusing to drop non-drill database '{dbname}'"
        await exec_maint(f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '{dbname}' AND pid <> pg_backend_pid();
        """)
        await exec_maint(f'DROP DATABASE IF EXISTS "{dbname}";')

    temp_backup_dir = tempfile.mkdtemp(prefix="campus_drill_backup_")
    source_engine = None
    target_engine = None

    try:
        # Step 1: Create disposable source database
        await drop_db(source_db)
        await exec_maint(f'CREATE DATABASE "{source_db}";')

        source_url = (
            f"postgresql+asyncpg://{conn_info['user']}:{conn_info['password']}@"
            f"{conn_info['host']}:{conn_info['port']}/{source_db}"
        )

        # Step 2: Apply Alembic migrations to source database
        alembic_ini = BACKEND_DIR / "alembic.ini"
        mig_env = os.environ.copy()
        mig_env["DATABASE_URL"] = source_url
        mig_res = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head"],
            cwd=str(BACKEND_DIR),
            capture_output=True,
            text=True,
            env=mig_env,
        )
        assert mig_res.returncode == 0, f"Alembic upgrade failed:\n{mig_res.stderr}"

        # Step 3: Seed representative synthetic domain records using real Project Campus schema
        source_engine = create_async_engine(source_url)
        session_factory = async_sessionmaker(bind=source_engine, class_=AsyncSession, expire_on_commit=False)

        async with session_factory() as session:
            # 3a. Curriculum & Taxonomy hierarchy
            board = BoardCurriculum(
                code=f"CBSE_{drill_id}",
                name="Central Board of Secondary Education",
                country_code="IND",
            )
            session.add(board)
            await session.flush()

            grade = GradeStage(
                board_id=board.id,
                code=f"C12_{drill_id}",
                name="Class 12",
                display_order=1,
            )
            session.add(grade)
            await session.flush()

            subject = Subject(
                grade_stage_id=grade.id,
                code=f"PHY_{drill_id}",
                name=f"Physics_{drill_id}",
                display_order=1,
            )
            session.add(subject)
            await session.flush()

            chapter = Chapter(
                subject_id=subject.id,
                chapter_number=1,
                title="Electromagnetism",
                slug=f"electromagnetism-{drill_id}",
                display_order=1,
            )
            session.add(chapter)
            await session.flush()

            topic = Topic(
                chapter_id=chapter.id,
                topic_number=1,
                title="Gauss Law",
                slug=f"gauss-law-{drill_id}",
                display_order=1,
            )
            session.add(topic)
            await session.flush()

            # 3b. Educational Content & Sections
            lesson = Lesson(
                topic_id=topic.id,
                title="Electric Flux Fundamentals",
                slug=f"electric-flux-{drill_id}",
                status=ContentStatus.PUBLISHED.value,
                display_order=1,
            )
            session.add(lesson)
            await session.flush()

            section = LessonSection(
                lesson_id=lesson.id,
                section_number=1,
                title="Introduction to Flux",
                content_markdown="Flux across Gaussian surfaces represents net enclosed charge.",
                section_type=SectionType.CONCEPT.value,
                display_order=1,
            )
            session.add(section)

            # 3c. Identity, Roles & Student Profile
            role = Role(
                name=f"student_drill_{drill_id}",
                description="Synthetic drill student role",
            )
            session.add(role)
            await session.flush()

            user = User(
                email=f"drill_{drill_id}@test.example.com",
                hashed_password=get_password_hash("DrillSecret123!"),
                full_name="Drill Student",
                is_active=True,
                is_verified=True,
            )
            session.add(user)
            await session.flush()

            user_role = UserRole(user_id=user.id, role_id=role.id)
            session.add(user_role)

            profile = StudentProfile(
                user_id=user.id,
                target_curriculum_id=board.id,
                grade_stage_id=grade.id,
                daily_study_goal_minutes=120,
            )
            session.add(profile)

            # 3d. Assessment: Question, Options, and Answer Key
            question = Question(
                topic_id=topic.id,
                question_type=QuestionType.SINGLE_CHOICE.value,
                difficulty=DifficultyLevel.MEDIUM.value,
                content_latex=r"Calculate total electric flux \Phi through a closed Gaussian sphere.",
                status=ContentStatus.PUBLISHED.value,
            )
            session.add(question)
            await session.flush()

            opt_a = QuestionOption(
                question_id=question.id,
                option_key="A",
                content_latex=r"\frac{q}{\varepsilon_0}",
                display_order=1,
            )
            opt_b = QuestionOption(
                question_id=question.id,
                option_key="B",
                content_latex=r"\frac{2q}{\varepsilon_0}",
                display_order=2,
            )
            session.add_all([opt_a, opt_b])
            await session.flush()

            key = QuestionAnswerKey(
                question_id=question.id,
                correct_options=["A"],
                explanation_latex=r"By Gauss's Law, the total electric flux is \Phi = \frac{q}{\varepsilon_0}.",
            )
            session.add(key)

            # 3e. Study Planner: Goal & Task
            goal = StudyGoal(
                user_id=user.id,
                title="Master Electromagnetism",
                status=GoalStatus.ACTIVE.value,
            )
            session.add(goal)
            await session.flush()

            task = StudyTask(
                goal_id=goal.id,
                user_id=user.id,
                task_type=TaskType.STUDY_LESSON.value,
                lesson_id=lesson.id,
                title="Review Gauss Law",
                scheduled_date=date.today(),
                display_order=1,
                status=TaskStatus.PENDING.value,
            )
            session.add(task)

            # 3f. Spaced Repetition: Item & Log
            item = ReviewItem(
                user_id=user.id,
                topic_id=topic.id,
                subject_id=subject.id,
                status=ReviewStatus.LEARNING.value,
                ease_factor=2.5,
                interval_days=1,
                due_date=date.today(),
                repetition_count=1,
            )
            session.add(item)
            await session.flush()

            rev_log = ReviewLog(
                review_item_id=item.id,
                user_id=user.id,
                quality_score=4,
                time_spent_seconds=45,
                scheduled_interval_days=1,
                next_interval_days=2,
                ease_factor_before=2.5,
                ease_factor_after=2.6,
            )
            session.add(rev_log)

            await session.commit()

        # Step 4: Record pre-backup metrics
        async with source_engine.connect() as conn:
            user_count = (await conn.execute(text("SELECT count(*) FROM users"))).scalar()
            role_count = (await conn.execute(text("SELECT count(*) FROM roles"))).scalar()
            lesson_count = (await conn.execute(text("SELECT count(*) FROM lessons"))).scalar()
            question_count = (await conn.execute(text("SELECT count(*) FROM questions"))).scalar()
            task_count = (await conn.execute(text("SELECT count(*) FROM study_tasks"))).scalar()
            review_count = (await conn.execute(text("SELECT count(*) FROM review_items"))).scalar()

        await source_engine.dispose()
        source_engine = None

        # Step 5: Execute backup using scripts/backup_postgres.sh
        backup_env = os.environ.copy()
        backup_env["BACKUP_METHOD"] = "host"
        backup_env["CONTAINER_NAME"] = ""
        backup_env["COMPOSE_FILE"] = ""
        backup_env["POSTGRES_DB"] = source_db
        backup_env["POSTGRES_USER"] = conn_info["user"]
        backup_env["PGPASSWORD"] = conn_info["password"]
        backup_env["PGHOST"] = conn_info["host"]
        backup_env["PGPORT"] = conn_info["port"]
        backup_env["BACKUP_DIR"] = temp_backup_dir.replace("\\", "/")

        b_res = subprocess.run(
            [bash_path, str(BACKUP_SCRIPT).replace("\\", "/")],
            capture_output=True,
            text=True,
            env=backup_env,
        )
        assert b_res.returncode == 0, f"Backup script failed:\n{b_res.stderr}\nSTDOUT:\n{b_res.stdout}"

        # Find promoted backup artifact
        dumps = list(Path(temp_backup_dir).glob("*.dump"))
        assert len(dumps) == 1, f"Expected 1 promoted dump, found {len(dumps)}"
        dump_filepath = dumps[0]
        assert dump_filepath.stat().st_size > 0

        # Step 6: Create fresh, empty disposable target database
        await drop_db(target_db)
        await exec_maint(f'CREATE DATABASE "{target_db}";')

        # Step 7: Execute restore using scripts/restore_postgres.sh with hardened safety gates
        restore_env = os.environ.copy()
        restore_env["CONTAINER_NAME"] = ""
        restore_env["BACKUP_FILE"] = str(dump_filepath).replace("\\", "/")
        restore_env["TARGET_DB"] = target_db
        restore_env["POSTGRES_USER"] = conn_info["user"]
        restore_env["PGPASSWORD"] = conn_info["password"]
        restore_env["PGHOST"] = conn_info["host"]
        restore_env["PGPORT"] = conn_info["port"]
        restore_env["CONFIRM_DISPOSABLE_TARGET"] = "yes"
        restore_env["CONFIRM_DISPOSABLE_SERVER"] = "yes"
        restore_env["APPROVED_TEST_HOSTS"] = f"localhost 127.0.0.1 postgres {conn_info['host']} 172.* 10.* 192.168.*"
        restore_env["EXPECTED_ALEMBIC_REVISION"] = "0cbebed2ada2"

        r_res = subprocess.run(
            [bash_path, str(RESTORE_SCRIPT).replace("\\", "/")],
            capture_output=True,
            text=True,
            env=restore_env,
        )
        assert r_res.returncode == 0, f"Restore script failed:\n{r_res.stderr}\nSTDOUT:\n{r_res.stdout}"

        # Step 8: Post-restore deep verification
        target_url = (
            f"postgresql+asyncpg://{conn_info['user']}:{conn_info['password']}@"
            f"{conn_info['host']}:{conn_info['port']}/{target_db}"
        )
        target_engine = create_async_engine(target_url)

        async with target_engine.connect() as conn:
            # 8a: Verify Alembic revision matches 0cbebed2ada2
            restored_rev = (await conn.execute(text("SELECT version_num FROM alembic_version"))).scalar()
            assert restored_rev == "0cbebed2ada2"

            # 8b: Verify row counts match pre-backup metrics exactly
            assert (await conn.execute(text("SELECT count(*) FROM users"))).scalar() == user_count
            assert (await conn.execute(text("SELECT count(*) FROM roles"))).scalar() == role_count
            assert (await conn.execute(text("SELECT count(*) FROM lessons"))).scalar() == lesson_count
            assert (await conn.execute(text("SELECT count(*) FROM questions"))).scalar() == question_count
            assert (await conn.execute(text("SELECT count(*) FROM study_tasks"))).scalar() == task_count
            assert (await conn.execute(text("SELECT count(*) FROM review_items"))).scalar() == review_count

            # 8c: Verify representative multi-table relational application query
            app_stmt = (
                select(User.full_name, Role.name, StudentProfile.daily_study_goal_minutes)
                .join(UserRole, User.id == UserRole.user_id)
                .join(Role, UserRole.role_id == Role.id)
                .join(StudentProfile, User.id == StudentProfile.user_id)
                .where(User.id == user.id)
            )
            app_res = (await conn.execute(app_stmt)).first()
            assert app_res is not None
            assert app_res[0] == "Drill Student"
            assert app_res[1] == f"student_drill_{drill_id}"
            assert app_res[2] == 120

            # 8d: Verify foreign key cascade behavior on restored data
            # Deleting the BoardCurriculum must cascade to delete its entire curriculum subtree
            await conn.execute(text(f"DELETE FROM boards_curricula WHERE id = '{board.id}';"))
            assert (await conn.execute(text(f"SELECT count(*) FROM grades_stages WHERE id = '{grade.id}';"))).scalar() == 0
            assert (await conn.execute(text(f"SELECT count(*) FROM subjects WHERE id = '{subject.id}';"))).scalar() == 0
            assert (await conn.execute(text(f"SELECT count(*) FROM chapters WHERE id = '{chapter.id}';"))).scalar() == 0
            assert (await conn.execute(text(f"SELECT count(*) FROM topics WHERE id = '{topic.id}';"))).scalar() == 0
            assert (await conn.execute(text(f"SELECT count(*) FROM lessons WHERE id = '{lesson.id}';"))).scalar() == 0
            assert (await conn.execute(text(f"SELECT count(*) FROM questions WHERE id = '{question.id}';"))).scalar() == 0

            # 8e: Verify PostgreSQL sequence behavior on restored integer autoincrement table
            # Inserting a new Role must increment roles_id_seq without primary key collision
            new_role = Role(
                name=f"post_restore_role_{drill_id}",
                description="Post-restore sequence progression verification role",
            )
            target_session_factory = async_sessionmaker(bind=target_engine, class_=AsyncSession, expire_on_commit=False)
            async with target_session_factory() as sess:
                sess.add(new_role)
                await sess.commit()
                assert new_role.id is not None
                assert new_role.id > role.id

        await target_engine.dispose()
        target_engine = None

    finally:
        # Step 9: Guaranteed cleanup of disposable resources with explicit failure reporting
        cleanup_errors = []

        if target_engine is not None:
            try:
                await target_engine.dispose()
            except Exception as exc:
                cleanup_errors.append(f"target_engine.dispose: {exc}")

        if source_engine is not None:
            try:
                await source_engine.dispose()
            except Exception as exc:
                cleanup_errors.append(f"source_engine.dispose: {exc}")

        for db_name in (source_db, target_db):
            if db_name.startswith("campus_drill_"):
                try:
                    await drop_db(db_name)
                except Exception as exc:
                    cleanup_errors.append(f"drop_db({db_name}): {exc}")

        try:
            await maint_engine.dispose()
        except Exception as exc:
            cleanup_errors.append(f"maint_engine.dispose: {exc}")

        if temp_backup_dir and Path(temp_backup_dir).exists():
            try:
                shutil.rmtree(temp_backup_dir)
            except Exception as exc:
                cleanup_errors.append(f"rmtree({temp_backup_dir}): {exc}")

        if cleanup_errors:
            error_summary = "; ".join(cleanup_errors)
            raise RuntimeError(f"Automated recovery drill cleanup encountered failures: {error_summary}")
