from collections.abc import Iterable


class User:
    def __init__(self, name, leaderboard_position, score, times_played, wins, failure) -> None:
        self.name = name
        self.leaderboard_position = leaderboard_position
        self.score = score
        self.times_played = times_played 
        self.wins = wins
        self.failure = failure
    def to_dictionary(self):
        return {
            'name' : self.name,
            'leaderboard_position' : self.leaderboard_position,
            'score' : self.score,
            'times_played' : self.times_played,
            'wins' : self.wins,
            'failure' : self.failure
        }