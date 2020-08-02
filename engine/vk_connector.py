import time

import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType


class VkApiConnector:
    """
    Класс для использования VK API
    """

    class MyVkLongPoll(VkLongPoll):
        """
        Переопределение класса с LongPoll для обработки типовых ошибок
        Позволяет более эффективно пользоваться ботов
        """

        def listen(self):
            while True:
                try:
                    for _event in self.check():
                        yield _event
                except Exception as err:
                    print('Longpoll Error (VK):', err)

    def __init__(self, token):
        """
        Инициализация VK API
        :param token: Токен для группы ВК
        """
        vk_session = vk_api.VkApi(token=token)

        self.longpoll = self.MyVkLongPoll(vk_session)

        self.vk = vk_session.get_api()

    def send_message(self, peer_id, message, keyboard=None, attachment=None):
        """
        Отправка сообщения пользователю
        :param peer_id: VK ID пользователя
        :param message: Сообщение пользователю
        :param keyboard: Json с клавиатурой
        :param attachment: Приложение к сообщению
        """
        self.vk.messages.send(
            user_id=peer_id,
            random_id=int(time.time()),
            message=message,
            keyboard=keyboard,
            attachment=attachment
        )

    @staticmethod
    def check_message(event):
        """
        Проверка того, что сообщение отправлено в личные сообщения сообщества
        :param event: Объект EVENT
        :return: Bool
        """
        return event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text

    def get_user_name(self, peer_id):
        """
        Получить имя пользователя из ВК
        :param peer_id: VK ID пользователя
        :return: ВК имя пользователя
        """
        return self.vk.users.get(user_ids=[peer_id])

    def prepare_photo_attachment(self, peer_id, filename):
        """
        Подготовить фото для отправки
        :param peer_id: VK ID пользователя
        :param filename: Путь к фотографии
        :return: Имя аттачмента для отправки фотографии
        """
        url = self.vk.photos.getMessagesUploadServer(peer_id=peer_id)['upload_url']

        pfile = requests.request(
            method='POST',
            url=url,
            files={'photo': open(filename, 'rb')}
        ).json()

        photo = self.vk.photos.saveMessagesPhoto(
            server=pfile['server'],
            photo=pfile['photo'],
            hash=pfile['hash']
        )[0]

        return f"photo{photo['owner_id']}_{photo['id']}"
