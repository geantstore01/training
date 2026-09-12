"""Schéma central SQLAlchemy 2.0. Aucun contenu personnel brut dans les traces IA."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean, CheckConstraint, Computed, DateTime, ForeignKey,
    ForeignKeyConstraint, Index, Integer, LargeBinary, MetaData, Numeric,
    String, Text, UniqueConstraint, text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    })


class Record:
    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


class Scoped(Record):
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), index=True)


def scope(*constraints):
    return (UniqueConstraint("tenant_id", "id"), *constraints)


def ref(column, table, target="id", ondelete="RESTRICT"):
    return ForeignKeyConstraint(["tenant_id", column], [f"{table}.tenant_id", f"{table}.{target}"], ondelete=ondelete)


def choice(column, values):
    return CheckConstraint(f"{column} IN ({','.join(repr(x) for x in values.split())})", name=f"{column}_values")


class ScienceRun(Scoped, Base):
    __tablename__ = "science_runs"
    student_id: Mapped[UUID]
    request_id: Mapped[UUID]
    chapter: Mapped[str] = mapped_column(String(20))
    setting: Mapped[str] = mapped_column(String(40))
    notebook_ciphertext: Mapped[bytes] = mapped_column(LargeBinary)
    observation: Mapped[dict] = mapped_column(JSONB)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = scope(ref("student_id", "students", ondelete="CASCADE"),
        UniqueConstraint("tenant_id", "student_id", "request_id"),
        choice("chapter", "matiere digestion circuits terre"))


class Tenant(Record, Base):
    __tablename__ = "tenants"
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), server_default="active")
    __table_args__ = (choice("status", "active suspended closing"),)


class User(Scoped, Base):
    __tablename__ = "users"
    # Login pseudonyme possible pour les élèves, aucune adresse électronique obligatoire.
    login: Mapped[str] = mapped_column(String(254))
    email_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)
    password_hash: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), server_default="pending")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    auth_version: Mapped[int] = mapped_column(server_default="1")
    __table_args__ = scope(UniqueConstraint("tenant_id", "login"), choice("status", "pending active locked deleted"),
        CheckConstraint("login = lower(login) AND length(login) >= 3", name="normalized_login"),
        CheckConstraint("auth_version > 0", name="auth_version_positive"))


class UserRole(Scoped, Base):
    __tablename__ = "user_roles"
    user_id: Mapped[UUID]
    role: Mapped[str] = mapped_column(String(20))
    __table_args__ = scope(ref("user_id", "users", ondelete="CASCADE"), UniqueConstraint("tenant_id", "user_id", "role"),
        choice("role", "student parent teacher school_admin content_creator sys_admin"))


class Guardian(Scoped, Base):
    __tablename__ = "guardians"
    user_id: Mapped[UUID]
    identity_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = scope(ref("user_id", "users"), UniqueConstraint("tenant_id", "user_id"))


class Student(Scoped, Base):
    __tablename__ = "students"
    user_id: Mapped[UUID]
    pseudonym: Mapped[str] = mapped_column(String(80))
    identity_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)
    curriculum_level_id: Mapped[UUID] = mapped_column(ForeignKey("curriculum_levels.id"))
    # Pas de date de naissance exacte ni d'informations médicales.
    accessibility_preferences: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    __table_args__ = scope(ref("user_id", "users"), UniqueConstraint("tenant_id", "user_id"),
        CheckConstraint("jsonb_typeof(accessibility_preferences) = 'object'", name="preferences_object"))


class GuardianStudent(Scoped, Base):
    __tablename__ = "guardian_students"
    guardian_id: Mapped[UUID]
    student_id: Mapped[UUID]
    relationship: Mapped[str] = mapped_column(String(20))
    authority_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_by: Mapped[UUID | None]
    verification_evidence_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = scope(ref("guardian_id", "guardians"), ref("student_id", "students"),
        ref("verified_by", "users"), UniqueConstraint("tenant_id", "guardian_id", "student_id"), choice("relationship", "parent legal_guardian"),
        CheckConstraint("revoked_at IS NULL OR (authority_verified_at IS NOT NULL AND revoked_at >= authority_verified_at)", name="revocation_order"))


class Teacher(Scoped, Base):
    __tablename__ = "teachers"
    user_id: Mapped[UUID]
    display_name: Mapped[str] = mapped_column(String(120))
    __table_args__ = scope(ref("user_id", "users"), UniqueConstraint("tenant_id", "user_id"))


class School(Scoped, Base):
    __tablename__ = "schools"
    name: Mapped[str] = mapped_column(String(200))
    uai: Mapped[str | None] = mapped_column(String(8))
    __table_args__ = scope(UniqueConstraint("tenant_id", "uai"), UniqueConstraint("tenant_id"),
        CheckConstraint("id = tenant_id", name="school_is_tenant"))


class Class(Scoped, Base):
    __tablename__ = "classes"
    school_id: Mapped[UUID]
    name: Mapped[str] = mapped_column(String(80))
    academic_year: Mapped[int]
    curriculum_level_id: Mapped[UUID | None] = mapped_column(ForeignKey("curriculum_levels.id"))
    __table_args__ = scope(ref("school_id", "schools"), UniqueConstraint("tenant_id", "school_id", "name", "academic_year"),
        CheckConstraint("academic_year BETWEEN 2020 AND 2200", name="year_range"))


class TeacherClass(Scoped, Base):
    __tablename__ = "teacher_classes"
    teacher_id: Mapped[UUID]
    class_id: Mapped[UUID]
    __table_args__ = scope(ref("teacher_id", "teachers"), ref("class_id", "classes"), UniqueConstraint("tenant_id", "teacher_id", "class_id"))


class Enrollment(Scoped, Base):
    __tablename__ = "enrollments"
    student_id: Mapped[UUID]
    class_id: Mapped[UUID]
    starts_on: Mapped[date]
    ends_on: Mapped[date | None]
    __table_args__ = scope(ref("student_id", "students"), ref("class_id", "classes"),
        UniqueConstraint("tenant_id", "student_id", "class_id", "starts_on"),
        CheckConstraint("ends_on IS NULL OR ends_on >= starts_on", name="date_order"),
        Index("uq_enrollments_active", "tenant_id", "student_id", "class_id", unique=True, postgresql_where=text("ends_on IS NULL")))


class Subject(Record, Base):
    __tablename__ = "subjects"
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))


class CurriculumLevel(Record, Base):
    __tablename__ = "curriculum_levels"
    code: Mapped[str] = mapped_column(String(3), unique=True)
    cycle: Mapped[int] = mapped_column(server_default="3")
    __table_args__ = (choice("code", "CM1 CM2"), CheckConstraint("cycle = 3", name="cycle_three"))


class CurriculumDomain(Record, Base):
    __tablename__ = "curriculum_domains"
    subject_id: Mapped[UUID] = mapped_column(ForeignKey("subjects.id"))
    code: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(200))
    __table_args__ = (UniqueConstraint("subject_id", "code"), UniqueConstraint("id", "subject_id"))


class Competency(Record, Base):
    __tablename__ = "competencies"
    domain_id: Mapped[UUID | None]
    objectives: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    common_errors: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    subject_id: Mapped[UUID] = mapped_column(ForeignKey("subjects.id"), index=True)
    curriculum_level_id: Mapped[UUID] = mapped_column(ForeignKey("curriculum_levels.id"), index=True)
    code: Mapped[str] = mapped_column(String(80))
    label: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    official_reference_url: Mapped[str] = mapped_column(Text)
    programme_version: Mapped[str] = mapped_column(String(80))
    effective_from: Mapped[date]
    effective_until: Mapped[date | None]
    __table_args__ = (ForeignKeyConstraint(["domain_id", "subject_id"], ["curriculum_domains.id", "curriculum_domains.subject_id"]),
        CheckConstraint("jsonb_typeof(objectives) = 'array' AND jsonb_typeof(common_errors) = 'array'", name="pedagogy_arrays"),
        UniqueConstraint("code", "programme_version"), CheckConstraint("effective_until IS NULL OR effective_until >= effective_from", name="validity_order"))


class CompetencyPrerequisite(Record, Base):
    __tablename__ = "competency_prerequisites"
    competency_id: Mapped[UUID] = mapped_column(ForeignKey("competencies.id"))
    prerequisite_id: Mapped[UUID] = mapped_column(ForeignKey("competencies.id"))
    __table_args__ = (UniqueConstraint("competency_id", "prerequisite_id"), CheckConstraint("competency_id <> prerequisite_id", name="no_self_dependency"),)


class Lesson(Scoped, Base):
    __tablename__ = "lessons"
    kind: Mapped[str] = mapped_column(String(30), server_default="lesson")
    slug: Mapped[str] = mapped_column(String(160))
    author_id: Mapped[UUID]
    __table_args__ = scope(ref("author_id", "users"), UniqueConstraint("tenant_id", "slug"), choice("kind", "lesson teaching_sheet learning_sequence"))


class LessonVersion(Scoped, Base):
    __tablename__ = "lesson_versions"
    editor_id: Mapped[UUID | None]
    review_round: Mapped[int] = mapped_column(server_default="0")
    lesson_id: Mapped[UUID]
    version: Mapped[int]
    title: Mapped[str] = mapped_column(String(240))
    body: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), server_default="draft")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = scope(ref("lesson_id", "lessons"), ref("editor_id", "users"), CheckConstraint("review_round >= 0", name="review_round_positive"), UniqueConstraint("tenant_id", "lesson_id", "version"),
        CheckConstraint("version > 0", name="positive_version"), choice("status", "draft pending_review approved archived"),
        CheckConstraint("(status = 'approved' AND published_at IS NOT NULL) OR (status IN ('draft','pending_review') AND published_at IS NULL) OR status = 'archived'", name="publication_date"),
        Index("uq_lesson_one_approved", "tenant_id", "lesson_id", unique=True, postgresql_where=text("status = 'approved'")))


class LessonCompetency(Scoped, Base):
    __tablename__ = "lesson_competencies"
    lesson_version_id: Mapped[UUID]
    competency_id: Mapped[UUID] = mapped_column(ForeignKey("competencies.id"))
    __table_args__ = scope(ref("lesson_version_id", "lesson_versions"), UniqueConstraint("tenant_id", "lesson_version_id", "competency_id"))


class Exercise(Scoped, Base):
    __tablename__ = "exercises"
    slug: Mapped[str] = mapped_column(String(160))
    author_id: Mapped[UUID]
    __table_args__ = scope(ref("author_id", "users"), UniqueConstraint("tenant_id", "slug"))


class ExerciseVersion(Scoped, Base):
    __tablename__ = "exercise_versions"
    pipeline_report: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    exercise_id: Mapped[UUID]
    version: Mapped[int]
    kind: Mapped[str] = mapped_column(String(30))
    prompt: Mapped[dict] = mapped_column(JSONB)
    # Accès réservé aux services de correction, jamais transmis par DTO élève.
    answer_spec: Mapped[dict] = mapped_column(JSONB)
    validator_name: Mapped[str] = mapped_column(String(120))
    validator_version: Mapped[str] = mapped_column(String(40))
    difficulty: Mapped[int]
    status: Mapped[str] = mapped_column(String(20), server_default="draft")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = scope(ref("exercise_id", "exercises"), UniqueConstraint("tenant_id", "exercise_id", "version"),
        CheckConstraint("version > 0 AND difficulty BETWEEN 1 AND 5", name="version_difficulty"),
        choice("kind", "multiple_choice integer decimal fraction short_text ordering matching fill_blanks step_problem timeline"), choice("status", "draft in_review published retired"),
        CheckConstraint("(status IN ('published','retired')) = (published_at IS NOT NULL)", name="publication_date"))


class ExerciseCompetency(Scoped, Base):
    __tablename__ = "exercise_competencies"
    exercise_version_id: Mapped[UUID]
    competency_id: Mapped[UUID] = mapped_column(ForeignKey("competencies.id"))
    weight: Mapped[Decimal] = mapped_column(Numeric(6, 5), server_default="1")
    __table_args__ = scope(ref("exercise_version_id", "exercise_versions"), UniqueConstraint("tenant_id", "exercise_version_id", "competency_id"), CheckConstraint("weight > 0 AND weight <= 1", name="weight_range"))


class LearningSession(Scoped, Base):
    __tablename__ = "learning_sessions"
    student_id: Mapped[UUID]
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), server_default="active")
    __table_args__ = scope(ref("student_id", "students"), UniqueConstraint("tenant_id", "id", "student_id"), choice("status", "active completed abandoned"),
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="time_order"),
        CheckConstraint("(status = 'active') = (ended_at IS NULL)", name="session_end"))


class ExerciseAttempt(Scoped, Base):
    __tablename__ = "exercise_attempts"
    submission_digest: Mapped[str | None] = mapped_column(String(64))
    assessment_result: Mapped[dict | None] = mapped_column(JSONB)
    student_id: Mapped[UUID]
    session_id: Mapped[UUID]
    exercise_version_id: Mapped[UUID]
    idempotency_key: Mapped[UUID]
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    score: Mapped[Decimal | None] = mapped_column(Numeric(6, 5))
    max_hint_level: Mapped[int] = mapped_column(server_default="0")
    __table_args__ = scope(ref("student_id", "students"), ref("exercise_version_id", "exercise_versions"),
        ForeignKeyConstraint(["tenant_id", "session_id", "student_id"], ["learning_sessions.tenant_id", "learning_sessions.id", "learning_sessions.student_id"]),
        UniqueConstraint("tenant_id", "idempotency_key"),
        UniqueConstraint("tenant_id", "id", "student_id", "exercise_version_id", name="uq_attempt_evidence_scope"),
        CheckConstraint("score BETWEEN 0 AND 1", name="score_range"), CheckConstraint("max_hint_level BETWEEN 0 AND 6", name="hint_range"),
        CheckConstraint("submitted_at IS NULL OR submitted_at >= started_at", name="time_order"),
        CheckConstraint("score IS NULL OR submitted_at IS NOT NULL", name="scored_submission"),
        Index("ix_attempts_student_time", "tenant_id", "student_id", "started_at"))


class Answer(Scoped, Base):
    __tablename__ = "answers"
    attempt_id: Mapped[UUID]
    part_key: Mapped[str] = mapped_column(String(80))
    response_ciphertext: Mapped[bytes] = mapped_column(LargeBinary)
    is_correct: Mapped[bool | None]
    feedback_code: Mapped[str | None] = mapped_column(String(80))
    __table_args__ = scope(ref("attempt_id", "exercise_attempts", ondelete="CASCADE"), UniqueConstraint("tenant_id", "attempt_id", "part_key"))


class Hint(Scoped, Base):
    __tablename__ = "hints"
    exercise_version_id: Mapped[UUID]
    level: Mapped[int]
    body: Mapped[dict] = mapped_column(JSONB)
    __table_args__ = scope(ref("exercise_version_id", "exercise_versions"), UniqueConstraint("tenant_id", "exercise_version_id", "level"), CheckConstraint("level BETWEEN 0 AND 6", name="level_range"))


class MasteryRecord(Scoped, Base):
    __tablename__ = "mastery_records"
    evaluation_level: Mapped[str] = mapped_column(String(20), server_default="non_evalué")
    student_id: Mapped[UUID]
    competency_id: Mapped[UUID] = mapped_column(ForeignKey("competencies.id"))
    probability: Mapped[Decimal] = mapped_column(Numeric(6, 5))
    evidence_count: Mapped[int] = mapped_column(server_default="0")
    algorithm_version: Mapped[str] = mapped_column(String(40))
    last_assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revision: Mapped[int] = mapped_column(server_default="1")
    __table_args__ = scope(ref("student_id", "students"), choice("evaluation_level", "non_evalué découverte en_cours fragile maîtrisé consolidé"), UniqueConstraint("tenant_id", "student_id", "competency_id"),
        CheckConstraint("probability BETWEEN 0 AND 1 AND evidence_count >= 0 AND revision > 0", name="mastery_range"))
    __mapper_args__ = {"version_id_col": revision}


class SpacedRepetitionItem(Scoped, Base):
    __tablename__ = "spaced_repetition_items"
    student_id: Mapped[UUID]
    competency_id: Mapped[UUID] = mapped_column(ForeignKey("competencies.id"))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    interval_days: Mapped[int] = mapped_column(server_default="0")
    ease_factor: Mapped[Decimal] = mapped_column(Numeric(5, 3), server_default="2.5")
    repetitions: Mapped[int] = mapped_column(server_default="0")
    algorithm_version: Mapped[str] = mapped_column(String(40))
    __table_args__ = scope(ref("student_id", "students"), UniqueConstraint("tenant_id", "student_id", "competency_id"),
        CheckConstraint("interval_days >= 0 AND ease_factor >= 1 AND repetitions >= 0", name="schedule_range"),
        Index("ix_repetition_due", "tenant_id", "student_id", "due_at"))


class AIInteraction(Scoped, Base):
    __tablename__ = "ai_interactions"
    student_id: Mapped[UUID]
    session_id: Mapped[UUID]
    request_id: Mapped[UUID]
    provider: Mapped[str] = mapped_column(String(20))
    model: Mapped[str] = mapped_column(String(120))
    prompt_template_version: Mapped[str] = mapped_column(String(80))
    hint_level: Mapped[int]
    input_tokens: Mapped[int] = mapped_column(server_default="0")
    output_tokens: Mapped[int] = mapped_column(server_default="0")
    cost_eur: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), server_default="0")
    latency_ms: Mapped[int]
    outcome: Mapped[str] = mapped_column(String(20))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    __table_args__ = scope(ref("student_id", "students"),
        ForeignKeyConstraint(["tenant_id", "session_id", "student_id"], ["learning_sessions.tenant_id", "learning_sessions.id", "learning_sessions.student_id"]),
        UniqueConstraint("tenant_id", "request_id"), choice("provider", "local cloud"), choice("outcome", "completed blocked failed fallback"),
        CheckConstraint("hint_level BETWEEN 0 AND 6 AND input_tokens >= 0 AND output_tokens >= 0 AND cost_eur >= 0 AND latency_ms >= 0", name="metrics_range"),
        CheckConstraint("expires_at > created_at", name="retention_order"))


class SafetyEvent(Scoped, Base):
    __tablename__ = "safety_events"
    interaction_id: Mapped[UUID | None]
    request_id: Mapped[UUID | None]
    student_id: Mapped[UUID | None]
    layer: Mapped[int]
    category: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(20))
    action: Mapped[str] = mapped_column(String(20))
    rule_version: Mapped[str] = mapped_column(String(80))
    # Codes uniquement, pas de copie du message de l'enfant.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    __table_args__ = scope(ref("interaction_id", "ai_interactions"), ref("student_id", "students"), CheckConstraint("layer BETWEEN 1 AND 10", name="layer_range"),
        choice("severity", "info low medium high critical"), choice("action", "allow redact block escalate"), CheckConstraint("expires_at > created_at", name="retention_order"))


class ContentSource(Scoped, Base):
    __tablename__ = "content_sources"
    title: Mapped[str] = mapped_column(String(240))
    url: Mapped[str] = mapped_column(Text)
    publisher: Mapped[str] = mapped_column(String(200))
    license: Mapped[str] = mapped_column(Text)
    checksum_sha256: Mapped[str] = mapped_column(String(64))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[UUID | None]
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = scope(ref("approved_by", "users"), UniqueConstraint("tenant_id", "checksum_sha256"),
        CheckConstraint("checksum_sha256 ~ '^[a-f0-9]{64}$'", name="sha256_format"),
        CheckConstraint("(approved_by IS NULL) = (approved_at IS NULL)", name="approval_pair"))


class ContentChunk(Scoped, Base):
    __tablename__ = "content_chunks"
    source_id: Mapped[UUID]
    ordinal: Mapped[int]
    body: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    embedding_model: Mapped[str | None] = mapped_column(String(120))
    search_vector: Mapped[str] = mapped_column(TSVECTOR, Computed("to_tsvector('french'::regconfig, body)", persisted=True))
    __table_args__ = scope(ref("source_id", "content_sources"), UniqueConstraint("tenant_id", "source_id", "ordinal"),
        CheckConstraint("ordinal >= 0", name="ordinal_range"), CheckConstraint("(embedding IS NULL) = (embedding_model IS NULL)", name="embedding_pair"),
        Index("ix_chunks_fts", "search_vector", postgresql_using="gin"),
        Index("ix_chunks_vector", "embedding", postgresql_using="hnsw", postgresql_ops={"embedding": "vector_cosine_ops"}))


class ContentReview(Scoped, Base):
    __tablename__ = "content_reviews"
    review_round: Mapped[int | None]
    lesson_version_id: Mapped[UUID | None]
    exercise_version_id: Mapped[UUID | None]
    reviewer_id: Mapped[UUID]
    decision: Mapped[str] = mapped_column(String(20))
    reason_code: Mapped[str] = mapped_column(String(80))
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    __table_args__ = scope(ref("lesson_version_id", "lesson_versions"), ref("exercise_version_id", "exercise_versions"), ref("reviewer_id", "users"),
        CheckConstraint("num_nonnulls(lesson_version_id, exercise_version_id) = 1", name="exactly_one_target"), choice("decision", "approved rejected changes_requested"))


class AuditLog(Scoped, Base):
    __tablename__ = "audit_logs"
    actor_id: Mapped[UUID | None]
    action: Mapped[str] = mapped_column(String(120))
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[UUID | None]
    correlation_id: Mapped[UUID]
    outcome: Mapped[str] = mapped_column(String(20))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    __table_args__ = scope(ref("actor_id", "users"), choice("outcome", "success denied failure"),
        CheckConstraint("expires_at > created_at", name="retention_order"), Index("ix_audit_time", "tenant_id", "created_at"))


class ConsentRecord(Scoped, Base):
    __tablename__ = "consent_records"
    student_id: Mapped[UUID]
    guardian_id: Mapped[UUID]
    purpose: Mapped[str] = mapped_column(String(80))
    policy_version: Mapped[str] = mapped_column(String(40))
    legal_basis: Mapped[str] = mapped_column(String(30))
    granted: Mapped[bool]
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_ciphertext: Mapped[bytes] = mapped_column(LargeBinary)
    event_type: Mapped[str] = mapped_column(String(20), server_default="legacy")
    recorded_by: Mapped[UUID | None]
    supersedes_id: Mapped[UUID | None]
    revision: Mapped[int] = mapped_column(server_default="1")
    __table_args__ = scope(ForeignKeyConstraint(["tenant_id", "guardian_id", "student_id"],
        ["guardian_students.tenant_id", "guardian_students.guardian_id", "guardian_students.student_id"]),
        ref("recorded_by", "users"), ref("supersedes_id", "consent_records"),
        choice("event_type", "legacy grant refuse withdraw"),
        CheckConstraint("revision > 0", name="revision_positive"),
        CheckConstraint("event_type = 'legacy' OR (recorded_by IS NOT NULL AND withdrawn_at IS NULL AND legal_basis = 'consent' AND granted = (event_type = 'grant'))", name="event_consistency"),
        UniqueConstraint("tenant_id", "student_id", "guardian_id", "purpose", "revision", name="uq_consent_stream_revision"),
        choice("legal_basis", "consent public_task legal_obligation contract"),
        CheckConstraint("withdrawn_at IS NULL OR (granted AND withdrawn_at >= recorded_at)", name="withdrawal_order"),
        CheckConstraint("expires_at IS NULL OR expires_at > recorded_at", name="expiry_order"),
        Index("ix_consent_lookup", "tenant_id", "student_id", "purpose", "recorded_at"))


class StudentAssent(Scoped, Base):
    __tablename__ = "student_assents"
    student_id: Mapped[UUID]
    recorded_by: Mapped[UUID]
    purpose: Mapped[str] = mapped_column(String(80))
    policy_version: Mapped[str] = mapped_column(String(40))
    agreed: Mapped[bool]
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("clock_timestamp()"))
    __table_args__ = scope(ref("student_id", "students"), ref("recorded_by", "users"),
        Index("ix_assent_lookup", "tenant_id", "student_id", "purpose", "recorded_at"))


class LearningGroup(Scoped, Base):
    __tablename__ = "learning_groups"
    class_id: Mapped[UUID]
    name: Mapped[str] = mapped_column(String(80))
    competency_id: Mapped[UUID | None] = mapped_column(ForeignKey("competencies.id"))
    __table_args__ = scope(ref("class_id", "classes"), UniqueConstraint("tenant_id", "class_id", "name"))


class GroupMember(Scoped, Base):
    __tablename__ = "group_members"
    group_id: Mapped[UUID]
    student_id: Mapped[UUID]
    __table_args__ = scope(ref("group_id", "learning_groups"), ref("student_id", "students"), UniqueConstraint("tenant_id", "group_id", "student_id"))


class LessonSource(Scoped, Base):
    __tablename__ = "lesson_sources"
    lesson_version_id: Mapped[UUID]
    source_id: Mapped[UUID]
    __table_args__ = scope(ref("lesson_version_id", "lesson_versions"), ref("source_id", "content_sources"), UniqueConstraint("tenant_id", "lesson_version_id", "source_id"))


class ExerciseSource(Scoped, Base):
    __tablename__ = "exercise_sources"
    exercise_version_id: Mapped[UUID]
    source_id: Mapped[UUID]
    __table_args__ = scope(ref("exercise_version_id", "exercise_versions"), ref("source_id", "content_sources"), UniqueConstraint("tenant_id", "exercise_version_id", "source_id"))


class MasteryEvidence(Scoped, Base):
    __tablename__ = "mastery_evidence"
    attempt_id: Mapped[UUID]
    student_id: Mapped[UUID]
    exercise_version_id: Mapped[UUID]
    competency_id: Mapped[UUID] = mapped_column(ForeignKey("competencies.id"))
    applied: Mapped[bool]
    correct: Mapped[bool]
    reason: Mapped[str] = mapped_column(String(30))
    probability_before: Mapped[Decimal] = mapped_column(Numeric(6, 5))
    probability_after: Mapped[Decimal] = mapped_column(Numeric(6, 5))
    algorithm_version: Mapped[str] = mapped_column(String(40))
    __table_args__ = scope(
        ForeignKeyConstraint(["tenant_id", "attempt_id", "student_id", "exercise_version_id"],
            ["exercise_attempts.tenant_id", "exercise_attempts.id", "exercise_attempts.student_id", "exercise_attempts.exercise_version_id"]),
        UniqueConstraint("tenant_id", "attempt_id", "competency_id"),
        CheckConstraint("probability_before BETWEEN 0 AND 1 AND probability_after BETWEEN 0 AND 1", name="probabilities"),
        choice("reason", "independent repeated assisted unrecognized"),
        Index("ix_evidence_repeat", "tenant_id", "student_id", "competency_id", "exercise_version_id", "created_at"))


class RagDocument(Scoped, Base):
    __tablename__ = "rag_documents"
    page_selection: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(240))
    checksum: Mapped[str] = mapped_column(String(64))
    version: Mapped[int]
    level: Mapped[str] = mapped_column(String(3))
    subject: Mapped[str] = mapped_column(String(30))
    history_chapter: Mapped[str | None] = mapped_column(String(40))
    programme_version: Mapped[str] = mapped_column(String(80))
    effective_from: Mapped[date]
    effective_until: Mapped[date | None]
    status: Mapped[str] = mapped_column(String(20), server_default="draft")
    created_by: Mapped[UUID]
    approved_by: Mapped[UUID | None]
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = scope(ref("created_by", "users"),
        ForeignKeyConstraint(["tenant_id", "approved_by"], ["users.tenant_id", "users.id"], ondelete="RESTRICT", name="fk_rag_approved_user"),
        UniqueConstraint("tenant_id", "url", "level", "subject", "version", name="uq_rag_document_version"),
        choice("status", "draft pending_review approved archived"), choice("level", "CM1 CM2"),
        choice("subject", "francais mathematiques histoire sciences"),
        CheckConstraint("history_chapter IS NULL OR (subject='histoire' AND level='CM2' AND history_chapter IN ('ferry','republique','industrie','guerre-14','guerre-39','europe'))", name="history_scope"),
        CheckConstraint("version > 0 AND checksum ~ '^[a-f0-9]{64}$'", name="snapshot"),
        CheckConstraint("effective_until IS NULL OR effective_until >= effective_from", name="dates"),
        CheckConstraint("(approved_by IS NULL) = (approved_at IS NULL) AND (status <> 'approved' OR approved_by IS NOT NULL)", name="approval"))


class RagPassage(Scoped, Base):
    __tablename__ = "rag_passages"
    document_id: Mapped[UUID]
    ordinal: Mapped[int]
    body: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(Vector(768))
    embedding_model: Mapped[str] = mapped_column(String(100))
    search_vector: Mapped[str] = mapped_column(TSVECTOR, Computed("to_tsvector('french', body)", persisted=True))
    __table_args__ = scope(ref("document_id", "rag_documents"), UniqueConstraint("tenant_id", "document_id", "ordinal"),
        CheckConstraint("ordinal >= 0 AND length(body) BETWEEN 1 AND 1800", name="bounds"),
        Index("ix_rag_search", "search_vector", postgresql_using="gin"),
        Index("ix_rag_vector", "embedding", postgresql_using="hnsw", postgresql_ops={"embedding": "vector_cosine_ops"}))


class RagReview(Scoped, Base):
    __tablename__ = "rag_reviews"
    document_id: Mapped[UUID]
    reviewer_id: Mapped[UUID]
    decision: Mapped[str] = mapped_column(String(20))
    reason_code: Mapped[str] = mapped_column(String(50))
    __table_args__ = scope(ref("document_id", "rag_documents"), ref("reviewer_id", "users"), choice("decision", "approved rejected"))


class TutorTurn(Scoped, Base):
    __tablename__ = "tutor_turns"
    attempt_id: Mapped[UUID]
    request_id: Mapped[UUID]
    request_digest: Mapped[str] = mapped_column(String(64))
    level: Mapped[int]
    response: Mapped[dict] = mapped_column(JSONB)
    passage_ids: Mapped[list] = mapped_column(JSONB)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = scope(ref("attempt_id", "exercise_attempts"), UniqueConstraint("tenant_id", "attempt_id", "request_id"),
        CheckConstraint("level BETWEEN 0 AND 6", name="level"),
        Index("ix_tutor_history", "tenant_id", "attempt_id", "created_at"))


class Mission(Scoped, Base):
    __tablename__ = "missions"
    class_id: Mapped[UUID]
    group_id: Mapped[UUID | None]
    author_id: Mapped[UUID]
    title: Mapped[str] = mapped_column(String(160))
    day: Mapped[date]
    status: Mapped[str] = mapped_column(String(20), server_default="published")
    __table_args__ = scope(ref("class_id", "classes"), ref("group_id", "learning_groups"), ref("author_id", "users"), choice("status", "published archived"))


class MissionExercise(Scoped, Base):
    __tablename__ = "mission_exercises"
    mission_id: Mapped[UUID]
    exercise_version_id: Mapped[UUID]
    ordinal: Mapped[int]
    __table_args__ = scope(ref("mission_id", "missions"), ref("exercise_version_id", "exercise_versions"),
        UniqueConstraint("tenant_id", "mission_id", "exercise_version_id"), CheckConstraint("ordinal >= 0", name="ordinal"))


class FeatureFlag(Scoped, Base):
    __tablename__ = "feature_flags"
    key: Mapped[str] = mapped_column(String(40))
    enabled: Mapped[bool]
    changed_by: Mapped[UUID]
    revision: Mapped[int] = mapped_column(server_default="1")
    __table_args__ = scope(ref("changed_by", "users"), UniqueConstraint("tenant_id", "key"),
        choice("key", "missions speech notifications"), CheckConstraint("revision > 0", name="revision"))


class SafetyCase(Scoped, Base):
    __tablename__ = "safety_cases"
    event_id: Mapped[UUID]
    reviewer_id: Mapped[UUID]
    resolution: Mapped[str] = mapped_column(String(40))
    __table_args__ = scope(ref("event_id", "safety_events",ondelete="CASCADE"), ref("reviewer_id", "users"),
        UniqueConstraint("tenant_id", "event_id"), choice("resolution", "reviewed escalated false_positive"))


class BackgroundJob(Scoped, Base):
    __tablename__ = "background_jobs"
    requested_by: Mapped[UUID]
    kind: Mapped[str] = mapped_column(String(40))
    idempotency_key: Mapped[UUID]
    payload: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), server_default="queued")
    attempts: Mapped[int] = mapped_column(server_default="0")
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    error_code: Mapped[str | None] = mapped_column(String(80))
    result: Mapped[dict | None] = mapped_column(JSONB)
    __table_args__ = scope(ref("requested_by", "users"), UniqueConstraint("tenant_id", "idempotency_key"),
        choice("kind", "weekly_reports difficulty_alerts exercise_batch privacy_purge"),
        choice("status", "queued completed failed"), CheckConstraint("attempts BETWEEN 0 AND 5", name="attempts"),
        Index("ix_jobs_ready", "status", "available_at"))


class Notification(Scoped, Base):
    __tablename__ = "notifications"
    recipient_id: Mapped[UUID]
    student_id: Mapped[UUID]
    kind: Mapped[str] = mapped_column(String(40))
    period: Mapped[date]
    body: Mapped[dict] = mapped_column(JSONB)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = scope(ref("recipient_id", "users"), ref("student_id", "students"),
        UniqueConstraint("tenant_id", "recipient_id", "student_id", "kind", "period", name="uq_notification_period"),
        choice("kind", "weekly_report difficulty_alert"))

class JobDispatch(Record, Base):
    """Enveloppes globales sans contenu personnel, destinées uniquement au worker."""
    __tablename__ = "job_dispatch"
    school_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id",ondelete="RESTRICT"))
    job_id: Mapped[UUID] = mapped_column(unique=True)
    ready_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=text("now()"),index=True)
    __table_args__ = (ForeignKeyConstraint(["school_id","job_id"],["background_jobs.tenant_id","background_jobs.id"],ondelete="CASCADE"),)


class TutorControl(Scoped, Base):
    __tablename__ = "tutor_controls"
    student_id: Mapped[UUID]
    enabled: Mapped[bool] = mapped_column(Boolean,server_default=text("true"))
    max_help: Mapped[int] = mapped_column(Integer,server_default=text("6"))
    changed_by: Mapped[UUID]
    revision: Mapped[int] = mapped_column(Integer,server_default=text("1"))
    __table_args__ = scope(ref("student_id","students"),ref("changed_by","users"),UniqueConstraint("tenant_id","student_id"),CheckConstraint("max_help BETWEEN 0 AND 6",name="help_range"),CheckConstraint("revision >= 1",name="control_revision"))
