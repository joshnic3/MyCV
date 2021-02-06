# What is modals where generated by Python and injected into hosted html?
from Library.constants import Component, Schema, Key
from Library.Utilities.core import Formatting
import datetime
from Library.data import Mapping


class HTMLComponents:

    HTML = {
        'alert': '<div id="{alert_id}" class="container alert alert-{alert_type} text-center" role="alert" style="display: none;">{content}</div>',
        'modal': {
            'modal': '<div class="modal fade" id="{modal_id}" tabindex="-1" role="dialog" aria-labelledby="{modal_id}" aria-hidden="true">',
            'dialog': '<div class="modal-dialog" role="document">',
            'content': '<div class="modal-content">',
            'header': '<div class="modal-header">',
            'body': '<div class="modal-body">',
            'title': '<h5 class="modal-title">',
            'close_button': '<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>'
        },
        'input': {
            'form': '<form class="{classes}">',
            'button': '<button type="button" class="{classes}" onclick="{on_click}" data-dismiss="{data_dismiss}">{content}</button>',
            'input': '<input type="{input_type}" class="{classes}" id="{input_id}" placeholder="{placeholder}" value="{value}" {readonly}>',
            'textarea': '<textarea class="{classes}" id="{textarea_id}" rows=5>{content}</textarea>',
            'date': '<input type="date" class={classes} id="{date_id}" value="{value}" {readonly} {max}>'
        }

    }

    @staticmethod
    def null(input_var):
        return '' if input_var is None else input_var

    @staticmethod
    def is_none(input_var):
        if input_var is None or input_var == Formatting.NONE_STRING or input_var == '':
            return True
        return False

    @staticmethod
    def wrap(open_tag, content, closing_tag=None):
        closing_tag_string = '</div>' if closing_tag is None else closing_tag
        return open_tag + content + closing_tag_string

    @staticmethod
    def div(content, class_name=None, id_name=None):
        open_tag = '<div'
        if id_name is not None:
            open_tag += ' id="{}"'.format(id_name)
        if class_name is not None:
            open_tag += ' class="{}">'.format(class_name)
        return HTMLComponents.wrap(open_tag, content)

    @staticmethod
    def modal(modal_id, title_html, body_html):
        modal_html = HTMLComponents.HTML.get('modal')
        title = HTMLComponents.wrap(modal_html.get('title'), title_html, '</h5>')
        close_button = modal_html.get('close_button')
        header = HTMLComponents.wrap(modal_html.get('header'), title + close_button)
        body = HTMLComponents.wrap(modal_html.get('body'), body_html)
        content = HTMLComponents.wrap(modal_html.get('content'), (header + body))
        dialog = HTMLComponents.wrap(modal_html.get('dialog'), content)
        return HTMLComponents.wrap(modal_html.get('modal').format(modal_id=modal_id), dialog)

    @staticmethod
    def input(input_id=None, input_type=None, classes=None, placeholder=None, readonly=False, value=None):
        input_html = HTMLComponents.HTML.get('input')
        input_div = input_html.get('input').format(
            input_id=HTMLComponents.null(input_id),
            input_type=HTMLComponents.null(input_type),
            placeholder=HTMLComponents.null(placeholder),
            classes=HTMLComponents.null(classes),
            value=HTMLComponents.null(value),
            readonly='readonly' if readonly else ''
        )
        return HTMLComponents.div(input_div, class_name='form-group')

    @staticmethod
    def textarea(input_id=None, classes=None, placeholder=None, content=None):
        input_html = HTMLComponents.HTML.get('input')
        textarea_div = input_html.get('textarea').format(
            textarea_id=HTMLComponents.null(input_id),
            placeholder=HTMLComponents.null(placeholder),
            classes=HTMLComponents.null(classes),
            content=HTMLComponents.null(content)
        )
        return HTMLComponents.div(textarea_div, class_name='form-group')

    @staticmethod
    def date(input_id=None, classes=None, value=None, max_today=True):
        input_html = HTMLComponents.HTML.get('input')
        # TODO if is none, tick no date checkbox, date readonly, value = today
        # TODO if is not none, clear no date checkbox, date write
        # Maybe? Could sort this somewhere else.
        today = Formatting.datetime_to_string(datetime.datetime.now(), format_string=Formatting.DATETIME_JS_FORMAT)
        readonly = False
        if HTMLComponents.is_none(value):
            # readonly = True
            value = today

        date_div = input_html.get('date').format(
            date_id=HTMLComponents.null(input_id),
            classes=HTMLComponents.null(classes),
            value=value,
            readonly='readonly' if readonly else '',
            max='max=' + today if max_today else ''
        )
        return HTMLComponents.div(date_div, class_name='form-group')

    @staticmethod
    def button(content, classes=None, onclick=None, data_dismiss=None):
        html = HTMLComponents.HTML.get('input')
        button_html = html.get('button').format(
            classes=HTMLComponents.null(classes),
            on_click=HTMLComponents.null(onclick),
            content=content,
            data_dismiss='' if data_dismiss is None else data_dismiss
        )
        return HTMLComponents.div(button_html, class_name='form-group')

    @staticmethod
    def alert(alert_id, content, alert_type='danger'):
        return HTMLComponents.HTML.get('alert').format(alert_id=alert_id, content=content, alert_type=alert_type)


