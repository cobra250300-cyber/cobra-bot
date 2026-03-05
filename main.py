import requests
import random
import os
import io
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات المركزية ---
TOKEN = '8287417165:AAHPHSh-WE6kIuy-Ueoo4QbQA7IP41oTKx4'

# --- دالة الترجمة (مهمة جداً لجودة الصور) ---
def translate_to_english(text):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={requests.utils.quote(text)}"
        response = requests.get(url, timeout=5)
        return response.json()[0][0][0]
    except:
        return text # إذا فشلت الترجمة، نرسل النص الأصلي

# --- دالة الذكاء الاصطناعي (أسرع) ---
def get_ai_response(text):
    try:
        url = f"https://text.pollinations.ai/{requests.utils.quote('أنت كوبرا، خبير تقني واسع المعرفة، أجب بالعربية وباختصار: ' + text)}"
        response = requests.get(url, timeout=10)
        return response.text.strip() if response.status_code == 200 else "⚠️ النظام مشغول حالياً."
    except:
        return "📡 خطأ في الاتصال بالقاعدة."

# --- [الأوامر] ---

# 1. أمر الصور المصلح (تحميل ثم إرسال) (/gen)
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_prompt = " ".join(context.args)
    if not user_prompt:
        await update.message.reply_text("❌ أرسل وصفاً للصورة بعد الأمر. مثال: `/gen هاكر حزين`")
        return

    # إظهار حالة "typing" ليعرف المستخدم أن البوت يعمل
    status_msg = await update.message.reply_text("⏳ جاري ترجمة الوصف ومعالجته في سيرفر التصميم...")
    
    try:
        # ترجمة الوصف العربي إلى إنجليزي لضمان عمل السيرفر
        english_prompt = translate_to_english(user_prompt)
        await status_msg.edit_text(f"🎨 جاري رسم: `{english_prompt}`...")
        
        # إعداد الرابط مع Seed عشوائي لمنع التكرار
        seed = random.randint(1, 1000000)
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(english_prompt)}?seed={seed}&width=1024&height=1024&nologo=true&model=flux"
        
        # --- الخطوة السحرية: تحميل الصورة إلى الذاكرة ---
        # بدلاً من إرسال رابط، البوت يقوم بتحميل الصورة أولاً
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
        image_response = requests.get(url, timeout=30) # زيادة المهلة
        
        if image_response.status_code == 200:
            # تحويل البيانات إلى ملف وهمي في الذاكرة
            image_file = io.BytesIO(image_response.content)
            image_file.name = 'cobra_design.jpg'
            
            # إرسال الصورة كملف حقيقي، وليس كرابط
            await update.message.reply_photo(
                photo=image_file, 
                caption=f"✅ **تم التصميم بنجاح بواسطة كوبرا**\n 🔍 الوصف: {user_prompt}",
                parse_mode='Markdown'
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ فشل السيرفر في توليد الصورة، حاول لاحقاً.")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ فشل المحرك. حاول تبسيط الوصف.\nالخطأ: {str(e)[:50]}")

# 2. أمر توليد الأرقام (/no)
async def phone_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📡 جاري سحب 100 رقم من شبكة Wecom...")
    prefix = "+97255"
    start_num = random.randint(2000000, 8000000)
    numbers = [f"{prefix}{start_num + i}" for i in range(100)]
    await update.message.reply_text("📱 **[الجزء 1]:**\n\n" + "\n".join(numbers[:50]), parse_mode='Markdown')
    await update.message.reply_text("📱 **[الجزء 2]:**\n\n" + "\n".join(numbers[50:]), parse_mode='Markdown')
    await msg.delete()

# 3. أمر البيانات الوهمية (/cod)
async def cod_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cards = [f"`4854{random.randint(1000,9999)}{random.randint(1000,9999)}{random.randint(1000,9999)}|{random.randint(1,12):02}|{random.randint(25,30)}|{random.randint(100,999)}`" for _ in range(5)]
    await update.message.reply_text("💳 **بيانات المحاكاة المستخرجة:**\n\n" + "\n".join(cards), parse_mode='Markdown')

# 4. أمر البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "💀 **[COBRA SYSTEM V10 ONLINE]**\n"
        "------------------------------\n"
        "مرحباً بك في الواجهة المركزية.\n\n"
        "• `/gen` [وصف] : تصميم صور (تم إصلاح مشكلة الرابط).\n"
        "• `/no` : استخراج 100 رقم Wecom.\n"
        "• `/cod` : بيانات محاكاة CC.\n"
        "• **دردشة:** تحدث معي مباشرة وسأجيبك."
    )
    await update.message.reply_text(welcome, parse_mode='Markdown')

# --- معالج الرسائل التلقائي (الرد الذكي) ---
async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.startswith('/'): return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = get_ai_response(update.message.text)
    await update.message.reply_text(f"💻 **[سجل كوبرا]:** {reply}")

# --- تشغيل النظام ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    # تسجيل الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", generate_image))
    app.add_handler(CommandHandler("no", phone_gen))
    app.add_handler(CommandHandler("cod", cod_cmd))
    
    # تسجيل معالج الرسائل العادية
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_handler))
    
    print("✅ Cobra v10 with Binary Image Sending is Running...")
    app.run_polling()
