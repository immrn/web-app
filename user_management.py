import os
import time
import hashlib
import re
import uuid
import smtplib, ssl
import math
import pyotp
import qrcode
import datetime as dt
import pandas as pd
import streamlit as st
from enum import Enum
from email.mime.text import MIMEText
from typing import Literal
from tweaker import st_tweaker
import streamlit.components.v1 as components

import state
import util
import config
import usage_tracking as track
from constants import SessionStateKey

# TODO:
# We could use cookies to keep an user logged in at multiple tabs. https://github.com/Mohamed-512/Extra-Streamlit-Components#cookie-manager
# Also we could use the Router feature to use real URL paths instead of query params: https://github.com/Mohamed-512/Extra-Streamlit-Components#router

# Editable constants:
NAME_OF_APP = config.NAME_OF_APP  # will appear in the uri if you generate TOTPs
URL_BASE = config.URL_BASE  # base link of your web app
PATH_TO_USER_DB_CSV = config.PATH_TO_USER_DB_CSV  # where you store your users authentication information
SMTP_SERVER = config.SMTP_SERVER  # smtp server of sender email adress
SENDER_EMAIL = config.SENDER_EMAIL_ADDRESS  # from where registration mails will be sent
PATH_TO_EMAIL_PW_FILE = config.PATH_TO_EMAIL_PW_FILE  # file containing the password of sender email address, gitignore this file!
# TIMEOUT of registration link after registration process started. Your users should get at least 10 min to click on the link in their registration email.
# But you should not keep the timeout value too big. Attackers could block emails by walking through registration processes.
REGISTRATION_TIMEOUT = dt.timedelta(minutes=30)
REGISTRATION_TIMEOUT_STRING = "30 Minuten"   # timeout as string for the email
RESET_PW_TIMEOUT = dt.timedelta(minutes=15)
RESET_PW_TIMEOUT_STRING = "15 Minuten"  # timeout as string for the email
INVALID_USERNAME_SYMBOLS = ["@"]  # keep the "@" in this list!
FORCE_TOTP_SETUP = True  # if True users have to setup totp once after logging in
PW_MIN_LENGTH = 8


# Constants: do not change!
Key = SessionStateKey.Common
FLUSH = "flush"
TOTP = "totp"
SETUP_TOTP = "setup_totp"
FINISH_TOTP_SETUP = "finish_totp_setup"
REGISTRATION = "registration"
REGISTRATION_MAIL_SENT = "registration_mail_sent"
RESET_PW = "reset_pw"
RESET_PW_MAIL_SENT = "reset_pw_mail_sent"
FINISH_RESET_PW = "finish_reset_pw"
LOGGED_IN = "logged_in"


def checkFiles():
    exit_app = False
    # DB file user_info.csv:
    if not os.path.exists(Users.csv_path):
        props = [attr for attr in dir(Users.Col) if not callable(getattr(Users.Col, attr)) and not attr.startswith("__")]
        f = open(Users.csv_path, "w")
        f.write(",".join(props))
        f.close()
    # gmail pw:
    if not os.path.exists(PATH_TO_EMAIL_PW_FILE):
        st.error("gmail_pw.txt file doesn't exist!")
        exit_app = True

    exit(1) if exit_app else None


