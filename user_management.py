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


Key = SessionStateKey.Common
FLUSH = "flush"
TOTP = "totp"
REGISTER = "register"
RESET_PW = "reset_pw"


class Users:
    csv_path = "user_info.csv"

    class Col:
        id = "id"
        name = "name"
        email = "email"
        salt = "salt"
        hashed_pw = "hashed_pw"
        secret = "secret"

    @staticmethod
    def isNameAvailable(name: str):
        user = Users.get_user_by("name", name)
        if user.empty:
            return True
        return False
    
    @staticmethod
    def isEmailAvailable(email: str):
        user = Users.get_user_by("email", email)
        if user.empty:
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
    def register_new(name: str, email: str, pw: str):
        if not Users.isNameAvailable(name) or \
            not Users.isEmailAvailable(email) or \
            not Users.isEmailValid(email):
            raise ValueError(
                "User name or email is already used. You should check \
                if these params already exist in your user database before \
                calling this function."
            )

        salt = os.urandom(16).hex()
        secret = ""
        df = Users.df()
        df = df.sort_values(Users.Col.id)
        highest_id = -1 if df.empty else df[Users.Col.id].iloc[-1]

        new_user = {
            Users.Col.id: highest_id + 1,
            Users.Col.name: name,
            Users.Col.email: email,
            Users.Col.salt: salt,
            Users.Col.hashed_pw: Users.hash_pw(pw, salt),
            Users.Col.secret: secret
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
        pass

    @staticmethod
    def df():
        df = pd.read_csv(Users.csv_path, sep=',')
        df[Users.Col.id] = df[Users.Col.id].astype(int)
        str_type_columns = [Users.Col.name, Users.Col.email, Users.Col.salt, Users.Col.hashed_pw, Users.Col.secret]
        df[str_type_columns] = df[str_type_columns].astype(str)
        return df
    
    @staticmethod
    def get_user_by(property: Literal["id", "name", "email"], value):
        df = Users.df()
        if property == "id":
            col = Users.Col.id
            try:
                value = int(value)
            except ValueError:
                raise TypeError("When parameter 'property' is 'id', value must be an integer!")
        elif property == "name":
            col = Users.Col.name
            try:
                value = str(value)
            except ValueError:
                raise TypeError("When parameter 'property' is 'name', value must be a string!")
        elif property == "email":
            col = Users.Col.email
            try:
                value = str(value)
            except ValueError:
                raise TypeError("When parameter 'property' is 'email', value must be a string!")
        else:
            raise ValueError(f"'{property}' is not a valid literal for parameter 'property'!")
        user = df[df[col] == value]
        return user

    @staticmethod
    def _send_email_(email: str, message: str):
        port = 465  # SSL
        with open("gmail_pw.txt") as file:
            password = file.readline()
        smtp_server = "smtp.gmail.com"
        sender_email = "user.study.totp.authentication@gmail.com"
        receiver_email = email

        ret = {}
        raised_error = None

        # Create a secure SSL context
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            try:
                ret = server.sendmail(sender_email, receiver_email, message)
            except (smtplib.SMTPHeloError, smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused, smtplib.SMTPNotSupportedError) as e:
                raised_error = e
        return ret, raised_error
        


    @staticmethod
    def send_registration_email(email: str):
        # TODO https://realpython.com/python-send-email/
        registration_uuid = str(uuid.uuid4())
        message = """\
        Subject: Hi there

        This message is sent from Python."""
        ret, raised_error = Users._send_email_(email, message)
        if ret != {} or raised_error:
            # TODO better error handling and user anweisungen
            st.error("Beim Senden der Registrierungs-Email ist etwas fehlgeschlagen.")
        


    @staticmethod
    def send_reset_pw_email(email: str):
        # TODO
        pw_reset_uuid = str(uuid.uuid4())
        message = """\
        Subject: Hi there

        This message is sent from Python."""
        ret, raised_error = Users._send_email_(email, message)
        if ret != {} or raised_error:
            # TODO better error handling and user anweisungen
            st.error("Beim Senden der Registrierungs-Email ist etwas fehlgeschlagen.")


def pad_top():
    for i in range(8):
        st.write("")


def flush_view():
    st.session_state[Key.logged_in] = True
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

    username = st_tweaker.text_input(label="Benutzername", id="username")
    pw = st_tweaker.text_input(label="Passwort", type='password', id="password")
    # Forgot your password?
    st.write(f'<div style="text-align: right"> <a href="/?page={RESET_PW}" target="_self">Passwort vergessen</a> </div><br>', unsafe_allow_html=True)
    login = st.button('Anmelden', use_container_width=True)
    login = True if pw != "" else login  # input pw and press enter -> no need to click "login"-button

    # Let new regsiter themself:
    st.write(f'<br><div style="text-align: center"> <a href="/?page={REGISTER}" target="_self">Neuen Account registrieren</a> </div>', unsafe_allow_html=True)

    if login:
        if not username or not pw:
            st.warning(f'Benutzername und Passwort eingeben.')
            exit(0)
        
        user = Users.get_user_by("name", username)

        if user.empty:
            st.warning(f'Dieser Benutzer existiert nicht.')
            exit(0)
        
        hashed_pw = Users.hash_pw(pw=pw, salt=user[Users.Col.salt][0])
        
        if user[Users.Col.hashed_pw][0] == hashed_pw:
            st.session_state[Key.logged_in] = FLUSH
            st.session_state[Key.user] = username
            time.sleep(0.1)  # needed to avoid multiple reruns of the flush view
            st.experimental_rerun()
        else:
            st.warning(f'Passwort ungültig')
            exit(0)
    exit(0)


def totp_view():
    pad_top()
    st.title("Anmelden")

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

    username_or_email = st_tweaker.text_input(
        label="Benutzername oder Email",
        id="reset_pw_username",
        placeholder="you@example.com"
    )
    reset = st.button('Passwort zurücksetzen', use_container_width=True)

    if reset or username_or_email != "":
        pass

    exit(0)



def register_view():
    pad_top()
    st.title("Registrieren")

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
        
        Users.register_new(name=username, email=email, pw=pw)
        Users.send_registration_email(email)

    exit(0)