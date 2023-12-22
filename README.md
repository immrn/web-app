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

```bash
streamlit run main.py
```

## Remote
-  https://totp-study.informatik.tu-freiberg.de
- `$ ssh root@docker2.xsitepool.tu-freiberg.de -p2222`
- `$ export PRODUCTION="True"`
- `$ cron` to start the cron process (when you are using a docker container, otherwise add cron to your init daemon)
- copy the content of `web-app/scripts/crontab` into the editor opened by the command `crontab -e`
- `$ git clone https://github.com/immrn/web-app.git`
- `$ sh setup.sh`
- start or resume to a screen and run the web app:
- screen:
    - `$ screen -S SESSION_NAME` create session
    - `$ screen -ls` list sessions
    - `$ screen -d ID` or `CTRL + A + D` detach from session
    - `$ screen -r ID` resume to screen
- `$ . ./venv/bin/activate`
- `$ streamlit run main.py --server.port=443 --server.address=0.0.0.0`

- copy files: `scp -P 2222 volume/download/app.apk root@docker2.xsitepool.tu-freiberg.de:/share/volume/download`

- 443 und 80 werden aktuell via 6001 und 6002 nach außen geroutet
- `/share` is persistent


## Management
### Remove a user:
`$ python scripts/rm_user.py USER_ID` will remove the user from `user_info.csv` and `transactions/USER_ID.csv`