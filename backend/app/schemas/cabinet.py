from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse
from app.schemas.series import Series
from app.schemas.student import StudentShort, StudentStats


class ChildCard(BaseModel):
    student: StudentShort = Field(..., description='Ребёнок')
    series: list[Series] = Field(default_factory=list, description='Действующие серии: регулярное расписание')
    stats: StudentStats = Field(default_factory=StudentStats, description='Статистика домашних заданий')


class ChildrenList(BaseModel):
    children: list[ChildCard] = Field(default_factory=list, description='Дети родителя')


class ChildrenResponse(BaseResponse):
    payload: ChildrenList = Field(default_factory=ChildrenList, description='Кабинет родителя: дети')


class SeriesList(BaseModel):
    series: list[Series] = Field(default_factory=list, description='Серии')


class SeriesListResponse(BaseResponse):
    payload: SeriesList = Field(default_factory=SeriesList, description='Регулярное расписание')
