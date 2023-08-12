import streamlit as st
import os
from constants import SessionStateKey
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
import state
import config


# Editable constants:
URL_BASE = config.URL_BASE  # base link of your web app
PATH_TO_USER_DB_CSV = "user_info.csv"  # where you store your users authentication information
SMTP_SERVER = config.SMTP_SERVER  # smtp server of sender email adress
SENDER_EMAIL = config.SENDER_EMAIL_ADDRESS  # from where registration mails will be sent
SENDER_EMAIL_PW_FILE = "gmail_pw.txt"  # file containing the password of sender email address, gitignore this file!
# TIMEOUT of registration link after registration process started. Your users should get at least 10 min to click on the link in their registration email.
# But you should not keep the timeout value too big. Attackers could block emails by walking through registration processes.
REGISTRATION_TIMEOUT = dt.timedelta(minutes=10)
REGISTRATION_TIMEOUT_STRING = "10 Minuten"   # timeout as string for the email


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

    @staticmethod
    def isNameAvailable(name: str):
        user = Users.get_user_by("name", name)
        if user == {}:
            return True
        return False
    
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
    def register_new(name: str, email: str, pw: str, reg_uuid: str):
        if not Users.isNameAvailable(name) or \
            not Users.isEmailAvailable(email) or \
            not Users.isEmailValid(email):
            raise ValueError(
                "User name or email is already used. You should check \
                if these params already exist in your user database before \
                calling this function."
            )

        salt = os.urandom(16).hex()
        secret = "TODO"
        df = Users.df()
        df = df.sort_values(Users.Col.id)
        highest_id = -1 if df.empty else df[Users.Col.id].iloc[-1]

        new_user = {
            Users.Col.id: highest_id + 1,
            Users.Col.name: name,
            Users.Col.email: email,
            Users.Col.salt: salt,
            Users.Col.hashed_pw: Users.hash_pw(pw, salt),
            Users.Col.secret: secret,
            Users.Col.reg_uuid: reg_uuid
        }
        df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
        df = df.set_index(Users.Col.id)
        df.to_csv(Users.csv_path)

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
        df[Users.Col.id] = df[Users.Col.id].astype(int)
        str_type_columns = [Users.Col.name, Users.Col.email, Users.Col.salt,
                            Users.Col.hashed_pw, Users.Col.secret, Users.Col.reg_uuid]
        df[str_type_columns] = df[str_type_columns].astype(str)
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
            col = Users.Col.id
            try:
                value = int(value)
            except TypeError:
                raise TypeError("When parameter 'property' is 'id', value must be an integer!")
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
        else:
            raise ValueError(f"'{property}' is not a valid literal for parameter 'property'!")
        user = df[df[col] == value]
        if not user.empty:
            return user.iloc[0].to_dict()
        return dict()

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

        ret, raised_error = Users._send_email_(
            email=email,
            subject="Registrierung für die Nutzerstudie zur TOTP Authentication",
            html=html)
        if ret != {} or raised_error:
            # TODO better error handling and user anweisungen
            st.error("Beim Senden der Registrierungs-Email ist etwas fehlgeschlagen.")
            st.write(f"ret:\n{ret}\n\nraised_error:\n{raised_error}")

    @staticmethod
    def send_reset_pw_email(email: str):
        # Design html mails easy with https://tabular.email/demo/blank
        pw_reset_uuid = str(uuid.uuid4())
        # mailto:name@bla.de?subject=Das ist ein Betreff
        subject="Passwort zurücksetzen - Nutzerstudie zur TOTP Authentication"
        message = ""
        ret, raised_error = Users._send_email_(
            email=email,
            subject=subject,
            message=message)
        if ret != {} or raised_error:
            # TODO better error handling and user anweisungen
            st.error("Beim Senden der Registrierungs-Email ist etwas fehlgeschlagen.")

    @staticmethod
    def set_reg_uuid_complete(reg_uuid: str) -> bool:
        """!
        Set the registration UUID to "complete".
        @param reg_uuid: UUID set for a user to complete their registration
        @return: False if there was no or more than a single matching reg_uuid in the table of users
        """
        df = Users.df()
        if df[Users.Col.reg_uuid].loc[df[Users.Col.reg_uuid] == reg_uuid].shape[0] != 1:
            return False
        df[Users.Col.reg_uuid].loc[df[Users.Col.reg_uuid] == reg_uuid] = "complete"
        df = df.set_index(Users.Col.id)
        df.to_csv(Users.csv_path)
        return True


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

    username = st_tweaker.text_input(label="Benutzername", id="username")
    pw = st_tweaker.text_input(label="Passwort", type='password', id="password")

    if state.value(Key.show_pw_warning) == True:
        cols = st.columns(2)
        # Invalid password:
        cols[0].write(f'<div style="text-align: left; color: #FF4B4B">Passwort ungültig</div>', unsafe_allow_html=True)
        # Forgot your password?
        cols[1].write(f'<div style="text-align: right"> <a href="/?page={RESET_PW}" target="_self">Passwort vergessen?</a> </div><br>', unsafe_allow_html=True)

    login = st.button('Anmelden', type="secondary", use_container_width=True)
    login = True if pw != "" else login  # input pw and press enter -> no need to click "login"-button

    # Let new users regsiter themself:
    st.write(f'<br><div style="text-align: center"> <a href="/?page={REGISTRATION}" target="_self">Registrieren</a> </div>', unsafe_allow_html=True)

    # TODO NEXT irgendwas stimmt mit dem login nicht
    # TODO NEXT regristration timeout logik in user db implementieren

    if login:
        st.session_state[Key.show_pw_warning] = False

        if pw == state.value(Key.pw_before):
            exit(0)

        st.session_state[Key.pw_before] = pw
        if not username or not pw:
            st.warning(f'Benutzername und Passwort eingeben.')
            exit(0)
        
        user = Users.get_user_by("name", username)

        if user == {}:
            st.warning(f'Dieser Benutzer existiert nicht.')
            exit(0)
        
        hashed_pw = Users.hash_pw(pw=pw, salt=user[Users.Col.salt])
        
        if user[Users.Col.hashed_pw] == hashed_pw:
            st.session_state[Key.state] = FLUSH
            st.session_state[Key.user_id] = user[Users.Col.id] # TODO NEXT ID NOT NAME
            time.sleep(0.1)  # needed to avoid multiple reruns of the flush view
            st.experimental_rerun()
        else:  # password wrong
            st.session_state[Key.show_pw_warning] = True
            st.experimental_rerun()

    exit(0)


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


