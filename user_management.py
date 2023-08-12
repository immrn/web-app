import streamlit as st
import os
from enum import Enum
import time
from tweaker import st_tweaker
import hashlib
import pandas as pd
from typing import Literal
import re
import uuid
import smtplib, ssl
from email.mime.text import MIMEText
import datetime as dt

from constants import SessionStateKey
import state
import config

# TODO:
# We could use cookies to keep an user logged in at multiple tabs. https://github.com/Mohamed-512/Extra-Streamlit-Components#cookie-manager
# Also we could use the Router feature to use real URL paths instead of query params: https://github.com/Mohamed-512/Extra-Streamlit-Components#router

# Editable constants:
URL_BASE = config.URL_BASE  # base link of your web app
PATH_TO_USER_DB_CSV = "user_info.csv"  # where you store your users authentication information
SMTP_SERVER = config.SMTP_SERVER  # smtp server of sender email adress
SENDER_EMAIL = config.SENDER_EMAIL_ADDRESS  # from where registration mails will be sent
SENDER_EMAIL_PW_FILE = "gmail_pw.txt"  # file containing the password of sender email address, gitignore this file!
# TIMEOUT of registration link after registration process started. Your users should get at least 10 min to click on the link in their registration email.
# But you should not keep the timeout value too big. Attackers could block emails by walking through registration processes.
REGISTRATION_TIMEOUT = dt.timedelta(minutes=30)
REGISTRATION_TIMEOUT_STRING = "30 Minuten"   # timeout as string for the email
INVALID_USERNAME_SYMBOLS = ["@"]  # keep the "@" in this list!


# Constants: do not change!
Key = SessionStateKey.Common
FLUSH = "flush"
TOTP = "totp"
REGISTRATION = "registration"
RESET_PW = "reset_pw"
REGISTRATION_MAIL_SENT = "registration_mail_sent"
LOGGED_IN = "logged_in"


class Users:
    csv_path = PATH_TO_USER_DB_CSV
    sender_email_pw_file = SENDER_EMAIL_PW_FILE

    class Col:
        id = "id"
        name = "name"
        email = "email"
        salt = "salt"
        hashed_pw = "hashed_pw"
        secret = "secret"
        reg_uuid = "reg_uuid"
        reg_timeout_utc = "reg_timeout_utc"

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
    def register_new(name: str, email: str, pw: str) -> str:
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
        secret = "TODO"
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
            Users.Col.reg_timeout_utc: timeout
        }
        new_user = pd.DataFrame(data=[new_user])
        new_user = new_user.set_index(Users.Col.id)
        
        df = pd.concat([df, new_user], ignore_index=True)
        df.index.name = Users.Col.id
        df.to_csv(Users.csv_path)
        return reg_uuid

    @staticmethod
    def hash_pw(pw, salt):
        return hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=pw.encode('UTF-8'),
            salt=bytes.fromhex(salt),
            iterations=700_000
        ).hex()
    
    @staticmethod
    def setup_totp():
        # TODO
        pass

    @staticmethod
    def df():
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
    def get_user_by(property: Literal["id", "name", "email", "reg_uuid"], value) -> dict():
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
        elif property in ["name", "email", "reg_uuid"]:  # strings
            if property == "name":
                col = Users.Col.name
            elif property == "email":
                col = Users.Col.email
            elif property == "reg_uuid":
                col = Users.Col.reg_uuid
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
        with open(Users.sender_email_pw_file) as file:
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
        
        # TODO reg_url must be the real url not localhost
        reg_url = URL_BASE + "?register=" + reg_uuid

        with open("registration_mail.html") as file:
            html = file.read()
        
        username = Users.get_user_by("email", email)[Users.Col.name]

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
    def send_reset_pw_email(email: str):
        # Design html mails easy with https://tabular.email/demo/blank
        pw_reset_uuid = str(uuid.uuid4())
        # mailto:name@bla.de?subject=Das ist ein Betreff
        subject="Passwort zurücksetzen - Nutzerstudie zur TOTP Authentication"
        message = ""
        return Users._send_email_(
            email=email,
            subject=subject,
            message=message)

    @staticmethod
    def finish_registration(reg_uuid: str) -> bool:
        """!
        Checks if the registration link did expire. Sets the reg_uuid in the database to "".
        @param reg_uuid: UUID set for a user to complete their registration
        @return: False if the registration link expired or there was no or more than a single matching reg_uuid in the table of users. This should never happen.
        """
        df = Users.df()
        if reg_uuid == "-" or df[Users.Col.reg_uuid].loc[df[Users.Col.reg_uuid] == reg_uuid].shape[0] != 1:
            return False
        
        user = Users.get_user_by("reg_uuid", reg_uuid)
        user_id = user[Users.Col.id]

        if dt.datetime.utcnow() > user[Users.Col.reg_timeout_utc]:
            # registration link expired --> delete this user:
            Users.rm_user(user_id)
            return False
        
        df.at[user_id, Users.Col.reg_uuid] = "-"

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


def flush_view():
    st.session_state[Key.state] = LOGGED_IN
    # We need those st.writes and the sleep to get the screen empty.
    # Otherwise, we will see the login screen while loading the first view:
    for i in range(25):
        st.write("")
    time.sleep(0.1)
    st.experimental_rerun()


