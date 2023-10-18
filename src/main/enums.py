from enum import Enum


class BaseStrEnum(str, Enum):
    @classmethod
    def get_choices(cls) -> list[tuple[str, str]]:
        return [(key.name, key.value) for key in cls]


class AnswerTypeEnum(BaseStrEnum):
    START = "START"
    HELP = "HELP"
    CENSOR = "CENSOR"


class UserRoleEnum(BaseStrEnum):
    ADMIN = "ADMIN"
    PREMIUM = "PREMIUM"
    BASE = "BASE"
