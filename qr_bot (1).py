import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import cv2
import numpy as np
import io
import os

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = '8702644463:AAEznMj2HjjH3ZeE_Dg7sUNk2FDY5E4IEiE'
PROXY_URL = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')

# Higher number of workers for parallel processing
executor = ThreadPoolExecutor(max_workers=10)
qr_detector = cv2.QRCodeDetector()

def process_qr_opencv(photo_bytes):
    """Extremely fast QR detection using OpenCV with grayscale conversion."""
    try:
        nparr = np.frombuffer(photo_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE) # Direct grayscale for speed
        
        if img is None:
            return []

        # Detect and decode
        data, bbox, straight_qrcode = qr_detector.detectAndDecode(img)
        if data:
            return [data]
        
        # Try multi-detection if single fails
        try:
            retval, decoded_info, points, straight_qrcodes = qr_detector.detectAndDecodeMulti(img)
            if retval:
                return [info for info in decoded_info if info]
        except:
            pass
            
        return []
    except Exception as e:
        logging.error(f"OpenCV Error: {e}")
        return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        await update.message.reply_text("QR code ပုံကို ပေးပို့ပါ။ အမြန်ဆုံး ဖတ်ပေးပါ့မယ်။")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # CRITICAL SPEED OPTIMIZATION: 
        # Instead of the largest photo [-1], use a medium-sized one [0 or 1] 
        # for much faster downloading while still being readable for QR.
        if update.message.photo:
            # photo[0] is smallest, photo[-1] is largest. 
            # We pick index 1 or 0 for speed.
            photo_index = 1 if len(update.message.photo) > 1 else 0
            file_obj = await update.message.photo[photo_index].get_file()
        elif update.message.document and update.message.document.mime_type.startswith('image/'):
            file_obj = await update.message.document.get_file()
        else:
            return

        # Fast download
        photo_bytes = await file_obj.download_as_bytearray()
        
        # Parallel decoding
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(executor, process_qr_opencv, photo_bytes)
        
        if not results:
            # If medium-sized fails, try the high-res one as fallback (only in private)
            if update.effective_chat.type == 'private' and update.message.photo and len(update.message.photo) > 1:
                file_obj = await update.message.photo[-1].get_file()
                photo_bytes = await file_obj.download_as_bytearray()
                results = await loop.run_in_executor(executor, process_qr_opencv, photo_bytes)
                if not results:
                    await update.message.reply_text("QR code မတွေ့ရှိပါဘူး။")
                    return
            else:
                return

        for text in results:
            await update.message.reply_text(f"QR Content:\n\n{text}")
            
    except Exception as e:
        logging.error(f"Handler Error: {e}")

if __name__ == '__main__':
    builder = ApplicationBuilder().token(TOKEN)
    if PROXY_URL:
        builder.proxy(PROXY_URL)
        builder.get_updates_proxy(PROXY_URL)

    # Use smaller connection pool and faster timeouts
    application = builder.build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_media))
    
    print("Turbo Speed Bot is starting...")
    application.run_polling(drop_pending_updates=True)
