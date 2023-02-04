def logger(log_string):
    with open('database/log.txt', 'a', encoding='utf-8') as file:
        file.write(f'{log_string}\n')
