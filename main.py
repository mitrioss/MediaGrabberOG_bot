# Импорт необходимых модулей
import os
import re
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, MediaUnavailable

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

# Паттерны для определения платформы по ссылке
PLATFORM_PATTERNS = {
    'youtube': r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)[\w-]+',
    'tiktok': r'(?:tiktok\.com/@[\w-]+/video/|vm\.tiktok\.com/)[\w-]+',
    'instagram': r'instagram\.com/(?:p|reel)/[\w-]+',
    'vk': r'(?:vk\.com|vkvideo\.ru)'
}

PLATFORM_NAMES_RU = {
    'youtube': 'YouTube',
    'tiktok': 'TikTok',
    'instagram': 'Instagram',
    'vk': 'ВКонтакте'
}

# Единственный экземпляр Instagram Client
insta_client = Client()


def detect_platform(url: str) -> str | None:
    """
    Определяет платформу по URL.
    """
    for platform, pattern in PLATFORM_PATTERNS.items():
        if re.search(pattern, url):
            return platform
    return None


async def download_with_yt_dlp(url: str, platform: str) -> str:
    """
    Скачивает видео через yt_dlp с тремя попытками.
    """
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'format': 'best',
        'quiet': True,
    }
    for attempt in range(1, 4):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except Exception as e:
            logger.warning(f"Попытка {attempt} не удалась: {e}")
            if attempt < 3:
                await asyncio.sleep(2)
            else:
                raise RuntimeError(f"Не удалось скачать с {platform}: {e}")


async def download_instagram(url: str) -> list[tuple[str, str]]:
    """
    Скачивает медиа из Instagram, поддерживает карусели.
    """
    try:
        if not insta_client.user_id:
            insta_client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

        media_pk = insta_client.media_pk_from_url(url)
        media = insta_client.media_info(media_pk)

        results: list[tuple[str, str]] = []
        resources = getattr(media, 'resources', [media])
        for resource in resources:
            if resource.media_type == 1:
                path = insta_client.photo_download(resource.pk, folder='downloads')
                results.append((path, 'photo'))
            elif resource.media_type == 2:
                path = insta_client.video_download(resource.pk, folder='downloads')
                results.append((path, 'video'))
        return results
    except (LoginRequired, MediaUnavailable) as e:
        raise RuntimeError(f"Ошибка Instagram: {e}")
    finally:
        insta_client.logout()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я MediaGrabBot. Пришли ссылку с YouTube, TikTok, Instagram или VK — я скачаю и отправлю медиа."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Отправьте ссылку с YouTube, TikTok, Instagram или VK. Команды: /start — запустить бота /help — помощь")


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    platform = detect_platform(url)
    if not platform:
        await update.message.reply_text("Неподдерживаемая платформа или неверная ссылка.")
        return

    msg = await update.message.reply_text(
        f"Скачиваю с {PLATFORM_NAMES_RU.get(platform, platform)}..."
    )

    os.makedirs('downloads', exist_ok=True)
    files: list[tuple[str, str]] = []
    try:
        if platform in ('youtube', 'tiktok', 'vk'):
            fp = await download_with_yt_dlp(url, platform)
            files.append((fp, 'video'))
        else:
            files.extend(await download_instagram(url))

        # Отправляем медиа
        for path, mtype in files:
            with open(path, 'rb') as f:
                if mtype == 'video':
                    await context.bot.send_video(chat_id=update.effective_chat.id, video=f)
                else:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=f)

        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
    except Exception as e:
        logger.error(f"Ошибка при обработке {url}: {e}")
        await msg.edit_text(f"Ошибка: {e}")
    finally:
        # Чистим временные файлы
        for path, _ in files:
            try:
                os.remove(path)
            except OSError:
                pass


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()


if __name__ == '__main__':
    main()
