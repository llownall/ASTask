import asyncio
import json
import random

import aiohttp
from flask import Blueprint, request

async_api = Blueprint('async_api', __name__, url_prefix='/async_api')


async def get_data_from_source(source_url):
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.get(source_url, timeout=2)
            return (await response.json()).get('data', [])
    except asyncio.exceptions.TimeoutError as exc:
        print(f'Timed out {source_url}')
        return []


@async_api.route('/all_data')
async def all_data():
    base_url = request.host_url[:-1] + async_api.url_prefix + f'/source/'

    tasks = []
    for index in range(1, 4):
        source_url = base_url + str(index)
        tasks.append(get_data_from_source(source_url))

    # ожидаем выполнения всех тасков и получаем их результаты
    tasks_results = await asyncio.gather(*tasks)
    all_data = [item for sublist in tasks_results for item in sublist]

    return {
        'items_count': len(all_data),
        'data': sorted(all_data, key=lambda item: item['id'])
    }


@async_api.route('/source/<int:source_id>')
async def source_data(source_id):
    await asyncio.sleep(1)

    # случайное событие
    random_option = random.choice(range(5))
    if random_option == 2:
        await asyncio.sleep(2)
    elif random_option == 3:
        return {}, 500

    index = source_id - 1
    id_range = list(range(1 + index * 10, 11 + index * 10)) + list(range(31 + index * 10, 41 + index * 10))

    with open('data.json', 'r') as file:
        file_data = json.load(file)
        data = [item for item in file_data if item['id'] in id_range]
        return {'data': data}


if __name__ == '__main__':
    # Код для создания файла с данными
    # Выполняется непосредственно при запуске этого скрипта (async_data.py)
    data = []
    for i in range(1, 61):
        data.append({'id': i, 'name': f'Test {i}'})
    with open('data.json', 'w') as file:
        json.dump(data, file, indent=4)
