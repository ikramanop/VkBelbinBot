import configparser
import json
import re

from database.connector import DbConnector
from engine.decypher import calculate_test
from engine.vk_connector import VkApiConnector

db_config_raw = configparser.ConfigParser()
vk_config_raw = configparser.ConfigParser()

db_config_raw.read('config/db_config.ini')
vk_config_raw.read('config/vk_config.ini')

DB_CONFIG = db_config_raw['DATABASE CONFIG']
VK_CONFIG = vk_config_raw['VK GROUP CONFIG']

PATTERN = re.compile(r'^(10|\d) (10|\d) (10|\d) (10|\d) (10|\d) (10|\d) (10|\d) (10|\d)$')

STATIC_TEXT = json.loads(open('./static/questions.json', 'r', encoding='UTF-8').read())

api = VkApiConnector(
    token=VK_CONFIG['VK_TOKEN'],
    group_id=VK_CONFIG['VK_GROUP_ID']
)

data = DbConnector(
    host=DB_CONFIG['DB_HOSTNAME'],
    port=DB_CONFIG['DB_PORT'],
    username=DB_CONFIG['DB_USERNAME'],
    password=DB_CONFIG['DB_PASSWORD'],
    db_name=DB_CONFIG['DB_NAME'],
)

for event in api.longpoll.listen():
    if api.check_message(event):
        if event.from_user:
            if data.get_user(event.user_id):
                if event.text.lower() == 'закончить тест':
                    data.delete_user(event.user_id)
                    data.delete_result(event.user_id)
                    api.send_message(
                        peer_id=event.user_id,
                        message='На этом закончим',
                        keyboard='{"buttons":[],"one_time":true}'
                    )
                    continue

                if data.get_user(event.user_id).phase == 0:
                    if event.text.lower() == 'начать тест' and data.get_user(event.user_id).active:
                        data.increment_user_phase(event.user_id)
                        data.init_json(
                            peer_id=event.user_id,
                            path_to_json='static/json_template.json'
                        )
                        api.send_message(
                            peer_id=event.user_id,
                            message=STATIC_TEXT['1']
                        )

                    else:
                        result = api.get_user_name(event.user_id)
                        data.add_result(
                            peer_id=event.user_id,
                            name=event.text,
                            vk_name=f"{result[0]['first_name']} {result[0]['last_name']}"
                        )
                        data.set_active(event.user_id)
                        api.send_message(
                            peer_id=event.user_id,
                            message=STATIC_TEXT['0'],
                            keyboard=open('./keyboards/keyboard_1.json', 'r', encoding='UTF-8').read()
                        )

                elif data.get_user(event.user_id).phase in list(range(1, 8)):
                    if PATTERN.match(event.text):
                        new_data = list(map(int, event.text.split(' ')))

                        if sum(new_data) != 10:
                            send_string = '🙄 Сумма введённых тобой баллов должна быть равна 10, пожалуйста, ' \
                                          'перепроверь. '
                            attachment = None
                        else:
                            data.update_json(
                                peer_id=event.user_id,
                                phase=data.get_user(event.user_id).phase,
                                new_data=new_data
                            )

                            data.increment_user_phase(event.user_id)

                            if data.get_user(event.user_id).phase == 8:
                                msg_attach = calculate_test(event.user_id, data)
                                send_string = msg_attach[0]
                                attachment = api.prepare_photo_attachment(event.user_id, msg_attach[1])
                            else:
                                send_string = STATIC_TEXT[str(data.get_user(event.user_id).phase)]
                                attachment = None

                        api.send_message(
                            peer_id=event.user_id,
                            message=send_string,
                            attachment=attachment
                        )
                    else:
                        api.send_message(
                            peer_id=event.user_id,
                            message='😩 Ожидается, что ты введёшь 8 чисел от 0 до 10 подряд через пробел.\nПример: 0 '
                                    '1 2 3 4 0 0 0'
                        )

                elif data.get_user(event.user_id).phase == 8:
                    api.send_message(
                        peer_id=event.user_id,
                        message='Тестирование завершено'
                    )

                else:
                    api.send_message(
                        peer_id=event.user_id,
                        message='???'
                    )

            else:
                try:
                    if json.loads(event.payload)['command'] == 'start':
                        data.add_user(event.user_id)
                        api.send_message(
                            peer_id=event.peer_id,
                            message='Введи своё имя'
                        )
                        api.send_message(
                            peer_id=event.user_id,
                            message='Такой команды нет! :('
                        )
                except (KeyError, AttributeError):
                    if event.text.lower() == 'начать':
                        data.add_user(event.user_id)
                        api.send_message(
                            peer_id=event.user_id,
                            message='Введи своё имя'
                        )
                    else:
                        api.send_message(
                            peer_id=event.user_id,
                            message='Такой команды нет! :('
                        )
