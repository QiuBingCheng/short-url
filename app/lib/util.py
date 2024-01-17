from app import app
from datetime import timedelta, timezone


USERNAME = app.config["USERNAME"]
PASSWORD = app.config["PASSWORD"]


# %%

def make_short_url(code):
    return f"{app.config['HOST']}/{code}"


def make_tracing_url(code):
    return f"{app.config['HOST']}/trace/{code}"

# %%


def date_str(created_time):
    return created_time.astimezone(timezone(timedelta(hours=8))
                                   ).strftime('%Y-%m-%d %H:%M:%S')


def is_admin(username: str, password: str):
    print(username, password)
    print(USERNAME, PASSWORD)
    return username == USERNAME and password == PASSWORD