class Users:
    csv_path = PATH_TO_USER_DB_CSV
    email_bg_color = config.COLOR_BACKGROUND
    email_primary_color = config.COLOR_PRIMARY

    class Col:
        id = "id"
        name = "name"
        email = "email"
        salt = "salt"
        hashed_pw = "hashed_pw"
        secret = "secret"
        reg_uuid = "reg_uuid"
        reg_timeout_utc = "reg_timeout_utc"
        reset_pw_uuid = "reset_pw_uuid"
        reset_pw_timeout_utc = "reset_pw_timeout_utc"

    @staticmethod
    def isNameAvailable(name: str):
        user = Users.get_user_by("name", name)
        if user == {}:
            return True
        return False
    
    @staticmethod
    def isNameValid(name: str):
        if any(s in name for s in INVALID_USERNAME_SYMBOLS):
            return False
        return True

    @staticmethod
    def isEmailAvailable(email: str):
        user = Users.get_user_by("email", email)
        if user == {}:
            return True
        return False

    @staticmethod
    def isEmailValid(email: str):
        if email.count("@") > 1:
            return False
        pattern = "^\S+@\S+\.\S+$"
        objs = re.search(pattern, email)
        try:
            if objs.string == email:
                return True
        except:
            return False

    @staticmethod
    def register_user(name: str, email: str, pw: str) -> str:
        """!
        Add a new user to your database. User's ID and other properties will be set automatically.
        A parameter (or you better say its value) is unique, when there is no user which stores the value already.
        For example: two users can't have the same email address
        @param name: name, must be unique, check it with Users.isNameVaild() and Users.isNameAvailable()
        @param email: email address, must be unique, check it with Users.isEmailVaild() and Users.isEmailAvailable()
        @param pw: password, plain text
        @return: uuid used to complete the registration process, use it as input for Users.sent_registration_email()
        """
        if not Users.isNameAvailable(name) or \
            not Users.isNameValid(name) or \
            not Users.isEmailAvailable(email) or \
            not Users.isEmailValid(email):
            raise ValueError(
                "User name or email is already used. You should check \
                if these params already exist in your user database before \
                calling this function."
            )

        reg_uuid = str(uuid.uuid4())
        salt = os.urandom(16).hex()
        secret = "-"
        df = Users.df()
        df = df.sort_index()
        highest_id = -1 if df.empty else df.index[-1]
        timeout = (dt.datetime.utcnow() + REGISTRATION_TIMEOUT).replace(microsecond=0)

        new_user = {
            Users.Col.id: highest_id + 1,
            Users.Col.name: name,
            Users.Col.email: email,
            Users.Col.salt: salt,
            Users.Col.hashed_pw: Users.hash_pw(pw, salt),
            Users.Col.secret: secret,
            Users.Col.reg_uuid: reg_uuid,
            Users.Col.reg_timeout_utc: timeout,
        }
        new_user = pd.DataFrame(data=[new_user])
        new_user = new_user.set_index(Users.Col.id)
        
        df = pd.concat([df, new_user], ignore_index=True)
        df.index.name = Users.Col.id
        df.to_csv(Users.csv_path)
        return reg_uuid

    @staticmethod
    def hash_pw(pw: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=pw.encode('UTF-8'),
            salt=bytes.fromhex(salt),
            iterations=700_000
        ).hex()

    @staticmethod
    def reset_pw(user_id: int, new_pw: str):
        salt = os.urandom(16).hex()
        hashed_pw = Users.hash_pw(new_pw, salt)
        df = Users.df()
        df.at[user_id, Users.Col.hashed_pw] = hashed_pw
        df.at[user_id, Users.Col.salt] = salt
        df.to_csv(Users.csv_path)

    @staticmethod
    def set_reset_pw_uuid(user_id: int):
        reset_pw_uuid = str(uuid.uuid4())
        timeout = (dt.datetime.utcnow() + RESET_PW_TIMEOUT).replace(microsecond=0)

        df = Users.df()
        df.at[user_id, Users.Col.reset_pw_uuid] = reset_pw_uuid
        df.at[user_id, Users.Col.reset_pw_timeout_utc] = timeout
        df.to_csv(Users.csv_path)

        return reset_pw_uuid

    @staticmethod
    def generate_totp_secret_uri(user_id: int) -> (str, str):
        """!
        Returns the otpauth uri which you can use too show a QR-Code to setup TOTP.
        The secret (base32) will be returned too.
        Returns Tuple(False, Flase) if the user already has setup a secret.
        @return: Tuple(uri: str, secret: str), both False if user owns a secret
        """
        user = Users.get_user_by("id", user_id)
        email = user[Users.Col.email]
        if user[Users.Col.secret] != "-":
            # user already owns a secret
            return False, False
        secret = pyotp.random_base32()
        # https://github.com/google/google-authenticator/wiki/Key-Uri-Format
        uri = f"otpauth://totp/{NAME_OF_APP}:{email}?" + \
            f"secret={secret}&" + \
            f"issuer={NAME_OF_APP}&" + \
            f"algorithm=SHA1&" + \
            f"digits=6&" + \
            f"period=30"

        return uri, secret

    @staticmethod
    def set_totp_secret_of_user(user_id: int, secret: str):
        df = Users.df()
        df.at[user_id, Users.Col.secret] = secret
        df.to_csv(Users.csv_path)

    @staticmethod
    def check_totp(user_id: int, totp: str, secret=None) -> bool:
        """!
        Check if totp is valid for the current time step and one time step in the past as well as one step in the future.
        @param totp: the totp input by user
        @param secret: only use at totp setup, because at this time user owns no secret
        @return: True if the totp is vaild
        """
        # https://github.com/pyauth/pyotp
        if not secret:
            secret = Users.get_user_by("id", user_id)[Users.Col.secret]
        hotp = pyotp.HOTP(secret)
        time_counter = math.floor(time.time() / 30)  # unix time
        valid_totp_list = [hotp.at(time_counter - 1), hotp.at(time_counter), hotp.at(time_counter + 1)]
        if totp in valid_totp_list:
            return True
        return False

    @staticmethod
    def df() -> pd.DataFrame:
        df = pd.read_csv(Users.csv_path, sep=',')
        # int:
        df[Users.Col.id] = df[Users.Col.id].astype(int)
        # string:
        str_type_columns = [Users.Col.name, Users.Col.email, Users.Col.salt,
                            Users.Col.hashed_pw, Users.Col.secret, Users.Col.reg_uuid]
        df[str_type_columns] = df[str_type_columns].astype(str)
        # datetime:
        df[Users.Col.reg_timeout_utc] = pd.to_datetime(df[Users.Col.reg_timeout_utc])
        df = df.set_index(Users.Col.id)
        return df
    
    @staticmethod
    def get_user_by(property: Literal["id", "name", "email", "reg_uuid", "reset_pw_uuid"], value) -> dict():
        """!
        Returns a single user. All possible properties are unique properties. So only one user exists for the value you enter.
        @param property: unique property of a user
        @param value: value of property to identify a user
        @return: dict() containing all properties of an user, empty dict() if user doesn't exist
        """
        df = Users.df()
        if property == "id":
            try:
                value = int(value)
            except TypeError:
                raise TypeError("When parameter 'property' is 'id', value must be an integer!")
            user = df[df.index == value]
        elif property in ["name", "email", "reg_uuid", "reset_pw_uuid"]:  # strings
            if property == "name":
                col = Users.Col.name
            elif property == "email":
                col = Users.Col.email
            elif property == "reg_uuid":
                col = Users.Col.reg_uuid
            elif property == "reset_pw_uuid":
                col = Users.Col.reset_pw_uuid
            try:
                value = str(value)
            except TypeError:
                raise TypeError(f"When parameter 'property' is {property}, value must be a string!")
            user = df[df[col] == value]
        else:
            raise ValueError(f"'{property}' is not a valid literal for parameter 'property'!")
        
        if not user.empty:
            user = user.reset_index()
            return user.iloc[0].to_dict()
        
        return dict()

    @staticmethod
    def rm_user(user_id: int):
        df = Users.df()
        df = df.drop(user_id)
        df.to_csv(Users.csv_path)

    @staticmethod
    def rm_all_users_with_expired_registration_link():
        df = Users.df()
        df = df.loc[~((df[Users.Col.reg_uuid] != "-") & (df[Users.Col.reg_timeout_utc] <= dt.datetime.utcnow()))]
        df.to_csv(Users.csv_path)

    @staticmethod
    def _send_email_(email: str, subject: str, html: str):
        port = 465  # SSL
        with open(PATH_TO_EMAIL_PW_FILE) as file:
            password = file.readline()
        smtp_server = SMTP_SERVER
        sender_email = SENDER_EMAIL
        receiver_email = email

        msg = MIMEText(html, 'html')
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        ret = {}
        raised_error = None

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            try:
                ret = server.sendmail(sender_email, receiver_email, msg.as_string())
            except (smtplib.SMTPHeloError, smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused, smtplib.SMTPNotSupportedError) as e:
                raised_error = e
        return ret, raised_error

    @staticmethod
    def send_registration_email(email: str, reg_uuid: str):
        # Design html mails easy with https://tabular.email/demo/blank
        
        reg_url = URL_BASE + "?register=" + reg_uuid

        with open("registration_mail.html") as file:
            html = file.read()
        
        username = Users.get_user_by("email", email)[Users.Col.name]

        html = html.replace("{_primary_color_}", Users.email_primary_color)
        html = html.replace("{_background_color_}", Users.email_bg_color)
        html = html.replace("{username}", username)
        html = html.replace("{registration_timeout}", REGISTRATION_TIMEOUT_STRING)
        html = html.replace("{reg_url}", reg_url)
        html = html.replace("{mailto_block_mail}",
        	"mail_to:user.study.totp.authentication@gmail.com" + \
            "&amp;" + \
            "?subject=Registrierungsmails%20ohne%20Registrierung" + \
            "?body=Ich%20erhalte%20mehrfach%20Registrierungsmails,%20" + \
                "obwohl%20ich%20mich%20nicht%20registriert%20habe.<br>" + \
                "Mit%20dieser%20Mail%20beantrage%20ich%20keine%20Mails%20mehr" + \
                "%20zu%20erhalten!"
        )

        return Users._send_email_(
            email=email,
            subject="Registrierung für die Nutzerstudie zur TOTP Authentication",
            html=html)

    @staticmethod
    def send_reset_pw_email(email: str, reset_pw_uuid: str):
        # TODO NEXT UI bauen und dann testen
        # Design html mails easy with https://tabular.email/demo/blank
        reset_pw_url = URL_BASE + "?reset_pw=" + reset_pw_uuid

        with open("reset_pw_mail.html") as file:
            html = file.read()

        username = Users.get_user_by("email", email)[Users.Col.name]

        html = html.replace("{_primary_color_}", Users.email_primary_color)
        html = html.replace("{_background_color_}", Users.email_bg_color)
        html = html.replace("{username}", username)
        html = html.replace("{reset_pw_timeout}", RESET_PW_TIMEOUT_STRING)
        html = html.replace("{reset_pw_url}", reset_pw_url)
        html = html.replace("{mailto_block_mail}",
        	"mail_to:user.study.totp.authentication@gmail.com" + \
            "&amp;" + \
            "?subject=Ich%20erhalte%20vermehrt%20Zurücksetzungsmails" + \
            "?body=Ich%20erhalte%20mehrfach%20Emails,%20die%20behaupten%20ich%20wöllte%20mein%20Passwort%20ändern,%20" + \
                "obwohl%20ich%20dies%20nicht%20beantragt%20habe.<br>" + \
                "Mit%20dieser%20Mail%20beantrage%20ich,%20keine%20weiteren%20Emails%20diesbezüglich%20" + \
                "%20zu%20erhalten!"
        )

        # mailto:name@bla.de?subject=Das ist ein Betreff
        subject="Passwort zurücksetzen - Nutzerstudie zur TOTP Authentication"
        return Users._send_email_(
            email=email,
            subject=subject,
            html=html)

    @staticmethod
    def check_expiration_of_uuid(property: Literal["reg_uuid", "reset_pw_uuid"] ,uuid: str) -> bool:
        """!
        Checks if the registration or reset_pw link did expire. If not expired, sets the reg_uuid or reset_pw_uuid in the database to "-" (means user did register/reset pw).
        @param property: "reg_uuid" or "reset_pw_uuid"
        @param uuid: UUID set for a user to complete their registration or reset passwort
        @return: False if the registration / reset pw link expired or there was no or more than a single matching reg_uuid / reset_pw_uuid in the table of users.
            This should never happen. True if the uuid didn't expire.
        """
        if property == "reg_uuid":
            col_uuid = Users.Col.reg_uuid
            col_timeout = Users.Col.reg_timeout_utc
        elif property == "reset_pw_uuid":
            col_uuid = Users.Col.reset_pw_uuid
            col_timeout = Users.Col.reset_pw_timeout_utc
        else:
            raise ValueError(f"Param 'property' = {property} must have the value 'reg_uuid' or 'reset_pw_uuid'.")
        
        df = Users.df()
        if (property == "reg_uuid" and uuid == "-") or df[col_uuid].loc[df[col_uuid] == uuid].shape[0] != 1:
            return False
        
        user = Users.get_user_by(col_uuid, uuid)
        user_id = user[Users.Col.id]
        print("\n---------\n")
        print(user)
        print(user[col_timeout])

        if property == "reg_uuid" and dt.datetime.utcnow() > user[col_timeout]:
            # registration link expired --> delete this user:
            Users.rm_user(user_id)
            return False
        
        elif property == "reset_pw_uuid" and dt.datetime.utcnow() > dt.datetime.fromisoformat(user[col_timeout]):
            df.at[user_id, col_uuid] = "-"
            return False
        
        df.at[user_id, col_uuid] = "-"

        df.to_csv(Users.csv_path)
        return True

    @staticmethod
    def did_user_finish_registration(user_id: int):
        reg_uuid = Users.get_user_by("id", user_id)[Users.Col.reg_uuid]
        return True if reg_uuid == "-" else False

    class RetCheckLogin(Enum):
        valid = 1
        invalid_pw = 2
        user_not_found = 3
        missing_username_or_email = 4
        missing_pw = 5
        not_fully_registered = 6

    @staticmethod
    def check_login(username_or_email: str, pw: str) -> RetCheckLogin:
        if not username_or_email:
            return Users.RetCheckLogin.missing_username_or_email
        if not pw:
            return Users.RetCheckLogin.missing_pw
        
        Users.rm_all_users_with_expired_registration_link()

        if "@" in username_or_email:  # we've got an email here, not an username
            property = "email"
            if Users.isEmailAvailable(username_or_email):
                return Users.RetCheckLogin.user_not_found
        else:  # we've got an username, not an email
            property = "name"
            if Users.isNameAvailable(username_or_email):
                return Users.RetCheckLogin.user_not_found
        
        user = Users.get_user_by(property, username_or_email)

        if not Users.did_user_finish_registration(user[Users.Col.id]):
            return Users.RetCheckLogin.not_fully_registered

        hashed_pw = Users.hash_pw(pw=pw, salt=user[Users.Col.salt])
        
        if user[Users.Col.hashed_pw] != hashed_pw:
            return Users.RetCheckLogin.invalid_pw
        
        return Users.RetCheckLogin.valid

