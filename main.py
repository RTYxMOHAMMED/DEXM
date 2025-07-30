import os
import subprocess
import sys
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)

# ================== الإعدادات ==================
AUTHORIZED_USER_ID =8436319138  # ايدي المستخدم المسموح له
TOKEN = "8295167666:AAGgCn4TsE-3U3QgE22Om_VCpqlJVzTnzmg"  # توكن البوت

TOOLS_DIR = "tools"
os.makedirs(TOOLS_DIR, exist_ok=True)

ACTIVE_PROCESSES = {}  # لحفظ العمليات النشطة {اسم_الملف: العملية}

# ==================================================
# رسالة الترحيب عند /start
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ إضافة أداة جديدة", callback_data="add_tool")],
        [InlineKeyboardButton("🎛 لوحة التحكم", callback_data="control_panel")],
        [InlineKeyboardButton("📦 تثبيت مكتبات", callback_data="install_lib")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome = (
        "👋 مرحباً بكم في بوت *سارة فون* 🎉\n"
        "استضافة أدوات بايثون مدفوعة ومجانية!\n\n"
        "اختر خياراً من القائمة أدناه:"
    )
    await update.message.reply_text(welcome, reply_markup=reply_markup, parse_mode="Markdown")

# ==================================================
# عرض جميع الأدوات في لوحة التحكم
# ==================================================
async def show_control_panel(query):
    tools = [f for f in os.listdir(TOOLS_DIR) if f.endswith(".py")]
    if not tools:
        await query.message.reply_text("❌ لا توجد أدوات مُضافة بعد.")
        return

    keyboard = []
    for tool in tools:
        keyboard.append([InlineKeyboardButton(f"🔧 {tool}", callback_data=f"tool_{tool}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("📌 اختر أداة للتحكم بها:", reply_markup=reply_markup)

# ==================================================
# عرض خيارات الأداة (تشغيل، إيقاف، حذف)
# ==================================================
async def tool_options(query, tool_name):
    keyboard = [
        [InlineKeyboardButton("▶️ تشغيل", callback_data=f"run_{tool_name}")],
        [InlineKeyboardButton("⏹️ إيقاف", callback_data=f"stop_{tool_name}")],
        [InlineKeyboardButton("❌ حذف", callback_data=f"delete_{tool_name}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    status = "🟢 تعمل" if tool_name in ACTIVE_PROCESSES else "🔴 متوقفة"
    await query.message.reply_text(f"⚙️ الأداة: `{tool_name}`\nالحالة: {status}", reply_markup=reply_markup, parse_mode="Markdown")

# ==================================================
# تشغيل الأداة
# ==================================================
async def run_tool(query, tool_name):
    if tool_name in ACTIVE_PROCESSES:
        await query.message.reply_text(f"⚠️ الأداة `{tool_name}` تعمل بالفعل!")
        return

    file_path = os.path.join(TOOLS_DIR, tool_name)
    try:
        proc = subprocess.Popen([sys.executable, file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        ACTIVE_PROCESSES[tool_name] = proc
        await query.message.reply_text(f"✅ تم تشغيل الأداة `{tool_name}` بنجاح.", parse_mode="Markdown")
    except Exception as e:
        error_msg = str(e)
        if "No module named" in error_msg:
            mod_name = error_msg.split("'")[1]
            await query.message.reply_text(f"🔧 جاري تثبيت المكتبة المفقودة: `{mod_name}`...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", mod_name], check=True)
                await query.message.reply_text(f"✅ تم تثبيت `{mod_name}` بنجاح. جرب التشغيل مرة أخرى.")
            except:
                await query.message.reply_text(f"❌ فشل تثبيت `{mod_name}`.")
        else:
            await query.message.reply_text(f"❌ خطأ في التشغيل:\n{e}")

# ==================================================
# إيقاف الأداة
# ==================================================
async def stop_tool(query, tool_name):
    if tool_name not in ACTIVE_PROCESSES:
        await query.message.reply_text(f"⚠️ الأداة `{tool_name}` غير نشطة.")
        return

    proc = ACTIVE_PROCESSES[tool_name]
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except:
        proc.kill()
    del ACTIVE_PROCESSES[tool_name]
    await query.message.reply_text(f"⏹️ تم إيقاف الأداة `{tool_name}`.")

# ==================================================
# حذف الأداة
# ==================================================
async def delete_tool(query, tool_name):
    file_path = os.path.join(TOOLS_DIR, tool_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        if tool_name in ACTIVE_PROCESSES:
            await stop_tool(query, tool_name)
        await query.message.reply_text(f"🗑️ تم حذف الأداة `{tool_name}` بنجاح.")
    else:
        await query.message.reply_text("❌ الملف غير موجود.")

# ==================================================
# معالجة جميع النقرات (مركزية - حل المشكلة)
# ==================================================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # إزالة علامة التحميل من الزر

    data = query.data
    user_id = query.from_user.id

    if user_id != AUTHORIZED_USER_ID:
        await query.message.reply_text("🚫 ليس لديك صلاحية للوصول.")
        return

    if data == "add_tool":
        await query.message.reply_text("📥 أرسل ملف بايثون (.py) لإضافته:")
        context.user_data["awaiting_tool"] = True

    elif data == "control_panel":
        await show_control_panel(query)

    elif data == "install_lib":
        await query.message.reply_text("📦 أرسل اسم المكتبة (مثل: `python-telegram-bot`) أو الأمر الكامل (مثل: `pip install ...`):")
        context.user_data["awaiting_lib"] = True

    elif data.startswith("run_"):
        tool_name = data.split("_", 1)[1]
        await run_tool(query, tool_name)

    elif data.startswith("stop_"):
        tool_name = data.split("_", 1)[1]
        await stop_tool(query, tool_name)

    elif data.startswith("delete_"):
        tool_name = data.split("_", 1)[1]
        await delete_tool(query, tool_name)

    elif data.startswith("tool_"):
        tool_name = data.split("_", 1)[1]
        await tool_options(query, tool_name)

# ==================================================
# معالجة إرسال الملفات (إضافة أداة)
# ==================================================
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != AUTHORIZED_USER_ID:
        return

    if not context.user_data.get("awaiting_tool"):
        return

    document = update.message.document
    if not document.file_name.endswith(".py"):
        await update.message.reply_text("⚠️ يرجى إرسال ملف بصيغة `.py` فقط.")
        return

    file = await document.get_file()
    file_path = os.path.join(TOOLS_DIR, document.file_name)
    await file.download_to_drive(file_path)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    await update.message.reply_text(
        f"✅ تم إضافة الأداة `{document.file_name}` بتاريخ {timestamp} بنجاح.",
        parse_mode="Markdown"
    )
    context.user_data["awaiting_tool"] = False

# ==================================================
# معالجة إرسال نص (تثبيت مكتبات)
# ==================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != AUTHORIZED_USER_ID:
        return

    if not context.user_data.get("awaiting_lib"):
        return

    text = update.message.text.strip()
    lib_name = text

    if text.startswith("pip install "):
        lib_name = text.replace("pip install ", "").split(" ")[0]
    else:
        text = f"pip install {text}"

    await update.message.reply_text(f"🔄انتضر شويه  جاري تثبيت المكتبة: `{lib_name}`...")
    try:
        result = subprocess.run(
            text.split(),
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8'
        )
        if result.returncode == 0:
            await update.message.reply_text(f"✅ تم تثبيت المكتبة `{lib_name}` بنجاح.")
        else:
            await update.message.reply_text(f"❌ خطأ:\n{result.stderr}")
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")

    context.user_data["awaiting_lib"] = False

# ==================================================
# بدء تشغيل البوت
# ==================================================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))  # ✅ معالج مركزي
    app.add_handler(MessageHandler(filters.Document.FileExtension("py"), handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 بوت سارة فون يعمل الآن... (اضغط /start في البوت)")
    app.run_polling()

if __name__ == "__main__":
    main()
