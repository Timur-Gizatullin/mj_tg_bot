from aiogram import Router, types

from main.models import GptContext

gpt_router = Router()


@gpt_router.callback_query(lambda c: c.data.startswith("gpt"))
async def gpt_callback(callback: types.CallbackQuery):
    gpt_contexts = await GptContext.objects.get_gpt_contexts_by_telegram_chat_id(callback.message.chat.id)
    await GptContext.objects.delete_gpt_contexts(gpt_contexts)

    await callback.answer("Контекст очищен")
