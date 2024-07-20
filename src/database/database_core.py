import os
from typing import ClassVar, Literal

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import db

from .database_errors import NullUserError
from .user import User

load_dotenv(".env")


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

    def add_user(  # noqa: PLR0913
        self,
        username: str,
        user_id: int,
        leaderboard_position: int = 0,
        score: int = 0,
        times_played: int = 0,
        wins: int = 0,
        failure: int = 0,
    ) -> None:
        """Add a user to the database using ref.set."""
        self._ref_user = self._ref.child(f"{user_id}")
        self._new_user = User(username, leaderboard_position, score, times_played, wins, failure).to_dictionary()
        self._ref_user.set(self._new_user)

    def update_value_for_user(
        self,
        user_id: str,
        value: int,
        key: Literal["leaderboard_position", "score", "times_played", "wins", "failure"],
    ) -> None:
        """Update the specified value for the specified user."""
        """self._ref = db.reference("/users")"""
        print(user_id)
        database_user = self._ref.child(str(user_id))
        print(database_user)
        if type(value) is not int:
            message = "Value should be a int"
            raise TypeError(message)
        if database_user.get():
            database_user.update({key: value})
            return
        raise NullUserError

    def get_user(self, user_id: str) -> dict:
        """Return a user a dict."""
        """self._ref = db.reference("/users")"""
        database_user = self._ref.child(str(user_id))
        if database_user.get():
            return database_user.get()
        raise NullUserError

    def get_all_servers(self) -> list:
        """Return all servers."""
        return db.reference("/server/").get()


"""
data = Database(ref=1262497899925995563)
data.add_user("lotus.css", "713130676387315772")
print(data.get_user("713130676387315772"))
print(data.get_all_server_ids())
print(data.get_all_user_ids())
"""
