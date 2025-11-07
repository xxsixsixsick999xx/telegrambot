import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ====== BACA TOKEN DAN CHAT ID DARI ENVIRONMENT VARIABLE (Render) ======
TOKEN = os.getenv("BOT_TOKEN")   # Nama variabel persis di Render Environment
CHAT_ID = os.getenv("CHAT_ID")   # Nama variabel persis di Render Environment

# ====== CEK VALIDASI TOKEN DAN CHAT ID ======
if not TOKEN or ":" not in TOKEN:
    raise SystemExit("❌ BOT_TOKEN kosong atau salah format. Cek Environment Variables di Render!")

if not CHAT_ID:
    raise SystemExit("❌ CHAT_ID kosong. Pastikan sudah diisi di Render Environment!")

# ====== COMMAND /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo! Bot PDGLabs siap!\n\n"
        "Ketik /post untuk melihat contoh auto-post dengan tombol website."
    )

# ====== COMMAND /post ======
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

# ====== OTOMATIS POST SETIAP JAM ======
async def auto_post(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID:
        keyboard = [[InlineKeyboardButton("🌐 Kunjungi Website", url="https://pdglabs.xyz/")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text="📰 Auto-post dari PDGLabs!\nKunjungi website resmi kami untuk update terbaru.",
            reply_markup=reply_markup
        )
        print(f"✅ Pesan otomatis terkirim ke {CHAT_ID}")
    else:
        print("⚠️ CHAT_ID tidak ditemukan. Cek Environment Variables di Render.")

# ====== FUNGSI UTAMA ======
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", post))

    # Auto-post setiap 1 jam
    scheduler = AsyncIOScheduler()
    scheduler.add_job(auto_post, "interval", hours=1, args=[ContextTypes.DEFAULT_TYPE])
    scheduler.start()

    print("✅ Bot PDGLabs sedang berjalan di Render...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
