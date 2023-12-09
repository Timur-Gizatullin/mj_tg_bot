from enum import Enum


class BaseStrEnum(str, Enum):
    @classmethod
    def get_choices(cls) -> list[tuple[str, str]]:
        return [(key.name, key.value) for key in cls]


class AnswerTypeEnum(BaseStrEnum):
    START = "START"
    HELP = "HELP"
    CENSOR = "CENSOR"
    GPT_OPTION = "GPT_OPTION"
    PRICES = "PRICES"
    UPSCALE_CONFIRM = "UPSCALE_CONFIRM"
    GPT_PRICE = "GPT_PRICE"


class UserRoleEnum(BaseStrEnum):
    ADMIN = "ADMIN"
    PREMIUM = "PREMIUM"
    BASE = "BASE"


class UserStateEnum(BaseStrEnum):
    PENDING = "PENDING"
    READY = "READY"
    BANNED = "BANNED"


class MerchantEnum(BaseStrEnum):
    YOOKASSA = "YOOKASSA"
    WALLET = "WALLET"


class CurrencyEnum(BaseStrEnum):
    RUB = "RUB"
    USD = "USD"


class ProductEnum(BaseStrEnum):
    TOKEN = "TOKEN"


class PriceEnum(BaseStrEnum):
    imagine = "imagine"
    blend = "blend"
    describe = "describe"
    vary = "vary"
    zoom = "zoom"
    pan = "pan"
    describe_retry = "describe_retry"
    upsample = "upsample"
    variation = "variation"
    reroll = "reroll"
    upscale__v5_2x = "upscale__v5_2x"
    upscale__v5_4x = "upscale__v5_4x"
    dalle = "dalle"
    gpt = "gpt"


class StatActionEnum(BaseStrEnum):
    MJ_QUERY = "MJ_QUERY"
    GPT_QUERY = "GPT_QUERY"
    DALLE_QUERY = "DALLE_QUERY"
