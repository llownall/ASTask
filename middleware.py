from functools import wraps

from flask import request, url_for, redirect

from models import Session, AppSession, db_engine


def require_user(func):
    """
    Декоратор добавляет объект модели User в запрос (flask.request),
    находя нужного пользователя по хешу сессии из cookies.
    Если хеша нет или пользователь не найден, перенаправляет на страницу логина.
    """
    @wraps(func)
    def add_user_to_request_middleware(*args, **kwargs):
        user = None
        session = Session()
        try:
            session_hash = request.cookies.get('session')
            app_session = session.query(AppSession).filter(AppSession.hash_ == session_hash).one()
            user = app_session.user
        except Exception as exc:
            print(exc)
        finally:
            session.close()

        if user is None:
            return redirect(url_for('login'))

        request.__setattr__('user', user)
        return func(*args, **kwargs)

    return add_user_to_request_middleware
