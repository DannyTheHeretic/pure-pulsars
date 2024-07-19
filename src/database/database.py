import os

import dotenv
import firebase_admin
from database_errors import *
from firebase_admin import db

dotenv.load_dotenv(".env")


class UserDatabase:
    def __init__(self) -> None:
        self._cred_obj = cred_obj = firebase_admin.credentials.Certificate(os.environ["CERT_PATH"])
        self._default_app = firebase_admin.initialize_app(cred_obj, {
	"databaseURL": "https://pure-pulsars-default-rtdb.firebaseio.com/",
	})
        self._ref = db.reference("/")
    def add_user(self, username : str) -> None:
        """Adds a user to the database using ref.set"""
        self._ref = db.reference(f"/users/{username}")
        # TODO: FIGURE OUT WHETHER IT WOULD BE BETTER TO STORE LEADERBOARD LENGTH IN THE DATABSE OR SORT LEADERBOARD AT RUNTIME
        self._new_user = {"score":0, "place_on_leaderboard" : 0}
        self._ref.set(self._new_user)
    def update_value(self, amount : int, user: str) -> None:
        """Updates a users score"""
        self._ref = db.reference("/users")
        database_user = self._ref.child(user)
        if database_user.get():
            database_user.update({"score" : database_user.get()["score"] + amount})
        else:
            raise NullUserError("User doesn't exist")


u = UserDatabase()




