import requests
import random
import io
import urllib.parse
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# التوكين الخاص بك (آمن للعمل على السيرفر)
TOKEN = '8287417165:AAHPHSh-WE6kIuy-Ueoo4QbQA7IP41oTKx4'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة ترحيبية احترافية باللغة العربية"""
    welcome_text = (
        "🐍 **مرحباً بك في بوت كوبرا (النسخة V10)**\n\n"
        "أنا مساعدك الذكي لتحويل الكلمات إلى لوحات فنية.\n\n"
        "🎨 **كيفية الاستخدام:**\n"
        "أرسل الأمر `/gen` متبوعاً بوصف الصورة.\n"
        "مثال: `/gen هاكر كوبرا في مدينة دبي المستقبلية`"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دالة التصميم المتقدمة"""
    prompt = " ".join(context.args)
    
    if not prompt:
        await update.message.reply_text("⚠️ يرجى كتابة وصف بعد الأمر! مثال: `/gen طائرة شبح`", parse_mode='Markdown')
        return

    # إشعار المستخدم بالبدء
    status_msg = await update.message.reply_text("⏳ **جاري معالجة طلبك وتصميم اللوحة...**", parse_mode='Markdown')

    try:
        # تحويل النص العربي ليكون متوافقاً مع الرابط
        encoded_prompt = urllib.parse.quote(prompt)
        seed = random.randint(1, 9999999)
        
        # رابط المحرك مع منع الشعارات وبأعلى دقة
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&nologo=true&width=1024&height=1024"
        
        # جلب الصورة من المحرك
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            # معالجة الصورة كملف لضمان الجودة ومنع الشعار
            image_stream = io.BytesIO(response.content)
            image_stream.name = 'cobra_v10_art.jpg'
            
            await update.message.reply_photo(
                photo=image_stream, 
                caption=f"✅ **تم التصميم بنجاح!**\n📝 **الوصف:** {prompt}",
                parse_mode='Markdown'
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ **فشل السيرفر في توليد الصورة، حاول لاحقاً.**")

    except Exception as e:
        print(f"Error in V10: {e}")
        await status_msg.edit_text("❌ **حدث خطأ فني أثناء المعالجة. تأكد من أن الوصف واضح.**")

if __name__ == '__main__':
    # بناء التطبيق
    app = ApplicationBuilder().token(TOKEN).build()

    # الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", generate_image))

    # بدء العمل بنظام Polling (مثالي للـ Background Worker في Render)
    print("Cobra V10 is Live and Ready!")
    app.run_polling()
