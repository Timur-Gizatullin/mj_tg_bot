import os

import django
import langdetect
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from main.enums import UserRoleEnum, UserStateEnum
from main.handlers.commands import gpt
from main.utils import callback_data_util

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

GPT_OPTION = """The ethereal quality of the charcoal brings a nostalgic feel that complements the natural light streaming softly through a lace-curtained window. In the background, the texture of the vintage furniture provides an intricate carpet of detail, with a monochromatic palette serving to emphasize the subject of the piece. This charcoal drawing imparts a sense of tranquillity and wisdom with an authenticity that captures the subject's essence. Use different lenses, cameras, focus, light and scenes options. 
 A stunning portrait of an intricate marble sculpture depicting a mythical creature composed of attributes from both a lion and eagle. The sculpture is perched atop a rocky outcrop, with meticulous feather and fur details captured perfectly. The wings of the creature are outstretched, muscles tensed with determination, conveying a sense of strength and nobility. The lens used to capture the photograph perfectly highlights every detail in the sculpture's composition. The image has a sharp focus and excellent clarity. Canon EF 24-70mm f/2.8L II USM lens at 50mm, ISO 100, f/5.6, 1/50s, --ar 4:3

 Astounding astrophotography image of the Milky Way over Stonehenge, emphasizing the human connection to the cosmos across time. The enigmatic stone structure stands in stark silhouette with the awe-inspiring night sky, showcasing the complexity and beauty of our galaxy. The contrast accentuates the weathered surfaces of the stones, highlighting their intricate play of light and shadow. Sigma Art 14mm f/1.8, ISO 3200, f/1.8, 15s --ar 16:9

 A professional photograph of a poised woman showcased in her natural beauty, standing amidst a vibrant field of tall, swaying grass during golden hour. The radiant rays of sun shimmer and cast a glow around her. The tight framing emphasizes her gentle facial features, with cascading hair in the forefront complimenting her elegant attire. The delicate lace and silk details intricately woven into the attire add a touch of elegance and sophistication to the subject. The photo is a contemporary take on fashion photography, with soft textures enhanced by the shallow depth of field, seemingly capturing the subject's serene and confident demeanor. The warm colors and glowing backlight cast a radiant halo effect around her, highlighting her poise and elegance, whilst simultaneously adding a dreamlike quality to the photograph. Otus 85mm f/1.4 ZF.2 Lens, ISO 200, f/4, 1/250s --ar 2:3

use different lens and cameras

You will now receive a text prompt from me and then create three creative prompts for the Midjourney AI art generator using the best practices mentioned above. Do not include explanations in your response. List three prompts with correct syntax without unnecessary words.
"""

TRANSLATOR_GPT_OPTION = (
    "You are a professional translator from Russian into English, "
    "everything that is said to you, you translate into English"
    "If you get message in english, just send it back, do not translate"
)


async def is_enough_balance(telegram_user, callback, amount):
    if telegram_user.balance - amount < 0:
        builder = InlineKeyboardBuilder()
        answer = f"Ваш баланс {telegram_user.balance}\n"
        lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
        builder.row(*lk_buttons)
        await callback.message.answer(answer, reply_markup=builder.as_markup())
        await callback.answer()
        return False

    return True


async def is_ready(telegram_user, callback):
    if telegram_user.state == UserStateEnum.PENDING:
        await callback.message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        await callback.answer()
        return False

    return True


async def is_can_use(telegram_user, callback, amount):
    if not await is_enough_balance(telegram_user, callback, amount):
        return False

    if not await is_ready(telegram_user, callback):
        return False

    return True


async def gpt_translate(message):
    locale = langdetect.detect(message)
    if locale == "en":
        prompt = message
    else:
        messages = [
            {
                "role": "system",
                "content": TRANSLATOR_GPT_OPTION,
            },
            {"role": "user", "content": message},
        ]

        prompt = await gpt.acreate(model="gpt-3.5-turbo", messages=messages)
        prompt = prompt.choices[0].message.content

    return prompt


async def get_gpt_prompt_suggestions(prompt, callback, user, data):
    messages = [
        {"role": "system", "content": GPT_OPTION},
        {"role": "user", "content": prompt},
    ]
    try:
        await callback.message.answer("Идет генерация ...")
        prompt_suggestions = await gpt.acreate(model="gpt-3.5-turbo", messages=messages)

        builder = InlineKeyboardBuilder()
        buttons = [
            types.InlineKeyboardButton(
                text=f"промпт {i}",
                callback_data=f"choose-gpt_{i}_{callback.message.chat.id}{callback.message.message_id}",
            )
            for i in range(1, 4)
        ]
        builder.row(*buttons)

        logger.debug(data["img"])
        if data["img"]:
            callback_data_util[f"img{callback.message.chat.id}{callback.message.message_id}"] = data["img"]
            logger.debug(callback_data_util)

        await callback.message.answer(text=prompt_suggestions.choices[0].message.content, reply_markup=builder.as_markup())

        user.balance -= 1
        if user.balance < 5:
            user.role = UserRoleEnum.BASE
        user.state = UserStateEnum.READY
        await user.asave()
        await callback.message.answer(text=f"Баланс в токенах: {user.balance}")
    except Exception as e:
        logger.error(e)
        user.state = UserStateEnum.READY
        await user.asave()
        await callback.message.answer("Что-то пошло не так :(")
