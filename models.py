import datetime
import hashlib

from sqlalchemy.orm import declarative_base, sessionmaker, relationship, backref
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean

db_engine = create_engine('postgresql://admin:iAud82@localhost:5432/as_task')
Base = declarative_base()
Session = sessionmaker(bind=db_engine)

password_salt = '23ri3fk'
session_salt = '367jh3v'


def generate_hash(salt, string):
    return hashlib.md5((string + salt).encode()).hexdigest()


class User(Base):
    __tablename__ = 'app_user'

    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    password_hash = Column(String(32))
    is_super = Column(Boolean, default=False)

    @staticmethod
    def get_password_hash(password):
        return generate_hash(password_salt, password)

    def get_or_create_app_session(self, session) -> str:
        if self.session is not None:
            return self.session.hash
        else:
            new_app_session = AppSession(user=self)
            hash = new_app_session.hash
            session.add(new_app_session)
            session.commit()
            return hash

    def __init__(self, username, password, is_super=False):
        self.username = username
        self.password_hash = self.get_password_hash(password)
        self.is_super = is_super

    def __repr__(self):
        return "<User(name='%s')>" % self.username


class AppSession(Base):
    __tablename__ = 'app_session'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('app_user.id', ondelete='CASCADE'))
    user = relationship('User', backref=backref('session', uselist=False))
    hash_ = Column(String(32), default='')

    @property
    def hash(self):
        # вернем существующий хеш или создадим новый
        if not self.hash_:
            print('new hash!')
            self.hash_ = generate_hash(session_salt, f'{self.user.id}{datetime.datetime.now().timestamp()}')
        return self.hash_


def initialize():
    """
    Создание таблиц и добавление первого суперпользователя
    """
    Base.metadata.drop_all(db_engine)
    Base.metadata.create_all(db_engine)

    session = Session()
    session.add_all([
        User(username='admin', password='admin', is_super=True),
    ])
    session.commit()
    session.close()


if __name__ == '__main__':
    initialize()
