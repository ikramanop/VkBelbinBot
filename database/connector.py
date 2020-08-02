import json

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from .models import Base, User, Result


class DbConnector:
    """
    Класс для подключения к базе данных MySQL и работе с данными пользователей
    """

    def __init__(self, host, port, db_name, username, password):
        """
        :param host: имя хоста сервера с базой данных
        :param port: порт сервера с базой данных
        :param db_name: имя базы данных
        :param username: пользователь базый данных
        :param password: пароль для пользователя
        """
        self.host = host
        self.port = port
        self.db_name = db_name
        self.username = username
        self.password = password

        self.connection = self.get_connection()

        self.session = sessionmaker(
            bind=self.connection.engine,
            autocommit=True
        )()

        Base.metadata.create_all(self.connection.engine)

    def get_connection(self):
        """
        Получение соединения с базой данных
        :return: Объект соединения
        """
        engine = sqlalchemy.create_engine(
            'mysql+pymysql://{user}:{password}@{host}:{port}/{db}'.format(
                user=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
                db=self.db_name
            ),
            encoding='utf8',
            pool_pre_ping=True,
            echo=True
        )

        return engine.connect()

    def get_user(self, peer_id):
        """
        Получение пользователя
        :param peer_id: VK ID пользователя
        :return: Объект пользователя
        """
        self.session.expire_all()
        self.session.flush()
        return self.session.query(User).filter_by(peer_id=peer_id).first()

    def increment_user_phase(self, peer_id):
        """
        Увеличение фазы пользователя на 1
        :param peer_id: VK ID пользователя
        """
        self.session.expire_all()
        user = self.get_user(peer_id)
        if user:
            self.session.query(User).filter_by(peer_id=peer_id). \
                update({"phase": user.phase + 1})
            self.session.flush()

    def add_user(self, peer_id):
        """
        Добавление нового пользователя
        :param peer_id: VK ID пользователя
        """
        self.session.expire_all()
        if not self.get_user(peer_id):
            user = User(peer_id=peer_id)
            self.session.add(user)
            self.session.flush()

    def set_active(self, peer_id):
        """
        Проставление пользователелю active = True
        :param peer_id: VK ID пользователя
        """
        self.session.expire_all()
        if self.get_user(peer_id):
            self.session.query(User).filter_by(peer_id=peer_id). \
                update({"active": True})
            self.session.flush()

    def delete_user(self, peer_id):
        """
        Удаление пользователя
        :param peer_id: VK ID пользователя
        """
        self.session.expire_all()
        if self.get_user(peer_id):
            self.session.query(User).filter_by(peer_id=peer_id). \
                delete(synchronize_session='fetch')
            self.session.flush()

    def init_json(self, peer_id, path_to_json):
        """
        Инициализация поля с данными по тесту
        :param peer_id: VK ID пользователя
        :param path_to_json: Путь к json-файлу с шаблоном инициализации
        """
        self.session.expire_all()
        if self.get_user(peer_id):
            self.session.query(User).filter_by(peer_id=peer_id). \
                update({f"json_points": open(path_to_json, 'r', encoding='UTF-8').read()})
            self.session.flush()

    def update_json(self, peer_id, phase, new_data):
        """
        Обновление json-поля с данными по тестированию
        :param peer_id: VK ID пользователя
        :param phase: Фаза пользователя, данные по которой нужно обновить
        :param new_data: Массив из 8 чисел с ответом на вопрос
        """
        self.session.expire_all()
        user = self.get_user(peer_id)
        if user:
            json_array = json.loads(user.json_points)
            for i, key in enumerate(json_array[str(phase)].keys()):
                json_array[str(phase)][key] = new_data[i]
            self.session.query(User).filter_by(peer_id=peer_id). \
                update({f"json_points": json.dumps(json_array)})
            self.session.flush()

    def get_result(self, peer_id):
        """
        Получение результата тестирования
        :param peer_id: VK ID пользователя
        :return: Объект результата
        """
        self.session.expire_all()
        self.session.flush()
        return self.session.query(Result).filter_by(peer_id=peer_id).first()

    def add_result(self, peer_id, name, vk_name):
        """
        Добавление результата нового пользователя
        :param peer_id: VK ID пользователя
        :param name: Имя, которое ввёл пользователь
        :param vk_name: Имя из ВК
        """
        self.session.expire_all()
        if not self.get_result(peer_id):
            result = Result(peer_id=peer_id, name=name, vk_name=vk_name)
            self.session.add(result)
            self.session.flush()

    def update_result(self, peer_id, text, priority):
        """
        Обновление результата тестирования
        :param peer_id: VK ID пользователя
        :param text: Результат тестирования (процентное соотношение)
        :param priority: Приоритетная роль
        :return:
        """
        self.session.expire_all()
        if self.get_user(peer_id):
            self.session.query(Result).filter_by(peer_id=peer_id). \
                update({"result": text, "priority": priority})
            self.session.flush()

    def delete_result(self, peer_id):
        """
        Удаление результата
        :param peer_id: VK ID пользователя
        """
        self.session.expire_all()
        if self.get_result(peer_id):
            self.session.query(Result).filter_by(peer_id=peer_id). \
                delete(synchronize_session='fetch')
            self.session.flush()
