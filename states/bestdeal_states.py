from telebot.handler_backends import State, StatesGroup


class BestDealStates(StatesGroup):
    ask_if_photos = State()  # data['photos_amount'], data['district_data']
    ask_point_of_interest = State()  # data['landmark']
    ask_distance = State()  # data['max_distance']
    make_request = State()
