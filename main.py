# ⚠️ تحذير: هذا الكود للاستخدام المحلي فقط! لا تنشره على الإنترنت أو GitHub

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

# ==================== التوكن مباشرة (للتشغيل السريع محلياً) ====================
# ⚠️ تنبيه: هذا غير آمن للنشر على الإنترنت
TOKEN = '8287417165:AAHPHSh-WE6kIuy-Ueoo4QbQA7IP41oTKx4'

# ==================== باقي الكود ====================

# إعداد التسجيل (logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== نظام التحكم ====================

# قائمة المستخدمين المصرح لهم (اتركها فارغة للسماح للجميع)
AUTHORIZED_USERS = set()

# معرف المطور - غيّره إلى معرف تليجرام الخاص بك
DEVELOPER_ID = 2132028510  # ⚠️ غيّر هذا الرقم إلى معرفك

# نظام تحديد المعدل (Rate Limiting)
class RateLimiter:
    def __init__(self, max_requests=5, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.users = {}  # user_id: [timestamp1, timestamp2, ...]
    
    def is_allowed(self, user_id):
        now = datetime.now()
        if user_id not in self.users:
            self.users[user_id] = []
        
        # تنظيف الطلبات القديمة
        self.users[user_id] = [t for t in self.users[user_id] 
                               if now - t < timedelta(seconds=self.time_window)]
        
        if len(self.users[user_id]) < self.max_requests:
            self.users[user_id].append(now)
            return True
        return False

rate_limiter = RateLimiter()

# ديكورator لتقييد الوصول
def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if AUTHORIZED_USERS and user_id not in AUTHORIZED_USERS:  # إذا كانت القائمة فارغة، السماح للجميع
            await update.message.reply_text("⛔ غير مصرح لك باستخدام هذا الأمر.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# ديكورator لتحديد المعدل
def rate_limit(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if not rate_limiter.is_allowed(user_id):
            await update.message.reply_text("⏰ أنت تستخدم الأوامر بسرعة كبيرة. انتظر قليلاً.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# ==================== أدوات المساعدة ====================

async def translate_to_english(text):
    """ترجمة النص إلى الإنجليزية"""
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(text)}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()[0][0][0]
    except Exception as e:
        logger.error(f"Translation error: {e}")
    return text

async def get_ai_response(text, user_id=None):
    """الحصول على رد من AI"""
    try:
        context_prefix = f"[User {user_id}] " if user_id else ""
        prompt = f"{context_prefix}أنت كوبرا، خبير تقني وهاكر أخلاقي واسع المعرفة. أجب بالعربية وباختصار واحترافية على: {text}"
        url = f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        logger.error(f"AI error: {e}")
    
    return "📡 النظام مشغول حالياً، حاول مرة أخرى لاحقاً."

# ==================== أداة فحص كلمة المرور ====================

def check_password(password):
    """فحص قوة كلمة المرور"""
    score = 0
    feedback = []

    # 1. اختبار الطول
    length = len(password)
    if length >= 12:
        score += 2
        feedback.append("✅ طول ممتاز!")
    elif length >= 8:
        score += 1
        feedback.append("✅ طول مناسب.")
    else:
        feedback.append("- كلمة المرور قصيرة جداً (يجب أن تكون 8 خانات على الأقل، ويفضل 12 فأكثر).")

    # 2. البحث عن أرقام
    if re.search(r"\d", password):
        score += 1
        if len(re.findall(r"\d", password)) >= 3:
            score += 1
            feedback.append("✅ تحتوي على 3 أرقام أو أكثر.")
        else:
            feedback.append("✅ تحتوي على أرقام.")
    else:
        feedback.append("- أضف أرقاماً لزيادة القوة.")

    # 3. البحث عن حروف كبيرة وصغيرة
    has_lower = bool(re.search(r"[a-z]", password))
    has_upper = bool(re.search(r"[A-Z]", password))
    
    if has_lower and has_upper:
        score += 1
        feedback.append("✅ مزيج جيد من الأحرف الكبيرة والصغيرة.")
    elif has_lower or has_upper:
        score += 0.5
        feedback.append("- استخدم مزيجاً من الحروف الكبيرة (A) والصغيرة (a) لزيادة القوة.")
    else:
        feedback.append("- أضف حروفاً إنجليزية كبيرة وصغيرة.")

    # 4. البحث عن رموز خاصة
    special_chars = r"[ !@#$%^&*(),.?\":{}|<>]"
    if re.search(special_chars, password):
        score += 1
        special_count = len(re.findall(special_chars, password))
        if special_count >= 2:
            score += 1
            feedback.append("✅ رموز خاصة متنوعة.")
        else:
            feedback.append("✅ تحتوي على رموز خاصة.")
    else:
        feedback.append("- أضف رموزاً خاصة مثل (@, #, $, %) لتعزيز القوة.")

    # 5. فحص إضافي: كلمات شائعة
    common_patterns = ["password", "123456", "qwerty", "admin", "123"]
    if any(pattern in password.lower() for pattern in common_patterns):
        feedback.append("⚠️ تجنب استخدام الكلمات أو الأنماط الشائعة في كلمات المرور.")
        score -= 1

    return max(0, score), feedback

# ==================== أوامر الإدارة ====================

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة مستخدم مصرح به (للمطور فقط)"""
    if update.effective_user.id != DEVELOPER_ID:
        await update.message.reply_text("⛔ هذا الأمر للمطور فقط.")
        return
    
    try:
        user_id = int(context.args[0])
        AUTHORIZED_USERS.add(user_id)
        await update.message.reply_text(f"✅ تمت إضافة المستخدم {user_id}")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ استخدام: /add_user [user_id]")

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إزالة مستخدم مصرح به"""
    if update.effective_user.id != DEVELOPER_ID:
        await update.message.reply_text("⛔ هذا الأمر للمطور فقط.")
        return
    
    try:
        user_id = int(context.args[0])
        if user_id in AUTHORIZED_USERS:
            AUTHORIZED_USERS.remove(user_id)
            await update.message.reply_text(f"✅ تمت إزالة المستخدم {user_id}")
        else:
            await update.message.reply_text("❌ المستخدم غير موجود في القائمة")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ استخدام: /remove_user [user_id]")

# ==================== الأوامر الرئيسية ====================

@rate_limit
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البداية"""
    user = update.effective_user
    welcome = f"""
💀 **COBRA SYSTEM V10 - ULTIMATE ONLINE**
------------------------------------------
مرحباً {user.first_name}! 👋

**الأوامر المتاحة:**
🎨 `/gen [وصف]` - توليد صور احترافية (بدون شعار)
📱 `/no` - استخراج 100 رقم Wecom تسلسلي
💳 `/cod` - توليد بيانات فيزا وهمية (لأغراض تعليمية)
🔊 `/voice [نص]` - تحويل النص إلى صوت هاكر
🔐 `/check [كلمة المرور]` - فحص قوة كلمة المرور
📊 `/stats` - إحصائيات النظام
ℹ️ `/about` - معلومات عن البوت

💬 **الدردشة:** تحدث معي مباشرة وسأجيبك تقنياً!
    """
    
    # إضافة أزرار تفاعلية
    keyboard = [
        [
            InlineKeyboardButton("📱 أرقام", callback_data='cmd_no'),
            InlineKeyboardButton("💳 فيزا", callback_data='cmd_cod')
        ],
        [
            InlineKeyboardButton("🎨 صور", callback_data='cmd_gen'),
            InlineKeyboardButton("🔊 صوت", callback_data='cmd_voice')
        ],
        [
            InlineKeyboardButton("🔐 فحص كلمة المرور", callback_data='cmd_check'),
            InlineKeyboardButton("ℹ️ عن البوت", callback_data='cmd_about')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome, reply_markup=reply_markup, parse_mode='Markdown')

@rate_limit
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """توليد الصور"""
    user_prompt = " ".join(context.args)
    if not user_prompt:
        await update.message.reply_text("❌ أرسل وصفاً بعد الأمر. مثال: `/gen هاكر كوبرا`")
        return
    
    status_msg = await update.message.reply_text("⏳ جاري المعالجة والتصميم...")
    try:
        # ترجمة الوصف للإنجليزية
        en_prompt = await translate_to_english(user_prompt)
        seed = random.randint(1, 1000000)
        
        # توليد الصورة بدون شعار
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(en_prompt)}?seed={seed}&width=1024&height=1024&nologo=true"
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            img = io.BytesIO(response.content)
            img.name = 'cobra.jpg'
            await update.message.reply_photo(
                photo=img, 
                caption=f"✅ تم التصميم: {user_prompt}\n🎲 Seed: {seed}"
            )
            await status_msg.delete()
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        await status_msg.edit_text("❌ فشل المحرك، حاول لاحقاً.")

@rate_limit
async def phone_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """توليد أرقام وهمية"""
    prefix = "+97255"
    start_num = random.randint(2000000, 8000000)
    numbers = [f"{prefix}{start_num + i}" for i in range(100)]
    
    # تقسيم الأرقام إلى مجموعتين
    part1 = "\n".join(numbers[:50])
    part2 = "\n".join(numbers[50:])
    
    await update.message.reply_text(f"📱 **قائمة أرقام Wecom المستخرجة:**\n\n{part1}")
    await update.message.reply_text(part2)

@rate_limit
async def visa_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """توليد بيانات فيزا وهمية للتعليم"""
    bins = ["4854", "5120", "4147", "4532", "4916"]
    cards = []
    
    for _ in range(5):
        b = random.choice(bins)
        card = f"`{b}{random.randint(1000,9999)}{random.randint(1000,9999)}{random.randint(1000,9999)}|{random.randint(1,12):02d}|{random.randint(25,30)}|{random.randint(100,999)}`"
        cards.append(card)
    
    message = "💳 **بيانات فيزا وهمية (لأغراض تعليمية فقط):**\n\n"
    message += "\n".join(cards)
    message += "\n\n⚠️ هذه البيانات وهمية ولا تعمل في الواقع"
    
    await update.message.reply_text(message, parse_mode='Markdown')

@rate_limit
async def text_to_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تحويل النص إلى صوت"""
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("❌ أرسل النص بعد الأمر. مثال: `/voice مرحباً بك`")
        return
    
    try:
        # محاولة الحصول على رابط الصوت
        url = f"https://dictation.io/proxy/tts?text={urllib.parse.quote(text)}&lang=ar-XA"
        await update.message.reply_voice(voice=url, caption=f"🔊 {text[:50]}...")
    except Exception as e:
        logger.error(f"Voice error: {e}")
        await update.message.reply_text("❌ فشل تحويل النص لصوت.")

@rate_limit
async def check_password_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فحص قوة كلمة المرور"""
    password = " ".join(context.args)
    if not password:
        await update.message.reply_text("❌ أرسل كلمة المرور بعد الأمر. مثال: `/check MyP@ss123`")
        return
    
    score, feedback = check_password(password)
    
    # توليد شريط القوة
    strength_bar = "█" * int(score) + "░" * (7 - int(score))
    
    # تحديد التصنيف
    if score >= 6:
        rating = "🟢 ممتازة"
    elif score >= 4:
        rating = "🟡 جيدة"
    elif score >= 2:
        rating = "🟠 ضعيفة"
    else:
        rating = "🔴 ضعيفة جداً"
    
    response = f"""
🔐 **نتيجة فحص كلمة المرور:**

القوة: {strength_bar} {score:.1f}/7
التصنيف: {rating}

**ملاحظات:**
{chr(10).join(feedback) if feedback else '✅ كلمة مرور ممتازة!'}
    """
    await update.message.reply_text(response, parse_mode='Markdown')

@rate_limit
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض إحصائيات البوت"""
    stats_text = f"""
📊 **إحصائيات النظام:**
• المستخدمون المصرح بهم: {len(AUTHORIZED_USERS)}
• المستخدمون النشطون: {len(rate_limiter.users)}
• وقت التشغيل: جاري...
• الإصدار: V10.0 Ultimate
    """
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معلومات عن البوت"""
    about_text = """
🤖 **عن COBRA V10**

نسخة متطورة من بوت كوبرا مع تحسينات شاملة:
✅ نظام حماية متكامل
✅ دعم الأوامر الصوتية
✅ توليد صور بدون شعار
✅ فحص قوة كلمات المرور
✅ واجهة تفاعلية بالأزرار
✅ نظام تحديد معدل الاستخدام

📌 **المطور:** الفريق التقني
📌 **الإصدار:** 10.0 Ultimate
📌 **آخر تحديث:** 2024
    """
    await update.message.reply_text(about_text, parse_mode='Markdown')

# ==================== معالج الأزرار ====================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الضغط على الأزرار"""
    query = update.callback_query
    await query.answer()
    
    # إرسال تعليمات لكل زر
    if query.data == 'cmd_no':
        await query.message.reply_text("📱 **للاستخدام:** أرسل `/no` للحصول على أرقام وهمية")
    elif query.data == 'cmd_cod':
        await query.message.reply_text("💳 **للاستخدام:** أرسل `/cod` للحصول على بيانات فيزا وهمية")
    elif query.data == 'cmd_gen':
        await query.message.reply_text("🎨 **للاستخدام:** أرسل `/gen [وصف الصورة]`")
    elif query.data == 'cmd_voice':
        await query.message.reply_text("🔊 **للاستخدام:** أرسل `/voice [النص]`")
    elif query.data == 'cmd_check':
        await query.message.reply_text("🔐 **للاستخدام:** أرسل `/check [كلمة المرور]`")
    elif query.data == 'cmd_about':
        await about_command(update, context)

# ==================== معالج الدردشة الذكية ====================

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج المحادثة العادية"""
    if update.message.text.startswith('/'): 
        return
    
    # إظهار مؤشر الكتابة
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # الحصول على رد من AI
    reply = await get_ai_response(update.message.text, update.effective_user.id)
    
    # إضافة توقيع زمني
    reply += f"\n\n— <i>كوبرا AI • {datetime.now().strftime('%H:%M')}</i>"
    
    await update.message.reply_text(reply, parse_mode='HTML')

# ==================== معالج الأخطاء ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء العام"""
    logger.error(f"Exception: {context.error}")
    try:
        if update and update.message:
            await update.message.reply_text("⚠️ حدث خطأ غير متوقع. تم تسجيل المشكلة وحلها قريباً.")
    except:
        pass

# ==================== تشغيل البوت ====================

if __name__ == '__main__':
    # تحذير أمني واضح
    print("=" * 60)
    print("⚠️  تنبيه أمني مهم  ⚠️".center(60))
    print("=" * 60)
    print("أنت تقوم بتشغيل البوت مع توكن مدمج في الكود!")
    print("هذا آمن فقط للاستخدام المحلي على جهازك الشخصي.")
    print("\n🚫 لا تنشر هذا الكود على الإنترنت")
    print("🚫 لا تشاركه مع أي شخص")
    print("🚫 لا ترفعه على GitHub")
    print("=" * 60)
    print("\n✅ جاري تشغيل البوت...\n")
    
    # إنشاء التطبيق
    app = ApplicationBuilder().token(TOKEN).build()
    
    # إضافة معالجات الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", generate_image))
    app.add_handler(CommandHandler("no", phone_gen))
    app.add_handler(CommandHandler("cod", visa_gen))
    app.add_handler(CommandHandler("voice", text_to_voice))
    app.add_handler(CommandHandler("check", check_password_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("about", about_command))
    
    # أوامر الإدارة (للمطور)
    app.add_handler(CommandHandler("add_user", add_user))
    app.add_handler(CommandHandler("remove_user", remove_user))
    
    # معالج الأزرار
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # معالج الدردشة
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_handler))
    
    # معالج الأخطاء
    app.add_error_handler(error_handler)
    
    # تشغيل البوت
    logger.info("✅ Cobra V10 Ultimate is Running...")
    logger.info("📢 البوت جاهز للاستخدام!")
    app.run_polling()
