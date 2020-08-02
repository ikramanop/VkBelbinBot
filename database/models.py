from sqlalchemy import Column, SmallInteger, Text, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """
    Объект пользователя, проходящего тест
    """
    __tablename__ = 'users'
    __table_args__ = (
        {'mysql_charset': 'utf8'}
    )

    peer_id = Column(String(50), nullable=False, primary_key=True)
    phase = Column(SmallInteger, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=False)
    json_points = Column(Text)


class Result(Base):
    """
    Объект результата прохождения теста пользователем
    """
    __tablename__ = 'results'
    __table_args__ = (
        {'mysql_charset': 'utf8'}
    )

    peer_id = Column(String(50), nullable=False, primary_key=True)
    name = Column(Text, nullable=False)
    vk_name = Column(Text, nullable=False)
    result = Column(Text, nullable=True)
    priority = Column(String(25), nullable=True)
