import os
import requests
import random
import io
import urllib.parse
import google.generativeai as genai
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات (سيتم جلبها من Render) ---
import os

# بدلاً من وضع التوكن مباشرة، نجعله يقرأه من إعدادات السيرفر
TOKEN = os.environ.get('BOT_TOKEN')

GEMINI_KEY = 'AIzaSyCrhUobT6vca2LjpuSspVaMfczqLdu89gU'
DEVELOPER_ID = 2132028510

# إعداد ذكاء جوجل جيميناي
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

# --- محرك الذكاء الاصطناعي الخارق ---
async def get_gemini_response(user_text):
    try:
        instruction = "أنت كوبرا V10، خبير أمن سيبراني وبرمجة. أجب باحترافية وتنسيق Markdown."
        response = model.generate_content(f"{instruction}\n\nUser: {user_text}")
        return response.text
    except:
        return "⚠️ المحرك منشغل بمعالجة بيانات أخرى، حاول مجدداً."

# --- الأوامر الرئيسية ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        f"💀 **[COBRA GEMINI V10 ONLINE]**\n"
        "تم دمج ذكاء Google Gemini Pro بنجاح.\n\n"
        "🎨 `/gen` : صور احترافية (AI)\n"
        "📱 `/no` : أرقام Wecom تسلسلية\n"
        "💳 `/cod` : فيزا وهمية (تعليمي)\n"
        "🔊 `/voice` : تحويل النص لصوت"
    )
    keyboard = [[InlineKeyboardButton("🎨 تصميم", callback_data='c1'), InlineKeyboardButton("📱 أرقام", callback_data='c2')]]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# توليد الصور (بدون شعار + ترجمة تلقائية)
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ اكتب وصف الصورة")
    
    msg = await update.message.reply_text("🎨 جاري التخيل والتصميم...")
    try:
        # ترجمة سريعة للإنجليزية لضمان الجودة
        trans_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(prompt)}"
        en_prompt = requests.get(trans_url).json()[0][0][0]
        
        seed = random.randint(1, 999999)
        img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(en_prompt)}?seed={seed}&nologo=true"
        
        res = requests.get(img_url)
        await update.message.reply_photo(photo=io.BytesIO(res.content), caption=f"✅ تم الإنجاز: {prompt}")
        await msg.delete()
    except: await msg.edit_text("❌ فشل المحرك.")

# الأرقام والفيزا
async def phone_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nums = [f"+97255{random.randint(2000000, 8000000) + i}" for i in range(100)]
    await update.message.reply_text("📱 **أرقام Wecom المستخرجة:**\n\n" + "\n".join(nums[:50]))

async def visa_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cards = [f"`4854{random.randint(1000,9999)}{random.randint(1000,9999)}{random.randint(1000,9999)}|{random.randint(1,12):02d}|28|{random.randint(100,999)}`" for _ in range(5)]
    await update.message.reply_text("💳 **فيزا وهمية:**\n\n" + "\n".join(cards), parse_mode='Markdown')

# تحويل النص لصوت
async def voice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if text:
        url = f"https://dictation.io/proxy/tts?text={urllib.parse.quote(text)}&lang=ar-XA"
        await update.message.reply_voice(voice=url)

# معالج الدردشة الذكي (Gemini)
async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.startswith('/'): return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = await get_gemini_response(update.message.text)
    await update.message.reply_text(f"🖥️ **[كوبرا الذكي]:**\n\n{reply}", parse_mode='Markdown')

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", generate_image))
    app.add_handler(CommandHandler("no", phone_cmd))
    app.add_handler(CommandHandler("cod", visa_cmd))
    app.add_handler(CommandHandler("voice", voice_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_handler))
    
    print("✅ Cobra System V10 (Gemini Edition) is Running...")
    app.run_polling()
