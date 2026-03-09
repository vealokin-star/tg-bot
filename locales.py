TEXTS = {
    "ru": {
        "choose_language": "🌍 Выберите язык / Choose language:",
        "language_set": "🇷🇺 Язык установлен: Русский",
        "welcome": (
            "👋 Привет! Я бот для скачивания видео из TikTok и Instagram.\n\n"
            "📎 Отправь мне ссылку на:\n"
            "• TikTok видео\n"
            "• Instagram Reels\n\n"
            "И я скачаю его для тебя! 🚀"
        ),
        "send_link": "🔗 Отправь ссылку на видео:",
        "downloading": "⏳ Скачиваю, подожди немного...",
        "done": "✅ Готово! Скачано с",
        "error": (
            "❌ Не удалось скачать.\n\n"
            "Возможные причины:\n"
            "• Приватный аккаунт\n"
            "• Ссылка недействительна\n"
            "• Временная ошибка\n\n"
            "Попробуй ещё раз позже."
        ),
        "unknown_url": (
            "❓ Не могу распознать ссылку.\n\n"
            "Поддерживаются ссылки с:\n"
            "• tiktok.com\n"
            "• instagram.com/reel/"
        ),
        "history_empty": "📭 У тебя пока нет истории запросов.",
        "history_title": "📋 *Последние 10 запросов:*\n\n",
        "stats_title": "📊 *Твоя статистика:*\n\n",
        "stats_total": "📥 Всего запросов",
        "stats_success": "✅ Успешных",
        "stats_failed": "❌ Ошибок",
        "btn_ru": "🇷🇺 Русский",
        "btn_en": "🇬🇧 English",
        "change_lang": "🌍 Сменить язык",
    },
    "en": {
        "choose_language": "🌍 Выберите язык / Choose language:",
        "language_set": "🇬🇧 Language set: English",
        "welcome": (
            "👋 Hello! I'm a bot for downloading videos from TikTok and Instagram.\n\n"
            "📎 Send me a link to:\n"
            "• TikTok video\n"
            "• Instagram Reels\n\n"
            "And I'll download it for you! 🚀"
        ),
        "send_link": "🔗 Send me a video link:",
        "downloading": "⏳ Downloading, please wait...",
        "done": "✅ Done! Downloaded from",
        "error": (
            "❌ Failed to download.\n\n"
            "Possible reasons:\n"
            "• Private account\n"
            "• Invalid link\n"
            "• Temporary service error\n\n"
            "Please try again later."
        ),
        "unknown_url": (
            "❓ Can't recognize the link.\n\n"
            "Supported links from:\n"
            "• tiktok.com\n"
            "• instagram.com/reel/"
        ),
        "history_empty": "📭 You have no request history yet.",
        "history_title": "📋 *Last 10 requests:*\n\n",
        "stats_title": "📊 *Your statistics:*\n\n",
        "stats_total": "📥 Total requests",
        "stats_success": "✅ Successful",
        "stats_failed": "❌ Failed",
        "btn_ru": "🇷🇺 Русский",
        "btn_en": "🇬🇧 English",
        "change_lang": "🌍 Change language",
    }
}


def t(lang: str, key: str) -> str:
    """Get translation string."""
    return TEXTS.get(lang, TEXTS["en"]).get(key, key)
