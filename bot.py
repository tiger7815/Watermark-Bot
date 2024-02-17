import os
import time
import json
import random
import asyncio
import aiohttp
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image
from core.ffmpeg import vidmark
from core.clean import delete_all, delete_trash
from pyrogram import Client, filters
from configs import Config
from core.handlers.main_db_handler import db
from core.display_progress import progress_for_pyrogram, humanbytes
from core.handlers.force_sub_handler import handle_force_subscribe
from core.handlers.upload_video_handler import send_video_handler
from core.handlers.broadcast_handlers import broadcast_handler
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors.exceptions.flood_420 import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, MessageNotModified

AHBot = Client(Config.BOT_USERNAME, bot_token=Config.BOT_TOKEN, api_id=Config.API_ID, api_hash=Config.API_HASH)


@AHBot.on_message(filters.command(["start", "help"]) & filters.private)
async def help_watermark(bot, cmd):
    if not await db.is_user_exist(cmd.from_user.id):
        await db.add_user(cmd.from_user.id)
        await bot.send_message(
            Config.LOG_CHANNEL,
            f"#NEW_USER: \n\nNew User [{cmd.from_user.first_name}](tg://user?id={cmd.from_user.id}) started @{Config.BOT_USERNAME} !!"
        )
    if Config.UPDATES_CHANNEL:
        fsub = await handle_force_subscribe(bot, cmd)
        if fsub == 400:
            return
    await cmd.reply_text(
        text=Config.USAGE_WATERMARK_ADDER,
        parse_mode="markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Developer", url="https://t.me/AbirHasan2005"), InlineKeyboardButton("Support Group", url="https://t.me/DevsZone")],
            [InlineKeyboardButton("Bots Channel", url="https://t.me/Discovery_Updates")],
            [InlineKeyboardButton("Source Code", url="https://github.com/AbirHasan2005/Watermark-Bot")]
        ]),
        disable_web_page_preview=True
    )


@AHBot.on_message(filters.command(["reset"]) & filters.private)
async def reset(bot, update):
    await db.delete_user(update.from_user.id)
    await db.add_user(update.from_user.id)
    await update.reply_text("Settings reset successfully")


@AHBot.on_message(filters.command("settings") & filters.private)
async def settings_bot(bot, cmd):
    if not await db.is_user_exist(cmd.from_user.id):
        await db.add_user(cmd.from_user.id)
        await bot.send_message(
            Config.LOG_CHANNEL,
            f"#NEW_USER: \n\nNew User [{cmd.from_user.first_name}](tg://user?id={cmd.from_user.id}) started @{Config.BOT_USERNAME} !!"
        )
    if Config.UPDATES_CHANNEL:
        fsub = await handle_force_subscribe(bot, cmd)
        if fsub == 400:
            return
    # --- Checks --- #
    position_tag = None
    watermark_position = await db.get_position(cmd.from_user.id)
    if watermark_position == "5:main_h-overlay_h":
        position_tag = "Bottom Left"
    elif watermark_position == "main_w-overlay_w-5:main_h-overlay_h-5":
        position_tag = "Bottom Right"
    elif watermark_position == "main_w-overlay_w-5:5":
        position_tag = "Top Right"
    elif watermark_position == "5:5":
        position_tag = "Top Left"

    watermark_size = await db.get_size(cmd.from_user.id)
    size_tag = f"{watermark_size}%"
    # --- Next --- #
    await cmd.reply_text(
        text="Here you can set your Watermark Settings:",
        disable_web_page_preview=True,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Watermark Position - {position_tag}", callback_data="lol")],
            [InlineKeyboardButton("Set Top Left", callback_data=f"position_5:5"), InlineKeyboardButton("Set Top Right", callback_data=f"position_main_w-overlay_w-5:5")],
            [InlineKeyboardButton("Set Bottom Left", callback_data=f"position_5:main_h-overlay_h"), InlineKeyboardButton("Set Bottom Right", callback_data=f"position_main_w-overlay_w-5:main_h-overlay_h-5")],
            [InlineKeyboardButton(f"Watermark Size - {size_tag}", callback_data="lel")],
            [InlineKeyboardButton("5%", callback_data="size_5"), InlineKeyboardButton("7%", callback_data="size_7"), InlineKeyboardButton("10%", callback_data="size_10"), InlineKeyboardButton("15%", callback_data="size_15"), InlineKeyboardButton("20%", callback_data="size_20")],
            [InlineKeyboardButton("25%", callback_data="size_25"), InlineKeyboardButton("30%", callback_data="size_30"), InlineKeyboardButton("35%", callback_data="size_30"), InlineKeyboardButton("40%", callback_data="size_40"), InlineKeyboardButton("45%", callback_data="size_45")],
            [InlineKeyboardButton(f"Reset Settings To Default", callback_data="reset")]
        ])
    )


