import streamlit as st

st.set_page_config(page_title="Nutzerstudie TOTP Authentication", page_icon="🎓️")

import banking
import user_management as um
import config
import state
import usage_tracking as track
from constants import SessionStateKey
import mist_views

Key = SessionStateKey.Common

# This must be the first code lines:
state.init()
track.init(st_key_for_username=Key.user_id)
#st.markdown(config.HIDE_STREAMLIT_STYLE, unsafe_allow_html=True)
st.markdown(config.footer, unsafe_allow_html=True)

# Login:
if not state.value(Key.state): # User is not logged in:
    query_params = st.experimental_get_query_params()
    if "page" in query_params.keys():
        if query_params["page"][0] == um.REGISTRATION:
            um.registration_view()
        elif query_params["page"][0] == um.RESET_PW:
            um.initiate_reset_pw_view()
        elif query_params["page"][0] == "about":
            mist_views.about()
        elif query_params["page"][0] == "contact":
            mist_views.contact()
        else:
            mist_views.not_found_404()
    elif "register" in query_params.keys():
        um.finish_registration_view(reg_uuid=query_params["register"][0])
    elif "reset_pw" in query_params.keys():
        um.reset_pw_view(reset_pw_uuid=query_params["reset_pw"][0])
    um.login_view()
elif state.value(Key.state) == um.TOTP:
    um.totp_view()
elif state.value(Key.state) == um.SETUP_TOTP:
    um.setup_totp_view()
elif state.value(Key.state) == um.REGISTRATION_MAIL_SENT:
    um.registration_mail_sent_view()
elif state.value(Key.state) == um.RESET_PW_MAIL_SENT:
    um.reset_pw_mail_sent_view(user_id=state.value(Key.user_id))
elif state.value(Key.state) == um.FINISH_RESET_PW:
    um.finish_reset_pw_view()
elif state.value(Key.state) == um.FINISH_TOTP_SETUP:
    um.finish_totp_setup_view()

# After login was successfull:
Key = SessionStateKey.Banking
if not state.value(Key.state):
    banking.transaction_view()
elif state.value(Key.state) == banking.TRANSACTION_SUCCESS:
    banking.transaction_success_view()
