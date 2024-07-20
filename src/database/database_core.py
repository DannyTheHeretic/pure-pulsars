import os
from typing import ClassVar, Literal

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import db

from .user import User

load_dotenv(".env")


class NullUserError(TypeError):
    """User Doesn't exist in firebase database."""

    def __init__(self) -> None:
        super().__init__("User doesn't exist")


class Database:
    """Class to interact with the user section of the Database."""

    SERVER_LIST: ClassVar = []

    def __init__(
        self,
        ref: int = 0,
    ) -> None:
        self._cred_obj = cred_obj = firebase_admin.credentials.Certificate(os.environ["CERT_PATH"])
        self._default_app = firebase_admin.initialize_app(
            cred_obj,
            {
                "databaseURL": "https://pure-pulsars-default-rtdb.firebaseio.com/",
            },
        )
        if ref:
            self._ref = db.reference(f"/server/{ref}/")
        else:
            self._ref = db.reference("/leaderboard/")

        self.SERVER_LIST = self.get_all_servers()

    def add_user(
        self,
        user_id: int,
        user: User,
    ) -> None:
        """Add a user to the database using ref.set."""
        _ref_user = self._ref.child(f"{user_id}")
        _new_user = user.to_dictionary()
        _ref_user.set(_new_user)

    def update_value_for_user(
        self,
        user_id: str,
        value: int,
        key: Literal["last_played", "score", "times_played", "wins", "failure"],
    ) -> None:
        """Update the specified value for the specified user."""
        """self._ref = db.reference("/users")"""
        database_user = self._ref.child(str(user_id))
        if database_user.get():
            database_user.update({key: value})
            return
        raise NullUserError

    def get_user(self, user_id: str) -> dict:
        """Return a user a dict."""
        database_user = self._ref.child(str(user_id))
        if database_user.get():
            return database_user.get()
        raise NullUserError

    def get_server(self) -> dict:
        """Get the specified server."""
        return self._ref.get()

    def get_all_servers(self) -> list:
        """Return all servers."""
        return db.reference("/server/").get()
