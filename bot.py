import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

from database import Database
from downloader import Downloader
from locales import t

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database()
downloader = Downloader()


# ── Keyboards ──────────────────────────────────────────────────────────────────

def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
    ]])


def main_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "change_lang"))]],
        resize_keyboard=True,
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_lang(user_id: int) -> str:
    return db.get_user_language(user_id) or "en"


# ── Handlers ───────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: Message):
    lang = db.get_user_language(message.from_user.id)
    if lang:
        # Already chose language — show welcome again
        await message.answer(t(lang, "welcome"), reply_markup=main_keyboard(lang))
        await message.answer(t(lang, "send_link"))
    else:
        await message.answer(
            t("en", "choose_language"),
            reply_markup=language_keyboard()
        )


@dp.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery):
    lang = callback.data.split(":")[1]
    db.set_user_language(callback.from_user.id, callback.from_user.username, lang)

    await callback.message.edit_text(t(lang, "language_set"))
    await callback.message.answer(t(lang, "welcome"), reply_markup=main_keyboard(lang))
    await callback.message.answer(t(lang, "send_link"))
    await callback.answer()


@dp.message(Command("language"))
async def cmd_language(message: Message):
    await message.answer(t("en", "choose_language"), reply_markup=language_keyboard())


@dp.message(Command("history"))
async def cmd_history(message: Message):
    lang = get_lang(message.from_user.id)
    history = db.get_user_history(message.from_user.id, limit=10)
    if not history:
        await message.answer(t(lang, "history_empty"))
        return

    text = t(lang, "history_title")
    for i, record in enumerate(history, 1):
        status_emoji = "✅" if record["status"] == "success" else "❌"
        url_preview = record["url"][:45] + "..." if len(record["url"]) > 45 else record["url"]
        text += f"{i}. {status_emoji} `{url_preview}`\n   _{record['created_at']}_\n\n"

    await message.answer(text, parse_mode="Markdown")


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    lang = get_lang(message.from_user.id)
    stats = db.get_user_stats(message.from_user.id)
    await message.answer(
        f"{t(lang, 'stats_title')}"
        f"{t(lang, 'stats_total')}: {stats['total']}\n"
        f"{t(lang, 'stats_success')}: {stats['success']}\n"
        f"{t(lang, 'stats_failed')}: {stats['failed']}\n",
        parse_mode="Markdown"
    )


@dp.message(F.text)
async def handle_text(message: Message):
    lang = get_lang(message.from_user.id)
    text = message.text.strip()

    # Language change button
    if text == t("ru", "change_lang") or text == t("en", "change_lang"):
        await message.answer(t("en", "choose_language"), reply_markup=language_keyboard())
        return

    # No language chosen yet
    if not db.get_user_language(message.from_user.id):
        await message.answer(t("en", "choose_language"), reply_markup=language_keyboard())
        return

    # Detect platform
    if "tiktok.com" in text:
        platform = "tiktok"
    elif "instagram.com" in text:
        platform = "instagram"
    else:
        await message.answer(t(lang, "unknown_url"))
        return

    request_id = db.save_request(
        user_id=message.from_user.id,
        username=message.from_user.username,
        url=text,
        platform=platform
    )

    status_msg = await message.answer(t(lang, "downloading"))

    try:
        result = await downloader.download(text, platform)

        if result["type"] == "video":
            await message.answer_video(
                types.FSInputFile(result["path"]),
                caption=f"{t(lang, 'done')} {platform.capitalize()}"
            )
        elif result["type"] == "photo":
            media = [types.InputMediaPhoto(media=types.FSInputFile(p)) for p in result["paths"]]
            await message.answer_media_group(media)
        elif result["type"] == "photos_and_videos":
            for path in result["paths"]:
                if path.endswith((".mp4", ".mov")):
                    await message.answer_video(types.FSInputFile(path))
                else:
                    await message.answer_photo(types.FSInputFile(path))

        db.update_request_status(request_id, "success")
        await status_msg.delete()
        downloader.cleanup(result.get("paths") or [result.get("path")])

    except Exception as e:
        logger.error(f"Download error: {e}")
        db.update_request_status(request_id, "failed", str(e))
        await status_msg.edit_text(t(lang, "error"))


# ── Entry point ────────────────────────────────────────────────────────────────

async def main():
    db.init()
    logger.info("Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
