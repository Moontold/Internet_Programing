"""Статистика домашних заданий ученика. Чистая функция: на входе счётчики из БД."""
from dataclasses import dataclass
from typing import Optional

from app.schemas.student import StudentStats


@dataclass(frozen=True)
class HomeworkCounts:
    done: int
    not_done: int
    avg_grade: Optional[float]


def homework_stats(counts: HomeworkCounts) -> StudentStats:
    """Доля сделанных среди проверенных (не проверенные не считаются) и средняя оценка."""
    checked = counts.done + counts.not_done
    percent = round(counts.done * 100 / checked) if checked > 0 else None
    avg = round(counts.avg_grade, 2) if counts.avg_grade is not None else None
    return StudentStats(homework_done_percent=percent, homework_avg_grade=avg)
