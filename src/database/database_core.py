"""Core funcitonaliry for interactions with the scoring database."""

import os
from typing import ClassVar, Literal

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import db

from .user import UserController

if load_dotenv(".env"):
    ...
else:
    load_dotenv("docker.env")


class NullUserError(TypeError):
    """User Doesn't exist in firebase database."""

    def __init__(self) -> None:
        super().__init__("User doesn't exist")


class DatabaseController:
    """Class to interact with the user section of the Database."""

    SERVER_LIST: ClassVar = []

    def __init__(
        self,
    ) -> None:
        self._cred_obj = cred_obj = firebase_admin.credentials.Certificate(os.environ["CERT_PATH"])
        self._default_app = firebase_admin.initialize_app(
            cred_obj,
            {
                "databaseURL": "https://pure-pulsars-default-rtdb.firebaseio.com/",
            },
        )
        self.SERVER_LIST = self.get_all_servers()

    async def add_user(
        self,
        user_id: int,
        user: UserController,
        guild_id: int,
    ) -> None:
        """Add a user to the database using ref.set.

        Args:
        ----
        user_id (int): The user's id.
        user (UserController): The user object.
        guild_id (int): The guild id.

        """
        database_user = await self.conn(guild_id, user_id)
        _new_user = user.to_dictionary()
        database_user.set(_new_user)

    async def update_value_for_user(
        self,
        guild_id: int,
        user_id: str,
        value: int,
        key: Literal["last_played", "score", "times_played", "wins", "failure"],
    ) -> None:
        """Update the specified value for the specified user.

        Args:
        ----
        guild_id (int): The guild id.
        user_id (str): The user id.
        value (int): The updated score.
        key (Literal["last_played", "score", "times_played", "wins", "failure"]): The key to update.

        Raises:
        ------
        NullUserError: If the user doesn't exist.

        """
        """self._ref = db.reference("/users")"""
        database_user = await self.conn(guild_id, user_id)
        if database_user.get():
            database_user.update({key: value})
            return
        raise NullUserError

    async def get_user(self, guild_id: int, user_id: int) -> dict[str, int | str]:
        """Return a user's information as a dict.

        Args:
        ----
        guild_id (int): The guild id.
        user_id (int): The user id.

        Returns:
        -------
        dict[str, int | str]: The user's information.

        Raises:
        ------
        NullUserError: If the user doesn't exist.

        """
        database_user = await self.conn(guild_id, user_id)
        if database_user.get():
            return database_user.get()
        raise NullUserError

    async def get_server(self, guild_id: int) -> dict:
        """Get server information as a dict.

        Args:
        ----
        guild_id (int): The guild id.

        Returns:
        -------
        dict: The server information.

        """
        """Get the specified server."""
        _ref = db.reference(f"/server/{guild_id}/")
        return _ref.get()

    async def get_all_servers(self) -> list:
        """Return all servers' information as a list."""
        return db.reference("/server/").get()

    async def conn(self, guild_id: int, user_id: int) -> db.Reference:
        """Return a connection to the db, for specific guilds/users.

        Args:
        ----
        guild_id (int): The guild id.
        user_id (int): The user id.

        Returns:
        -------
        db.Reference: The reference to the user.

        """
        _ref = db.reference(f"/server/{guild_id}/")
        return _ref.child(str(user_id))


# Pre-instantiated controller object.
DATA = DatabaseController()
