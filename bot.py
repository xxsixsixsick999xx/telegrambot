import datetime
import os
import asyncio
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ====== BACA TOKEN DAN CHAT ID DARI ENVIRONMENT VARIABLE (Render) ======
TOKEN = os.getenv("BOT_TOKEN")   # Token dari BotFather
CHAT_ID = os.getenv("CHAT_ID")   # Gunakan ID channel (format: -100xxxxxxxxxx)

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
        "👋 Halo! Bot PDGLabs aktif dan siap kirim ke channel!\n\n"
        "Ketik /post untuk kirim contoh ke channel.\n"
        "Ketik /channel untuk uji kirim manual."
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

    await context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown", reply_markup=reply_markup)
    await update.message.reply_text("✅ Pesan berhasil dikirim ke channel!")
    print(f"📩 Manual post dikirim oleh {update.effective_user.username or update.effective_user.first_name}")

# ====== COMMAND /channel (tes kirim manual ke channel) ======
async def channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text="📢 Tes kirim ke channel berhasil!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Website", url="https://pdglabs.xyz/")]])
        )
        await update.message.reply_text("✅ Pesan uji berhasil dikirim ke channel!")
        print(f"✅ Tes kirim ke channel berhasil oleh {update.effective_user.username or update.effective_user.first_name}")
    except Exception as e:
        print(f"⚠️ Gagal kirim ke channel: {e}")
        await update.message.reply_text(f"❌ Gagal kirim ke channel: {e}")

# ====== AUTO POST KE CHANNEL SETIAP JAM ======
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
            text="🟢 Bot PDGLabs sudah online dan siap kirim ke channel!"
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
    app.add_handler(CommandHandler("channel", channel))

    # Scheduler auto-post
    scheduler = AsyncIOScheduler()
    scheduler.add_job(auto_post, "interval", hours=1, args=[app])
    scheduler.start()

    # Kirim notifikasi saat bot aktif
    await notify_startup(app)

    print("✅ Bot PDGLabs sedang berjalan di Render...")
    await app.run_polling()

# ====== FIX LOOP UNTUK RENDER ======
if __name__ == "__main__":
    nest_asyncio.apply()  # mencegah error "event loop is already running"
    asyncio.run(main())
