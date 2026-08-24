import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import internetarchive as ia

# आपके बोट और आर्काइव की जानकारी
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
ARCHIVE_ACCESS_KEY = os.environ.get("ACCESS_KEY")
ARCHIVE_SECRET_KEY = os.environ.get("SECRET_KEY")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    # चेक करें कि वीडियो या डॉक्यूमेंट भेजा गया है या नहीं
    file_obj = message.video or message.document
    if not file_obj:
        await message.reply_text("❌ कृपया कोई वैध वीडियो फाइल (Video या Document) भेजें!")
        return

    status_msg = await message.reply_text("📥 वीडियो डाउनलोड हो रहा है, कृपया इंतज़ार करें...")
    
    # टेलीग्राम से फाइल डाउनलोड करना
    file = await context.bot.get_file(file_obj.file_id)
    file_name = file_obj.file_name if hasattr(file_obj, 'file_name') and file_obj.file_name else "movie.mp4"
    
    local_path = f"./{file_name}"
    await file.download_to_drive(local_path)
    
    await status_msg.edit_text("🚀 वीडियो Archive.org पर अपलोड हो रहा है...")

    # Archive.org पर अपलोड करने की प्रक्रिया
    identifier = f"movieadda-{file_obj.file_id[-10:]}"
    config = {
        's3': {
            'access': ARCHIVE_ACCESS_KEY,
            'secret': ARCHIVE_SECRET_KEY
        }
    }

    try:
        ia.upload(
            identifier,
            files=[local_path],
            metadata={'mediatype': 'movies', 'title': file_name},
            config=config
        )
        
        # परमानेंट लिंक तैयार करना
        permanent_link = f"https://archive.org/download/{identifier}/{file_name}"
        await status_msg.edit_text(f"✅ **सफलतापूर्वक अपलोड हो गया!**\n\n🔗 **Permanent Link:**\n{permanent_link}")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ अपलोड करने में त्रुटि आई: {str(e)}")
        
    finally:
        # फोन/सर्वर से लोकल फाइल हटाना ताकि स्पेस फुल न हो
        if os.path.exists(local_path):
            os.remove(local_path)

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: BOT_TOKEN नहीं मिला!")
        return
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.VIDEO | filters.DOCUMENT, handle_video))
    print("🤖 Uploader Bot सफलतापूर्वक शुरू हो गया है...")
    app.run_polling()

if __name__ == '__main__':
    main()
