# web-app

## Prerequisites
- install Python 3.11
- if using linux maybe you need to install python3.11-venv

## Setup & Execution (using bash)

On Windows `./venv/bin` should be `./venv/Scripts`

```bash
python3.11 -m venv venv
. ./venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

TODO Email account installation


```bash
streamlit run main.py
```

## Remote
-  https://totp-study.informatik.tu-freiberg.de
- `$ ssh root@docker2.xsitepool.tu-freiberg.de -p2222`
- `$ export PRODUCTION="True"`
- `$ git clone https://github.com/immrn/web-app.git`
- `$ sh setup.sh`
- `$ . ./venv/bin/activate`
- `$ streamlit run main.py --server.port=443 --server.address=0.0.0.0`
- 443 und 80 werden aktuell via 6001 und 6002 nach außen geroutet
- `/share` ist persistent
- screen:
    - `$ screen -S SESSION_NAME` create session
    - `$ screen -ls` list sessions
    - `$ screen -d ID` or `CTRL + A + D` detach from session
    - `$ screen -r ID` resume to screen

## Management
### Remove a user:
`$ python scripts/rm_user.py USER_ID` will remove the user from `user_info.csv` and `transactions/USER_ID.csv`