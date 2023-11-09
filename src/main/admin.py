from django.contrib import admin

from main.models import (
    BanWord,
    Blend,
    Channel,
    Describe,
    DsMjUser,
    GptContext,
    OptionPrice,
    Pay,
    Price,
    Prompt,
    Referral,
    TelegramAnswer,
    User,
)
from main.models.user import UserAudit

admin.site.register(User, UserAudit)
admin.site.register(BanWord)
admin.site.register(TelegramAnswer)
admin.site.register(Referral)
admin.site.register(Prompt)
admin.site.register(Pay)
admin.site.register(Describe)
admin.site.register(Blend)
admin.site.register(GptContext)
admin.site.register(Price)
admin.site.register(Channel)
admin.site.register(DsMjUser)
admin.site.register(OptionPrice)
