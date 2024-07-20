class User:
    """The Basic User Class."""

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        last_played: int,
        score: int,
        times_played: int,
        wins: int,
        failure: int,
    ) -> None:
        self.name = name
        self.last_played = last_played
        self.score = score
        self.times_played = times_played
        self.wins = wins
        self.failure = failure

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
