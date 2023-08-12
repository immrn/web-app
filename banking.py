import streamlit as st
import state
from constants import SessionStateKey
import usage_tracking as track
from streamlit_modal import Modal
import streamlit.components.v1 as components

Key = SessionStateKey.Banking

_RECIPIENT_HELP = "Geben Sie eine beliebige IBAN an.  \nDies ist keine echte Überweisung."
_REFERENCE_HELP = "Geben Sie einen beliebigen Verwendungszweck an.  \nDies ist keine echte Überweisung."
_VALUE_HELP = "Geben Sie einen beliebigen Betrag an.  \nDies ist keine echte Überweisung."


def transaction_view():
    st.title("Überweisung")

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
        placeholder="Nachricht an der Empfänger"
    )

    value = st.number_input(
        label="Betrag",
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
        label="Überprüfen",
        key=Key.confirm,
        type="primary",
        use_container_width=True,
    )

    cancel = col[1].button(
        label="Abbrechen",
        key=Key.cancel,
        type="secondary",
        use_container_width=True,
    )
