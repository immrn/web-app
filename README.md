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
