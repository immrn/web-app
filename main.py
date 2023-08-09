import streamlit as st
import banking

st.set_page_config(page_title="TOTP Authentication Study", page_icon="🎓️")

import user_management as um
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
if not state.value(Key.logged_in): # User is not logged in:
    query_params = st.experimental_get_query_params()
    if "page" in query_params.keys():
        if query_params["page"][0] == um.REGISTER:
            um.register_view()
        elif query_params["page"][0] == um.RESET_PW:
            um.reset_pw_view()
    um.login_view()
if state.value(Key.logged_in) == um.TOTP:
    um.totp_view()
if state.value(Key.logged_in) == um.FLUSH:
    track.login()
    um.flush_view()

# After login was successfull:
banking.draw_screen()
