"""Проекция занятия по роли смотрящего: одно место, где решается, кто что видит. Без БД.

Репетитор видит всё. Родитель и ученик видят занятие, только если в нём участвует
свой ребёнок или сам ученик; у остальных участников — только имя. Ученик не видит
ставку и комментарий для родителя, заметки репетитора не видит никто, кроме него.
"""
from dataclasses import dataclass
from typing import Optional

from app.models import File, HomeworkStatus, Lesson, LessonStatus, LessonStudent, Role
from app.schemas import lesson as schemas
from app.schemas.file import FileInfo


@dataclass(frozen=True)
class Access:
    role: str
    student_ids: Optional[frozenset[int]]  # None — репетитор, ему видны все ученики

    def can_see(self, student_id: int) -> bool:
        return self.student_ids is None or student_id in self.student_ids

    def allows(self, lesson: Lesson) -> bool:
        """Занятие доступно, если смотрит репетитор или в нём участвует «свой» ученик."""
        return self.student_ids is None or any(self.can_see(student_id=item.student_id) for item in lesson.participants)


TUTOR_ACCESS = Access(role=Role.TUTOR, student_ids=None)


def to_file_info(file: File) -> FileInfo:
    return FileInfo(
        id=file.id,
        original_name=file.original_name,
        size=file.size,
        mime=file.mime,
        created_at=file.created_at,
    )


def _participant(item: LessonStudent, access: Access) -> schemas.LessonParticipant:
    if not access.can_see(student_id=item.student_id):
        return schemas.LessonParticipant(student_id=item.student_id, full_name=item.student.user.full_name)
    return schemas.LessonParticipant(
        student_id=item.student_id,
        full_name=item.student.user.full_name,
        price=item.price if access.role != Role.STUDENT else None,
        homework_status=item.homework_status,
        homework_grade=item.homework_grade,
    )


def _common_format(lesson: Lesson) -> Optional[str]:
    formats = {item.student.format for item in lesson.participants}
    return formats.pop() if len(formats) == 1 else None


def _homework_pending(lesson: Lesson, access: Access) -> bool:
    """Плашка «домашка не сделана»: занятие проведено, у своего ученика статус не «сделано»."""
    if lesson.status != LessonStatus.HELD or access.student_ids is None:
        return False
    return any(
        item.student_id in access.student_ids and item.homework_status != HomeworkStatus.DONE
        for item in lesson.participants
    )


def visible_student_ids(lesson: Lesson, access: Access) -> list[int]:
    return [item.student_id for item in lesson.participants if access.can_see(student_id=item.student_id)]


def project_short(lesson: Lesson, access: Access, title: str) -> schemas.LessonShort:
    return schemas.LessonShort(
        id=lesson.id,
        series_id=lesson.series_id,
        scheduled_start=lesson.scheduled_start,
        duration_minutes=lesson.duration_minutes,
        status=lesson.status,
        detached=lesson.detached,
        topic=lesson.topic,
        title=title,
        format=_common_format(lesson=lesson),
        participants=[_participant(item=item, access=access) for item in lesson.participants],
        homework_pending=_homework_pending(lesson=lesson, access=access),
        has_homework=bool(lesson.homework_text.strip()) or bool(lesson.files),
    )


def project_full(lesson: Lesson, access: Access, title: str, previous_grade: Optional[int]) -> schemas.Lesson:
    return schemas.Lesson(
        **project_short(lesson=lesson, access=access, title=title).model_dump(),
        original_start=lesson.original_start,
        homework_text=lesson.homework_text,
        homework_saved_at=lesson.homework_saved_at,
        parent_comment=lesson.parent_comment if access.role != Role.STUDENT else None,
        tutor_notes=lesson.tutor_notes if access.role == Role.TUTOR else None,
        files=[to_file_info(file=item) for item in lesson.files],
        previous_grade=previous_grade,
    )
