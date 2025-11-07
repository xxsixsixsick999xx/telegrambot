import os
import datetime
import nest_asyncio
import asyncio
import requests
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Terapkan patch agar event loop tidak error di Render
nest_asyncio.apply()

# ===== KONFIGURASI ENVIRONMENT =====
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ADMIN_ID = os.getenv("ADMIN_ID", CHAT_ID)
PORT = int(os.environ.get("PORT", 10000))
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "telegrambot-ytdk.onrender.com")

if not TOKEN or ":" not in TOKEN:
    raise SystemExit("❌ BOT_TOKEN kosong atau salah format. Pastikan diisi di Environment Variables.")
if not CHAT_ID:
    raise SystemExit("❌ CHAT_ID belum diisi di Render Environment!")

# ===== HANDLER /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Maaf, kamu bukan admin PDGLabs.")
        return
    await update.message.reply_text(
        "👋 Halo Admin PDGLabs!\n"
        "Bot aktif dan siap digunakan.\n\n"
        "Ketik /post untuk melihat contoh posting otomatis."
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
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

# ===== APLIKASI TELEGRAM =====
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("post", post))

# ===== WEBHOOK HANDLER UNTUK TELEGRAM =====
async def webhook_handler(request):
    data = await request.json()
    await app.update_queue.put(Update.de_json(data, app.bot))
    print("📩 Pesan diterima dari Telegram.")
    return web.Response(text="✅ Update diterima")

# ===== ROUTE HEALTH CHECK =====
async def healthcheck(request):
    return web.Response(text="✅ PDGLabs Bot aktif dan sehat")

# ===== MAIN LOOP =====
async def main():
    # Registrasi webhook otomatis
    webhook_url = f"https://{RENDER_HOSTNAME}/{TOKEN}"
    print(f"🔗 Mendaftarkan webhook ke: {webhook_url}")
    set_hook = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}")
    print("🌐 Webhook set result:", set_hook.json())

    # Jalankan web server untuk menerima update Telegram
    app_web = web.Application()
    app_web.router.add_post(f"/{TOKEN}", webhook_handler)
    app_web.router.add_get("/", healthcheck)

    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"✅ PDGLabs Bot sedang berjalan di port {PORT} dan webhook aktif di {webhook_url}")

    # Tetap hidup terus agar Render tidak mematikan container
    while True:
        await asyncio.sleep(3600)  # tidur 1 jam lalu lanjut lagi (loop infinite)

# Jalankan event loop utama
asyncio.get_event_loop().run_until_complete(main())
