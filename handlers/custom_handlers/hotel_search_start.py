from telebot.types import Message
from states.hotel_search_start_states import HotelSearchStartStates
from states.lowprice_states import LowPriceStates
from states.highprice_states import HighPriceStates
from states.bestdeal_states import BestDealStates
from loader import bot
from api_tools import get_from_url, get_from_txt
from config_data import config
import datetime
from keyboards.inline import markup


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def a_start(message: Message) -> None:
    bot.set_state(message.from_user.id, HotelSearchStartStates.ask_city, message.chat.id)
    bot.send_message(message.from_user.id, 'Введите название города латиницей:')
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:  # Контекстный манагер
        data['command'] = message.text.replace('/', '')


@bot.message_handler(state=HotelSearchStartStates.ask_city)
def a_city(message: Message) -> None:
    # -----формирование строки запроса
    city = message.text.lower()
    url = "https://hotels4.p.rapidapi.com/locations/v2/search"
    querystring = {"query": city, "locale": "ru_RU"}
    headers = {
        "X-RapidAPI-Key": config.RAPID_API_KEY,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }
    # -----запрос данных
    request_anser = get_from_url.request_to_api(url, headers, querystring)
    try:
        if 'found in' in request_anser:
            bot.send_message(message.from_user.id, f'Город {city.title()} уже смотрели.')
            districts = get_from_txt.get_districts(request_anser['found in'])
        elif 'saved to' in request_anser:
            bot.send_message(message.from_user.id, f'Город {city.title()} еще не смотрели.')
            districts = get_from_txt.get_districts(request_anser['saved to'])
        else:
            bot.send_message(message.from_user.id, f'Что-то пошло не так.\n{request_anser}')
            bot.delete_state(message.from_user.id)
            return
    except Exception:
        print(f'Что-то пошло не так.\n{request_anser}')
        bot.send_message(message.from_user.id, f'Что-то пошло не так.\n{request_anser}')
        bot.delete_state(message.from_user.id)
        return
    # -----проверка названия города по наличию районов
    if len(districts) == 0:
        bot.send_message(message.from_user.id, 'Похоже, с названием города что-то не так. Попробуйте ввести другое.')
        return
    # -----сохраняем данные
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:  # Контекстный манагер
        data['city'] = city
    # -----выбор района
    bot.set_state(message.from_user.id, HotelSearchStartStates.ask_district, message.chat.id)
    bot.send_message(message.from_user.id, 'Уточните, пожалуйста:', reply_markup=markup.district_markup(districts))


@bot.callback_query_handler(func=lambda call: True, state=HotelSearchStartStates.ask_district)
def a_district(call) -> None:
    with bot.retrieve_data(call.from_user.id) as data:  # Контекстный манагер
        data['district'] = call.data
    bot.set_state(call.from_user.id, HotelSearchStartStates.ask_checkin)
    bot.send_message(call.from_user.id, f'Введите дату заселения. (dd/mm/yyyy)')


@bot.message_handler(state=HotelSearchStartStates.ask_checkin)
def a_checkin(message: Message) -> None:
    try:
        checkin_date = datetime.datetime.strptime(message.text, '%d/%m/%Y').date()
    except Exception:
        bot.send_message(message.from_user.id, f'Что-то не так с датой заселения.\n'
                                               f'Введите дату заселения. (dd/mm/yyyy)')
    else:
        with bot.retrieve_data(message.from_user.id) as data:  # Контекстный манагер
            data['checkin_date'] = checkin_date
        bot.set_state(message.from_user.id, HotelSearchStartStates.ask_checkout)
        bot.send_message(message.from_user.id, f'На сколько дней заселяемся?')


@bot.message_handler(state=HotelSearchStartStates.ask_checkout)
def a_checkout(message: Message) -> None:
    with bot.retrieve_data(message.from_user.id) as data:  # Контекстный манагер
        checkin_date = data['checkin_date']
    try:
        days = int(message.text)
        checkout_date = checkin_date + datetime.timedelta(days=days)
    except Exception:
        bot.send_message(message.from_user.id, f'Что-то не так.\n'
                                               f'На сколько дней заселяемся? (просто цифрой)')
    else:
        with bot.retrieve_data(message.from_user.id) as data:  # Контекстный манагер
            data['checkout_date'] = checkout_date
        bot.set_state(message.from_user.id, HotelSearchStartStates.ask_hotels_amount)
        bot.send_message(message.from_user.id, 'Список из скольки отелей вывести? (1-10)')


@bot.message_handler(state=HotelSearchStartStates.ask_hotels_amount)
def a_hotels_amount(message: Message) -> None:
    if message.text.isdigit():
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:  # Контекстный манагер
            if 1 <= int(message.text) <= 10:
                data['hotels_amount'] = int(message.text)
            elif int(message.text) > 10:
                data['hotels_amount'] = 10
            else:
                bot.send_message(message.from_user.id, 'Нужно ввести цифру.(1-10)')
                return
            target_command = data['command']
        if target_command == 'lowprice':
            bot.set_state(message.from_user.id, LowPriceStates.ask_if_photos, message.chat.id)
        elif target_command == 'highprice':
            bot.set_state(message.from_user.id, HighPriceStates.ask_if_photos, message.chat.id)
        elif target_command == 'bestdeal':
            bot.set_state(message.from_user.id, BestDealStates.ask_if_photos, message.chat.id)
        bot.send_message(message.from_user.id, 'Сколько приложить фото? (0-4)')
    else:
        bot.send_message(message.from_user.id, 'Нужно ввести цифру.(1-10)')
