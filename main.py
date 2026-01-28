from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio
import yt_dlp
import os

from config import API_ID, API_HASH, BOT_TOKEN, OWNER_NAME

# ---------------- BOT INIT ----------------
app = Client(
    "musicbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

vc = PyTgCalls(app)

# ---------------- SONG FETCH ----------------
def get_song(query):
    ydl_opts = {
        "format": "bestaudio",
        "quiet": True,
        "outtmpl": "song.%(ext)s"
    }

    if not query.startswith("http"):
        query = f"ytsearch1:{query}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if "entries" in info:
            info = info["entries"][0]

    duration = info.get("duration", 0)
    m = duration // 60
    s = duration % 60

    return {
        "title": info["title"],
        "duration": f"{m}:{s:02d}",
        "thumbnail": info["thumbnail"],
        "file": "song.webm"
    }

# ---------------- BUTTONS ----------------
def player_buttons():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("▶", callback_data="resume"),
                InlineKeyboardButton("⏸", callback_data="pause"),
                InlineKeyboardButton("⏹", callback_data="stop"),
            ],
            [
                InlineKeyboardButton("Close", callback_data="close")
            ]
        ]
    )

# ---------------- PLAY COMMAND ----------------
@app.on_message(filters.command("play") & filters.group)
async def play(_, message):
    if len(message.command) < 2:
        return await message.reply("❌ `/play song name` likho")

    query = " ".join(message.command[1:])
    searching = await message.reply("🔍 Searching song...")

    song = get_song(query)

    await vc.join_group_call(
        message.chat.id,
        AudioPiped(song["file"], HighQualityAudio())
    )

    caption = f"""
➤ **Started Streaming |**

▸ **Title :** {song['title']}
▸ **Duration :** {song['duration']}
▸ **Requested By :** {message.from_user.first_name}

━━━━━━━━━━━━━━━
🤖 *This bot is created by {OWNER_NAME}*
"""

    await searching.delete()

    await message.reply_photo(
        photo=song["thumbnail"],
        caption=caption,
        reply_markup=player_buttons()
    )

# ---------------- BUTTON CALLBACKS ----------------
@app.on_callback_query(filters.regex("pause"))
async def pause_cb(_, cb):
    await vc.pause_stream(cb.message.chat.id)
    await cb.answer("Paused ⏸")

@app.on_callback_query(filters.regex("resume"))
async def resume_cb(_, cb):
    await vc.resume_stream(cb.message.chat.id)
    await cb.answer("Playing ▶")

@app.on_callback_query(filters.regex("stop"))
async def stop_cb(_, cb):
    await vc.leave_group_call(cb.message.chat.id)
    await cb.message.edit("⏹ Music stopped")

@app.on_callback_query(filters.regex("close"))
async def close_cb(_, cb):
    await cb.message.delete()

# ---------------- START ----------------
vc.start()
app.run()