class HTMLModals:

    INJECTION_DIV_ID = 'injectedModal'
    ALERT_INJECTION_ID = 'injectAlert'
    SUCCESS_INJECTION_ID = 'injectSuccess'

    def __init__(self, display_text_mapping_path):

        self.mapping = Mapping(display_text_mapping_path)

    def _add_button(self, edit_type, row_id):
        return HTMLComponents.button('Add', classes='btn btn-primary btn-sm form-control',
                                     onclick='addSubmit(\'{}\', \'{}\')'.format(edit_type, row_id))

    def _save_delete_buttons(self, edit_type, row_id):
        save = HTMLComponents.button('Save', classes='btn btn-primary btn-sm form-control',
                                     onclick='editSubmit(\'{}\', \'{}\')'.format(edit_type, row_id))
        # Only some data can be deleted.
        delete = '' if edit_type not in Component.CAN_DELETE else HTMLComponents.button(
            'Delete {}'.format(self.mapping.get_display_text(edit_type, Key.TITLE)),
            classes='btn btn-outline-danger btn-sm form-control',
            onclick='requestDeleteModal(\'{}\', \'{}\')'.format(edit_type, row_id)
        )
        return save + delete

    def _edit_form(self, edit_type, row_id, user_data=None):

        def get_current_row():
            if user_data is not None:
                data_rows = user_data if edit_type == Component.USER else user_data.get(edit_type)
                data_rows = data_rows if isinstance(data_rows, list) else [data_rows]
                for row in data_rows:
                    if row.get(Schema.ID) == row_id:
                        return row
            return {}

        # Get data.
        current_data = get_current_row()
        dao = Mapping.DAOS.get(edit_type)

        # Generate HTML.
        form_parts = [
            HTMLComponents.alert(self.ALERT_INJECTION_ID, '', alert_type='warning'),
            HTMLComponents.alert(self.SUCCESS_INJECTION_ID, '', alert_type='success')
        ]

        for key in Key.TO_DISPLAY:
            if key in dao.SCHEMA:
                form_parts.append('<h5 class="">{}</h5>'.format(self.mapping.get_display_text(edit_type, key)))
                current_value = current_data.get(key) if current_data else ''
                if key in [Key.START, Key.END]:
                    form_parts.append(HTMLComponents.date(key, 'form-control', value=current_value, max_today=True))
                elif key == Key.TEXT:
                    form_parts.append(HTMLComponents.textarea(key, 'form-control', content=current_value))
                else:
                    form_parts.append(HTMLComponents.input(key, 'text', 'form-control', value=current_value))

        # If user data is provided the data already exists and is being modified so show the save/delete buttons.
        # If no user data is provided, we are adding a new row so show add button.
        if user_data is not None:
            form_parts.append(self._save_delete_buttons(edit_type, row_id))
        else:
            form_parts.append(self._add_button(edit_type, row_id))

        form_html = HTMLComponents.HTML.get('input').get('form').format(classes='p-1 m-0"')
        return HTMLComponents.wrap(form_html, ''.join(form_parts))

    def share_modal(self, base_url, user_id):
        # Generate user link.
        link = 'http://' + base_url + '?id=' + user_id

        # Generate HTML.
        html = HTMLComponents.HTML.get('input')
        form_parts = [
            '<h5 class="">Direct Link</h5>',
            # TODO warn if user is hidden from other users.
            HTMLComponents.alert('copyToClipboardAlertContainer', 'Copied link to clipboard!', alert_type='info'),
            HTMLComponents.input('shareText', 'text', 'form-control', value=link, readonly=True),
            HTMLComponents.button('Copy to Clipboard!', classes='btn btn-primary btn-sm form-control',
                                  onclick='copyToClipboard()'),
        ]
        form_html = html.get('form').format(classes='p-1 m-0"')
        form = HTMLComponents.wrap(form_html, ''.join(form_parts))
        return HTMLComponents.modal(HTMLModals.INJECTION_DIV_ID, 'Share', form)

    def login_modal(self):
        # TODO Should use same keys and mapping as add and edit do.
        # Generate HTML.
        html = HTMLComponents.HTML.get('input')
        form_parts = [
            HTMLComponents.alert(HTMLModals.ALERT_INJECTION_ID, '', alert_type='warning'),
            HTMLComponents.input('loginEmail', 'text', 'form-control', placeholder='Email'),
            HTMLComponents.input('loginPassword', 'password', 'form-control', placeholder='Password'),
            HTMLComponents.button('Login', classes='btn btn-primary btn-sm form-control', onclick='loginSubmit()'),
        ]
        form_html = html.get('form').format(classes='p-1 m-0"')
        form = HTMLComponents.wrap(form_html, ''.join(form_parts))
        return HTMLComponents.modal(HTMLModals.INJECTION_DIV_ID, 'Login', form)

    def signup_modal(self):
        # TODO Should use same keys and mapping as add and edit do.
        # Generate HTML.
        html = HTMLComponents.HTML.get('input')
        form_parts = [
            HTMLComponents.alert(HTMLModals.ALERT_INJECTION_ID, '', alert_type='warning'),
            HTMLComponents.alert(HTMLModals.SUCCESS_INJECTION_ID, '', alert_type='success'),
            HTMLComponents.input('signUpDisplayName', 'text', 'form-control', placeholder='Display Name'),
            HTMLComponents.input('signUpHeadline', 'text', 'form-control', placeholder='Headline'),
            '<hr>',
            HTMLComponents.input('signUpEmail', 'text', 'form-control', placeholder='Email'),
            HTMLComponents.input('signUpPassword', 'password', 'form-control', placeholder='Password'),
            HTMLComponents.input('signUpVerifyPassword', 'password', 'form-control', placeholder='Confirm Password'),
            HTMLComponents.button('Sign Up', classes='btn btn-primary btn-sm form-control', onclick='signUpSubmit()'),
        ]
        form_html = html.get('form').format(classes='p-1 m-0"')
        form = HTMLComponents.wrap(form_html, ''.join(form_parts))
        return HTMLComponents.modal(HTMLModals.INJECTION_DIV_ID, 'Sign Up', form)

    def manage_modal(self, user_data):
        # Generate HTML.
        html = HTMLComponents.HTML.get('input')
        form_parts = [
            # TODO Look at that is-valid function in boostrap for validation prompts to user.
            HTMLComponents.alert(HTMLModals.ALERT_INJECTION_ID, '', alert_type='warning'),
            HTMLComponents.alert(HTMLModals.SUCCESS_INJECTION_ID, '', alert_type='success'),
            '<h5 class="">Email</h5>',
            HTMLComponents.input(Schema.EMAIL, 'text', 'form-control', value=user_data[Schema.EMAIL]),

            HTMLComponents.button('Save', classes='btn btn-primary btn-sm form-control',
                                  onclick='editEmail()'),
            '<hr>',
            '<h5 class="">Change Password</h5>',
            HTMLComponents.input('password', 'password', 'form-control', placeholder='New Password'),
            HTMLComponents.input('password_check', 'password', 'form-control', placeholder='Confirm New Password'),
            HTMLComponents.button('Change', classes='btn btn-primary btn-sm form-control', onclick='submitPasswordChange()'),
            '<hr>',
            '<h5 class="">Close Account</h5>',
            HTMLComponents.button('Close and Delete All Data', classes='btn btn-outline-danger btn-sm form-control',
                                  onclick='requestDeleteModal(\'{}\', \'{}\')'.format(Component.USER,
                                                                                      user_data[Schema.ID]))
        ]
        form_html = html.get('form').format(classes='p-1 m-0"')
        form = HTMLComponents.wrap(form_html, ''.join(form_parts))
        return HTMLComponents.modal(HTMLModals.INJECTION_DIV_ID, 'Manage', form)

    def delete_modal(self, delete_type, row_id):
        # Generate HTML.
        html = HTMLComponents.HTML.get('input')
        message = '<p>Are you sure you want to do that?</p>'
        form_parts = [
            HTMLComponents.button('No I don\'t', classes='btn btn-primary btn-sm form-control', onclick='',
                                  data_dismiss="modal"),
            HTMLComponents.button('Delete Permanently', classes='btn btn-danger btn-sm form-control',
                                  onclick='deleteSubmit(\'{}\', \'{}\')'.format(delete_type, row_id)),
        ]
        form_html = html.get('form').format(classes='p-1 m-0"')
        form = HTMLComponents.wrap(message + form_html, ''.join(form_parts))
        return HTMLComponents.modal(HTMLModals.INJECTION_DIV_ID, 'Delete', form)

    def edit_modal(self, edit_type, row_id, user_data):
        title = self.mapping.get_display_text(edit_type, Key.TITLE, default_text=False)
        modal_parts = [
            HTMLComponents.alert(self.ALERT_INJECTION_ID, '', alert_type='warning'),
            HTMLComponents.alert(self.SUCCESS_INJECTION_ID, '', alert_type='success'),
            self._edit_form(edit_type, row_id, user_data=user_data)
        ]
        return HTMLComponents.modal(HTMLModals.INJECTION_DIV_ID, 'Edit ' + (title if title else ''), ''.join(modal_parts))

    def add_modal(self, add_type, row_id):
        form = self._edit_form(add_type, row_id)
        title = self.mapping.get_display_text(add_type, Key.TITLE, default_text=False)
        return HTMLComponents.modal(HTMLModals.INJECTION_DIV_ID, 'Add ' + (title if title else ''), form)


