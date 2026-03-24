import asyncio, logging, os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, URLInputFile
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

# دالة لجلب رابط الملف المباشر دون تحميله على السيرفر
def get_direct_url(url):
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['url'], info.get('title', 'Music')

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if await check_subscription(message.from_user.id):
        await message.answer(f"🎵 أهلاً بك! أرسل رابط الأغنية للتحميل المباشر.")
    else:
        await message.answer("⚠️ يجب الاشتراك أولاً لتفعيل البوت:", reply_markup=sub_kb())

@dp.callback_query(lambda c: c.data == "check_sub")
async def process_check_sub(callback_query: types.CallbackQuery):
    if await check_subscription(callback_query.from_user.id):
        await callback_query.message.edit_text("✅ تم التفعيل! أرسل الرابط الآن.")
    else:
        await callback_query.answer("⚠️ لم تشترك بعد في القناة!", show_alert=True)

@dp.message()
async def handle_music(message: types.Message):
    if not message.text or "http" not in message.text: return
    if not await check_subscription(message.from_user.id):
        await message.answer("❌ اشترك أولاً:", reply_markup=sub_kb())
        return

    m = await message.answer("⏳ جاري استخراج رابط التحميل...")
    try:
        direct_url, title = await asyncio.to_thread(get_direct_url, message.text)
        await message.answer_audio(audio=URLInputFile(direct_url, filename=f"{title}.mp3"), caption=f"✅ تم التحميل!\n🛒 متجر رامي: {CHANNEL_ID}")
        await m.delete()
    except Exception as e:
        logging.error(e)
        await m.edit_text("❌ عذراً، هذا الرابط غير مدعوم حالياً أو خاص.")

# استقرار السيرفر
async def handle_web(request): return web.Response(text="Bot is Running!")
async def main():
    app = web.Application(); app.router.add_get('/', handle_web)
    runner = web.AppRunner(app); await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
