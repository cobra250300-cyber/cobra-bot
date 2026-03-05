import os
import random
import io
import httpx
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

# إعداد السجلات (Logs)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# التوكن الخاص بك تم وضعه هنا مباشرة
TOKEN = '8287417165:AAHPHSh-WE6kIuy-Ueoo4QbQA7IP41oTKx4'

# ذاكرة الجلسات
user_memory = {}

async def translate_to_english(text):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {"client": "gtx", "sl": "auto", "tl": "en", "dt": "t", "q": text}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=5.0)
            return response.json()[0][0][0]
        except:
            return text

async def get_ai_response_advanced(user_id, text):
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    user_memory[user_id].append(f"المستخدم: {text}")
    context_string = "\n".join(user_memory[user_id][-5:])
    
    system_prompt = "أنت 'كوبرا'، خبير تقني متمكن. أجب بالعربية بذكاء واختصار مع إيموجي تقني. سياق الحوار:\n"
    full_prompt = f"{system_prompt}\n{context_string}\nكوبرا:"
    url = f"https://text.pollinations.ai/{httpx.utils.quote(full_prompt)}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=15.0)
            if response.status_code == 200:
                ai_reply = response.text.strip()
                user_memory[user_id].append(f"كوبرا: {ai_reply}")
                return ai_reply
            return "⚠️ النظام مشغول حالياً."
        except:
            return "📡 خطأ في الاتصال بالدماغ المركزي."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "💀 **[COBRA SYSTEM V11 - ONLINE]**\n"
        "------------------------------\n"
        "النظام يعمل الآن بالتوكن المباشر.\n\n"
        "• `/gen` [وصف] : توليد صور.\n"
        "• `/no` : استخراج أرقام.\n"
        "• `/cod` : محاكاة بيانات.\n"
        "• **الدردشة:** تحدث معي مباشرة."
    )
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_prompt = " ".join(context.args)
    if not user_prompt:
        await update.message.reply_text("❌ أرسل وصفاً للصورة.")
        return

    status_msg = await update.message.reply_text("⏳ جاري المعالجة...")
    try:
        english_prompt = await translate_to_english(user_prompt)
        seed = random.randint(1, 1000000)
        url = f"https://image.pollinations.ai/prompt/{httpx.utils.quote(english_prompt)}?seed={seed}&width=1024&height=1024&nologo=true&model=flux"
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
        async with httpx.AsyncClient() as client:
            image_res = await client.get(url, timeout=40.0)
        
        if image_res.status_code == 200:
            image_file = io.BytesIO(image_res.content)
            image_file.name = 'cobra.jpg'
            await update.message.reply_photo(photo=image_file, caption=f"✅ تم التصميم لـ: {user_prompt}")
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ فشل السيرفر.")
    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ تقني.")

async def phone_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prefix = "+97255"
    numbers = [f"{prefix}{random.randint(2000000, 8000000)}" for _ in range(50)]
    await update.message.reply_text("📱 **قائمة الأرقام:**\n\n" + "\n".join(numbers), parse_mode='Markdown')

async def cod_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cards = [f"`4854{random.randint(1000,9999)}{random.randint(1000,9999)}{random.randint(1000,9999)}|{random.randint(1,12):02}|{random.randint(25,30)}|{random.randint(100,999)}`" for _ in range(5)]
    await update.message.reply_text("💳 **بيانات المحاكاة:**\n\n" + "\n".join(cards), parse_mode='Markdown')

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text or update.message.text.startswith('/'): return
    user_id = update.effective_user.id
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    reply = await get_ai_response_advanced(user_id, update.message.text)
    await update.message.reply_text(f"🛡️ **[COBRA AI]:** {reply}", parse_mode='Markdown')

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", generate_image))
    app.add_handler(CommandHandler("no", phone_gen))
    app.add_handler(CommandHandler("cod", cod_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_handler))
    print("🚀 Cobra is running with direct token...")
    app.run_polling()
