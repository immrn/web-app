import streamlit as st
import os
from constants import SessionStateKey
import time


# This is how you named your user and logged_in st.session_state key:
USER_KEY = SessionStateKey.Common.user
LOGGED_IN_KEY = SessionStateKey.Common.logged_in

credentials = {
    'test-user': '1234',
    "1": "1",
}

# _USER_AND_PASSWORD_STRING_ shoud be i.e. 'user_1:pw_user_1;user_2:pw_user_2;.........'
credentials_env = os.getenv('_USERS_AND_PASSWORD_STRING_')
if credentials_env:
    user_pw_pairs = credentials_env.split(';')
    credentials = {pair.split(':')[0]: pair.split(':')[1] for pair in user_pw_pairs}

_FLUSH_VIEW_ = "flush_view"


def flush_view():
    st.session_state[LOGGED_IN_KEY] = True
    # We need those st.writes and the sleep to get the screen empty.
    # Otherwise, we will see the login screen while loading the first view:
    for i in range(25):
        st.write("")
    time.sleep(0.1)
    st.experimental_rerun()


def create_view():
    for i in range(10):
        st.write("")

    user = st.text_input(label="Benutzername")
    pw = st.text_input(label="Passwort", type='password')
    login = st.button('Anmelden', use_container_width=True)
    login = True if pw != "" else login  # input pw and press enter -> no need to click "login"-button

    if login:
        if not user or not pw:
            st.warning(f'Benutzername und Passwort eingeben.')

        if user in credentials.keys():
            if credentials[user] == pw:
                st.session_state[LOGGED_IN_KEY] = _FLUSH_VIEW_
                st.session_state[USER_KEY] = user
                time.sleep(0.1)  # needed to avoid multiple reruns of the flush view
                st.experimental_rerun()
            else:
                st.warning(f'Passwort ungültig')
        else:
            st.warning(f'Dieser Benutzer existiert nicht.')
    exit(0)
