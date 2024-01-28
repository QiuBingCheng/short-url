from functools import wraps
from flask import redirect, url_for, request
from app import user_manager
from app.lib.user_manager import ClientType


def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        # Check if the user is logged in
        if user_manager.user_type == ClientType.VISITOR:
            # Redirect to the login page if not logged in
            login_url = url_for('member.login', next=request.path)
            return redirect(login_url)

        # If logged in, proceed with the route function
        return route_function(*args, **kwargs)

    return wrapper
