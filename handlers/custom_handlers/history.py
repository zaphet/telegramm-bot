from telebot.types import Message
from loader import bot


@bot.message_handler(commands=['history'])
def go_history(message: Message) -> None:
    with open('database/log.txt', 'r', encoding='utf-8') as file:
        bot.send_message(message.from_user.id, file.read())
