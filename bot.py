import os
import datetime
import nest_asyncio
import asyncio
import requests
import logging
from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===== Patch event loop untuk Render =====
nest_asyncio.apply()

# ===== KONFIGURASI ENVIRONMENT =====
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ADMIN_ID = os.getenv("ADMIN_ID", CHAT_ID)
PORT = int(os.environ.get("PORT", 10000))
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "telegrambot-ytdk.onrender.com")

if not TOKEN or ":" not in TOKEN:
    raise SystemExit("❌ BOT_TOKEN kosong atau salah format.")
if not CHAT_ID:
    raise SystemExit("❌ CHAT_ID belum diisi di Render Environment!")

# ===== KONFIGURASI LOGGING =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== PENYIMPANAN DATA SEMENTARA =====
pending_uploads = {}
scheduler = AsyncIOScheduler()
scheduler.start()

# ===== HANDLER /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo Admin PDGLabs!\n"
        "Bot aktif dan siap digunakan.\n\n"
        "📦 Gunakan perintah berikut:\n"
        "/post → kirim posting cepat\n"
        "/upload → kirim teks/gambar untuk dijadwalkan\n"
        "/schedule <menit> → jadwalkan postingan\n"
        "/cancel → batalkan semua jadwal aktif"
    )

# ===== HANDLER /post =====
async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🌐 Kunjungi Website", url="https://pdglabs.xyz/")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = (
        "🚀 *PDGLabs Update!*\n\n"
        "Kami hadir dengan inovasi terbaru hari ini!\n"
        "Klik tombol di bawah untuk mengunjungi website resmi kami.\n\n"
        f"🕒 {datetime.datetime.now().strftime('%d %B %Y, %H:%M')}"
    )
    await context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown", reply_markup=reply_markup)
    await update.message.reply_text("✅ Postingan berhasil dikirim ke channel!")

# ===== HANDLER /upload =====
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    pending_uploads[chat_id] = {"type": None, "file": None, "caption": None}
    await update.message.reply_text("📤 Kirim teks atau gambar yang ingin dijadwalkan.")
    logger.info(f"Menunggu upload dari {chat_id}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in pending_uploads:
        pending_uploads[chat_id]["type"] = "text"
        pending_uploads[chat_id]["caption"] = update.message.text
        await update.message.reply_text("✅ Pesan disimpan! Gunakan /schedule <menit> untuk atur waktu posting.")
    else:
        await update.message.reply_text("ℹ️ Kirim /upload dulu sebelum mengirim konten.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in pending_uploads:
        file = await update.message.photo[-1].get_file()
        pending_uploads[chat_id]["type"] = "photo"
        pending_uploads[chat_id]["file"] = file.file_path
        pending_uploads[chat_id]["caption"] = update.message.caption or "📸 Foto PDGLabs!"
        await update.message.reply_text("✅ Foto disimpan! Gunakan /schedule <menit> untuk atur waktu posting.")
    else:
        await update.message.reply_text("ℹ️ Kirim /upload dulu sebelum kirim foto.")

# ===== HANDLER /schedule =====
async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id not in pending_uploads or not pending_uploads[chat_id].get("caption"):
        await update.message.reply_text("⚠️ Tidak ada konten yang diunggah. Kirim /upload dulu.")
        return

    try:
        delay = int(context.args[0]) if context.args else 1
    except ValueError:
        await update.message.reply_text("⚠️ Gunakan format: /schedule <menit>")
        return

    content = pending_uploads[chat_id]
    post_time = datetime.datetime.now() + datetime.timedelta(minutes=delay)

    async def send_scheduled():
        if content["type"] == "photo":
            await context.bot.send_photo(chat_id=CHAT_ID, photo=content["file"], caption=content["caption"])
        else:
            await context.bot.send_message(chat_id=CHAT_ID, text=content["caption"])
        logger.info(f"🕒 Jadwal posting {chat_id} tayang {post_time}")
        await context.bot.send_message(chat_id=chat_id, text="✅ Postingan otomatis berhasil dikirim!")

    scheduler.add_job(send_scheduled, 'date', run_date=post_time)
    await update.message.reply_text(f"🕒 Jadwal posting diset {delay} menit dari sekarang.")
    logger.info(f"Menjadwalkan posting dari {chat_id} dalam {delay} menit.")

# ===== HANDLER /cancel =====
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jobs = scheduler.get_jobs()
    if not jobs:
        await update.message.reply_text("⏹ Tidak ada jadwal aktif.")
        return
    for job in jobs:
        job.remove()
    await update.message.reply_text("🧹 Semua jadwal posting dibatalkan.")
    logger.info("Semua jadwal dibersihkan.")

# ===== WEBHOOK HANDLER =====
async def webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    logger.info("📩 Update diterima dari Telegram.")
    return web.Response(text="✅ Webhook OK", status=200)

# ===== HEALTH CHECK =====
async def healthcheck(request):
    return web.Response(text="✅ PDGLabs Bot aktif dan sehat", status=200)

# ===== MAIN FUNCTION =====
async def main():
    webhook_url = f"https://{RENDER_HOSTNAME}/{TOKEN}"
    logger.info(f"🔗 Mendaftarkan webhook ke {webhook_url}")
    result = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}")
    logger.info(f"🌐 Webhook set result: {result.json()}")

    # AIOHTTP server
    app_web = web.Application()
    app_web.router.add_post(f"/{TOKEN}", webhook_handler)
    app_web.router.add_get("/", healthcheck)

    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logger.info(f"✅ Bot PDGLabs berjalan di port {PORT}")
    logger.info("📡 Menunggu pesan Telegram...")

    while True:
        await asyncio.sleep(60)

# ===== BUILD TELEGRAM APP =====
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("post", post))
application.add_handler(CommandHandler("upload", upload))
application.add_handler(CommandHandler("schedule", schedule))
application.add_handler(CommandHandler("cancel", cancel))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

# ===== JALANKAN =====
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.warning("🛑 Bot dihentikan manual.")
    finally:
        import time
        logger.info("♻️ Menjaga koneksi tetap hidup di Render...")
        while True:
            time.sleep(600)
