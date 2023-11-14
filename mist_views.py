import streamlit as st
from streamlit_javascript import st_javascript
import config

def not_found_404():
    st.title("404: Page not found", anchor=False)
    # TODO Link to Homepage
    exit(0)


def about():
    st.title("Über die Studie", anchor=False)
    st.markdown(
        f"""
        Dies ist eine Web-Anwendung im Rahmen einer Nutzerstudie an der [TU Bergakademie Freiberg](https://tu-freiberg.de). 
        Ziel der Studie ist die Analyse eines erweiterten Verfahrens der Zwei-Faktor-Authentisierung. 
        Das Verfahren nennt sich [Time-based One-time Passwords](https://www.ionos.de/digitalguide/server/sicherheit/totp/) (TOTP), deutsch _zeitbasierte Einmalpasswörter_. 

        Allerdings wurde dieses Verfahren im Rahmen der Studie, wie folgt, erweitert:  
        Eine Extension im Chrome-Browser des Nutzers erkennt den Anmeldevorgang und erfragt per Bluetooth das TOTP vom Smartphone des Nutzers. 
        Auf dem Smartphone muss der Anmeldevorgang bestätigt werden, damit das Smartphone das TOTP an die Extension sendet. 
        Die Extension versucht das TOTP in das entsprechende Eingabefeld einzusetzen und zu bestätigen. 
        Ziel ist es dem Nutzer mehr Usability und Schutz vor Phishing-Websites zu bieten. 
        Denn das normale TOTP-Verfahren bietet keinen Schutz vor Diebstahl der Anmeldedaten auf Phishing-Websites. Das erweiterte Verfahren dagegen stellt sicher, dass ein TOTP nur dann vom Smartphone zur Extension übertragen wird, wenn die aktuelle URL im Browser in der TOTP-App des Smartphones hinterlegt ist.

        Das erweiterte TOTP-Verfahren bietet auch eine sichere, aber weniger nutzerfreundliche Option an, falls eine Bluetooth-Verbindung nicht möglich ist. 
        Dabei scanned der Nutzer mit der TOTP-App seines Smartphones einen QR-Code ein, den die Extension generiert, sobald das TOTP vom Webservice verlangt wird. 
        Dieser QR-Code enthält unter anderem die URL der Website. 
        Die TOTP-App des Smartphones überprüft wieder, ob sie für diese URL ein TOTP erstellen kann und zeigt es dann auf dem Display an. 
        Nun muss der Nutzer das TOTP nur noch händisch auf der Website eingeben.
        
        Vielen Dank, dass du dich für die Studie interessierst bzw. an ihr teilnimmst!

        Bei Fragen kontaktiere mich per Email: [{config.SENDER_EMAIL_ADDRESS}](mailto:{config.SENDER_EMAIL_ADDRESS})
        """
    )
    exit(0)


def contact():
    st.title("Kontakt", anchor=False)
    st.markdown(
        f"""
        Marian Käsemodel  
        Student der TU Bergakademie Freiberg  
        Email: [{config.SENDER_EMAIL_ADDRESS}](mailto:{config.SENDER_EMAIL_ADDRESS})  
        """
    )
    exit(0)


def download():

    os = st_javascript("""window.navigator.platform;""")
    st.write(f"OS = {os}")
    os = st_javascript("""navigator.appVersion.indexOf('Win');""")
    st.write(f"OS = {'Windows' if os != -1 else 'not Windows'}")

    link_chrome_download = "https://www.google.com/chrome/"

    st.title("Blue TOTP installieren")
    st.markdown("Diese Anleitung hilft Ihnen, Blue TOTP auf ihrem Windows PC und auf Ihrem Android Smartphone zu installieren.")
    st.subheader("Voraussetzungen")
    st.markdown(
        f"""
        - bluetoothfähiger Windows PC + [Chrome Browser]({link_chrome_download})
        - Android Smartphone
        """    
    )
    st.subheader("Installation (Windows)")
    st.markdown(
        f"""
        1. Führen Sie die folgenden Schritte nur auf einem Windows PC aus.
        2. Installiere die [Blue TOTP Extension](TODO) im Chrome Browser.
        3. Laden Sie das Programm **_Blue TOTP Service_** herunter und installieren Sie es.
        """
    )
    cols = st.columns([1,35])
    cols[1].download_button(
        label="Blue TOTP Service herunterladen",
        file_name="todo-test-file",
        data="TODO-testdata",
    )

    st.subheader("Installation (Android)")
    st.markdown(
        f"""
        Suchen Sie im "Play Store" nach "Blue TOTP" oder scannen Sie den folgenden QR-Code mit ihrem Android-Smartphone:  
        TODO Play Store Blue TOTP QR Code
        """
    )

    st.markdown(
        f"""
        <style>
        footer {{visibility: hidden;}}
        </style
        """
    , unsafe_allow_html=True)
    exit(0)