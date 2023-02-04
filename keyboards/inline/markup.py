from telebot import types


def district_markup(districts):
    destinations = types.InlineKeyboardMarkup()
    for district in districts:
        destinations.add(types.InlineKeyboardButton(text=district['name'],
                                                    callback_data=f'{district["destination_id"]}'))
    return destinations


def point_of_interest_markup(landmarks):
    points = types.InlineKeyboardMarkup()
    for landmark in landmarks:
        points.add(types.InlineKeyboardButton(text=landmark,
                                              callback_data=f'{landmark}'))
    return points


if __name__ == '__main__':
    pass
