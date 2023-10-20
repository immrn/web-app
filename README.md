# web-app

## Prerequisites
- install Python 3.11
- if using linux maybe you need to install python3.11-venv

## Setup & Execution (using bash)
```bash
python3.11 -m venv venv
. ./venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

On Windows `./venv/bin` should be `./venv/Scripts` 

```bash
streamlit run main.py
```

## Remote
-  https://totp-study.informatik.tu-freiberg.de
- `$ ssh root@docker2.xsitepool.tu-freiberg.de -p2222`
- run `./setup.sh`
- 443 und 80 werden aktuell via 6001 und 6002 nach außen geroutet
- `/share` ist persistent
- `streamlit run main.py --server.port 6001`
- python3 -m http.server 6001