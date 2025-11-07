import os
import nest_asyncio
import asyncio
import logging
import requests
import datetime
from aiohttp import web
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# === Patch untuk Render ===
nest_asyncio.apply()

# === Konfigurasi Environment ===
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHAT_ID")  # ID channel tujuan (gunakan tanda -100 di depan)
ADMIN_ID = os.getenv("ADMIN_ID", CHANNEL_ID)
PORT = int(os.environ.get("PORT", 10000))
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "telegrambot-ytdk.onrender.com")

if not TOKEN:
    raise SystemExit("❌ BOT_TOKEN belum diatur di Render Environment!")
if not CHANNEL_ID:
    raise SystemExit("❌ CHAT_ID (Channel tujuan) belum diatur!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Storage sementara konten (RAM)
scheduled_posts = {}
latest_upload = {}

# === Aplikasi Telegram ===
application = ApplicationBuilder().token(TOKEN).build()

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo! Bot PDGLabs siap menerima konten.\n\n"
        "Kirim foto/video + caption untuk dijadwalkan.\n\n"
        "🕓 Perintah:\n"
        "• /schedule <menit> → kirim terjadwal\n"
        "• /list → lihat jadwal\n"
        "• /cancel <id> → hapus jadwal\n"
        "• /postnow → langsung posting\n"
        "• /id → lihat ID kamu"
    )

# === /id ===
async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 ID Telegram kamu: {update.message.chat_id}")

# === Simpan konten terakhir yang dikirim ===
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != int(ADMIN_ID):
        return await update.message.reply_text("🚫 Kamu tidak punya izin mengunggah konten.")

    caption = update.message.caption or "(tidak ada caption)"
    media = None

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        media = ("photo", file_id)
    elif update.message.video:
        file_id = update.message.video.file_id
        media = ("video", file_id)
    else:
        return await update.message.reply_text("⚠️ Kirim foto atau video dengan caption.")

    latest_upload[update.message.chat_id] = {"media": media, "caption": caption}
    await update.message.reply_text("✅ Konten tersimpan! Ketik `/schedule <menit>` untuk jadwalkan upload.")

# === /schedule ===
async def schedule_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != int(ADMIN_ID):
        return await update.message.reply_text("🚫 Akses hanya untuk admin!")

    if update.message.chat_id not in latest_upload:
        return await update.message.reply_text("⚠️ Belum ada konten tersimpan. Kirim dulu foto/video!")

    try:
        delay = int(context.args[0])
    except (IndexError, ValueError):
        return await update.message.reply_text("❌ Gunakan format: `/schedule <menit>`")

    content = latest_upload[update.message.chat_id]
    post_time = datetime.datetime.now() + datetime.timedelta(minutes=delay)
    job_id = f"job_{int(post_time.timestamp())}"

    scheduled_posts[job_id] = {"time": post_time, "content": content}
    scheduler.add_job(send_scheduled_post, "date", run_date=post_time, args=[content, job_id])

    await update.message.reply_text(
        f"📆 Konten dijadwalkan untuk {post_time.strftime('%d %B %Y %H:%M')}\n🆔 ID: `{job_id}`",
        parse_mode="Markdown",
    )

# === Kirim ke Channel ===
async def send_scheduled_post(content, job_id):
    media_type, file_id = content["media"]
    caption = content["caption"]

    try:
        if media_type == "photo":
            await application.bot.send_photo(CHANNEL_ID, file_id, caption=caption)
        elif media_type == "video":
            await application.bot.send_video(CHANNEL_ID, file_id, caption=caption)

        logger.info(f"✅ Posting berhasil ke channel (Job: {job_id})")
        scheduled_posts.pop(job_id, None)

    except Exception as e:
        logger.error(f"❌ Gagal kirim postingan: {e}")

# === /list ===
async def list_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not scheduled_posts:
        return await update.message.reply_text("🗓 Tidak ada jadwal posting.")
    msg = "📅 Jadwal posting aktif:\n\n"
    for job_id, data in scheduled_posts.items():
        msg += f"🆔 {job_id}\n⏰ {data['time'].strftime('%d %B %Y %H:%M')}\n\n"
    await update.message.reply_text(msg)

# === /cancel ===
async def cancel_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("⚠️ Gunakan format: `/cancel <id>`")

    job_id = context.args[0]
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        scheduled_posts.pop(job_id, None)
        await update.message.reply_text(f"❌ Jadwal `{job_id}` dibatalkan.", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ ID tidak ditemukan.")

# === /postnow ===
async def post_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id not in latest_upload:
        return await update.message.reply_text("⚠️ Tidak ada konten terakhir yang bisa dikirim.")

    await send_scheduled_post(latest_upload[update.message.chat_id], "manual")
    await update.message.reply_text("🚀 Konten dikirim ke channel sekarang!")

# === Setup Command Handlers ===
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("id", get_id))
application.add_handler(CommandHandler("schedule", schedule_post))
application.add_handler(CommandHandler("list", list_schedule))
application.add_handler(CommandHandler("cancel", cancel_schedule))
application.add_handler(CommandHandler("postnow", post_now))
application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handle_media))

# === Scheduler ===
scheduler = AsyncIOScheduler()
scheduler.start()

# === Webhook ===
async def webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return web.Response(text="✅ OK", status=200)

# === Healthcheck ===
async def healthcheck(request):
    return web.Response(text="✅ PDGLabs Bot aktif", status=200)

# === Main ===
async def main():
    webhook_url = f"https://{RENDER_HOSTNAME}/{TOKEN}"
    logger.info(f"🔗 Mendaftarkan webhook ke {webhook_url}")
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}")

    await application.initialize()
    await application.start()

    app_web = web.Application()
    app_web.router.add_post(f"/{TOKEN}", webhook_handler)
    app_web.router.add_get("/", healthcheck)

    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logger.info(f"✅ Bot PDGLabs berjalan di port {PORT}")
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
