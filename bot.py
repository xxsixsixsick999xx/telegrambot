import os
import datetime
import nest_asyncio
import asyncio
import requests
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Terapkan patch event loop
nest_asyncio.apply()

# ===== ENV CONFIG =====
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ADMIN_ID = os.getenv("ADMIN_ID", CHAT_ID)
PORT = int(os.environ.get("PORT", 10000))
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "telegrambot-ytdk.onrender.com")

if not TOKEN or ":" not in TOKEN:
    raise SystemExit("❌ BOT_TOKEN kosong atau salah format.")
if not CHAT_ID:
    raise SystemExit("❌ CHAT_ID belum diisi di Render Environment!")

# ===== COMMAND HANDLERS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Halo! Bot PDGLabs aktif dan siap digunakan!\nKetik /post untuk contoh posting otomatis.")

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

# ===== TELEGRAM APP =====
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("post", post))

# ===== WEBHOOK HANDLER =====
async def webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.update_queue.put(update)
        print("📩 Update diterima dari Telegram")
        return web.Response(text="✅ Webhook OK", status=200)
    except Exception as e:
        print(f"❌ Error webhook: {e}")
        return web.Response(text=f"Error: {e}", status=500)

# ===== HEALTHCHECK =====
async def healthcheck(request):
    return web.Response(text="✅ PDGLabs Bot aktif dan sehat", status=200)

# ===== MAIN SERVER =====
async def main():
    webhook_url = f"https://{RENDER_HOSTNAME}/{TOKEN}"
    print(f"🔗 Mendaftarkan webhook ke {webhook_url}")
    result = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}")
    print("🌐 Webhook set result:", result.json())

    app_web = web.Application()
    app_web.router.add_post(f"/{TOKEN}", webhook_handler)
    app_web.router.add_get("/", healthcheck)

    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"✅ Bot PDGLabs berjalan di port {PORT}")
    print("📡 Menunggu pesan Telegram...")

    while True:
        await asyncio.sleep(60)

# ===== START =====
if __name__ == "__main__":
    asyncio.run(main())
