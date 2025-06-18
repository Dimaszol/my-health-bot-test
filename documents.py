import html
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from registration import user_states
from db_postgresql import get_documents_by_user, update_document_confirmed, get_user_language, t
from vector_db_postgresql import mark_chunks_unconfirmed

async def handle_show_documents(target, user_id: int):
    documents = await get_documents_by_user(user_id)
    lang = await get_user_language(user_id)

    if not documents:
        await target.answer(t("no_documents", lang))
        return

    if not isinstance(user_states.get(user_id), dict) or user_states[user_id].get("mode") != "viewing_documents":
        user_states[user_id] = {"mode": "viewing_documents", "offset": 0}
    offset = user_states[user_id]["offset"]
    limited_docs = documents[offset:offset + 5]

    for doc in limited_docs:
        doc_id = doc["id"]
        title = html.escape(doc["title"])
        date = doc["date"]
        if doc.get("file_type") == "note":
            # Заметка — без кнопки скачивания
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[ 
                InlineKeyboardButton(text=t("btn_view", lang), callback_data=f"view_{doc_id}"),
                InlineKeyboardButton(text=t("btn_ignore", lang), callback_data=f"ignore_{doc_id}")
            ]])
        else:
            # Обычный документ — с кнопкой скачивания
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[ 
                InlineKeyboardButton(text=t("btn_view", lang), callback_data=f"view_{doc_id}"),
                InlineKeyboardButton(text=t("btn_download", lang), callback_data=f"download_{doc_id}"),
                InlineKeyboardButton(text=t("btn_ignore", lang), callback_data=f"ignore_{doc_id}")
            ]])
        from utils.security import safe_send_message
        await safe_send_message(
            target,
            f"🕒 {str(date)[:10]}",
            title=f"📄 {title}",
            reply_markup=keyboard
        )

    # Добавляем кнопку "Показать ещё", если есть больше документов
    if offset == 0 and len(documents) <= 5:
        await target.answer(t("all_documents_shown", lang))
    elif len(documents) > offset + 5:
        remaining = len(documents) - (offset + 5)
        more_button = InlineKeyboardMarkup(inline_keyboard=[[ 
            InlineKeyboardButton(text=t("btn_show_more", lang), callback_data="more_docs")
        ]])
        await target.answer(t("more_documents", lang, count=remaining), reply_markup=more_button)

    else:
        await target.answer(t("all_documents_shown", lang))

async def handle_ignore_document(callback: types.CallbackQuery, doc_id: int):
    from db_postgresql import get_document_by_id

    user_id = callback.from_user.id
    doc = await get_document_by_id(doc_id)
    lang = await get_user_language(user_id)

    if not doc or doc["user_id"] != user_id:
        await callback.message.answer(t("document_not_found", lang))
        return

    await update_document_confirmed(doc_id, confirmed=False)
    mark_chunks_unconfirmed(doc_id)
    await callback.message.delete()
    await callback.answer(t("excluded", lang))

async def send_note_controls(message: types.Message, doc_id: int):
    from db_postgresql import get_document_by_id, get_user_language, t
    user_id = message.from_user.id
    lang = await get_user_language(user_id)

    doc = await get_document_by_id(doc_id)
    if not doc:
        await message.answer(t("note_not_found", lang))
        return

    title = html.escape(doc["title"])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[ 
        InlineKeyboardButton(text=t("btn_rename", lang), callback_data=f"rename_{doc_id}"),
        InlineKeyboardButton(text=t("btn_ignore", lang), callback_data=f"ignore_{doc_id}")
    ]])
    await message.answer(
        t("note_title", lang, title=title),
        reply_markup=keyboard,
        parse_mode="HTML"
    )
