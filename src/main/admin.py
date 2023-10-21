from django.contrib import admin

from main.models import BanWord, Pay, Prompt, Referral, TelegramAnswer, User
from main.models.user import UserAudit

admin.site.register(User, UserAudit)
admin.site.register(BanWord)
admin.site.register(TelegramAnswer)
admin.site.register(Referral)
admin.site.register(Prompt)
admin.site.register(Pay)
