import json
import sys
from http import HTTPStatus

from flask import Flask, request, Response
from flask_cors import CORS

from Library.constants import CookieNames, SCHEMA, CvParts
from Library.html import HTMLModals
from Library.logic import Controller, Authenticator
from Library.core import Formatting

BASE_URL = '192.168.8.100:8888'
DB_PATH = '/Users/joshnicholls/Desktop/myCV/data.db'

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'

controller = Controller(DB_PATH)
authenticator = Authenticator(DB_PATH)


def build_response(data, status_code=HTTPStatus.OK):
    response = Response(data, status=status_code, mimetype='application/json')
    response.headers.add("Access-Control-Allow-Origin", 'http://{}'.format(BASE_URL))
    response.headers.add("Access-Control-Allow-Credentials", "true")
    response.headers.add("Access-Control-Allow-Headers: Content-Type", "*")
    return response


@app.route('/users', methods=['GET'])
def users():
    requested_user_id = request.args.get('id', default=None, type=str)
    if requested_user_id:
        user_dict = controller.get_full_user_data(requested_user_id, date_format=Formatting.DATETIME_PP_FORMAT,
                                                  replace_none=True)
        if user_dict:
            return build_response(json.dumps(user_dict))
        else:
            return build_response(json.dumps(None))
    else:
        return build_response(json.dumps(None), status_code=HTTPStatus.NO_CONTENT)


@app.route('/users/basic', methods=['GET'])
def basic_users():
    requested_user_id = request.args.get('id', default=None, type=str)
    if requested_user_id:
        user_dict = controller.get_user_data(user_id=requested_user_id)
        if user_dict:
            return build_response(json.dumps(user_dict))
        else:
            return build_response(json.dumps(None))
    else:
        return build_response(json.dumps(None), status_code=HTTPStatus.NO_CONTENT)


@app.route('/users/edit', methods=['POST'])
def edit():
    # Extract cookies for authentication.
    session_key = request.cookies.get(CookieNames.SESSION_KEY)
    user_id_from_cookie = request.cookies.get(CookieNames.USER_ID)

    # Convert 'null' to None.
    session_key = None if session_key == 'null' else session_key
    user_id_from_cookie = None if user_id_from_cookie == 'null' else user_id_from_cookie

    # Extract edit dictionary.
    edit_dict = request.get_json()

    if all([True for var in [session_key, user_id_from_cookie, edit_dict] if var is not None]):
        if authenticator.validate_session(session_key, user_id_from_cookie):
            controller.edit(user_id_from_cookie, edit_dict, edit_dict.get('edit_id'))
            return build_response(json.dumps({'success': 'Change made successfully! Refresh the page to see it.'}))
    return build_response(json.dumps({'error': 'You are not authorised to make this change.'}))


@app.route('/users/add', methods=['POST'])
def add():
    # Extract cookies for authentication.
    session_key = request.cookies.get(CookieNames.SESSION_KEY)
    user_id_from_cookie = request.cookies.get(CookieNames.USER_ID)

    # Extract add dictionary.
    add_dict = request.get_json()

    if all([True for var in [session_key, user_id_from_cookie, add_dict] if var is not None]):
        if authenticator.validate_session(session_key, user_id_from_cookie):
            controller.add(user_id_from_cookie, add_dict)
            return build_response(json.dumps({'success': 'Change made successfully! Refresh the page to see it.'}))
    return build_response(json.dumps({'error': 'You are not authorised to make this change.'}))


@app.route('/users/delete', methods=['POST'])
def delete():
    # Extract cookies for authentication.
    session_key = request.cookies.get(CookieNames.SESSION_KEY)
    user_id_from_cookie = request.cookies.get(CookieNames.USER_ID)

    # Extract add dictionary.
    delete_dict = request.get_json()

    if all([True for var in [session_key, user_id_from_cookie, delete_dict] if var is not None]):
        if authenticator.validate_session(session_key, user_id_from_cookie):
            controller.delete(delete_dict.get('delete_type'), delete_dict.get(SCHEMA.ID))

            # Force sign out if deleting user, for everything else just refresh.
            if delete_dict.get('delete_type') == CvParts.INFO:
                response_dict = {'success': 'Data deleted!', 'signout': ''}
            else:
                response_dict = {'success': 'Data deleted!', 'refresh': None}
            return build_response(json.dumps(response_dict))
    return build_response(json.dumps({'error': 'You are not authorised to make this change.'}))


