import asyncio
import logging
import os
import uuid
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiohttp import web
import yt_dlp

# --- الإعدادات ---
API_TOKEN = '8764560809:AAGIP_1z_xFZv5TMezYEemYSZTnI5P-VznY' 
CHANNEL_ID = '@Ramy_Premium'
CHANNEL_LINK = 'https://t.me/Ramy_Premium'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

async def check_subscription(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'creator', 'administrator']
    except: return False

def sub_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 اشترك في القناة لتفعيل البوت", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="✅ تم الاشتراك، ابدأ التحميل", callback_data="check_sub")]
    ])

# دالة تحميل الصوت فقط
def download_audio(url):
    unique_id = uuid.uuid4().hex
    output_filename = f"music_{unique_id}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_filename,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        return f"{output_filename}.mp3"

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if await check_subscription(message.from_user.id):
        await message.answer(f"🎵 أهلاً بك يا {message.from_user.first_name}!\n\nأرسل رابط الأغنية (Spotify أو YouTube) وسأقوم بتحويلها لملف صووتي MP3 فوراً. 🚀")
    else:
        await message.answer("⚠️ عذراً، يجب الاشتراك في قناة المتجر أولاً:", reply_markup=sub_kb())

@dp.callback_query(lambda c: c.data == "check_sub")
async def process_check_sub(callback_query: types.CallbackQuery):
    if await check_subscription(callback_query.from_user.id):
        await callback_query.message.edit_text("تم التفعيل! أرسل رابط الأغنية الآن. ✅")
    else:
        await callback_query.answer("⚠️ لم تشترك بعد!", show_alert=True)

@dp.message()
async def handle_music(message: types.Message):
    if not message.text or "http" not in message.text: return
    
    if not await check_subscription(message.from_user.id):
        await message.answer("❌ اشترك أولاً:", reply_markup=sub_kb())
        return

    m = await message.answer("⏳ جاري سحب الموسيقى وتحويلها... انتظر لحظة")
    
    try:
        path = await asyncio.to_thread(download_audio, message.text)
        await message.answer_audio(
            audio=FSInputFile(path),
            caption=f"✅ تم التحميل بنجاح!\n\n🛒 متجر رامي: {CHANNEL_ID}"
        )
        if os.path.exists(path): os.remove(path)
        await m.delete()
    except Exception as e:
        logging.error(e)
        await m.edit_text("❌ حدث خطأ! تأكد من أن الرابط صحيح وعام.")

# استقرار Render
async def handle(request): return web.Response(text="Music Bot is Running! 🎶")
async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 8080))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
