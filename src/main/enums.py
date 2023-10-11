from enum import Enum


class BaseEnum(str, Enum):
    @classmethod
    def get_choices(cls) -> list[tuple[str, str]]:
        return [(key.name, key.value) for key in cls]


class AnswerTypeEnum(BaseEnum):
    START = "START"
    HELP = "HELP"
    CENSOR = "CENSOR"