@app.route('/auth/login', methods=['POST'])
def login():
    # Extract data.
    data = request.get_json()

    # Client will save this as a cookie.
    user_data = controller.get_user_data(email=data.get("email"))
    if user_data:
        # Will have to decrypt password, probs should do it on this level as server will maintain private/public keys.
        session_key = authenticator.start_session(user_data.get('id'), data.get("password"))
        if session_key:
            data = {
                CookieNames.USER_ID: user_data.get('id'),
                CookieNames.SESSION_KEY: session_key
            }
            return build_response(json.dumps(data))
        else:
            return build_response(json.dumps({'error': 'Incorrect password!'}))
    else:
        return build_response(json.dumps({'error': 'User does not exist!'}))


@app.route('/auth/changepassword', methods=['POST'])
def change_password():
    # Extract cookies for authentication.
    session_key = request.cookies.get(CookieNames.SESSION_KEY)
    user_id_from_cookie = request.cookies.get(CookieNames.USER_ID)

    # Extract data.
    data = request.get_json()

    if authenticator.validate_session(session_key, user_id_from_cookie):
        authenticator.set_password(user_id_from_cookie, data.get('password'))
        return build_response(json.dumps({'success': 'Password changed successfully!'}))

    return build_response(json.dumps({'error': 'User not authorised to change this password.'}))


@app.route('/users/signup', methods=['POST'])
def sign_up():
    # Extract data.
    data = request.get_json()

    # Add user.
    user_id = controller.new_user(data.get('email'), data.get('display_name'), data.get('headline'))
    if user_id:
        authenticator.set_password(user_id, data.get('password'))
        data = {
            'user_id': user_id,
            'email': data.get("email"),
            'success': 'Account created!'
        }
        return build_response(json.dumps(data))
    else:
        return build_response(json.dumps({'error': 'Email address already registered!'}))


@app.route('/html/modal/share', methods=['GET'])
def share_modal():
    requested_user_id = request.args.get('user_id', default=None, type=str)
    modal_html = HTMLModals.share_modal(BASE_URL, requested_user_id)
    return build_response(json.dumps(modal_html))


@app.route('/html/modal/login', methods=['GET'])
def login_modal():
    modal_html = HTMLModals.login_modal()
    return build_response(json.dumps(modal_html))


@app.route('/html/modal/signup', methods=['GET'])
def signup_modal():
    modal_html = HTMLModals.signup_modal()
    return build_response(json.dumps(modal_html))


@app.route('/html/modal/edit', methods=['GET'])
def edit_modal():
    user_id_from_cookie = request.cookies.get(CookieNames.USER_ID)
    requested_edit_type = request.args.get('edit_type', default=None, type=str)
    requested_row_id = request.args.get('row_id', default=None, type=str)
    modal_html = controller.generate_edit_modal(requested_edit_type, requested_row_id, user_id_from_cookie)
    return build_response(json.dumps(modal_html))


@app.route('/html/modal/add', methods=['GET'])
def add_modal():
    requested_add_type = request.args.get('add_type', default=None, type=str)
    requested_row_id = request.args.get('row_id', default=None, type=str)
    modal_html = HTMLModals.add_modal(requested_add_type, requested_row_id)
    return build_response(json.dumps(modal_html))


@app.route('/html/modal/delete', methods=['GET'])
def delete_modal():
    requested_delete_type = request.args.get('delete_type', default=None, type=str)
    requested_row_id = request.args.get('row_id', default=None, type=str)
    modal_html = HTMLModals.delete_modal(requested_delete_type, requested_row_id)
    return build_response(json.dumps(modal_html))


@app.route('/html/modal/manage', methods=['GET'])
def manage_modal():
    user_id_from_cookie = request.cookies.get(CookieNames.USER_ID)
    modal_html = controller.generate_manage_modal(user_id_from_cookie)
    return build_response(json.dumps(modal_html))


def main():
    app.run('0.0.0.0')


if __name__ == '__main__':
    sys.exit(main())
