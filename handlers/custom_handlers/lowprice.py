from telebot.types import Message
from states.hotel_search_start_states import HotelSearchStartStates
from states.lowprice_states import LowPriceStates
from loader import bot
from api_tools import get_from_url, get_from_txt
from config_data import config
import datetime
import log_wrighter


@bot.message_handler(state=LowPriceStates.ask_if_photos)
def a_photos(message: Message) -> None:
    if message.text.isdigit():
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:  # Контекстный манагер
            if 0 <= int(message.text) <= 4:
                data['photos_amount'] = int(message.text)
            elif int(message.text) > 4:
                data['photos_amount'] = 4
            else:
                bot.send_message(message.from_user.id, 'Нужно ввести цифру.(0-4)')
                return
            bot.set_state(message.from_user.id, LowPriceStates.make_request, message.chat.id)
            bot.send_message(message.from_user.id, f'Итак:\nГород: {data["city"].title()}\n'
                                                   f'Колличество отелей: {data["hotels_amount"]}\n'
                                                   f'Колличество фотрграфий: {data["photos_amount"]}\n'
                                                   f'Всё верно? (да\\нет)')
    else:
        bot.send_message(message.from_user.id, 'Нужно ввести цифру.(0-4)')


@bot.message_handler(state=LowPriceStates.make_request)
def a_request(message: Message) -> None:
    if message.text == 'да':
        # -----формирование строки запроса
        url = "https://hotels4.p.rapidapi.com/properties/list"
        headers = {
            "X-RapidAPI-Key": config.RAPID_API_KEY,
            "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
        }
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:  # Контекстный манагер
            # --- логирование
            log_string = f'{str(datetime.datetime.now())} /lowprice\nГород: {data["city"].title()}\nНайденные отели:'
            log_wrighter.logger(log_string)

            querystring = {"destinationId": data['district'], "pageNumber": "1",
                           "pageSize": data["hotels_amount"],
                           "checkIn": datetime.date.today() + datetime.timedelta(days=1),
                           "checkOut": datetime.date.today() + datetime.timedelta(days=2), "adults1": "1",
                           "sortOrder": "PRICE",
                           "locale": "ru_RU", "currency": "USD"}
            photos_amount = data["photos_amount"]
        # -----запрос данных
        request_anser = get_from_url.request_to_api(url, headers, querystring)
        try:
            if 'found in' in request_anser:
                bot.send_message(message.from_user.id, 'Такой запрос уже был.')  # debug
                file_path = request_anser['found in']
            elif 'saved to' in request_anser:
                bot.send_message(message.from_user.id, 'Такого запроса ещё не было.')  # debug
                file_path = request_anser['saved to']
            else:
                bot.send_message(message.from_user.id, f'Что-то пошло не так.\n{request_anser}')  # debug
                bot.delete_state(message.from_user.id)
                return
        except Exception:
            print(f'Что-то пошло не так.\n{request_anser}')
            bot.send_message(message.from_user.id, f'Что-то пошло не так.\n{request_anser}')  # debug
            bot.delete_state(message.from_user.id)
            return
        # -----вывод результата
        for elem in get_from_txt.get_results(file_path)['data']['body']['searchResults']['results']:
            # -----фотки
            request_anser = get_from_url.request_to_api("https://hotels4.p.rapidapi.com/properties/get-hotel-photos",
                                                        headers, {"id": elem['id']})
            try:
                if 'found in' in request_anser:
                    photo_path = request_anser['found in']
                elif 'saved to' in request_anser:
                    photo_path = request_anser['saved to']
                else:
                    bot.send_message(message.from_user.id,
                                     f'Похоже, фотографий для {elem["name"]} не нашлось.\n{request_anser}')  # debug
                    photo_path = None
            except Exception:
                print(f'Фотографий для {elem["name"]} не нашлось.\n{request_anser}')
                bot.send_message(message.from_user.id,
                                 f'Фотографий для {elem["name"]} не нашлось.\n{request_anser}')  # debug
                photo_path = None
            if photo_path:
                photos_list = get_from_txt.get_photos(photo_path, photos_amount)
            else:
                photos_list = []
            # -----финальный вывод
            log_string = f"{elem['name']} hotels.com/ho{elem['id']}"
            log_wrighter.logger(log_string)
            bot.send_message(message.from_user.id,
                             f"{elem['name']}\n"
                             f"Адрес:{elem['address']['locality']} {elem['address']['streetAddress']}\n"
                             f"Расстояние до {elem['landmarks'][0]['label']} - {elem['landmarks'][0]['distance']}\n"
                             f"Стоимость: {elem['ratePlan']['price']['current']}\n"
                             f"Колличество фотрграфий: {len(photos_list)}\n"
                             f"hotels.com/ho{elem['id']}")
            for photo_url in photos_list:
                bot.send_photo(message.chat.id, photo=photo_url, caption=elem['name'])
        # -----выход из lowprice
        bot.send_message(message.from_user.id, 'Это всё что я нашёл.')
        log_wrighter.logger('\n')
        bot.delete_state(message.from_user.id)
        return

    elif message.text == 'нет':
        bot.set_state(message.from_user.id, HotelSearchStartStates.ask_city, message.chat.id)
        bot.send_message(message.from_user.id, 'Тогда начнём с начала. Какой город?')
        return
    else:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:  # Контекстный манагер
            bot.send_message(message.from_user.id, f'Итак:\nГород: {data["city"].title()}\n'
                                                   f'Колличество отелей: {data["hotels_amount"]}\n'
                                                   f'Колличество фотрграфий: {data["photos_amount"]}\n'
                                                   f'Всё верно? (да\\нет)')