@AHBot.on_message((filters.document | filters.video | filters.photo) & filters.private)
async def vid_watermark_adder(bot, cmd):
    if not await db.is_user_exist(cmd.from_user.id):
        await db.add_user(cmd.from_user.id)
        await bot.send_message(
            Config.LOG_CHANNEL,
            f"#NEW_USER: \n\nNew User [{cmd.from_user.first_name}](tg://user?id={cmd.from_user.id}) started @{Config.BOT_USERNAME} !!"
        )
    if Config.UPDATES_CHANNEL:
        fsub = await handle_force_subscribe(bot, cmd)
        if fsub == 400:
            return
    # --- Noobie Process --- #
    if cmd.photo or (cmd.document and cmd.document.mime_type.startswith("image/")):
        editable = await cmd.reply_text("Downloading Image ...")
        watermark_path = os.path.join(Config.DOWN_PATH, str(cmd.from_user.id), "thumb.jpg")
        await asyncio.sleep(5)
        c_time = time.time()
        await bot.download_media(
            message=cmd,
            file_name=watermark_path,
        )
        await editable.delete()
        await cmd.reply_text("This Saved as Next Video Watermark!\n\nNow Send any Video to start adding Watermark to the Video!")
        return
    else:
        pass
    working_dir = os.path.join(Config.DOWN_PATH, "WatermarkAdder")
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    watermark_path = os.path.join(Config.DOWN_PATH, str(cmd.from_user.id), "thumb.jpg")
    if not os.path.exists(watermark_path):
        await cmd.reply_text("You Didn't Set Any Watermark!\n\nSend any JPG or PNG Picture ...")
        return
    file_type = cmd.video or cmd.document
    if not file_type.mime_type.startswith("video/"):
        await cmd.reply_text("This is not a Video!\n\nSend me a Video to Add Watermark.")
        return
    # --- Progress Start --- #
    editable = await cmd.reply_text("Downloading ...")
    c_time = time.time()
    vid_dir_path = os.path.join(Config.DOWN_PATH, str(cmd.from_user.id))
    if not os.path.isdir(vid_dir_path):
        os.makedirs(vid_dir_path)
    vid_path = await cmd.download(
        file_name=vid_dir_path
    )
    # --- Media Info --- #
    video_info = await bot.get_media_group(
        chat_id=cmd.chat.id,
        message_id=cmd.message_id
    )
    try:
        duration = video_info[0].duration
    except AttributeError:
        duration = 0
    metadata = extractMetadata(createParser(vid_path))
    if metadata:
        duration = metadata.get("duration").seconds
    else:
        duration = 0
    # --- Progress Check --- #
    def prog_func(current, total):
        now = time.time()
        diff = now - c_time
        prog_str = "[{0}{1}]".format(
            ''.join(["■" for i in range(math.floor(current * 10 / total))]),
            ''.join(["□" for i in range(10 - math.floor(current * 10 / total))])
        )
        return f"{humanbytes(current)} of {humanbytes(total)}\nProgress: {((current * 100) / total):.2f}%\nETA: {((diff / current) * (total - current)):.2f} Seconds\n{prog_str}"

    await editable.edit(
        text="Starting to Add Watermark to Video ...",
        parse_mode="markdown"
    )
    wm_pos = await db.get_position(cmd.from_user.id)
    wm_size = await db.get_size(cmd.from_user.id)
    await asyncio.sleep(3)
    # --- Progress End --- #
    await asyncio.gather(
        vidmark(
            input_vid_path=vid_path,
            out_vid_path=os.path.join(vid_dir_path, "watermarked.mp4"),
            watermark_path=watermark_path,
            pos=wm_pos,
            size=wm_size,
            prog=prog_func
        )
    )
    await send_video_handler(
        bot,
        cmd,
        editable,
        vid_dir_path,
        duration
    )


@AHBot.on_callback_query(filters.regex(pattern=r"^position_"))
async def position_cq(bot, cmd):
    pos = cmd.data.split("_", 1)[-1]
    await db.update_position(cmd.from_user.id, pos)
    await cmd.answer("Position Updated Successfully!")
    await settings_bot(bot, cmd.message)


@AHBot.on_callback_query(filters.regex(pattern=r"^size_"))
async def size_cq(bot, cmd):
    size = cmd.data.split("_", 1)[-1]
    await db.update_size(cmd.from_user.id, size)
    await cmd.answer("Size Updated Successfully!")
    await settings_bot(bot, cmd.message)


@AHBot.on_callback_query(filters.regex(pattern=r"reset"))
async def reset_settings(bot, cmd):
    await db.update_position(cmd.from_user.id, "5:main_h-overlay_h")
    await db.update_size(cmd.from_user.id, "7")
    await cmd.answer("Settings Reset to Default Successfully!")
    await settings_bot(bot, cmd.message)
