from telebot.handler_backends import State, StatesGroup


class HotelSearchStartStates(StatesGroup):
    ask_city = State()  # data['command'], data['city']
    ask_district = State()  # data['district']
    ask_checkin = State()  # data['checkin_date']
    ask_checkout = State()  # data['checkout_date']
    ask_hotels_amount = State()  # data['hotels_amount']
