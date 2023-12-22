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
        Das erweiterte Verfahren basiert auf dem bereits etablierten Verfahren [Time-based One-time Passwords](https://www.ionos.de/digitalguide/server/sicherheit/totp/) (TOTP), deutsch _zeitbasierte Einmalpasswörter_. 

        Die Erweiterungen umfassen folgende Funktionen:  
        Eine Extension im Chrome-Browser des Nutzers erkennt den Anmeldevorgang und erfragt per Bluetooth das TOTP vom Smartphone des Nutzers. 
        Auf dem Smartphone muss der Anmeldevorgang bestätigt werden, damit das Smartphone das TOTP an die Extension sendet. 
        Die Extension versucht das TOTP in das entsprechende Eingabefeld auf der Website einzusetzen und zu bestätigen. 
        Ziel ist es dem Nutzer mehr Usability und Schutz vor Phishing-Websites zu bieten. 
        Denn das normale TOTP-Verfahren bietet keinen Schutz vor Diebstahl der Anmeldedaten auf Phishing-Websites. Das erweiterte Verfahren dagegen stellt sicher, dass ein TOTP nur dann vom Smartphone zur Extension übertragen wird, wenn die aktuelle URL im Browser in der TOTP-App des Smartphones hinterlegt ist.
        
        Vielen Dank, dass Sie sich für die Studie interessieren bzw. an ihr teilnehmen!

        Bei Fragen kontaktieren Sie mich per Email: [{config.SENDER_EMAIL_ADDRESS}](mailto:{config.SENDER_EMAIL_ADDRESS})
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


def _not_windows_message():
    st.error("Sie befinden sich aktuell nicht auf einem Windows PC. Wechseln Sie auf einen Windows PC und rufen Sie diese Website erneut auf.")


def _download_button_blue_totp_service():
    with open("volume/download/service.exe", "rb") as file:
        st.download_button(
            label="Blue TOTP Service herunterladen",
            file_name="Blue TOTP Service Setup.exe",
            data=file,
            mime="application/octet-stream"
        )


def download():
    is_windows = True if st_javascript("""navigator.appVersion.indexOf('Win');""") != -1 else False
    link_chrome_download = "https://www.google.com/chrome/"

    st.title("Blue TOTP installieren", anchor=False)

    st.markdown("Diese Anleitung hilft Ihnen, Blue TOTP auf Ihrem Windows PC und auf Ihrem Android Smartphone zu installieren.")
    st.subheader("Voraussetzungen")
    if not is_windows:
        _not_windows_message()
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
        2. Laden Sie das Programm **_Blue TOTP Service_** herunter und installieren Sie es.
        """
    )
    cols = st.columns([1,35])
    with cols[1]:
        _download_button_blue_totp_service()
    st.markdown(f"""
        3. Installieren Sie die [Blue TOTP Extension](TODO) im Chrome Browser.
        """
    )

    # st.subheader("Installation (Android)")
    # st.markdown(
    #     f"""
    #     Suchen Sie im **Play Store** nach <q>_Blue TOTP_</q> oder scannen Sie den folgenden QR-Code mit Ihrem Android-Smartphone:  
    #     TODO Play Store Blue TOTP QR Code
    #     """,
    # unsafe_allow_html=True)
    exit(0)

def download_only_service():
    is_windows = True if st_javascript("""navigator.appVersion.indexOf('Win');""") != -1 else False

    st.title("Blue TOTP Service", anchor=False)

    if not is_windows:
        _not_windows_message()

    st.markdown(f"""
        1. Laden Sie das Programm **_Blue TOTP Service_** auf Ihren Windows-PC herunter.
        """
    )
    cols = st.columns([1,35])
    with cols[1]:
        _download_button_blue_totp_service()
    st.markdown(f"""
        2. Installieren Sie es.
        3. Öffnen Sie wieder die Blue TOTP Extension in Ihrem Chrome Browser.
        """
    )

    exit(0)


def download_prototype():
    is_windows = True if st_javascript("""navigator.appVersion.indexOf('Win');""") != -1 else False
    link_chrome_download = "https://www.google.com/chrome/"

    st.title("Blue TOTP installieren PROTOTYPE", anchor=False)

    st.info("Diese Seite dient nur für die Installation der Prototypen. Es ist noch nicht der Stand, der in der Studie verwendet wird. " +
            "Die offizielle Download Page findet man hier: [https://totp-study.informatik.tu-freiberg.de/?page=download](https://totp-study.informatik.tu-freiberg.de/?page=download)")

    st.markdown("Diese Anleitung hilft Ihnen, Blue TOTP auf Ihrem Windows PC und auf Ihrem Android Smartphone zu installieren.")
    st.subheader("Voraussetzungen")
    if not is_windows:
        _not_windows_message()
    st.markdown(
        f"""
        - bluetoothfähiger Windows PC + [Chrome Browser]({link_chrome_download})
        - Android Smartphone
        """    
    )
    st.markdown("---")

    st.subheader("Installation (Android)")
    st.markdown("1. Laden Sie folgende .apk Datei **MIT IHREM SMARTPHONE** herunter, oder kopieren Sie die Datei nach dem Download auf Ihr Smartphone:")
    cols = st.columns([1,35])
    with cols[1]:
        with open("volume/download/app.apk", "rb") as file:
            st.download_button(
                label="Blue TOTP App herunterladen",
                file_name="Blue TOTP App.apk",
                data=file,
                mime="application/octet-stream"
            )
    st.markdown("Auf Ihrem Smartphone:")
    st.markdown(f"""
        2. Öffnen Sie einen File Manager.
        3. Navigieren Sie zu dem Ort an dem Sie die .apk-Datei gespeichert haben.
        4. Tippen Sie auf die .apk-Datei und öffnen Sie anschließend die App. Ggf. müssen Sie dem File Manager die Erlaubnis geben, die APK zu installieren.
        5. Ignorieren Sie das Onboarding in der App. Die weiteren Schritte auf dieser Website, erklären Ihnen was zu tun ist.
        6. Geben Sie der App alle Berechtigungen, die Sie erfragt. Andernfalls müssen Sie die Berechtigungen händisch der App zuweisen oder die App erneut installieren. 
    """)
    st.markdown("---")

    st.subheader("Installation Blue TOTP Service")
    st.markdown(f"""
        1. Führen Sie die folgenden Schritte nur auf einem Windows PC aus.
        2. Laden Sie das Programm **_Blue TOTP Service_** herunter, installieren und starten Sie es.
        """
    )
    cols = st.columns([1,35])
    with cols[1]:
        _download_button_blue_totp_service()
    st.markdown("3. Ignorieren Sie auch hier das Onboarding.")
    st.markdown("---")

    st.subheader("Installation Blue TOTP Chrome Extension")
    st.markdown("1. Laden Sie die Blue TOTP Extension herunter.")
    cols = st.columns([1,35])
    with cols[1]:
        with open("volume/download/ext.zip", "rb") as file:
            st.download_button(
                label="Blue TOTP Chrome Extension herunterladen",
                file_name="Blue TOTP Chrome Extension.zip",
                data=file,
                mime="application/zip"
            )

    st.markdown(f"""
        2. Entpacken Sie `totp-ext.zip`.
        3. Öffnen Sie Ihren Chrome Browser und besuchen sie folgende URL: `chrome://extensions`
        4. Aktivieren Sie rechts oben den **Entwicklermodus**. 
        5. Klicken Sie auf **Entpackte Erweiterung laden** und wählen Sie `totp-ext`. Evtl. müssen Sie für den folgenden Schritt nun den Chrome Browser neu starten.
        6. Drücken Sie den **Erweiterungen**-Button in Chrome (Puzzle-Symbol in der rechten oberen Ecke) und pinnen sie Blue TOTP an.
    """)

    exit(0)