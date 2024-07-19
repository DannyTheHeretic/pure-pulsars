class User: #noqa: D101
    def __init__( #noqa: PLR0913
        self, name: str, leaderboard_position: int, score: int, times_played: int, wins: int, failure: int,
    ) -> None:
        self.name = name
        self.leaderboard_position = leaderboard_position
        self.score = score
        self.times_played = times_played
        self.wins = wins
        self.failure = failure

    def to_dictionary(self) -> dict:
        """Convert it to a dictionary."""
        return {
            "name": self.name,
            "leaderboard_position": self.leaderboard_position,
            "score": self.score,
            "times_played": self.times_played,
            "wins": self.wins,
            "failure": self.failure,
        }
