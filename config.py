from config_util import (getenv_bool, getenv_int, getenv_switch_str)

PRODUCTION = getenv_bool("PRODUCTION", False)

WEBSERVICE_NAME = "SimPay"
WEBSERVICE_ICON = "💸"

SENDER_EMAIL_ADDRESS = "user.study.totp.authentication@gmail.com"
SENDER_EMAIL_NAME = WEBSERVICE_NAME
SMTP_SERVER = "smtp.gmail.com"
URL_BASE = "http://localhost:8501/"
NAME_OF_APP = "Simuliertes Banking"
PATH_TO_USER_DB_CSV = "volume/user_info.csv"
PATH_TO_EMAIL_PW_FILE = "gmail_pw.txt"
PATH_TO_USAGE_TRACKING_FILE = "volume/usage_tracking.csv"
PATH_TO_TRANSACTIONS_DIR = "volume/transactions"

COLOR_PRIMARY = "#6bfab1"
COLOR_SECONDARY = "#FAFAFA"
COLOR_BACKGROUND = "#0E1117"
COLOR_SECONDARY_BACKGROUND = "#262730"

if PRODUCTION:
    URL_BASE = "https://totp-study.informatik.tu-freiberg.de/"
    PATH_TO_USER_DB_CSV = "/share/volume/user_info.csv"
    PATH_TO_EMAIL_PW_FILE = "/share/volume/gmail_pw.txt"
    PATH_TO_USAGE_TRACKING_FILE = "/share/volume/usage_tracking.csv"
    PATH_TO_TRANSACTIONS_DIR = "/share/volume/transactions"

# -------------------- Streamlit stuff -------------------- #

# Should the user see the hamburger menu in the top right corner:
HIDE_TOP_RIGHT_HAMBURGER_MENU = PRODUCTION

STREAMLIT_STYLE=f"""
    <style>
        {"#" if HIDE_TOP_RIGHT_HAMBURGER_MENU else ""}MainMenu {{visibility: hidden;}}

        .reportview-container {{
            margin-top: -2em;
        }}
        .stDeployButton {{display:none;}}
        #stDecoration {{display:none;}}

        a:link , a:visited{{
            color: #2e9aff;
            background-color: transparent;
            text-decoration: underline;
        }}

        .main > .block-container {{
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 4rem;
            padding-right: 4rem;
        }}
        header {{visibility: hidden;}}

        a:hover,  a:active {{
            color: #42D0C9;
            background-color: transparent;
            text-decoration: underline;
        }}

        footer {{visibility: hidden;}}
    </style>
"""

CUSTOM_FOOTER =f"""
    <style>
        html {{
            min-height: 100%;
        }}
        /* ------- Footer ------- */
        .footer {{
            position: fixed;
            margin-top: 40px;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: transparent;
            color: #666666;
            text-align: center;
        }}
        .footer a:link {{
            color: #666666;
        }}
        .footer a:visited {{
            color: #666666;
        }}
        .footer a:hover {{
            color: #dddddd;
        }}
        .footer a:active {{
            color: #dddddd;
        }}
    </style>
    <div class="footer">
        <p>
            <a href="/" target="_self">Home</a> &#160 | &#160
            <a href="/?page=about" target="_blank">Über die Studie</a> &#160 | &#160 
            <a href="/?page=contact" target="_blank">Kontakt</a>
        </p>
    </div>
"""