def reset_pw_view():
    pad_top()
    st.title("Passwort zurücksetzen")
    pad_after_title()

    username_or_email = st_tweaker.text_input(
        label="Benutzername oder Email",
        id="reset_pw_username",
        placeholder="you@example.com"
    )
    st.write("")
    reset = st.button('Passwort zurücksetzen', use_container_width=True)

    if reset or username_or_email != "":
        pass

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
    if username != "" and not Users.isNameAvailable(username):
        st.warning("Dieser Name ist bereits vergeben.")
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
        
        reg_uuid = str(uuid.uuid4())

        with st.spinner('Daten werden verarbeitet ...'):
            Users.register_new(name=username, email=email, pw=pw, reg_uuid=reg_uuid)
            Users.send_registration_email(email, reg_uuid=reg_uuid)

        st.session_state[Key.state] = REGISTRATION_MAIL_SENT
        user_id = Users.get_user_by("name", username)[Users.Col.id]
        st.session_state[Key.user_id] =  user_id
        st.experimental_rerun()

    exit(0)


def registration_mail_sent_view(user_id: int):
    pad_top()
    st.title("Fast geschafft!:rocket:", anchor=False)
    pad_after_title()

    email = Users.get_user_by("id", user_id)[Users.Col.email]
    st.subheader(f"Dir wurde eine Email an {email} gesendet, um die Registierung abzuschließen.", anchor=False)
    exit(0)


def finish_registration_view(reg_uuid: str):
    pad_top()
    registration_finished = Users.set_reg_uuid_complete(reg_uuid=reg_uuid)

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