def pad(lines: int):
    for i in range(lines):
        st.write("")


def pad_top():
    pad(2)


def pad_after_title():
    pad(2)


def login_view():
    # TODO block IP address after n failed login attempts for m hours.
    col1, col2 = st.columns([2,9])
    with col1:
        st.markdown("""
        <style>
        .big-font {
            font-size:90px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="big-font">🏦</div>', unsafe_allow_html=True)
    with col2:
        pad(1)
        st.title("Simuliertes Banking", False)
        st.markdown("_Simulierter Banking-Dienst einer Nutzerstudie_")
    pad(1)
    st.header("Anmelden", False)
    pad_after_title()

    if "focus_id" not in st.session_state:
        st.session_state.focus_id = 0

    ret_check_login = state.value(Key.ret_check_login)
    changed_pw = state.value(Key.changed_pw)
    changed_username_or_email = state.value(Key.changed_username_or_email)

    def username_or_email_changed():
        st.session_state[Key.changed_username_or_email] = True
        if st.session_state.focus_id >= 0:
            st.session_state.focus_id = 1

    # autocomplete: https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/autocomplete
    username_or_email = st_tweaker.text_input(
        label="Benutzername oder Email",
        id="username",
        on_change=username_or_email_changed,
        autocomplete="username")
    if ret_check_login == Users.RetCheckLogin.missing_username_or_email:
        st.warning("Benutzername eingeben.")
        st.session_state.focus_id = 0
    elif ret_check_login == Users.RetCheckLogin.user_not_found:
        st.warning("Dieser Benutzer existiert nicht.")
        st.session_state.focus_id = 0
    elif ret_check_login == Users.RetCheckLogin.not_fully_registered:
        st.info("Registrierung noch nicht abgeschlossen. Schau in dein Email-Postfach und im Spam.")

    def pw_changed():
        st.session_state[Key.changed_pw] = True
        st.session_state.focus_id = -1

    pw = st_tweaker.text_input(
        label="Passwort",
        type='password',
        id="password",
        on_change=pw_changed,
        autocomplete="current-password")
    if ret_check_login == Users.RetCheckLogin.missing_pw:
        st.warning("Passwort eingeben.")
        st.session_state.focus_id = 1
    elif ret_check_login == Users.RetCheckLogin.invalid_pw:
        cols = st.columns(2)
        cols[0].warning("Passwort ungültig.")
        cols[1].write(f'<div style="text-align: right"> <a href="/?page={RESET_PW}" target="_self">Passwort vergessen?</a> </div><br>', unsafe_allow_html=True)
        st.session_state.focus_id = 1

    # this part of the code focuses input on username text input and then on password input
    components.html(
        f"""
        <div>some hidden container</div>
        <p>{st.session_state.focus_id}</p>
        <script>
            var input = window.parent.document.querySelectorAll("input[type=text],input[type=password]");
            // for (var i = 0; i < input.length; ++i) {{
            //     input[i].focus();
            // }}
            if ({st.session_state.focus_id} >= 0) {{
                input[{st.session_state.focus_id}].focus();
            }}
        </script>
        """,
        height=0,
    )

    login = st_tweaker.button(label='Anmelden', type="secondary", use_container_width=True, id="login")
    # Pressing [ENTER] will start a login attempt -> no need to click "login"-button
    login = True if changed_pw or (changed_username_or_email and pw != "") else login

    # Let new users regsiter themself:
    st.write(f'<br><div style="text-align: center"> <a href="/?page={REGISTRATION}" target="_self">Registrieren</a> </div>', unsafe_allow_html=True)

    if login:
        new_ret_check_login = Users.check_login(
            username_or_email=username_or_email,
            pw=pw
        )
        st.session_state[Key.ret_check_login] = new_ret_check_login
        
        if new_ret_check_login == Users.RetCheckLogin.valid:
            property = "email" if "@" in username_or_email else "name"
            user = Users.get_user_by(property, username_or_email)

            if FORCE_TOTP_SETUP and user[Users.Col.secret] == "-":
                st.session_state[Key.state] = SETUP_TOTP
            elif user[Users.Col.secret] != "-":
                st.session_state[Key.state] = TOTP
            else:
                st.session_state[Key.state] = LOGGED_IN
            
            st.session_state[Key.user_id] = user[Users.Col.id]
            if state.value(Key.state) == LOGGED_IN:
                track.login()
            
            st.experimental_rerun()
        else:
            st.session_state[Key.changed_pw] = False
            st.session_state[Key.changed_username_or_email] = False
            st.experimental_rerun()
    
    st.session_state[Key.changed_pw] = False
    st.session_state[Key.changed_username_or_email] = False
    exit(0)


def totp_view():
    pad_top()
    st.title("Anmelden")
    pad_after_title()

    totp_input = st_tweaker.text_input(
        label="Token",
        help="Dieses Token / Einmalpasswort wird alle 30 Sekunden von einem Smartphone generiert.",
        id="totp",
        autocomplete="one-time-code"
    )

    if totp_input:
        if Users.check_totp(
                user_id=state.value(Key.user_id),
                totp=totp_input):
            track.login()
            st.session_state[Key.state] = LOGGED_IN
            st.experimental_rerun()
        else:
            st.warning("TOTP ungültig")

    exit(0)


def setup_totp_view():
    st.title("Einrichten der Zwei-Faktor-Authentisierung", anchor=False)
    pad_after_title()

    cols = st.columns(2)
    user_id = state.value(Key.user_id)

    if Key.curr_totp_uri_and_secret not in st.session_state:
        uri, secret = Users.generate_totp_secret_uri(user_id)
        st.session_state[Key.curr_totp_uri_and_secret] = uri, secret
    else:
        uri, secret = st.session_state[Key.curr_totp_uri_and_secret]
    
    print("uri:", uri)
    print("secret:", secret)
    

    if not uri:
        st.write("Du hast die Einrichtung der Zwei-Faktor-Authentisierung bereits durchgeführt.")
        exit(0)

    # Step 1: scan qr code
    cols[0].header("1. QR-Code scannen")
    cols[0].write("Scanne folgenden Code mit deinem Smartphone. Wahrscheinlich benötigst Du eine One-time Password (OTP) App.")
    # TODO eigene TOTP App hier verlinken, wenn im Android store?

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color=config.COLOR_SECONDARY)

    file_name = f"tmp_qr_code_{str(uuid.uuid4())}.png"
    img.save(file_name)
    cols[1].image(file_name, use_column_width=True)
    os.remove(file_name)

    # Step 2: check totp
    cols = st.columns(2)
    cols[0].write("")
    cols[0].header("2. Prüfen")
    cols[0].write("Gib das TOTP an, welches die App generiert hat.")

    cols[1].write("")
    cols[1].write("")
    cols[1].write("")
    totp_input = cols[1].text_input(label="TOTP (6-stellige Zahl)")

    if totp_input:
        if Users.check_totp(
                user_id=user_id,
                totp=totp_input,
                secret=secret):
            Users.set_totp_secret_of_user(user_id, secret)
            st.session_state[Key.state] = LOGGED_IN
            cols[1].success("TOTP bestätigt!")
            time.sleep(1.5)
            st.experimental_rerun()
        else:
            cols[1].warning("TOTP ungültig")

    
    exit(0)


def finish_totp_setup_view():
    pad_top()
    st.subheader("Zwei-Faktor-Authentisierung wurde eingerichtet! :white_check_mark:", anchor=False)
    time.sleep(2)
    st.session_state[Key.state] = LOGGED_IN
    st.experimental_rerun()


def initiate_reset_pw_view():
    pad_top()
    st.title("Passwort zurücksetzen")
    pad_after_title()
    
    allow_reset = True
    username_or_email = st.text_input(
        label="Benutzername oder Email"
    )

    if username_or_email != "":
        if "@" in username_or_email:
            if Users.isEmailAvailable(username_or_email):
                st.warning("Es existiert kein Benutzer mit dieser Email.")
                allow_reset = False
        else:
            if Users.isNameAvailable(username_or_email):
                st.warning("Dieser Benutzer existiert nicht.")
                allow_reset = False
    
    st.write("")
    reset = st.button('Passwort zurücksetzen', use_container_width=True)

    if reset and username_or_email != "" and allow_reset:
        user = Users.get_user_by("email", username_or_email) if "@" in username_or_email else Users.get_user_by("name", username_or_email)
        
        util.center_spinner()
        with st.spinner(""):
            reset_pw_uuid = Users.set_reset_pw_uuid(user[Users.Col.id])
            ret, raised_error = Users.send_reset_pw_email(user[Users.Col.email], reset_pw_uuid=reset_pw_uuid)
            if ret != {} or raised_error:
                # TODO better error handling and user anweisungen
                st.error("Beim Senden der Email zum Zurücksetzen des Passworts ist etwas fehlgeschlagen.")
                st.stop()
            else:
                st.session_state[Key.user_id] = user[Users.Col.id]
                st.session_state[Key.state] = RESET_PW_MAIL_SENT
                st.experimental_rerun()

    exit(0)


def reset_pw_mail_sent_view(user_id: int):
    pad_top()
    
    pad_after_title()
    email = Users.get_user_by("id", user_id)[Users.Col.email]
    st.subheader(f"Es wurde eine Email an {email} gesendet. Befolge die darin befindlichen Anweisungen. Schau auch im Spam-Ordner.", anchor=False)
    exit(0)


def reset_pw_view(reset_pw_uuid: str):
    pad_top()
    reset_pw_allowed = Users.check_expiration_of_uuid(property="reset_pw_uuid", uuid=reset_pw_uuid)
    
    allow_pw_reset = True

    if reset_pw_allowed:
        st.title("Passwort zurücksetzen", anchor=False)
        pad_after_title()

        new_pw = st.text_input(label="Neues Passwort", type="password")
        if new_pw != "" and len(new_pw) < PW_MIN_LENGTH:
            st.warning(f"Passwort muss mindestens {PW_MIN_LENGTH} Zeichen enthalten")
            allow_pw_reset = False

        new_pw_repeated = st.text_input(label="Neues Passwort wiederholen", type="password")
        if "" not in [new_pw, new_pw_repeated] and new_pw != new_pw_repeated:
            st.warning("Wiederholtes Passwort muss übereinstimmen")
            allow_pw_reset = False

        confirm = st.button(label="Bestätigen", use_container_width=True)

        if confirm and allow_pw_reset:
            user = Users.get_user_by(property="reset_pw_uuid", value=reset_pw_uuid)
            Users.reset_pw(user_id=user[Users.Col.id], new_pw=new_pw)
            st.session_state[Key.state] = FINISH_RESET_PW
    else:
        st.title("Dieser Link ist leider abgelaufen.")
        # Offer to repeat registration:
        st.write(f'Du kannst dein Passwort <a href="/?page={RESET_PW}" target="_self">erneut zurücksetzen</a>.', unsafe_allow_html=True)
    
    exit(0)


def finish_reset_pw_view():
    pad_top()
    
    st.title("Passwort zurücksetzen", anchor=False)
    pad_after_title()
    st.write("Du hast dein Passwort erfolgreich zurückgesetzt.")
    st.write(f'<a href="/" target="_self">Zur Anmeldung</a>', unsafe_allow_html=True)

    exit(0)


def registration_view():
    pad_top()
    st.title("Registrieren")
    pad_after_title()

    allow_register = True

    email = st.text_input(label="Email", placeholder="you@example.com")
    if email != "":
        if not Users.isEmailValid(email):
            st.warning("Geben Sie eine gültige Email ein.")
            allow_register = False
        if not Users.isEmailAvailable(email):
            st.warning("Diese Email ist bereits vergeben.")
            allow_register = False
    
    username = st.text_input(label="Benutzername")
    if username != "":
        if not Users.isNameAvailable(username):
            st.warning("Name bereits vergeben")
            allow_register = False
        if not Users.isNameValid(username):
            st.warning(f"Der Name enthält eines der ungültigen Zeichen: {','.join(INVALID_USERNAME_SYMBOLS)}")
            allow_register = False

    pw = st.text_input(label="Passwort", placeholder="mindestens 8 Zeichen", type='password')
    if pw != "" and len(pw) < PW_MIN_LENGTH:
        st.warning(f"Passwort muss mindestens {PW_MIN_LENGTH} Zeichen enthalten")
        allow_register = False
    pw_repeated = st.text_input(label="Passwort (wiederholen)", type='password')
    if "" not in [pw_repeated, pw] and pw_repeated != pw:
            st.warning("Wiederholtes Passwort muss übereinstimmen")
            allow_register = False

    register = st.button('Registrieren', use_container_width=True)

    if register and allow_register:
        if "" in [email, username, pw, pw_repeated]:
            st.warning("Füllen Sie jedes Feld aus.")
            exit(0)

        util.center_spinner()  
        with st.spinner(""):
            reg_uuid = Users.register_user(name=username, email=email, pw=pw)
            ret, raised_error = Users.send_registration_email(email, reg_uuid=reg_uuid)
            if ret != {} or raised_error:
                # TODO better error handling and user anweisungen
                st.error("Beim Senden der Registrierungs-Email ist etwas fehlgeschlagen.")
                st.write(f"ret:\n{ret}\n\nraised_error:\n{raised_error}")
                st.stop()

        st.session_state[Key.state] = REGISTRATION_MAIL_SENT
        user_id = Users.get_user_by("name", username)[Users.Col.id]
        st.session_state[Key.user_id] = user_id
        st.experimental_rerun()

    exit(0)


def registration_mail_sent_view():
    pad_top()
    st.title("Fast geschafft!:rocket:", anchor=False)
    pad_after_title()
    user_id = state.value(Key.user_id)
    email = Users.get_user_by("id", user_id)[Users.Col.email]
    st.subheader(f"Dir wurde eine Email an {email} gesendet, um die Registierung abzuschließen. Schau auch im Spam-Ordner nach.", anchor=False)
    exit(0)


def finish_registration_view(reg_uuid: str):
    pad_top()
    registration_finished = Users.check_expiration_of_uuid(property="reg_uuid", uuid=reg_uuid)

    if registration_finished:
        st.title("Registrierung abgeschlossen", anchor=False)
        pad_after_title()
        st.write("Du hast dich erfolgreich registriert.")
        st.write(f'<a href="/" target="_self">Zur Anmeldung</a>', unsafe_allow_html=True)
    else:
        st.title("Dein Link zur Registrierung ist abgelaufen.", anchor=False)
        pad_after_title()
        # Offer to repeat registration:
        st.write(f'Registriere dich <a href="/?page={REGISTRATION}" target="_self">hier</a> erneut.', unsafe_allow_html=True)
    exit(0)
