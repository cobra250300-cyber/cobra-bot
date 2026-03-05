import requests, random, io
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = '8287417165:AAHPHSh-WE6kIuy-Ueoo4QbQA7IP41oTKx4'

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = " ".join(context.args)
    if not p: return await update.message.reply_text("❌ اكتب وصفاً.")
    status = await update.message.reply_text("⏳ جاري التصميم...")
    try:
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(p)}?seed={random.randint(1,999999)}&nologo=true"
        response = requests.get(url, timeout=40)
        if response.status_code == 200:
            img = io.BytesIO(response.content)
            img.name = 'cobra.jpg'
            await update.message.reply_photo(photo=img, caption=f"✅ تم التصميم: {p}")
            await status.delete()
    except:
        await status.edit_text("❌ خطأ في السيرفر.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("gen", generate_image))
    app.run_polling()
