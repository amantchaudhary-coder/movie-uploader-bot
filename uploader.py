    import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from internetarchive import upload, get_item

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables from Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    file = message.video or message.document
    
    if not file:
        await message.reply_text("कृपया कोई वीडियो या डॉक्यूमेंट फाइल भेजें।")
        return

    sent_msg = await message.reply_text("📥 फाइल डाउनलोड हो रही है, कृपया प्रतीक्षा करें...")
    
    try:
        # Telegram से फाइल डाउनलोड करना
        new_file = await context.bot.get_file(file.file_id)
        file_name = file.file_name or "uploaded_video.mp4"
        local_path = f"/tmp/{file_name}"
        
        await new_file.download_to_drive(local_path)
        
        await sent_msg.edit_text("☁️ Internet Archive पर अपलोड किया जा रहा है...")
        
        # Internet Archive पर अपलोड करने की डिटेल्स
        identifier = f"telegram_bot_upload_{file.file_id[-10:]}"
        meta = {
            'mediatype': 'movies',
            'collection': 'opensource_movies',
            'title': file_name
        }
        
        # Archive पर अपलोड करना
        upload(
            identifier=identifier,
            files=[local_path],
            metadata=meta,
            access_key=ACCESS_KEY,
            secret_key=SECRET_KEY
        )
        
        # डाउनलोड लिंक तैयार करना
        download_url = f"https://archive.org/download/{identifier}/{file_name}"
        
        await sent_msg.edit_text(
            f"✅ **अपलोड सफल रहा!**\n\n"
            f"📁 **फाइल नाम:** {file_name}\n"
            f"🔗 **डाउनलोड लिंक:**\n{download_url}",
            parse_mode="Markdown"
        )
        
        # लोकल स्टोरेज से फाइल हटाना
        if os.path.exists(local_path):
            os.remove(local_path)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await sent_msg.edit_text(f"❌ अपलोड करने में विफल रहा!\nएरर: {str(e)}")

def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable is missing!")
        return

    # Telegram Bot एप्लीकेशन शुरू करना
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # यहाँ अब सही बड़े अक्षरों वाले फिल्टर्स का इस्तेमाल किया गया है
    app.add_handler(MessageHandler(filters.VIDEO | filters.DOCUMENT, handle_video))

    print("🤖 बोट शुरू हो गया है और काम कर रहा है...")
    app.run_polling()

if __name__ == "__main__":
    main()
