import logging
import time
import re
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
from info import ADMINS, LOG_CHANNEL
from database.ia_filterdb import save_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import temp, get_readable_time
from math import ceil

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

lock = asyncio.Lock()

# ----------------- नई जोड़ी गई /index टेक्स्ट कमांड -----------------
@Client.on_message(filters.command('index') & filters.user(ADMINS))
async def text_index_command(bot, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ कृपया चैनल का यूजरनेम दें।\nउदाहरण: `/index @movie4uyt`")
    
    chat_id = message.command[1]
    msg = await message.reply_text("🔍 चैनल की जांच की जा रही है...")
    
    try:
        chat = await bot.get_chat(chat_id)
        async for last_msg in bot.get_chat_history(chat.id, limit=1):
            last_msg_id = last_msg.id
    except Exception as e:
        return await msg.edit(f"❌ एरer: {e}\nसुनिश्चित करें कि यूजरनेम सही है और बॉट उस चैनल में जुड़ा है।")
    
    buttons = [
        [InlineKeyboardButton('Yes, Start Indexing', callback_data=f'index#accept#{chat.id}#{last_msg_id}#{message.from_user.id}')],
        [InlineKeyboardButton('Close', callback_data='close_data')]
    ]
    await msg.edit(
        f"📋 **चैनल मिला!**\n\n**नाम:** {chat.title}\n**ID:** `{chat.id}`\n**कुल अनुमानित मैसेज:** `{last_msg_id}`\n\nक्या आप इंडेक्सिंग शुरू करना चाहते हैं?",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ----------------- पुराना पुराना कोड यहाँ से चालू होता है -----------------
@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    if query.data.startswith('index_cancel'):
        temp.CANCEL = True
        return await query.answer("Cancelling Indexing")
    _, raju, chat, lst_msg_id, from_user = query.data.split("#")
    if raju == 'reject':
        await query.message.delete()
        await bot.send_message(int(from_user),
                               f'Your Submission for indexing {chat} has been declined by our moderators.',
                               reply_to_message_id=int(lst_msg_id))
        return

    if lock.locked():
        return await query.answer('Wait until previous process complete.', show_alert=True)
    msg = query.message

    await query.answer('Processing...⏳', show_alert=True)
    if int(from_user) not in ADMINS:
        await bot.send_message(int(from_user),
                               f'Your Submission for indexing {chat} has been accepted by our moderators and will be added soon.',
                               reply_to_message_id=int(lst_msg_id))
    await msg.edit(
        "Starting Indexing",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('Cancel', callback_data='index_cancel')]]
        )
    )
    try:
        chat = int(chat)
    except:
        chat = chat
    await index_files_to_db(int(lst_msg_id), chat, msg, bot)

