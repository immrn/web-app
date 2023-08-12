from config_util import (getenv_bool, getenv_int, getenv_switch_str)

SENDER_EMAIL_ADDRESS = "user.study.totp.authentication@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
URL_BASE = "http://localhost:8501/"

# -------------------- Streamlit stuff -------------------- #

# Should the user see the hamburger menu in the top right corner:
HIDE_TOP_RIGHT_HAMBURGER_MENU = getenv_bool('_HIDE_TOP_RIGHT_HAMBURGER_MENU_', True)

footer=f"""
    <style>
        {"#" if HIDE_TOP_RIGHT_HAMBURGER_MENU else ""}MainMenu {{visibility: hidden;}}

        a:link , a:visited{{
            color: #2e9aff;
            background-color: transparent;
            text-decoration: underline;
        }}

        footer {{visibility: hidden;}}

        a:hover,  a:active {{
            color: #42D0C9;
            background-color: transparent;
            text-decoration: underline;
        }}

        .footer {{
            position: fixed;
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