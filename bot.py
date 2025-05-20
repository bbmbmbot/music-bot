import os
import re
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

ffmpeg_path = r"C:\FFmpeg\ffmpeg-7.1.1-essentials_build\bin"
os.environ["PATH"] += os.pathsep + ffmpeg_path

BOT_TOKEN = '7820967332:AAFfKslQRCAKuD-12zxu6OfZdxaEsvPWElE'  # <-- вставьте сюда токен вашего бота

# Кнопки меню
menu_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("🎵 Найти песню", callback_data='find_song')],
    ]
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я музыкальный бот.\n"
        "Нажми кнопку ниже, чтобы найти песню.",
        reply_markup=menu_keyboard
    )


async def download_music(query: str) -> tuple[str, str, str, str]:
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'song_%(id)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    # Попытка скачать с YouTube
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=True)
        if 'entries' in info and info['entries']:
            info = info['entries'][0]
            filename = ydl.prepare_filename(info)
            mp3_filename = os.path.splitext(filename)[0] + '.mp3'

            title = info.get('title', 'Unknown title')
            artist = info.get('artist') or info.get('uploader') or 'Unknown artist'
            thumbnail = info.get('thumbnail')

            clean_title = re.sub(r'[\\/:"*?<>|]+', '', title)
            clean_artist = re.sub(r'[\\/:"*?<>|]+', '', artist)
            new_filename = f"{clean_artist} — {clean_title}.mp3"
            os.rename(mp3_filename, new_filename)

            return new_filename, clean_title, clean_artist, thumbnail

    # Если не нашли на YouTube, пробуем SoundCloud
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"scsearch:{query}", download=True)
        if 'entries' in info and info['entries']:
            info = info['entries'][0]
            filename = ydl.prepare_filename(info)
            mp3_filename = os.path.splitext(filename)[0] + '.mp3'

            title = info.get('title', 'Unknown title')
            artist = info.get('artist') or info.get('uploader') or 'Unknown artist'
            thumbnail = info.get('thumbnail')

            clean_title = re.sub(r'[\\/:"*?<>|]+', '', title)
            clean_artist = re.sub(r'[\\/:"*?<>|]+', '', artist)
            new_filename = f"{clean_artist} — {clean_title}.mp3"
            os.rename(mp3_filename, new_filename)

            return new_filename, clean_title, clean_artist, thumbnail

    raise Exception("Песня не найдена ни на YouTube, ни на SoundCloud.")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'find_song':
        context.user_data['awaiting_query'] = True
        await query.message.reply_text("Напиши название или исполнителя песни, которую хочешь найти.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_query'):
        query_text = update.message.text
        context.user_data['awaiting_query'] = False
        msg = await update.message.reply_text(f"🔍 Ищу: {query_text} ...")

        try:
            mp3_file, title, artist, thumbnail = await download_music(query_text)

            if thumbnail:
                await update.message.reply_photo(photo=thumbnail)

            with open(mp3_file, 'rb') as audio:
                await update.message.reply_audio(audio=audio, title=title, performer=artist)

            os.remove(mp3_file)
            await msg.edit_text("Готово! Вот твоя песня 🎶")
        except Exception as e:
            await msg.edit_text(f"❌ Ошибка при загрузке: {e}")
    else:
        await update.message.reply_text("Нажми кнопку «Найти песню», чтобы начать.")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен и готов к работе!")
    app.run_polling()


if __name__ == '__main__':
    main()

