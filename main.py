import streamlit as st
import banking

st.set_page_config(page_title="Nutzerstudie TOTP Authentication", page_icon="🎓️")

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
            um.reset_pw_view()
        elif query_params["page"][0] == "about":
            mist_views.about()
        elif query_params["page"][0] == "contact":
            mist_views.contact()
        else:
            mist_views.not_found_404()
    elif "register" in query_params.keys():
        um.finish_registration_view(reg_uuid=query_params["register"][0])
    um.login_view()
elif state.value(Key.state) == um.TOTP:
    um.totp_view()
elif state.value(Key.state) == um.FLUSH:
    track.login()
    um.flush_view()
elif state.value(Key.state) == um.REGISTRATION_MAIL_SENT:
    um.registration_mail_sent_view(user_id=state.value(Key.user_id))

# After login was successfull:
banking.transaction_view()
