import os
import json
import datetime
import asyncio
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ===== KONFIGURASI DASAR =====
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")        # ID channel, contoh: -100xxxx
ADMIN_ID = os.getenv("ADMIN_ID")      # ID kamu sendiri
DATA_FILE = "queue.json"

# ===== LOAD & SAVE DATA =====
def load_queue():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"scheduled": [], "repeat": []}

def save_queue(queue):
    with open(DATA_FILE, "w") as f:
        json.dump(queue, f, indent=4)

queue_data = load_queue()

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        return await update.message.reply_text("❌ Anda tidak diizinkan menggunakan bot ini.")
    await update.message.reply_text(
        "👋 Halo Admin PDGLabs!\n\n"
        "Gunakan:\n"
        "📸 Kirim gambar (caption = teks + link)\n"
        "⏰ /schedule HH:MM → Jadwal sekali\n"
        "🔁 /repeat HH:MM → Jadwal harian tetap\n"
        "📋 /list → Lihat semua jadwal\n"
        "📅 /next → Lihat postingan terdekat\n"
        "🗑️ /delete N → Hapus jadwal ke-N"
    )

# ====== UPLOAD KONTEN ======
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        return await update.message.reply_text("❌ Anda bukan admin bot ini.")

    if not update.message.photo:
        return await update.message.reply_text("📷 Kirim gambar dengan caption dan link!")

    photo = update.message.photo[-1].file_id
    caption = update.message.caption or "Tanpa caption"

    queue_data["pending"] = {"photo_id": photo, "caption": caption}
    save_queue(queue_data)

    await update.message.reply_text(
        "✅ Konten disimpan sementara.\nKirim `/schedule HH:MM` atau `/repeat HH:MM` untuk jadwal.",
        parse_mode="Markdown"
    )

# ====== /schedule HH:MM ======
async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        return await update.message.reply_text("❌ Anda bukan admin bot ini.")
    if "pending" not in queue_data:
        return await update.message.reply_text("⚠️ Kirim gambar dulu sebelum menjadwalkan.")

    try:
        time_str = context.args[0]
        datetime.datetime.strptime(time_str, "%H:%M")  # validasi waktu
    except:
        return await update.message.reply_text("⚠️ Format waktu salah. Contoh: `/schedule 14:30`", parse_mode="Markdown")

    new_item = {
        "photo_id": queue_data["pending"]["photo_id"],
        "caption": queue_data["pending"]["caption"],
        "schedule": time_str,
        "type": "once"
    }

    queue_data["scheduled"].append(new_item)
    del queue_data["pending"]
    save_queue(queue_data)

    await update.message.reply_text(f"⏰ Jadwal posting sekali ditambahkan untuk {time_str}.")
    print(f"📅 Jadwal baru ditambahkan: {time_str}")

# ====== /repeat HH:MM ======
async def repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        return await update.message.reply_text("❌ Anda bukan admin bot ini.")
    if "pending" not in queue_data:
        return await update.message.reply_text("⚠️ Kirim gambar dulu sebelum menjadwalkan.")

    try:
        time_str = context.args[0]
        datetime.datetime.strptime(time_str, "%H:%M")
    except:
        return await update.message.reply_text("⚠️ Format waktu salah. Contoh: `/repeat 09:00`", parse_mode="Markdown")

    new_item = {
        "photo_id": queue_data["pending"]["photo_id"],
        "caption": queue_data["pending"]["caption"],
        "schedule": time_str,
        "type": "repeat"
    }

    queue_data["repeat"].append(new_item)
    del queue_data["pending"]
    save_queue(queue_data)

    await update.message.reply_text(f"🔁 Jadwal harian tetap ditambahkan untuk {time_str}.")
    print(f"♻️ Jadwal harian baru: {time_str}")

# ====== /list ======
async def list_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        return await update.message.reply_text("❌ Anda bukan admin bot ini.")

    msg = "📋 *Daftar Jadwal:*\n\n"

    if not queue_data["scheduled"] and not queue_data["repeat"]:
        return await update.message.reply_text("📭 Tidak ada jadwal.", parse_mode="Markdown")

    if queue_data["scheduled"]:
        msg += "🕒 *Sekali:*\n"
        for i, item in enumerate(queue_data["scheduled"], 1):
            msg += f"{i}. {item['schedule']} — {item['caption'][:40]}...\n"
        msg += "\n"

    if queue_data["repeat"]:
        msg += "🔁 *Harian:*\n"
        for i, item in enumerate(queue_data["repeat"], 1):
            msg += f"{i}. {item['schedule']} — {item['caption'][:40]}...\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

# ====== /next ======
async def next_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        return await update.message.reply_text("❌ Anda bukan admin bot ini.")
    
    times = [item['schedule'] for item in queue_data["scheduled"]] + [item['schedule'] for item in queue_data["repeat"]]
    if not times:
        return await update.message.reply_text("📭 Tidak ada postingan dijadwalkan.")

    next_time = min(times)
    await update.message.reply_text(f"📅 Jadwal posting terdekat: {next_time}")

# ====== /delete N ======
async def delete_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        return await update.message.reply_text("❌ Anda bukan admin bot ini.")
    try:
        index = int(context.args[0]) - 1
        if index < len(queue_data["scheduled"]):
            deleted = queue_data["scheduled"].pop(index)
        else:
            index -= len(queue_data["scheduled"])
            deleted = queue_data["repeat"].pop(index)
        save_queue(queue_data)
        await update.message.reply_text(f"🗑️ Jadwal {deleted['schedule']} dihapus.")
    except:
        await update.message.reply_text("⚠️ Gunakan format: `/delete 1`", parse_mode="Markdown")

# ====== AUTO POSTER ======
async def auto_post(app):
    now = datetime.datetime.now().strftime("%H:%M")
    to_remove = []

    # Jadwal sekali
    for item in queue_data["scheduled"]:
        if item["schedule"] == now:
            await send_to_channel(app, item)
            to_remove.append(item)

    # Jadwal harian
    for item in queue_data["repeat"]:
        if item["schedule"] == now:
            await send_to_channel(app, item)

    # Hapus yang sudah dikirim (sekali)
    for item in to_remove:
        queue_data["scheduled"].remove(item)
    if to_remove:
        save_queue(queue_data)

# ====== KIRIM KE CHANNEL ======
async def send_to_channel(app, item):
    try:
        keyboard = [[InlineKeyboardButton("🌐 Website", url="https://pdglabs.xyz/")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await app.bot.send_photo(
            chat_id=CHAT_ID,
            photo=item["photo_id"],
            caption=item["caption"],
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

        await app.bot.send_message(chat_id=ADMIN_ID, text=f"✅ Postingan {item['schedule']} terkirim ke channel.")
        print(f"✅ Postingan {item['schedule']} terkirim.")
    except Exception as e:
        print(f"⚠️ Gagal kirim postingan: {e}")

# ====== FUNGSI UTAMA ======
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upload", upload))
    app.add_handler(CommandHandler("schedule", schedule))
    app.add_handler(CommandHandler("repeat", repeat))
    app.add_handler(CommandHandler("list", list_schedule))
    app.add_handler(CommandHandler("next", next_post))
    app.add_handler(CommandHandler("delete", delete_schedule))
    app.add_handler(MessageHandler(filters.PHOTO, upload))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(auto_post, "interval", minutes=1, args=[app])
    scheduler.start()

    print("✅ PDGLabs Scheduler Pro+ sedang berjalan di Render...")
    await app.run_polling()

# ====== FIX LOOP UNTUK RENDER ======
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
