from telebot.handler_backends import State, StatesGroup


class HighPriceStates(StatesGroup):
    ask_if_photos = State() # data['photos_amount']
    make_request = State()
