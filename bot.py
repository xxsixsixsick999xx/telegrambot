import datetime
import os
import asyncio
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ====== KONFIGURASI DASAR ======
TOKEN = os.getenv("BOT_TOKEN")   # Token dari BotFather
CHAT_ID = os.getenv("CHAT_ID")   # ID Channel (format: -100xxxxxxxxxx)
BANNER_URL = os.getenv("BANNER_URL", "https://pdglabs.xyz/banner.jpg")  # URL gambar (opsional)

# ====== CEK VALIDASI ======
if not TOKEN or ":" not in TOKEN:
    raise SystemExit("❌ BOT_TOKEN kosong / salah. Cek Environment Variables di Render!")
if not CHAT_ID:
    raise SystemExit("❌ CHAT_ID kosong. Pastikan diisi dengan ID channel (format: -100xxxx)!")

# ====== COMMAND /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"👤 User {user.username or user.first_name} menjalankan /start")
    await update.message.reply_text(
        "👋 Halo! Bot PDGLabs siap kirim postingan ke channel!\n\n"
        "Ketik /post untuk kirim contoh manual.\n"
        "Ketik /channel untuk tes kirim ke channel."
    )

# ====== COMMAND /post ======
async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_post(context, manual=True)
    await update.message.reply_text("✅ Postingan terkirim ke channel!")

# ====== COMMAND /channel (tes kirim) ======
async def channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_post(context, manual=True, test=True)
    await update.message.reply_text("✅ Tes kirim channel berhasil!")

# ====== FUNGSI KIRIM POST (bisa dipanggil manual / otomatis) ======
async def send_post(context: ContextTypes.DEFAULT_TYPE, manual=False, test=False):
    try:
        keyboard = [[InlineKeyboardButton("🌐 Kunjungi Website", url="https://pdglabs.xyz/")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        caption = (
            "🚀 *PDGLabs Update!*\n\n"
            "Kami hadir dengan inovasi terbaru hari ini!\n"
            "Klik tombol di bawah untuk mengunjungi website resmi kami.\n\n"
            f"🕒 {datetime.datetime.now().strftime('%d %B %Y, %H:%M')}"
        )

        # Jika test mode, kirim teks berbeda
        if test:
            caption = "📢 *Tes kirim ke channel PDGLabs berhasil!*\nCek tombol di bawah 👇"

        # Kirim gambar dengan caption
        await context.bot.send_photo(
            chat_id=CHAT_ID,
            photo=BANNER_URL,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

        # Logging
        if manual:
            print(f"✅ Manual post terkirim ke {CHAT_ID}")
        else:
            print(f"✅ Auto post terkirim ke {CHAT_ID}")

    except Exception as e:
        print(f"⚠️ Gagal kirim postingan: {e}")

# ====== AUTO POST SETIAP JAM ======
async def auto_post(app):
    await send_post(app)

# ====== NOTIFIKASI SAAT BOT ONLINE ======
async def notify_startup(app):
    try:
        await app.bot.send_message(
            chat_id=CHAT_ID,
            text="🟢 Bot PDGLabs sudah online dan siap kirim postingan dengan gambar!"
        )
        print(f"✅ Notifikasi startup terkirim ke {CHAT_ID}")
    except Exception as e:
        print(f"⚠️ Gagal kirim notifikasi startup: {e}")

# ====== FUNGSI UTAMA ======
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", post))
    app.add_handler(CommandHandler("channel", channel))

    # Jadwal auto post setiap jam
    scheduler = AsyncIOScheduler()
    scheduler.add_job(auto_post, "interval", hours=1, args=[app])
    scheduler.start()

    await notify_startup(app)
    print("✅ Bot PDGLabs sedang berjalan di Render...")
    await app.run_polling()

# ====== FIX LOOP UNTUK RENDER ======
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
