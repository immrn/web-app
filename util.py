import streamlit as st


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