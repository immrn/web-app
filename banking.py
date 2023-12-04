import streamlit as st
import streamlit.components.v1 as components
import time
import datetime as dt
import platform
from millify import millify

import util
import state
import config
import usage_tracking as track
import user_management as um
from constants import SessionStateKey

Key = SessionStateKey.Banking

TRANSACTION_SUCCESS = "transaction_success"
BALANCE_OVERDRAW = 10000

# TODO anpassen falls SimPay ok
_RECIPIENT_HELP = "Geben Sie eine beliebige IBAN an.  \nDies ist keine echte Online-Zahlung."
_REFERENCE_HELP = "Geben Sie eine beliebige Nachricht an.  \nDies ist keine echte Online-Zahlung."
_VALUE_HELP = "Geben Sie einen beliebigen Betrag an.  \nDies ist keine echte Online-Zahlung."


def transaction_view():
    cols = st.columns([2,1])
    cols[0].title("Geld senden", anchor=False)
    cols[1].write(f'<br><div style="text-align: right; color: #AFAFAF;"> <i> Dies ist keine echte Zahlung. </i></div>', unsafe_allow_html=True)
    
    recipient = st.text_input(
        label="Emfpänger",
        key=Key.recipient,
        help=_RECIPIENT_HELP,
        on_change=track.cb.edit_text,
        kwargs={"key": Key.recipient},
        placeholder="Email"
    )

    value = st.text_input(
        label="Betrag in €",
        key=Key.value,
        placeholder="0,00",
        on_change=track.cb.edit_text,
        kwargs={"key": Key.value},
        help=_VALUE_HELP,
    )
    if "," in value:
        value = value.replace(",",".")

    message = st.text_input(
        label="Nachricht",
        key=Key.message, 
        help=_REFERENCE_HELP,
        on_change=track.cb.edit_text,
        kwargs={"key": Key.message},
        placeholder="Schreibe eine Nachricht"
    )
    
    col = st.columns([1,2,1])

    confirm = col[1].button(
        label="Senden",
        key=Key.confirm,
        type="secondary",
        use_container_width=True,
        on_click=track.cb.click,
        kwargs={"key": Key.confirm},
        disabled=True if state.get_state("did_rerun_after_transaction") else False
    )    
    
    if confirm or state.get_state("did_rerun_after_transaction"):
        if "did_rerun_after_transaction" not in st.session_state:
            st.session_state["did_rerun_after_transaction"] = False
        
        # Hande invalid inputs:
        balance = get_balance(st.session_state[SessionStateKey.Common.user_id])
        exit_app = False
        try:
            value = float(value)
        except:
            st.warning("Ungültiger Betrag. Geben Sie eine Zahl für den Betrag ein.")
            exit_app = True
        if recipient == "":
            st.warning("Geben Sie einen Empfänger an.")
            exit_app = True
        if value == 0:
            st.warning("Geben Sie einen Betrag an.")
            exit_app = True
        if isinstance(value, float | int) and value > balance + BALANCE_OVERDRAW:
            st.warning(f"Wählen Sie einen geringeren Betrag. Sie können Ihr Konto nicht mit mehr als {BALANCE_OVERDRAW} € überziehen.")
            exit_app = True
        if exit_app:
            exit(0)
        
        util.center_spinner()
        with st.spinner(""):
            if not st.session_state["did_rerun_after_transaction"]:
                um.Users.do_transaction(
                    user_id=st.session_state[SessionStateKey.Common.user_id],
                    recipient=recipient,
                    value=value,
                    message=message
                )
                st.session_state["did_rerun_after_transaction"] = True
                st.rerun()
            else:
                del st.session_state["did_rerun_after_transaction"]
                time.sleep(2)
        
        st.session_state[Key.state] = TRANSACTION_SUCCESS
        st.rerun()


def transaction_success_view():
    st.title("Geld senden", anchor=False)
    st.write("")
    st.success("✅ Ihre simulierte Zahlung wurde bestätigt.")
    st.write("_Sie können sich nun abmelden. Melden Sie sich **morgen** erneut an und tätigen Sie eine weitere simulierte Zahlung._")
    new_payment = st.columns(3)[1].button(
        label="Neue Zahlung",
        key=Key.new_payment,
        use_container_width=True
    )
    if new_payment:
        st.session_state[Key.state] = None
        # for key in [Key.message, Key.value, Key.recipient]:
        #     del st.session_state[state._STATE + key]
        #     del st.session_state[state._SHADOW + key]
        st.rerun()


def overview():
    # Balance:
    st.title("Bilanz", False)
    user_id = st.session_state[SessionStateKey.Common.user_id]
    balance = get_balance(user_id)
    color = config.COLOR_PRIMARY if balance >= 0 else "#ff4545"
    balance_str = balance_to_str(balance)

    st.markdown(f'<div style="color: {color}; font-size: 50px;">{balance_str}</div>', True)
    st.write("")

    # History:
    df = um.Users.get_transactions(user_id)
    if not df.empty:
        st.title("Verlauf", False)
        for idx, row in df.iterrows():
            log_box(
                timestamp=idx,
                recipient=row["recipient"],
                value=row["value"],
                message=row["message"]
            )


def get_balance(user_id):
    user = um.Users.get_user_by(um.Users.Col.id, user_id)
    return float(user[um.Users.Col.balance])


def balance_to_str(balance):
    return ("%.2f" % round(balance, 2)).replace(".",",") + " €"


def log_box(timestamp: dt.datetime, recipient: str, value: float, message: str):
        msg_len = 35
        message = message if len(message) < msg_len else message[0:msg_len] + "..."
        if message == "nan":
            message = ""
        else:
            message = "\"" + message + "\""

        if value < 10000:
            value = ("%.2f" % round(value, 2)).replace(".",",") + " €"
        else:
            value = millify(value) + " €"

        match platform.system():
            case "Windows":
                s = "#"
            case "Darwin" | "Linux":
                s = "-"
            case _:
                s = ""

        st.markdown(f"""
            <style>
                .grid-container {{
                    border: 2px solid #4A4A4A;
                    border-radius: 10px;
                    padding: 5px;
                    display: grid;
                    grid-template-columns: 5% 40% 25% 15% 15%;
                    gap: 0px;
                    margin-bottom: 10px;
                }}
                .grid-container > div {{
                    margin: auto;
                    padding: 5px;
                    border: 0px solid #1F1F1F;
                    word-wrap: break-word;
                    word-break: break-word;
                }}
            </style>
            <body>
            <div class="grid-container">
                <div>
                    an</div>
                <div style="margin-left: 5px;">
                    <b><font color="{config.COLOR_PRIMARY}">{recipient}</font></b></div>
                <div style="text-align: left; margin-left: 0px;">
                    <i>{message}</i></div>
                <div>
                    <font color="#ababab">{timestamp.strftime(f"%{s}d.%{s}m.%y %{s}H:%M")}</font></div>
                <div style="text-align: right; margin-right: 0px; font-size: 19px;">
                    <b><font color="#ffc278">{value}</font></b></div>
            </div>
            </body>
            """, True)


def logout_button():
    st.write("")
    logout = st.button(
        label="Abmelden",
        key=Key.logout,
        use_container_width=True
    )

    if logout:
        track.logout()
        for _state in st.session_state:
            del st.session_state[_state]
        st.rerun()