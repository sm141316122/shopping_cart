from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email


class LoginForm(FlaskForm):
    email = EmailField("Email", render_kw={"placeholder": "請輸入電子郵件"}, validators=[DataRequired()])
    password = PasswordField("Password", render_kw={"placeholder": "請輸入密碼"}, validators=[DataRequired()])
    submit = SubmitField("登入")


class RegisterForm(FlaskForm):
    email = EmailField("Email", render_kw={"placeholder": "請輸入電子郵件"}, validators=[DataRequired()])
    password = PasswordField("Password", render_kw={"placeholder": "請輸入密碼"}, validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", render_kw={"placeholder": "確認密碼"}, validators=[DataRequired()])
    submit = SubmitField("註冊")
