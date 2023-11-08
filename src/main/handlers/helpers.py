import os

import django
import langdetect
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from main.enums import UserRoleEnum, UserStateEnum, AnswerTypeEnum
from main.handlers.commands import gpt
from main.models import TelegramAnswer
from main.utils import callback_data_util

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t_bot.settings")
django.setup()

GPT_OPTION = """Use the following info as a reference to create ideal Midjourney prompts. 

Every time use every option provided further:

➖ Focus on clear and very concise descriptions, with different concepts separated by commas, then follow it with any parameters. Parameters are not separated by commas.

➖ Be specific and vivid: Describe every single aspect of the image, including: Subject, Style, Color, Medium, Composition, Lighting, Shadows, Mood, Environment, Time Era, Perspective, Depth of Field, Textures, Scale and Proportions, Foreground, Midground, Background, Weather, Material Properties, Time of Day, Motion or Stillness, Season, Cultural Context, Architectural Style, Patterns and Repetition, Emotions and Expressions, Clothing and Accessories, Setting, Reflections or Transparency, Interactions among Subjects, Symbolism, Light Source and Direction, Art Techniques or Mediums, Artistic Style or in the Style of a Specific Artist, Contrasting Elements, Framing or Compositional Techniques, Imaginary or Fictional Elements, Dominant Color Palette, and any other relevant context.

➖ Aim for rich and elaborate prompts: Provide ample detail to capture the essence of the desired image and use the examples below as a reference to craft intricate and comprehensive prompts which allow Midjourney to generate images with high accuracy and fidelity.

➖ For photos, Incorporate relevant camera settings like focal length, aperature, ISO, & shutter speed. Specify high end lenses such as Sony G Master, Canon L Series, Zeiss Otus series for higher quality images.

➖ Select the aspect ratio by adding the --ar <value>:<value> parameter. Choose suitable aspect ratios for portraits (9:16, 3:4, 2:3) and landscapes (16:9, 2:1, 3:2), considering the composition and desired framing.

➖ Exclude elements with --no: Add --no followed by the unwanted element to exclude it from the image, ensuring the final output aligns with your vision. Use this only there’s a high likelihood of something showing up in the image that we don't want.

➖ Diversify your prompts: Explore various styles, moods, colors, art mediums, and aspect ratios to create a wide range of visually appealing and unique images.

Here are 6 example prompts. The first 3 are artistic, the last 3 are photos. Use these examples to determine desired length of each prompt.

➖ Digital art of an enchanting piano recital set within a serene forest clearing, a grand piano as the centerpiece, the musician, a young woman with flowing locks and an elegant gown, gracefully playing amidst the vibrant green foliage and deep brown tree trunks, her fingers dancing across the keys with an air of passion and skill, soft pastel colors adding a touch of whimsy, warm, dappled sunlight filtering through the leaves, casting a dreamlike glow on the scene, a harmonious fusion of music and nature, eye-level perspective immersing the viewer in the tranquil woodland setting, a captivating blend of art and the natural world --ar 2:1

➖ A heartwarming Disney-Pixar style animation, rich in detail and vividness, featuring a chipmunk and a field mouse as two intrepid animal scouts, standing determinedly at the edge of a dense forest, their matching windbreakers and baseball caps adding a touch of whimsy to their appearance, satchels and gear neatly organized and ready for the grand adventure that lies ahead. The enchanting forest, alive with lush green foliage, intricate underbrush, and the occasional rustle of unseen creatures, provides a captivating backdrop for this charming tale of friendship and exploration. Above them, the sky is adorned with delicate wispy clouds, casting a soft, ethereal glow over the scene. The animation boasts intricate textures and meticulous shading, embodying the signature Disney-Pixar style, creating a sense of depth and immersion that draws the viewer into the magical world of these endearing animal companions and their daring exploits --ar 3:2
➖ Detailed charcoal drawing of a gentle elderly woman, with soft and intricate shading in her wrinkled face, capturing the weathered beauty of a long and fulfilling life. The ethereal quality of the charcoal brings a nostalgic feel that complements the natural light streaming softly through a lace-curtained window. In the background, the texture of the vintage furniture provides an intricate carpet of detail, with a monochromatic palette serving to emphasize the subject of the piece. This charcoal drawing imparts a sense of tranquillity and wisdom with an authenticity that captures the subject's essence.

➖ A stunning portrait of an intricate marble sculpture depicting a mythical creature composed of attributes from both a lion and eagle. The sculpture is perched atop a rocky outcrop, with meticulous feather and fur details captured perfectly. The wings of the creature are outstretched, muscles tensed with determination, conveying a sense of strength and nobility. The lens used to capture the photograph perfectly highlights every detail in the sculpture's composition. The image has a sharp focus and excellent clarity. Canon EF 24-70mm f/2.8L II USM lens at 50mm, ISO 100, f/5.6, 1/50s, --ar 4:3

➖ Astounding astrophotography image of the Milky Way over Stonehenge, emphasizing the human connection to the cosmos across time. The enigmatic stone structure stands in stark silhouette with the awe-inspiring night sky, showcasing the complexity and beauty of our galaxy. The contrast accentuates the weathered surfaces of the stones, highlighting their intricate play of light and shadow. Sigma Art 14mm f/1.8, ISO 3200, f/1.8, 15s --ar 16:9

➖ A professional photograph of a poised woman showcased in her natural beauty, standing amidst a vibrant field of tall, swaying grass during golden hour. The radiant rays of sun shimmer and cast a glow around her. The tight framing emphasizes her gentle facial features, with cascading hair in the forefront complimenting her elegant attire. The delicate lace and silk details intricately woven into the attire add a touch of elegance and sophistication to the subject. The photo is a contemporary take on fashion photography, with soft textures enhanced by the shallow depth of field, seemingly capturing the subject's serene and confident demeanor. The warm colors and glowing backlight cast a radiant halo effect around her, highlighting her poise and elegance, whilst simultaneously adding a dreamlike quality to the photograph. Otus 85mm f/1.4 ZF.2 Lens, ISO 200, f/4, 1/250s --ar 2:3

You will now receive a text prompt from me and then create three creative prompts for the Midjourney AI art generator using the best practices mentioned above. Do not include explanations in your response. List three prompts with correct syntax without unnecessary words. Each prompt should contain be at least 1000 symbols or more long. Every time use lens, iso and style option.
"""  # noqa:E501

