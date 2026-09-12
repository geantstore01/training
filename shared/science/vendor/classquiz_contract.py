# SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
# SPDX-License-Identifier: MPL-2.0
# Source: mawoka-myblock/classquiz, commit 711bdde7a7dcd2d217cfc75dbbbb2592a78582d3
# Extracted seven unmodified data-model classes; imports reduced to their needs.
from enum import Enum
from pydantic import BaseModel, field_validator, ValidationInfo

class ABCDQuizAnswer(BaseModel):
    right: bool
    answer: str
    color: str | None = None


class RangeQuizAnswer(BaseModel):
    min: int
    max: int
    min_correct: int
    max_correct: int


class VotingQuizAnswer(BaseModel):
    answer: str
    image: str | None = None
    color: str | None = None


class QuizQuestionType(str, Enum):
    ABCD = "ABCD"
    RANGE = "RANGE"
    VOTING = "VOTING"
    SLIDE = "SLIDE"
    TEXT = "TEXT"
    ORDER = "ORDER"
    CHECK = "CHECK"


class TextQuizAnswer(BaseModel):
    answer: str
    case_sensitive: bool


class QuizQuestion(BaseModel):
    question: str
    time: str  # in Secs
    type: None | QuizQuestionType = QuizQuestionType.ABCD
    answers: list[ABCDQuizAnswer] | RangeQuizAnswer | list[TextQuizAnswer] | list[VotingQuizAnswer] | str
    image: str | None = None
    hide_results: bool | None = False

    @field_validator("answers")
    def answers_not_none_if_abcd_type(cls, v, info: ValidationInfo):
        if info.data["type"] == QuizQuestionType.ABCD and not isinstance(v[0], ABCDQuizAnswer):
            raise ValueError("Answers can't be none if type is ABCD")
        if info.data["type"] == QuizQuestionType.RANGE and not isinstance(v, RangeQuizAnswer):
            raise ValueError("Answer must be from type RangeQuizAnswer if type is RANGE")
        if info.data["type"] == QuizQuestionType.VOTING and not isinstance(v[0], VotingQuizAnswer):
            raise ValueError("Answer must be from type VotingQuizAnswer if type is VOTING")
        if info.data["type"] == QuizQuestionType.TEXT and not isinstance(v[0], TextQuizAnswer):
            raise ValueError("Answer must be from type TextQuizAnswer if type is TEXT")
        if info.data["type"] == QuizQuestionType.ORDER and not isinstance(v[0], VotingQuizAnswer):
            raise ValueError("Answer must be from type VotingQuizAnswer if type is ORDER")
        if info.data["type"] == QuizQuestionType.SLIDE and not isinstance(v, str):
            raise ValueError("Answer must be from type SlideElement if type is SLIDE")
        if info.data["type"] == QuizQuestionType.CHECK and not isinstance(v[0], ABCDQuizAnswer):
            raise ValueError("Answers can't be none if type is CHECK")
        return v


class QuizInput(BaseModel):
    public: bool | None = False
    title: str
    description: str
    cover_image: str | None = None
    background_color: str | None = None
    questions: list[QuizQuestion]
    background_image: str | None = None
