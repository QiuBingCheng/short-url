
from flask import session
from enum import Enum


class CurrentUserManager():

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CurrentUserManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Initialization method, called only if the instance hasn't been initialized before
        if not self._initialized:
            self._initialized = True

    def set_user_model(self, user_model):
        self.User = user_model

    def login(self, user_id):
        session["user_id"] = user_id

    def logout(self):
        session.pop('user_id', None)

    def _get_current_user(self):
        # Retrieve the current user from the session user_id and the User model
        user_id = session.get("user_id")
        return self.User.query.get(user_id) if user_id is not None else None

    def _get_current_user_type(self):
        # Determine the client type based on the current user's login and authentication status
        user = self._get_current_user()

        if user:
            is_logged_in = True
            is_authenticated = user.is_authenticated
        else:
            is_logged_in = False
            is_authenticated = False

        return ClientTypeChecker.get_client_type(is_logged_in, is_authenticated)

    @property
    def user(self):
        return self._get_current_user()

    @property
    def user_type(self):
        return self._get_current_user_type()


class ClientType(Enum):
    VISITOR = 'VISITOR'
    UNVERIFIED_MEMBER = 'UNVERIFIED_MEMBER'
    VERIFIED_MEMBER = 'VERIFIED_MEMBER'


class ClientTypeChecker:
    @staticmethod
    def get_client_type(is_logged_in, has_verified_email):
        """
        Determine the client's type.

        Parameters:
            is_logged_in (bool): Whether the cient is logged in.
            has_verified_email (bool): Whether the client has verified the email.

        Returns:
            ClientType: Enumeration representing the customer type.
        """
        if not is_logged_in:
            return ClientType.VISITOR
        elif not has_verified_email:
            return ClientType.UNVERIFIED_MEMBER
        else:
            return ClientType.VERIFIED_MEMBER