TRANSLATOR_GPT_OPTION = (
    "You are a professional translator from Russian into English, "
    "everything that is said to you, you translate into English"
    "If you get message in english, just send it back, do not translate"
)


async def is_enough_balance(telegram_user, callback, amount):
    reply = """Ваш баланс {}.

💰 Вам доступно только  5 бесплатных токенов ежедневно. 

🌇Пополни свой счёт и получи быстрые генерации без очереди! 🎆

💤 Или возвращайтесь завтра!"""
    if telegram_user.balance - amount < 0:
        builder = InlineKeyboardBuilder()
        lk_buttons = (types.InlineKeyboardButton(text="Пополнить баланс Тарифы", callback_data="lk_options"),)
        builder.row(*lk_buttons)
        await callback.message.answer(reply.format(telegram_user.balance), reply_markup=builder.as_markup())
        await callback.answer()
        return False

    return True


async def is_ready(telegram_user, callback):
    if telegram_user.state == UserStateEnum.PENDING:
        await callback.message.answer("🛑 Пожалуйста дождитесь завершения предыдущего запроса!")
        await callback.answer()
        return False
    if telegram_user.state == UserStateEnum.BANNED:
        await callback.message.answer("🛑 Ваш аккаунт был ограничен, обратитесь к администратору")
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
        {"role": "system", "content": await TelegramAnswer.objects.get_message_by_type(AnswerTypeEnum.GPT_OPTION)},
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

        await callback.message.answer(
            text=prompt_suggestions.choices[0].message.content, reply_markup=builder.as_markup()
        )

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
