import requests
import random
import io
import urllib.parse
import os
import logging
import re
import asyncio
from datetime import datetime, timedelta
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ==================== الإعدادات المركزية ====================
import os

# بدلاً من وضع التوكن مباشرة، نجعله يقرأه من إعدادات السيرفر
TOKEN = os.environ.get('BOT_TOKEN')


# معرف المطور الخاص بك (تم التحديث)
DEVELOPER_ID = 2132028510  

# ==================== نظام التحكم والأمان ====================

AUTHORIZED_USERS = set()

class RateLimiter:
    def __init__(self, max_requests=5, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.users = {}
    
    def is_allowed(self, user_id):
        now = datetime.now()
        if user_id not in self.users:
            self.users[user_id] = []
        self.users[user_id] = [t for t in self.users[user_id] 
                               if now - t < timedelta(seconds=self.time_window)]
        if len(self.users[user_id]) < self.max_requests:
            self.users[user_id].append(now)
            return True
        return False

rate_limiter = RateLimiter()

def rate_limit(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if not rate_limiter.is_allowed(user_id):
            await update.message.reply_text("⏰ نظام الحماية: أنت ترسل أوامر بسرعة كبيرة، انتظر قليلاً.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# ==================== أدوات المساعدة الذكية ====================

async def translate_to_english(text):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(text)}"
        response = requests.get(url, timeout=5)
        return response.json()[0][0][0]
    except: return text

async def get_ai_response(text):
    try:
        prompt = f"أنت كوبرا، خبير تقني وهاكر أخلاقي، أجب بالعربية وباختصار واحترافية على: {text}"
        url = f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}"
        response = requests.get(url, timeout=10)
        return response.text.strip() if response.status_code == 200 else "⚠️ النظام مشغول حالياً."
    except: return "📡 فشل الاتصال بالقاعدة."

# ==================== الأوامر الرئيسية ====================

@rate_limit
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        f"💀 **[COBRA SYSTEM V10 - ONLINE]**\n"
        f"مرحباً بك يا مدير النظام.\n\n"
        "🎨 `/gen` : توليد صور احترافية (بدون شعار).\n"
        "📱 `/no` : استخراج 100 رقم Wecom.\n"
        "💳 `/cod` : بيانات فيزا وهمية للتعليم.\n"
        "🔊 `/voice` : تحويل النص لصوت هاكر.\n"
        "🔐 `/check` : فحص قوة كلمة المرور.\n"
    )
    keyboard = [[InlineKeyboardButton("📱 أرقام", callback_data='cmd_no'), InlineKeyboardButton("💳 فيزا", callback_data='cmd_cod')],
                [InlineKeyboardButton("🎨 صور", callback_data='cmd_gen'), InlineKeyboardButton("🔊 صوت", callback_data='cmd_voice')]]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

@rate_limit
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_prompt = " ".join(context.args)
    if not user_prompt:
        await update.message.reply_text("❌ أرسل وصفاً بعد الأمر.")
        return
    status = await update.message.reply_text("⏳ جاري المعالجة...")
    try:
        en_prompt = await translate_to_english(user_prompt)
        seed = random.randint(1, 1000000)
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(en_prompt)}?seed={seed}&nologo=true&width=1024&height=1024"
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            await update.message.reply_photo(photo=io.BytesIO(res.content), caption=f"✅ تم التصميم: {user_prompt}")
            await status.delete()
    except: await status.edit_text("❌ فشل المحرك.")

@rate_limit
async def phone_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nums = [f"+97255{random.randint(2000000, 8000000) + i}" for i in range(100)]
    await update.message.reply_text("📱 **قائمة الأرقام:**\n\n" + "\n".join(nums[:50]))
    await update.message.reply_text("\n".join(nums[50:]))

@rate_limit
async def visa_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cards = [f"`4854{random.randint(1000,9999)}{random.randint(1000,9999)}{random.randint(1000,9999)}|{random.randint(1,12):02d}|{random.randint(25,30)}|{random.randint(100,999)}`" for _ in range(5)]
    await update.message.reply_text("💳 **بيانات تعليمية:**\n\n" + "\n".join(cards), parse_mode='Markdown')

@rate_limit
async def text_to_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if text:
        url = f"https://dictation.io/proxy/tts?text={urllib.parse.quote(text)}&lang=ar-XA"
        await update.message.reply_voice(voice=url)
    else: await update.message.reply_text("❌ اكتب نصاً.")

# أوامر الإدارة (للمطور فقط)
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == DEVELOPER_ID:
        uid = int(context.args[0])
        AUTHORIZED_USERS.add(uid)
        await update.message.reply_text(f"✅ تمت إضافة {uid}")
    else: await update.message.reply_text("⛔ للمطور فقط.")

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.startswith('/'):
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply = await get_ai_response(update.message.text)
        await update.message.reply_text(f"💻 **[كوبرا]:** {reply}\n\n— {datetime.now().strftime('%H:%M')}", parse_mode='HTML')

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", generate_image))
    app.add_handler(CommandHandler("no", phone_gen))
    app.add_handler(CommandHandler("cod", visa_gen))
    app.add_handler(CommandHandler("voice", text_to_voice))
    app.add_handler(CommandHandler("add", add_user))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_handler))
    
    print(f"✅ Cobra System V10 is running for Admin: {DEVELOPER_ID}")
    app.run_polling()
