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

# ===== Patch event loop =====
nest_asyncio.apply()

# ===== Konfigurasi =====
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

# ===== Handler =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo! Bot PDGLabs aktif dan siap digunakan.\n\n"
        "Perintah:\n"
        "• /post — kirim posting cepat\n"
        "• /id — lihat ID Telegram kamu"
    )
    logger.info(f"✅ /start dari {update.effective_chat.id}")

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

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 ID Telegram kamu: {update.message.chat_id}")

# ===== Buat instance aplikasi =====
application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("post", post))
application.add_handler(CommandHandler("id", get_id))

# ===== Webhook handler =====
async def webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        logger.info("📩 Update diterima & diproses handler.")
        return web.Response(text="✅ OK", status=200)
    except Exception as e:
        logger.error(f"❌ Error di webhook_handler: {e}")
        return web.Response(text=f"❌ Error: {e}", status=500)

# ===== Health check =====
async def healthcheck(request):
    return web.Response(text="✅ PDGLabs Bot aktif & sehat", status=200)

# ===== Main =====
async def main():
    webhook_url = f"https://{RENDER_HOSTNAME}/{TOKEN}"
    logger.info(f"🔗 Mendaftarkan webhook ke {webhook_url}")
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}")

    # Inisialisasi aplikasi telegram terlebih dahulu
    await application.initialize()
    await application.start()
    logger.info("✅ Application Telegram siap menerima update.")

    # Jalankan server aiohttp
    app_web = web.Application()
    app_web.router.add_post(f"/{TOKEN}", webhook_handler)
    app_web.router.add_get("/", healthcheck)

    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logger.info(f"✅ Bot PDGLabs berjalan di port {PORT}")
    logger.info("📡 Menunggu pesan Telegram...")

    # Biarkan aplikasi berjalan terus
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.warning("🛑 Bot dihentikan manual.")
        try:
            asyncio.get_event_loop().run_until_complete(application.stop())
            asyncio.get_event_loop().run_until_complete(application.shutdown())
        except Exception:
            pass
        import time
        logger.info("♻️ Menjaga koneksi tetap hidup di Render...")
        while True:
            time.sleep(600)
