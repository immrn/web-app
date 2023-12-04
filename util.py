import streamlit as st
import config

def header():
    st.header(config.WEBSERVICE_ICON + " " + config.WEBSERVICE_NAME, False)


def center_spinner():
    st.markdown("""
        <style>
        div.stSpinner > div {
            text-align:center;
            align-items: center;
            justify-content: center;
        }
        </style>""", unsafe_allow_html=True
    )  