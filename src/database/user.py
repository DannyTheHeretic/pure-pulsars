"""User information classes for the database."""

from typing import NamedTuple


class _User(NamedTuple):
    """User NamedTuple."""

    name: str = ""
    last_played: int = 0
    score: int = 0
    times_played: int = 0
    wins: int = 0
    failure: int = 0


class UserController:
    """The Basic User Class."""

    def __init__(self, info: _User) -> None:
        """Initialize the User Class.

        Args:
        ----
        info (_User): The user information.

        Notes:
        -----
        User information is stored as a NamedTuple. See _User for more
        information on what names are expected.

        """
        self.name = info.name
        self.last_played = info.last_played
        self.score = info.score
        self.times_played = info.times_played
        self.wins = info.wins
        self.failure = info.failure

    def to_dictionary(self) -> dict:
        """Return user as a Dictionary."""
        return {
            "name": self.name,
            "last_played": self.last_played,
            "score": self.score,
            "times_played": self.times_played,
            "wins": self.wins,
            "failure": self.failure,
        }
