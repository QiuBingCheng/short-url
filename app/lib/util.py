from app import app


def make_short_url(code):
    return f"{app.config['HOST']}/{code}"


def make_tracing_url(code):
    return f"{app.config['HOST']}/trace/{code}"
