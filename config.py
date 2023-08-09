from config_util import (getenv_bool, getenv_int, getenv_switch_str)

# -------------------- Streamlit stuff -------------------- #

# Should the user see the hamburger menu in the top right corner:
HIDE_TOP_RIGHT_HAMBURGER_MENU = getenv_bool('_HIDE_TOP_RIGHT_HAMBURGER_MENU_', False)

HIDE_STREAMLIT_STYLE = f"""
    <style>
    .block-container {{
        padding-top: {3}rem;
        padding-bottom: {0}rem;
        padding-left: {2}rem;
        padding-right: {2}rem;
    }}
    {"#" if HIDE_TOP_RIGHT_HAMBURGER_MENU else ""}MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
"""