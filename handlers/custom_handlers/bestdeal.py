from telebot.types import Message
import log_wrighter
from states.hotel_search_start_states import HotelSearchStartStates
from states.bestdeal_states import BestDealStates
from loader import bot
from api_tools import get_from_url, get_from_txt
from config_data import config
import datetime
from keyboards.inline import markup
import re


@bot.message_handler(state=BestDealStates.ask_if_photos)
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
            # -----формирование строки запроса
            url = "https://hotels4.p.rapidapi.com/properties/list"
            headers = {
                "X-RapidAPI-Key": config.RAPID_API_KEY,
                "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
            }
            querystring = {"destinationId": data['district'], "pageNumber": "1",
                           "pageSize": 25,
                           "checkIn": datetime.date.today() + datetime.timedelta(days=1),
                           "checkOut": datetime.date.today() + datetime.timedelta(days=2), "adults1": "1",
                           "sortOrder": "PRICE",
                           "locale": "ru_RU", "currency": "USD"}
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
            # --- получаем отели района
            district_data = get_from_txt.get_results(file_path)
            data['district_data'] = district_data
            # --- создаём список имён точек интереса
            landmarks = []
            for elem in district_data['data']['body']['searchResults']['results']:
                landmarks = [label['label'] for label in elem['landmarks']]
                break
            # --- просим выбрать точку интереса
            bot.set_state(message.from_user.id, BestDealStates.ask_point_of_interest)
            bot.send_message(message.from_user.id, 'Расстояние до чего вас интересует?',
                             reply_markup=markup.point_of_interest_markup(landmarks))
    else:
        bot.send_message(message.from_user.id, 'Нужно ввести цифру.(0-4)')


@bot.callback_query_handler(func=lambda call: True, state=BestDealStates.ask_point_of_interest)
def a_point_of_interest(call) -> None:
    with bot.retrieve_data(call.from_user.id) as data:  # Контекстный манагер
        data['landmark'] = call.data
    bot.set_state(call.from_user.id, BestDealStates.ask_distance)
    bot.send_message(call.from_user.id, f'Укажите предельное расстояние в километрах (например: 2.5).')


@bot.message_handler(state=BestDealStates.ask_distance)
def a_distance(message: Message) -> None:
    try:
        distance = float(message.text.replace(',', '.'))
    except Exception:
        bot.send_message(message.from_user.id, f'Укажите предельное расстояние в километрах (например: 2.5).')
        return

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:  # Контекстный манагер
        data['max_distance'] = distance
    bot.set_state(message.from_user.id, BestDealStates.make_request, message.chat.id)
    bot.send_message(message.from_user.id, f'Итак:\nГород: {data["city"].title()}\n'
                                           f'Точка интереса: {data["landmark"]}\n'
                                           f'Максимальное удаление {data["max_distance"]} км.\n'
                                           f'Колличество отелей: {data["hotels_amount"]}\n'
                                           f'Колличество фотрграфий: {data["photos_amount"]}\n'
                                           f'Всё верно? (да\\нет)')


@bot.message_handler(state=BestDealStates.make_request)
def a_request(message: Message) -> None:
    if message.text == 'да':
        # -----вывод результата
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:  # Контекстный манагер
            # --- логирование
            log_string = f'{str(datetime.datetime.now())} /bestdeal\nГород: {data["city"].title()}\nНайденные отели:'
            log_wrighter.logger(log_string)

            pattern = rf"(?<={data['landmark']}', 'distance': ')\S+"
            # --- вывод подходящих по дистанции отелей
            counter = 0
            for elem in data['district_data']['data']['body']['searchResults']['results']:
                # --- ищем дистанцию
                find = re.search(pattern, str(elem))  # -> 5,9
                if not find:
                    # print(f'Расстояние {elem["name"]} - {data["landmark"]} = {find} ')  # debug
                    distance = data['max_distance'] + 1
                else:
                    distance = float(find.group().replace(',', '.'))  # -> <class 'float'> 5.9
                if distance <= data['max_distance']:
                    # -----фотки
                    request_anser = get_from_url.request_to_api(
                        "https://hotels4.p.rapidapi.com/properties/get-hotel-photos",
                        {"X-RapidAPI-Key": config.RAPID_API_KEY, "X-RapidAPI-Host": "hotels4.p.rapidapi.com"},
                        {"id": elem['id']})
                    try:
                        if 'found in' in request_anser:
                            photo_path = request_anser['found in']
                        elif 'saved to' in request_anser:
                            photo_path = request_anser['saved to']
                        else:
                            bot.send_message(message.from_user.id,
                                             f'Похоже, фотографий для {elem["name"]} не нашлось.\n{request_anser}')
                            photo_path = None
                    except Exception:
                        bot.send_message(message.from_user.id,
                                         f'Фотографий для {elem["name"]} не нашлось.\n{request_anser}')
                        photo_path = None
                    if photo_path:
                        photos_list = get_from_txt.get_photos(photo_path, data['photos_amount'])
                    else:
                        photos_list = []
                    # --- финальный вывод
                    bot.send_message(message.from_user.id, f"{elem['name']}, {elem['ratePlan']['price']['current']} "
                                                           f"за ночь. {distance} км до {data['landmark']}")
                    # -----финальный вывод
                    log_string = f"{elem['name']} hotels.com/ho{elem['id']}"
                    log_wrighter.logger(log_string)
                    bot.send_message(message.from_user.id,
                                     f"{elem['name']}\n"
                                     f"Адрес:{elem['address']['locality']} {elem['address']['streetAddress']}\n"
                                     f"{distance} км до {data['landmark']}\n"
                                     f"Стоимость: {elem['ratePlan']['price']['current']}\n"
                                     f"Колличество фотрграфий: {len(photos_list)}\n"
                                     f"hotels.com/ho{elem['id']}")

                    counter += 1
                    for photo_url in photos_list:
                        bot.send_photo(message.chat.id, photo=photo_url, caption=elem['name'])
                # -----выход из вывода
                if counter == data['hotels_amount']:
                    break
        # -----выход из bestdeal
        if counter == 0:
            bot.send_message(message.from_user.id, 'Похоже ни чего не найдено.')
            log_wrighter.logger('\n')
        else:
            bot.send_message(message.from_user.id, 'Вот и всё что я нашёл.')
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
                                                   f'Точка интереса: {data["landmark"]}\n'
                                                   f'Максимальное удаление {data["max_distance"]} км.\n'
                                                   f'Колличество отелей: {data["hotels_amount"]}\n'
                                                   f'Колличество фотрграфий: {data["photos_amount"]}\n'
                                                   f'Всё верно? (да\\нет)')
