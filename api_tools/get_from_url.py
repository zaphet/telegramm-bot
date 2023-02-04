import json
import requests
import os


def request_to_api(url, headers, querystring):
    try:
        # -----файл для запросов по городу
        if "query" in querystring:
            file_path = f'database/{url.split("/")[-1]}_{querystring["query"]}.txt'
        # -----файл для запросов по району
        elif "destinationId" in querystring:
            file_path = f'database/{url.split("/")[-1]}_{querystring["sortOrder"]}_' \
                        f'{querystring["destinationId"]}_{querystring["pageSize"]}.txt'
        # -----файл для запроса по фоткам
        elif "id" in querystring:
            file_path = f'database/{url.split("/")[-1]}_{querystring["id"]}.txt'
        # -----файл для неожиданных запросов
        else:
            file_path = f'database/{url.split("/")[-1]}_temp.txt'

        # ----если такой запрос уже был
        if os.path.exists(file_path):
            return {'found in': file_path}
        # -----если такого запроса еще небыло
        else:
            response = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
            if response.status_code == requests.codes.ok:
                response_data = json.loads(response.text)

                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(response_data, file, indent=4)
                return {'saved to': file_path}
            else:
                return response.status_code

    except Exception as exc:
        return f'{type(exc)} {exc}'


if __name__ == '__main__':
    pass
