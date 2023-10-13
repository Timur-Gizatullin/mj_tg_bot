from enum import Enum


class BaseStrEnum(str, Enum):
    @classmethod
    def get_choices(cls) -> list[tuple[str, str]]:
        return [(key.name, key.value) for key in cls]


class BaseIntEnum(int, Enum):
    @classmethod
    def get_choices(cls) -> list[tuple[str, int]]:
        return [(key.name, key.value) for key in cls]


class AnswerTypeEnum(BaseStrEnum):
    START = "START"
    HELP = "HELP"
    CENSOR = "CENSOR"


class UserRoleEnum(BaseIntEnum):
    ADMIN = 1
    PREMIUM = 2
    BASE = 3