def login_view():
    # TODO block IP address after n failed login attempts for m hours.
    pad_top()
    st.title("Anmelden")
    pad_after_title()

    ret_check_login = state.value(Key.ret_check_login)
    changed_pw = state.value(Key.changed_pw)
    changed_username_or_email = state.value(Key.changed_username_or_email)

    def username_or_email_changed():
        st.session_state[Key.changed_username_or_email] = True

    username_or_email = st_tweaker.text_input(
        label="Benutzername",
        id="username",
        on_change=username_or_email_changed)
    if ret_check_login == Users.RetCheckLogin.missing_username_or_email:
        st.warning("Benutzername eingeben.")
    elif ret_check_login == Users.RetCheckLogin.user_not_found:
        st.warning("Dieser Benutzer existiert nicht.")
    elif ret_check_login == Users.RetCheckLogin.not_fully_registered:
        st.info("Registrierung noch nicht abgeschlossen. Schau in dein Email-Postfach und im Spam.")

    def pw_changed():
        st.session_state[Key.changed_pw] = True

    pw = st_tweaker.text_input(
        label="Passwort",
        type='password',
        id="password",
        on_change=pw_changed)
    if ret_check_login == Users.RetCheckLogin.missing_pw:
        st.warning("Passwort eingeben.")
    elif ret_check_login == Users.RetCheckLogin.invalid_pw:
        cols = st.columns(2)
        cols[0].warning("Passwort ungültig.")
        cols[1].write(f'<div style="text-align: right"> <a href="/?page={RESET_PW}" target="_self">Passwort vergessen?</a> </div><br>', unsafe_allow_html=True)

    login = st.button('Anmelden', type="secondary", use_container_width=True)
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
            user_id = Users.get_user_by(property, username_or_email)[Users.Col.id]
            st.session_state[Key.state] = FLUSH
            st.session_state[Key.user_id] = user_id
            time.sleep(0.1)  # needed to avoid multiple reruns of the flush view
            st.experimental_rerun()
        else:
            st.session_state[Key.changed_pw] = False
            st.session_state[Key.changed_username_or_email] = False
            st.experimental_rerun()
    
    st.session_state[Key.changed_pw] = False
    st.session_state[Key.changed_username_or_email] = False
    exit(0)

# TODO implementieren
def totp_view():
    pad_top()
    st.title("Anmelden")
    pad_after_title()

    totp = st_tweaker.text_input(
        label="Token",
        help="Dieses Token wird alle 30 Sekunden von einem Gerät generiert.",
        id="totp"
    )

    if totp:
        user=st.session_state[Key.user]
        # TODO: Check totp here

    
    exit(0)

# TODO testen:
def reset_pw_view():
    pad_top()
    st.title("Passwort zurücksetzen")
    pad_after_title()
    
    allow_reset = True
    username_or_email = st_tweaker.text_input(
        label="Benutzername oder Email",
        id="reset_pw_username",
        placeholder="you@example.com"
    )

    if username_or_email != "":
        # TODO Check if username, email exists
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

    if (reset or username_or_email != "") and allow_reset:
        email = Users.get_user_by("email", username_or_email) if "@" in username_or_email else Users.get_user_by("name", username_or_email)
        ret, raised_error = Users.send_reset_pw_email(email)
        if ret != {} or raised_error:
            # TODO better error handling and user anweisungen
            st.error("Beim Senden der Registrierungs-Email ist etwas fehlgeschlagen.")
        else:
            st.info(f"Es wurde eine Email an {email} gesendet. Befolge die darin befindlichen Anweisungen. Schau auch im Spam-Ordner nach.")

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
    
    # TODO restrict the valid symbols for a username (we don't want any cryptic stuff).
    username = st.text_input(label="Benutzername")
    if username != "":
        if not Users.isNameAvailable(username):
            st.warning("Dieser Name ist bereits vergeben.")
            allow_register = False
        if not Users.isNameValid(username):
            st.warning(f"Der Name enthält eines der ungültigen Zeichen: {','.join(INVALID_USERNAME_SYMBOLS)}")
            allow_register = False

    # TODO do a dictionary scan to ensure users don't use dictionary
    # words (e.g. "house") within their passwords.
    pw = st.text_input(label="Passwort (mindestens 8 Zeichen)", type='password')
    pw_repeated = st.text_input(label="Passwort (wiederholen)", type='password')
    if "" not in [pw_repeated, pw] and pw_repeated != pw:
            st.warning("Wiederholtes Passwort muss übereinstimmen.")
            allow_register = False

    register = st.button('Registrieren', use_container_width=True)

    if register and allow_register:
        if "" in [email, username, pw, pw_repeated]:
            st.warning("Füllen Sie jedes Feld aus.")
            exit(0)

        with st.spinner('Daten werden verarbeitet ...'):
            reg_uuid = Users.register_new(name=username, email=email, pw=pw)
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


def registration_mail_sent_view(user_id: int):
    pad_top()
    st.title("Fast geschafft!:rocket:", anchor=False)
    pad_after_title()
    email = Users.get_user_by("id", user_id)[Users.Col.email]
    st.subheader(f"Dir wurde eine Email an {email} gesendet, um die Registierung abzuschließen. Schau auch im Spam-Ordner nach.", anchor=False)
    exit(0)


def finish_registration_view(reg_uuid: str):
    pad_top()
    registration_finished = Users.finish_registration(reg_uuid=reg_uuid)

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
