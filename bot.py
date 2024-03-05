import os
import time
import json
import random
import asyncio
import aiohttp
import subprocess
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image
from pyrogram import Client, filters
from configs import Config
from core.handlers.main_db_handler import db
from core.display_progress import progress_for_pyrogram, humanbytes
from core.handlers.force_sub_handler import handle_force_subscribe
from core.handlers.upload_video_handler import send_video_handler
from core.handlers.broadcast_handlers import broadcast_handler
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserNotParticipant, MessageNotModified

AHBot = Client(Config.BOT_USERNAME, bot_token=Config.BOT_TOKEN, api_id=Config.API_ID, api_hash=Config.API_HASH)


@AHBot.on_message(filters.command(["start", "help"]) & filters.private)
async def HelpWatermark(bot, cmd):
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
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Developer", url="https://t.me/AbirHasan2005"),
             InlineKeyboardButton("Support Group", url="https://t.me/DevsZone")],
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


async def get_duration(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return float(result.stdout)


def get_video_duration(filepath):
    metadata = extractMetadata(createParser(filepath))
    if metadata.has("duration"):
        return metadata.get('duration').seconds
    else:
        return 0


@AHBot.on_message(filters.command("settings") & filters.private)
async def SettingsBot(bot, cmd):
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
    ## --- Checks --- ##
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
    if int(watermark_size) == 5:
        size_tag = "5%"
    elif int(watermark_size) == 7:
        size_tag = "7%"
    elif int(watermark_size) == 10:
        size_tag = "10%"
    elif int(watermark_size) == 15:
        size_tag = "15%"
    elif int(watermark_size) == 20:
        size_tag = "20%"
    elif int(watermark_size) == 25:
        size_tag = "25%"
    elif int(watermark_size) == 30:
        size_tag = "30%"
    elif int(watermark_size) == 35:
        size_tag = "35%"
    elif int(watermark_size) == 40:
        size_tag = "40%"
    elif int(watermark_size) == 45:
        size_tag = "45%"
    else:
        size_tag = "7%"
    ## --- Next --- ##
    await cmd.reply_text(
        text="Here you can set your Watermark Settings:",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(f"Watermark Position - {position_tag}", callback_data="lol")],
                [InlineKeyboardButton("Set Top Left", callback_data=f"position_5:5"),
                 InlineKeyboardButton("Set Top Right", callback_data=f"position_main_w-overlay_w-5:5")],
                [InlineKeyboardButton("Set Bottom Left", callback_data=f"position_5:main_h-overlay_h"),
                 InlineKeyboardButton("Set Bottom Right",
                                      callback_data=f"position_main_w-overlay_w-5:main_h-overlay_h-5")],
                [InlineKeyboardButton(f"Watermark Size - {size_tag}", callback_data="lel")],
                [InlineKeyboardButton("5%", callback_data=f"size_5"), InlineKeyboardButton("7%", callback_data=f"size_7"),
                 InlineKeyboardButton("10%", callback_data=f"size_10"), InlineKeyboardButton("15%", callback_data=f"size_15"),
                 InlineKeyboardButton("20%", callback_data=f"size_20")],
                [InlineKeyboardButton("25%", callback_data=f"size_25"), InlineKeyboardButton("30%", callback_data=f"size_30"),
                 InlineKeyboardButton("35%", callback_data=f"size_35"), InlineKeyboardButton("40%", callback_data=f"size_40"),
                 InlineKeyboardButton("45%", callback_data=f"size_45")],
                [InlineKeyboardButton(f"Reset Settings To Default", callback_data="reset")]
            ]
        )
    )


@AHBot.on_message((filters.document | filters.video | filters.photo) & filters.private)
async def VidWatermarkAdder(bot, cmd):
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
    if Config.WATERMARK_CHANNEL:
        watermark_channel = int(Config.LOG_CHANNEL)
        try:
            media = cmd
            watermarked_media = await media.forward(chat_id=watermark_channel)
            await watermarked_media.reply_text("Forwarded to Handler")
            if Config.DELETE_AFTER_TRANSFER:
                await media.delete()
        except FloodWait as e:
            await asyncio.sleep(e.x)
            return await media.copy_to(watermark_channel)
        except Exception as e:
            await media.reply_text(e)
            return
    else:
        await cmd.reply_text("Contact to [Assistant](https://t.me/AbirHasan2005) to set `WATERMARK_CHANNEL`.")
        return


@AHBot.on_message(filters.command(["broadcast"]) & filters.private & filters.user(Config.OWNER_ID))
async def broadcast_handler_open(bot, cmd):
    await broadcast_handler(bot, cmd)


@AHBot.on_message(filters.command(["getsubs"]) & filters.private & filters.user(Config.OWNER_ID))
async def get_all_subs(bot, cmd):
    await cmd.reply_text(text=await db.total_users())


@AHBot.on_message(filters.command(["send"]) & filters.private & filters.user(Config.OWNER_ID))
async def send_vid(bot, message):
    await send_video_handler(bot, message)


@AHBot.on_callback_query(filters.regex(pattern=r"position_(.*)"))
async def change_position(bot, cq):
    current_position = await db.get_position(cq.from_user.id)
    if current_position == cq.data.split("_")[1]:
        await cq.answer("You have already set this position!", show_alert=True)
        return
    await db.set_position(cq.from_user.id, cq.data.split("_")[1])
    await cq.answer("Position Changed Successfully!", show_alert=True)


@AHBot.on_callback_query(filters.regex(pattern=r"size_(.*)"))
async def change_size(bot, cq):
    current_size = await db.get_size(cq.from_user.id)
    if current_size == cq.data.split("_")[1]:
        await cq.answer("You have already set this size!", show_alert=True)
        return
    await db.set_size(cq.from_user.id, cq.data.split("_")[1])
    await cq.answer("Size Changed Successfully!", show_alert=True)


@AHBot.on_callback_query(filters.regex(pattern=r"reset"))
async def reset_settings(bot, cq):
    await db.delete_user(cq.from_user.id)
    await db.add_user(cq.from_user.id)
    await cq.answer("Settings reset successfully!", show_alert=True)


AHBot.run()
