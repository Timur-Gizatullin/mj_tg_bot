from django.contrib import admin

from main.models import BanWord, DiscordQueue, Referral, TelegramAnswer, User

admin.site.register(User)
admin.site.register(BanWord)
admin.site.register(TelegramAnswer)
admin.site.register(Referral)
admin.site.register(DiscordQueue)
