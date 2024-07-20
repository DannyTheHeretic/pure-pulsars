import firebase_admin
from dotenv import load_dotenv
from firebase_admin import db

from database.database_errors import NullUserError

load_dotenv(".env")


class LeaderboardDatabase:
    """Manage the leaderbaords."""

    def __init__(self) -> None:
        self._cred_obj = cred_obj = firebase_admin.credentials.Certificate(
            "pure-pulsars-firebase-adminsdk-e6qzr-9b1c9a771d.json"
        )
        self._default_app = firebase_admin.initialize_app(
            cred_obj,
            {
                "databaseURL": "https://pure-pulsars-default-rtdb.firebaseio.com/",
            },
        )
        self._ref = db.reference("/leaderboard")
        self._leaderboard_dict_global = self._ref.child("leaderboard").get()

    def _add_user_to_leaderboard(
        self, user_id: int, leaderboard_id: str
    ) -> dict:  # leave leaderboard id blank to go to global leaderboard
        self._ref = db.reference(f"/leaderboard/{leaderboard_id}")
        amount_of_users = self._ref.child("amount_of_users").get()
        self._leaderboard_dict = self._ref.child("leaderboard").get()
        self._leaderboard_dict = dict(self._leaderboard_dict)
        self._leaderboard_dict[user_id] = {"score": 0, "place": amount_of_users + 1}
        self._leaderboard = self._ref.child("leaderboard")
        self._leaderboard.set(self._leaderboard_dict)
        self._ref.child("amount_of_users").set(amount_of_users + 1)
        return self._leaderboard_dict

    def get_leaderboard_global(self) -> dict:
        """Return the global leaderboard as a dictionary."""
        return self._leaderboard_dict_global

    def get_user_global(self, user: str) -> tuple:
        """Get a user's global leaderboard data."""
        try:
            return self.get_leaderboard()[user]
        except KeyError as e:
            raise NullUserError from e

    """def add_guild(self, guild_id, members):
        pass
    def update_placement(self, userID):
        pass"""
