import os
from typing import Literal

import dotenv
import firebase_admin
from database_errors import NullUserError
from firebase_admin import db
from user import User

dotenv.load_dotenv(".env")


class UserDatabase:
    """Class to interact with the user section of the Database."""

    def __init__(self) -> None:
        self._cred_obj = cred_obj = firebase_admin.credentials.Certificate(os.environ["CERT_PATH"])
        self._default_app = firebase_admin.initialize_app(
            cred_obj,
            {
                "databaseURL": "https://pure-pulsars-default-rtdb.firebaseio.com/",
            },
        )
        self._ref = db.reference("/")

    def add_user(self, username: str) -> None:
        """Add a user to the database using ref.set."""
        self._ref = db.reference(f"/users/{username}")
        # TODO: FIGURE OUT WHETHER IT WOULD BE BETTER TO STORE LEADERBOARD
        # LENGTH IN THE DATABSE OR SORT LEADERBOARD AT RUNTIME
        self._new_user = User(username, 0, 0, 0, 0, 0).to_dictionary()
        self._ref.set(self._new_user)


    def update_value_for_user(
        self,
        value: int,
        user: str,
        key: Literal["name", "leaderboard_position", "score", "times_played", "wins", "failure"],
    ) -> None:
        """Update the specified value for the specified user."""
        self._ref = db.reference("/users")
        database_user = self._ref.child(user)
        if type(value) is not int:
            message = "Value should be a int"
            raise TypeError(message)
        if database_user.get():
            database_user.update({key: value})
        raise NullUserError

    def get_user(self, user: str) -> dict:
        """Return a user a dict."""
        self._ref = db.reference("/users")
        database_user = self._ref.child(user)
        if database_user.get():
            return database_user.get()
        raise NullUserError



u = UserDatabase()

