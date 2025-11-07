import datetime
import os
import asyncio
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
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
    user = update.effective_user
    print(f"👤 User {user.username or user.first_name} menjalankan /start")
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
    print(f"📩 Manual post dikirim oleh {update.effective_user.username or update.effective_user.first_name}")

# ====== AUTO POST SETIAP JAM ======
async def auto_post(app):
    try:
        keyboard = [[InlineKeyboardButton("🌐 Kunjungi Website", url="https://pdglabs.xyz/")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await app.bot.send_message(
            chat_id=CHAT_ID,
            text="📰 Auto-post dari PDGLabs!\nKunjungi website resmi kami untuk update terbaru.",
            reply_markup=reply_markup
        )
        print(f"✅ Pesan otomatis terkirim ke {CHAT_ID}")
    except Exception as e:
        print(f"⚠️ Gagal kirim pesan otomatis: {e}")

# ====== NOTIFIKASI STARTUP ======
async def notify_startup(app):
    try:
        await app.bot.send_message(
            chat_id=CHAT_ID,
            text="🟢 Bot PDGLabs sudah online dan siap digunakan!"
        )
        print(f"✅ Notifikasi startup terkirim ke {CHAT_ID}")
    except Exception as e:
        print(f"⚠️ Gagal kirim notifikasi startup: {e}")

# ====== FUNGSI UTAMA ======
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Tambah handler command
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", post))

    # Scheduler untuk auto-post
    scheduler = AsyncIOScheduler()
    scheduler.add_job(auto_post, "interval", hours=1, args=[app])
    scheduler.start()

    # Kirim notifikasi saat bot aktif
    await notify_startup(app)

    print("✅ Bot PDGLabs sedang berjalan di Render...")
    await app.run_polling()

# ====== FIX LOOP UNTUK RENDER ======
if __name__ == "__main__":
    nest_asyncio.apply()  # biar event loop bisa jalan di Render tanpa bentrok
    asyncio.run(main())
