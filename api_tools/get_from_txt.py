import json
import re


def get_districts(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            city_data = json.load(file)
        city_districts = list()
        for key_name in city_data['suggestions']:
            if key_name['group'] == 'CITY_GROUP':
                for entities in key_name['entities']:
                    city_districts.append({'name': entities['name'], 'destination_id': entities['destinationId']})
    except Exception as exc:
        return f'{type(exc)} {exc}'
    else:
        return city_districts


def get_results(path):
    try:

        with open(path, 'r') as file:
            result = json.load(file)

    except Exception as exc:
        return f'{type(exc)} {exc}'
    else:
        return result


def get_photos(path, amount):
    try:

        with open(path, 'r') as file:
            data = json.load(file)
            result = [re.sub(r'\{size}', 'z', obj['baseUrl']) for obj in data['hotelImages']]

    except Exception as exc:
        print(f'{type(exc)} {exc}')
        return []
    else:
        return result[0: amount]


if __name__ == '__main__':
    pass
