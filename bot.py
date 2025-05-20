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

# Указываем путь до FFmpeg (если установлен вручную)
ffmpeg_path = r"C:\FFmpeg\ffmpeg-7.1.1-essentials_build\bin"
os.environ["PATH"] += os.pathsep + ffmpeg_path

# Вставь свой токен ниже
BOT_TOKEN = '7820967332:AAFfKslQRCAKuD-12zxu6OfZdxaEsvPWElE'

# Клавиатура
menu_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🎵 Найти песню", callback_data='find_song')],
    [InlineKeyboardButton("🔥 Хиты", callback_data='popular')],
])

# Обработчик /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я музыкальный бот.\nНажми кнопку ниже, чтобы найти песню или послушать хиты.",
        reply_markup=menu_keyboard
    )

# Загрузка песни
async def send_song(query: str, message, context):
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

    search_queries = [f"ytsearch:{query}", f"scsearch:{query}"]
    for search_query in search_queries:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=True)
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

                if thumbnail:
                    await message.reply_photo(photo=thumbnail)

                with open(new_filename, 'rb') as audio:
                    await message.reply_audio(audio=audio, title=title, performer=artist)

                os.remove(new_filename)
                await message.reply_text("✅ Готово! Вот твоя песня 🎶")
                return
        except Exception as e:
            print(f"[Ошибка при поиске в {search_query}]: {e}")

    await message.reply_text("❌ Песня не найдена ни на YouTube, ни на SoundCloud.")

# Обработка кнопок
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'find_song':
        context.user_data['awaiting_query'] = True
        await query.message.reply_text("🎧 Напиши название или исполнителя песни.")
    elif query.data == 'popular':
        await send_song("топ хиты", query.message, context)

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_query'):
        query_text = update.message.text
        context.user_data['awaiting_query'] = False
        msg = await update.message.reply_text(f"🔍 Ищу: {query_text} ...")

        try:
            await send_song(query_text, update.message, context)
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"❌ Ошибка при загрузке: {e}")
    else:
        await update.message.reply_text("Выбери действие с помощью кнопок 👇", reply_markup=menu_keyboard)

# Запуск
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
