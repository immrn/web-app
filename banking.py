import streamlit as st
import streamlit.components.v1 as components
import time

import util
import state
import usage_tracking as track
from constants import SessionStateKey

Key = SessionStateKey.Banking

TRANSACTION_SUCCESS = "transaction_success"

_RECIPIENT_HELP = "Geben Sie eine beliebige IBAN an.  \nDies ist keine echte Überweisung."
_REFERENCE_HELP = "Geben Sie einen beliebigen Verwendungszweck an.  \nDies ist keine echte Überweisung."
_VALUE_HELP = "Geben Sie einen beliebigen Betrag an.  \nDies ist keine echte Überweisung."


def transaction_view():
    cols = st.columns(2)
    cols[0].title("Überweisung", anchor=False)
    cols[1].write(f'<br><div style="text-align: right"> <i> Dies ist keine echte Überweisung. </i></div>', unsafe_allow_html=True)
    
    recipient = st.text_input(
        label="Empfänger",
        key=Key.recipient, 
        value=state.value(key=Key.recipient, default=""),
        help=_RECIPIENT_HELP,
        on_change=track.cb.edit_text,
        kwargs={"key": Key.recipient},
        placeholder="IBAN eingeben"
    )

    reference = st.text_input(
        label="Verwendungszeck",
        key=Key.reference, 
        value=state.value(key=Key.reference, default=""),
        help=_REFERENCE_HELP,
        on_change=track.cb.edit_text,
        kwargs={"key": Key.reference},
        placeholder="Nachricht an Empfänger"
    )

    value = st.number_input(
        label="Betrag in €",
        key=Key.value,
        min_value=0.00,
        step=1.00,
        value=state.value(key=Key.value, default=0.00),
        format="%f",
        on_change=track.cb.edit_text,
        kwargs={"key": Key.value},
        help=_VALUE_HELP,
    )
    
    col = st.columns(2)

    confirm = col[0].button(
        label="Überweisen",
        key=Key.confirm,
        type="primary",
        use_container_width=True,
        on_click=track.cb.click,
        kwargs={"key": Key.confirm}
    )

    cancel = col[1].button(
        label="Abbrechen",
        key=Key.cancel,
        type="secondary",
        use_container_width=True,
    )

    if confirm:
        util.center_spinner()
        with st.spinner(""):
            time.sleep(2)
        st.session_state[Key.state] = TRANSACTION_SUCCESS
        st.rerun()
    if cancel:
        st.info("Überweisung abgebrochen")

def transaction_success_view():
    st.title("Überweisung", anchor=False)
    st.write("")
    st.success("Ihre Überweisung wurde bestätigt.")
    st.write("Bitte Schließen Sie den Tab und melden Sie sich morgen erneut an.")