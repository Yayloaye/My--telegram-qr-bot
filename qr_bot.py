import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pyzbar.pyzbar import decode
from PIL import Image
import io
import os

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = '8702644463:AAEznMj2HjjH3ZeE_Dg7sUNk2FDY5E4IEiE'

# Use proxy if available in environment
PROXY_URL = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! QR code ပုံကို ပေးပို့ပေးပါ။ ကျွန်တော် link ပြန်ထုတ်ပေးပါ့မယ်။\n\n"
        "Hello! Send me a QR code image and I'll extract the link for you."
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Get the photo with the highest resolution
        photo_file = await update.message.photo[-1].get_file()
        
        # Download the photo to a byte stream
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Open image using PIL
        img = Image.open(io.BytesIO(photo_bytes))
        
        # Decode QR code
        decoded_objects = decode(img)
        
        if not decoded_objects:
            await update.message.reply_text("QR code မတွေ့ရှိပါဘူး။ ကျေးဇူးပြု၍ ပုံကြည်လင်တာကို ပြန်ပို့ပေးပါ။\nNo QR code found. Please send a clearer image.")
            return

        for obj in decoded_objects:
            qr_data = obj.data.decode('utf-8')
            await update.message.reply_text(f"QR Content:\n\n{qr_data}")
    except Exception as e:
        logging.error(f"Error handling photo: {e}")
        await update.message.reply_text("အမှားတစ်ခု ဖြစ်သွားပါတယ်။ နောက်မှ ပြန်ကြိုးစားကြည့်ပါ။\nAn error occurred. Please try again later.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Check if the document is an image
        if update.message.document.mime_type and update.message.document.mime_type.startswith('image/'):
            doc_file = await update.message.document.get_file()
            doc_bytes = await doc_file.download_as_bytearray()
            
            img = Image.open(io.BytesIO(doc_bytes))
            decoded_objects = decode(img)
            
            if not decoded_objects:
                await update.message.reply_text("QR code မတွေ့ရှိပါဘူး။\nNo QR code found.")
                return

            for obj in decoded_objects:
                qr_data = obj.data.decode('utf-8')
                await update.message.reply_text(f"QR Content:\n\n{qr_data}")
        else:
            await update.message.reply_text("ကျေးဇူးပြု၍ ပုံကို ပေးပို့ပေးပါ။\nPlease send an image file.")
    except Exception as e:
        logging.error(f"Error handling document: {e}")
        await update.message.reply_text("အမှားတစ်ခု ဖြစ်သွားပါတယ်။ နောက်မှ ပြန်ကြိုးစားကြည့်ပါ။\nAn error occurred. Please try again later.")

if __name__ == '__main__':
    builder = ApplicationBuilder().token(TOKEN)
    
    # Configure proxy if it exists
    if PROXY_URL:
        builder.proxy(PROXY_URL)
        builder.get_updates_proxy(PROXY_URL)
        print(f"Using proxy: {PROXY_URL}")

    application = builder.build()
    
    start_handler = CommandHandler('start', start)
    photo_handler = MessageHandler(filters.PHOTO, handle_photo)
    document_handler = MessageHandler(filters.Document.IMAGE, handle_document)
    
    application.add_handler(start_handler)
    application.add_handler(photo_handler)
    application.add_handler(document_handler)
    
    print("Bot is starting...")
    application.run_polling()
