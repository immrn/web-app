import streamlit as st
import time

st.set_page_config(page_title="Artikelfertigung")

import login
import config
import state
import usage_tracking as track
from constants import SessionStateKey

Key = SessionStateKey.Common

# This must be the first code lines:
state.init()
track.init(st_key_for_username=Key.user)
st.markdown(config.HIDE_STREAMLIT_STYLE, unsafe_allow_html=True)

# Login:
if not state.value(Key.logged_in):
    login.create_view()
if state.value(Key.logged_in) == "flush_view":
    track.login()
    login.flush_view()

# After login was successfull:
st.markdown("# You are logged in!")
