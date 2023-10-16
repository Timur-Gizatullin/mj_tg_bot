from django.contrib import admin

from main.models import BanWord, Prompt, Referral, TelegramAnswer, User, MjUser, Pay

admin.site.register(User)
admin.site.register(BanWord)
admin.site.register(TelegramAnswer)
admin.site.register(Referral)
admin.site.register(Prompt)
admin.site.register(MjUser)
admin.site.register(Pay)