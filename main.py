import requests
import random
import io
import urllib.parse
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات المركزية ---
TOKEN = '8287417165:AAHPHSh-WE6kIuy-Ueoo4QbQA7IP41oTKx4'

# --- 1. دالة الترجمة (لتحسين جودة الصور) ---
def translate_to_english(text):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(text)}"
        response = requests.get(url, timeout=5)
        return response.json()[0][0][0]
    except:
        return text

# --- 2. محرك الرد الذكي (Cobra AI) ---
def get_ai_response(text):
    try:
        prompt = f"أنت كوبرا، خبير تقني وهاكر أخلاقي واسع المعرفة، أجب بالعربية وباختصار واحترافية على: {text}"
        url = f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}"
        response = requests.get(url, timeout=10)
        return response.text.strip() if response.status_code == 200 else "⚠️ النظام مشغول حالياً."
    except:
        return "📡 خطأ في الاتصال بالقاعدة السحابية."

# --- [الأوامر الرئيسية] ---

# أمر البداية /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "💀 **[COBRA SYSTEM V10 - ULTIMATE ONLINE]**\n"
        "------------------------------------------\n"
        "مرحباً بك في نظام التحكم المركزي.\n\n"
        "🎨 `/gen` [وصف] : توليد صور احترافية (بدون شعار).\n"
        "📱 `/no` : استخراج 100 رقم Wecom تسلسلي.\n"
        "💳 `/cod` : توليد بيانات فيزا وهمية (لأغراض تعليمية).\n"
        "🔊 `/voice` [نص] : تحويل النص إلى صوت هاكر.\n"
        "💬 **الدردشة:** تحدث معي مباشرة وسأجيبك تقنياً."
    )
    await update.message.reply_text(welcome, parse_mode='Markdown')

# أمر الصور /gen (بدون شعار + ترجمة)
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_prompt = " ".join(context.args)
    if not user_prompt:
        await update.message.reply_text("❌ أرسل وصفاً بعد الأمر. مثال: `/gen هاكر كوبرا`")
        return
    
    status_msg = await update.message.reply_text("⏳ جاري المعالجة والتصميم...")
    try:
        en_prompt = translate_to_english(user_prompt)
        seed = random.randint(1, 1000000)
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(en_prompt)}?seed={seed}&width=1024&height=1024&nologo=true"
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            img = io.BytesIO(response.content)
            img.name = 'cobra.jpg'
            await update.message.reply_photo(photo=img, caption=f"✅ تم التصميم: {user_prompt}")
            await status_msg.delete()
    except:
        await status_msg.edit_text("❌ فشل المحرك، حاول لاحقاً.")

# أمر الأرقام /no
async def phone_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prefix = "+97255"
    start_num = random.randint(2000000, 8000000)
    numbers = [f"{prefix}{start_num + i}" for i in range(100)]
    await update.message.reply_text("📱 **قائمة أرقام Wecom المستخرجة:**\n\n" + "\n".join(numbers[:50]))
    await update.message.reply_text("\n".join(numbers[50:]))

# أمر الفيزا الوهمية /cod
async def visa_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bins = ["4854", "5120", "4147"]
    cards = []
    for _ in range(5):
        b = random.choice(bins)
        card = f"{b}{random.randint(1000,9999)}{random.randint(1000,9999)}{random.randint(1000,9999)}|{random.randint(1,12):02}|{random.randint(25,30)}|{random.randint(100,999)}"
        cards.append(f"`{card}`")
    await update.message.reply_text("💳 **بيانات فيزا وهمية (للتعليم):**\n\n" + "\n".join(cards), parse_mode='Markdown')

# أمر الصوت /voice
async def text_to_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("❌ أرسل النص بعد الأمر. مثال: `/voice مرحباً بك`")
        return
    
    try:
        url = f"https://dictation.io/proxy/tts?text={urllib.parse.quote(text)}&lang=ar-XA"
        await update.message.reply_voice(voice=url, caption="🔊 تسجيل صوتي من نظام كوبرا")
    except:
        await update.message.reply_text("❌ فشل تحويل النص لصوت.")

# الرد التلقائي الذكي
async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.startswith('/'): return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = get_ai_response(update.message.text)
    await update.message.reply_text(f"💻 **[سجل كوبرا]:** {reply}", parse_mode='Markdown')

# --- تشغيل البوت ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", generate_image))
    app.add_handler(CommandHandler("no", phone_gen))
    app.add_handler(CommandHandler("cod", visa_gen))
    app.add_handler(CommandHandler("voice", text_to_voice))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_handler))
    
    print("✅ Cobra V10 Ultimate is Running...")
    app.run_polling()
