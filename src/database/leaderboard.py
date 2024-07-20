import os

import firebase_admin
from database_errors import NullUserError
from dotenv import load_dotenv
from firebase_admin import db
from user import User

load_dotenv('.env')
class LeaderboardDatabase:
    '''Manage the leaderbaord part of the database.'''

    def __init__(self) -> None:
        self._cred_obj = cred_obj = firebase_admin.credentials.Certificate(os.environ["CERT_PATH"])
        self._default_app = firebase_admin.initialize_app(
            cred_obj,
            {
                "databaseURL": "https://pure-pulsars-default-rtdb.firebaseio.com/",
            },
        )
        self._ref = db.reference("/leaderboard")
        self._leaderboard_dict = self._ref.child('leaderboard').get()
    def add_user_to_leaderboard(self, user: User) -> dict:
        '''Add a user to the leaderbaord.'''
        amount_of_users = self._ref.child('amount_of_users').get()
        self._leaderboard_dict = self._ref.child('leaderboard').get()
        self._leaderboard_dict = dict(self._leaderboard_dict)
        self._leaderboard_dict[user] = {"score" : 0, "place" : 0 }
        self._leaderboard = self._ref.child('leaderboard')
        self._leaderboard.set(self._leaderboard_dict)
        self._ref.child('amount_of_users').set(amount_of_users+1)
        return self._leaderboard_dict
    def get_leaderboard(self) -> dict:
        '''Return the leaderboard as a dictionary.'''
        return self._leaderboard_dict
    def get_user(self, user : str) -> tuple:
        '''Get a user's leader board data.'''
        try:
            return self.get_leaderboard()[user]
        except KeyError as e:
            raise NullUserError from e

