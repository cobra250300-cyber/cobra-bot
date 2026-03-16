import os
import requests
import random
import io
import urllib.parse
import google.generativeai as genai
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ==================== الإعدادات (تُجلب من بيئة السيرفر) ====================
TOKEN = os.environ.get('BOT_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_KEY')
DEVELOPER_ID = int(os.environ.get('DEVELOPER_ID', 2132028510))

# إعداد ذكاء جيميناي مع تخفيف قيود الحجب للمواضيع التقنية
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ==================== محرك الذكاء الاصطناعي (جيميناي + احتياطي) ====================
async def get_smart_response(user_text):
    try:
        instruction = "أنت كوبرا V10، خبير تقني وهاكر أخلاقي. أجب باحترافية وتنسيق Markdown."
        response = model.generate_content(f"{instruction}\n\nUser: {user_text}", safety_settings=SAFETY_SETTINGS)
        return response.text
    except:
        # المحرك الاحتياطي في حال تعطل جيميناي
        try:
            res = requests.get(f"https://text.pollinations.ai/{urllib.parse.quote(user_text)}")
            return res.text + "\n\n*(الرد عبر النظام الاحتياطي)*"
        except:
            return "⚠️ عذراً، جميع أنظمة الذكاء مشغولة حالياً."

# ==================== الأوامر البرمجية ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        f"💀 **[COBRA SYSTEM V10 - ULTIMATE]**\n"
        f"تم دمج الذكاء الخارق ونظام الحماية السحابي.\n\n"
        "🎨 `/gen` : توليد صور (AI)\n"
        "📱 `/no` : استخراج أرقام Wecom\n"
        "💳 `/cod` : بيانات فيزا (تعليمي)\n"
        "🔊 `/voice` : تحويل النص لصوت"
    )
    keyboard = [[InlineKeyboardButton("📱 أرقام", callback_data='c1'), InlineKeyboardButton("💳 فيزا", callback_data='c2')]]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("❌ أرسل الوصف بعد الأمر. مثال: `/gen هاكر` ")
    
    msg = await update.message.reply_text("⏳ جاري المعالجة والتصميم...")
    try:
        # ترجمة الوصف للإنجليزية لضمان أفضل نتيجة صور
        tr_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(prompt)}"
        en_prompt = requests.get(tr_url).json()[0][0][0]
        
        seed = random.randint(1, 999999)
        img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(en_prompt)}?seed={seed}&nologo=true"
        
        res = requests.get(img_url)
        await update.message.reply_photo(photo=io.BytesIO(res.content), caption=f"✅ تم التصميم لمدير كوبرا: {prompt}")
        await msg.delete()
    except: await msg.edit_text("❌ فشل محرك الصور.")

async def phone_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nums = [f"+97255{random.randint(2000000, 8000000) + i}" for i in range(100)]
    await update.message.reply_text("📱 **قائمة الأرقام المستخرجة:**\n\n" + "\n".join(nums[:50]))

async def visa_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cards = [f"`4854{random.randint(1000,9999)}{random.randint(1000,9999)}{random.randint(1000,9999)}|{random.randint(1,12):02d}|28|{random.randint(100,999)}`" for _ in range(5)]
    await update.message.reply_text("💳 **بيانات فيزا للتعليم:**\n\n" + "\n".join(cards), parse_mode='Markdown')

async def voice_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if text:
        url = f"https://dictation.io/proxy/tts?text={urllib.parse.quote(text)}&lang=ar-XA"
        await update.message.reply_voice(voice=url)

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.startswith('/'): return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = await get_smart_response(update.message.text)
    await update.message.reply_text(f"🖥️ **[كوبرا]:**\n\n{reply}", parse_mode='Markdown')

# ==================== التشغيل الرئيسي ====================
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", generate_image))
    app.add_handler(CommandHandler("no", phone_tool))
    app.add_handler(CommandHandler("cod", visa_tool))
    app.add_handler(CommandHandler("voice", voice_tool))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_handler))
    
    print(f"🚀 Cobra System V10 is Live! Admin: {DEVELOPER_ID}")
    app.run_polling()
