import os
import datetime
import nest_asyncio
import asyncio
import requests
import logging
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ===== Patch event loop untuk Render =====
nest_asyncio.apply()

# ===== KONFIGURASI ENVIRONMENT =====
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ADMIN_ID = os.getenv("ADMIN_ID", CHAT_ID)
PORT = int(os.environ.get("PORT", 10000))
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "telegrambot-ytdk.onrender.com")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not TOKEN or ":" not in TOKEN:
    raise SystemExit("❌ BOT_TOKEN kosong atau salah format.")
if not CHAT_ID:
    raise SystemExit("❌ CHAT_ID belum diisi di Render Environment!")

# ===== HANDLER /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo! Bot PDGLabs aktif dan siap digunakan.\n\n"
        "Perintah tersedia:\n"
        "• /post — kirim posting cepat\n"
        "• /id — lihat ID Telegram kamu"
    )
    logger.info(f"✅ /start dari {update.effective_chat.id}")

# ===== HANDLER /post =====
async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🌐 Kunjungi Website", url="https://pdglabs.xyz/")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = (
        "🚀 *PDGLabs Update!*\n\n"
        "Inovasi terbaru kami hadir hari ini!\n"
        "Klik tombol di bawah untuk mengunjungi website resmi kami.\n\n"
        f"🕒 {datetime.datetime.now().strftime('%d %B %Y, %H:%M')}"
    )
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
    logger.info("✅ Pesan /post terkirim")

# ===== HANDLER /id =====
async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 ID Telegram kamu: {update.message.chat_id}")

# ===== BANGUN APLIKASI TELEGRAM =====
application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("post", post))
application.add_handler(CommandHandler("id", get_id))

# ===== WEBHOOK HANDLER =====
async def webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    try:
        await application.process_update(update)
        logger.info("📩 Update diterima dan diproses handler.")
    except Exception as e:
        logger.error(f"❌ Error dalam process_update: {e}")
    return web.Response(text="✅ OK", status=200)

# ===== HEALTHCHECK =====
async def healthcheck(request):
    return web.Response(text="✅ PDGLabs Bot aktif dan sehat", status=200)

# ===== MAIN SERVER =====
async def main():
    webhook_url = f"https://{RENDER_HOSTNAME}/{TOKEN}"
    logger.info(f"🔗 Mendaftarkan webhook ke {webhook_url}")
    result = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}")
    logger.info(f"🌐 Webhook set result: {result.json()}")

    # ===== Inisialisasi dan start Application (WAJIB) =====
    await application.initialize()
    await application.start()
    logger.info("✅ Application Telegram berhasil diinisialisasi dan berjalan.")

    # ===== Jalankan server aiohttp =====
    app_web = web.Application()
    app_web.router.add_post(f"/{TOKEN}", webhook_handler)
    app_web.router.add_get("/", healthcheck)

    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logger.info(f"✅ Bot PDGLabs berjalan di port {PORT}")
    logger.info("📡 Menunggu pesan Telegram...")

    # ===== Loop agar tetap hidup =====
    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.warning("🛑 Bot dihentikan manual.")
    finally:
        await application.stop()
        await application.shutdown()
        logger.info("👋 Bot PDGLabs ditutup dengan aman.")

# ===== START =====
if __name__ == "__main__":
    asyncio.run(main())