@Client.on_message((filters.forwarded | (filters.regex(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")) & filters.text ) & filters.private & filters.incoming)
async def send_for_index(bot, message):
    if message.text:
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(message.text)
        if not match:
            return await message.reply('Invalid link')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id  = int(("-100" + chat_id))
    elif message.forward_from_chat and message.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = message.forward_from_message_id
        chat_id = message.forward_from_chat.username or message.forward_from_chat.id
    else:
        return
    try:
        await bot.get_chat(chat_id)
    except ChannelInvalid:
        return await message.reply('This may be a private channel / group. Make me an admin over there to index the files.')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Invalid Link specified.')
    except Exception as e:
        logger.exception(e)
        return await message.reply(f'Errors - {e}')
    try:
        k = await bot.get_messages(chat_id, last_msg_id)
    except:
        return await message.reply('Make Sure That Iam An Admin In The Channel, if channel is private')
    if k.empty:
        return await message.reply('This may be group and i am not a admin of the group.')

    if message.from_user.id in ADMINS:
        buttons = [
            [InlineKeyboardButton('Yes', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')],
            [InlineKeyboardButton('Close', callback_data='close_data')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        return await message.reply(
            f'Do you Want To Index This Channel/ Group ?\n\nChat ID/ Username: <code>{chat_id}</code>\nLast Message ID: <code>{last_msg_id}</code>\n\nɴᴇᴇᴅ sᴇᴛsᴋɪᴘ 👉🏻 /setskip',
            reply_markup=reply_markup)

    if type(chat_id) is int:
        try:
            link = (await bot.create_chat_invite_link(chat_id)).invite_link
        except ChatAdminRequired:
            return await message.reply('Make sure I am an admin in the chat and have permission to invite users.')
    else:
        link = f"@{message.forward_from_chat.username}"
    buttons = [
        [InlineKeyboardButton('Accept Index', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')],
        [InlineKeyboardButton('Reject Index', callback_data=f'index#reject#{chat_id}#{message.id}#{message.from_user.id}')]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await bot.send_message(LOG_CHANNEL,
                           f'#IndexRequest\n\nBy : {message.from_user.mention} (<code>{message.from_user.id}</code>)\nChat ID/ Username - <code> {chat_id}</code>\nLast Message ID - <code>{last_msg_id}</code>\nInviteLink - {link}',
                           reply_markup=reply_markup)
    await message.reply('ThankYou For the Contribution, Wait For My Moderators to verify the files.')

@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def set_skip_number(bot, message):
    if ' ' in message.text:
        _, skip = message.text.split(" ")
        try:
            skip = int(skip)
        except:
            return await message.reply("Skip number should be an integer.")
        await message.reply(f"Successfully set SKIP number as {skip}")
        temp.CURRENT = int(skip)
    else:
        await message.reply("Give me a skip number")

def get_progress_bar(percent, length=10):
    """Creates an emoji-based progress bar."""
    filled = int(length * percent / 100)
    unfilled = length - filled
    return '🟩' * filled + '⬜️' * unfilled

async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0
    BATCH_SIZE = 200
    start_time = time.time()

    async with lock:
        try:
            current = temp.CURRENT
            temp.CANCEL = False
            total_messages = lst_msg_id
            total_fetch = lst_msg_id - current
            if total_messages <= 0:
                await msg.edit(
                    "🚫 No Messages To Index.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Close', callback_data='close_data')]])
                )
                return
            batches = ceil(total_messages / BATCH_SIZE)
            for batch in range(batches):
                if temp.CANCEL:
                    break
                start_id = current + 1
                end_id = min(current + BATCH_SIZE, lst_msg_id)
                message_ids = range(start_id, end_id + 1)
                try:
                    messages = await bot.get_messages(chat, list(message_ids))
                    if not isinstance(messages, list):
                        messages = [messages]
                except Exception as e:
                    errors += len(message_ids)
                    current += len(message_ids)
                    continue
                for message in messages:
                    current += 1
                    try:
                        if message.empty:
                            deleted += 1
                            continue
                        elif not message.media:
                            no_media += 1
                            continue
                        elif message.media not in [enums.MessageMediaType.DOCUMENT, enums.MessageMediaType.VIDEO]:
                            unsupported += 1
                            continue
                        
                        # यहाँ फ़ाइल को डेटाबेस में सेव करने का लॉजिक काम करेगा
                        file_saved = await save_file(message)
                        if file_saved:
                            total_files += 1
                        else:
                            duplicate += 1
                    except Exception as e:
                        errors += 1
                
                # प्रोग्रेस बार अपडेट करने के लिए
                percent = (current / total_messages) * 100
                progress = get_progress_bar(percent)
                try:
                    await msg.edit(
                        f"📊 **Indexing Progress:**\n"
                        f"🔄 {progress} {percent:.1f}%\n"
                        f"📂 Saved: `{total_files}` | 🗂️ Duplicate: `{duplicate}`\n"
                        f"⏰ Time: `{get_readable_time(time.time() - start_time)}`"
