import telebot
import socket

TOKEN = "8488441176:AAFfABzqcKOrVfYBHzZ4EADU70RcFTxgkA8"
bot = telebot.TeleBot(TOKEN)

def get_ip():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

@bot.message_handler(commands=['start'])
def send_test(message):
    current_ip = get_ip()
    test_url = f"http://{current_ip}:8080/math-test/f360ce73-6028-4cc7-b508-588cfd274c2d/"
    bot.send_message(message.chat.id, f"📚 Математический тест:\n{test_url}")

print("Бот запущен!")
bot.polling()