import asyncio, logging, os, uuid
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiohttp import web
import yt_dlp

# --- الإعدادات (ضع توكن بوت الموسيقى هنا) ---
API_TOKEN = '8764560809:AAGIP_1z_xFZv5TMezYEemYSZTnI5P-VznY' 
CHANNEL_ID = '@Ramy_Premium'
CHANNEL_LINK = 'https://t.me/Ramy_Premium'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# دالة التحقق من الاشتراك الإجباري
async def check_subscription(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'creator', 'administrator']
    except Exception as e:
        logging.error(f"Subscription check error: {e}")
        return False

# لوحة مفاتيح الاشتراك
def sub_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 اشترك في القناة لتفعيل البوت", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="✅ تم الاشتراك، ابدأ التحميل", callback_data="check_sub")]
    ])

# دالة تحميل الصوت وتحويله لـ MP3
def download_audio(url):
    unique_id = uuid.uuid4().hex
    out_name = f"music_{unique_id}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_name,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        return f"{out_name}.mp3"

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if await check_subscription(message.from_user.id):
        await message.answer(f"🎵 أهلاً بك يا {message.from_user.first_name}!\n\nأرسل رابط الأغنية (Spotify أو YouTube) وسأحولها لـ MP3 فوراً. 🚀")
    else:
        await message.answer("⚠️ عذراً، يجب الاشتراك في قناة المتجر أولاً:", reply_markup=sub_kb())

@dp.callback_query(lambda c: c.data == "check_sub")
async def process_check_sub(callback_query: types.CallbackQuery):
    if await check_subscription(callback_query.from_user.id):
        await callback_query.message.edit_text("✅ تم التفعيل بنجاح! أرسل رابط الأغنية الآن.")
    else:
        await callback_query.answer("⚠️ لم تشترك بعد في القناة!", show_alert=True)

@dp.message()
async def handle_music(message: types.Message):
    if not message.text or "http" not in message.text: return
    
    if not await check_subscription(message.from_user.id):
        await message.answer("❌ يجب الاشتراك أولاً للاستفادة من الخدمة:", reply_markup=sub_kb())
        return

    wait_msg = await message.answer("⏳ جاري سحب الموسيقى والتحويل... انتظر لحظة")
    
    try:
        file_path = await asyncio.to_thread(download_audio, message.text)
        await message.answer_audio(
            audio=FSInputFile(file_path),
            caption=f"✅ تم التحميل بنجاح!\n\n🛒 متجر رامي: {CHANNEL_ID}"
        )
        if os.path.exists(file_path): os.remove(file_path)
        await wait_msg.delete()
    except Exception as e:
        logging.error(f"Download error: {e}")
        await wait_msg.edit_text("❌ حدث خطأ! تأكد أن الرابط عام (Public) ويعمل.")

# --- نظام الاستقرار لـ Render (حل مشكلة Port) ---
async def handle_web(request):
    return web.Response(text="Music Bot is Live! 🎶")

async def main():
    app = web.Application()
    app.router.add_get('/', handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # ربط البوت بالمنفذ الذي يطلبه Render تلقائياً
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    logging.info(f"Web server started on port {port}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
