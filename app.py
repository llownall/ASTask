from flask import Flask, render_template, request, redirect, url_for, make_response, abort
from sqlalchemy import text

from async_data import async_api
from middleware import require_user
from models import *

app = Flask(__name__)
app.register_blueprint(async_api)


@app.route('/users')
@require_user
def users():
    """
    Метод сериализует и возвращает всех пользователей
    """
    fields = [
        'id',
        'username',
        'is_super',
    ]

    session = Session()
    users = session.query(User).all()
    session.close()
    return {'users': [{k: v for k, v in user.__dict__.items() if k in fields} for user in users]}


@app.route('/')
@require_user
def home():
    return render_template('main_page.html')


@app.route('/add', methods=['POST'])
@require_user
def add_user():
    if not request.user.is_super:
        abort(401)

    session = Session()
    try:
        session.add_all([
            User(
                username=request.form['username'],
                password=request.form['password'],
                is_super=request.form.get('is_super', 'off') == 'on',
            ),
        ])
        session.commit()
    except Exception as exc:
        print(exc)
        return {'error_message': str(exc)}, 400
    finally:
        session.close()
    return {}


@app.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@require_user
def update_user(user_id):
    if not request.user.is_super:
        abort(401)

    session = Session()
    user = session.query(User).get(user_id)
    if request.method == 'POST':
        if username := request.form['username']:
            user.username = username
        if password := request.form['password']:
            user.password_hash = User.get_password_hash(password)
        if request.form.get('is_super') == 'on':
            user.is_super = True
        else:
            user.is_super = False
        session.commit()
        session.close()
        return redirect(url_for('home'))

    session.close()
    return render_template('edit_page.html', user=user)


@app.route('/delete/<int:user_id>')
@require_user
def delete_user(user_id):
    if not request.user.is_super:
        abort(401)

    with db_engine.connect() as connection:
        connection.execute(text('DELETE FROM app_user WHERE id = :user_id'), user_id=user_id)
    return redirect(url_for('home'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session = Session()
        if (user := session.query(User).filter(
                User.username == request.form.get('username'),
                User.password_hash == User.get_password_hash(request.form.get('password')),
        ).one_or_none()) is not None:
            # если существует пользователь с таким именем и паролем,
            # добавим ему в cookies хеш сессии для дальнейшей его идентификации
            redirect_response = make_response(redirect(url_for('home')))
            redirect_response.set_cookie('session', user.get_or_create_app_session(session))
            session.close()
            return redirect_response
        else:
            return render_template('login.html', error_message='Неверное имя пользователя или пароль')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """
    Удаляем хеш сессии из cookies
    """
    redirect_response = make_response(redirect(url_for('login')))
    redirect_response.delete_cookie('session')
    return redirect_response


if __name__ == '__main__':
    app.run()
