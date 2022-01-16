import pytest
from bbreplay import Peekable, TeamType
from bbreplay.player import Player
from bbreplay.state import GameState
from bbreplay.teams import Team


class iter_(Peekable):
    def __init__(self, generator):
        super().__init__(generator)
        self.__i = 0

    def next(self):
        datum = super().next()
        print(f"\tConsuming {type(datum).__name__} {self.__i}: {datum}")
        self.__i += 1
        return datum


@pytest.fixture
def home_player_1():
    return Player(1, "Player1H", 4, 4, 4, 4, 1, 0, 40000, [])


@pytest.fixture
def home_player_2():
    return Player(2, "Player2H", 4, 4, 4, 4, 1, 0, 40000, [])


@pytest.fixture
def home_player_3():
    return Player(3, "Player3H", 4, 4, 4, 4, 1, 0, 40000, [])


@pytest.fixture
def home_team(home_player_1, home_player_2, home_player_3):
    home_team = Team("Home Halflings", "Halfling", 40000, 3, 3, 0, TeamType.HOME)
    home_team.add_player(0, home_player_1)
    home_team.add_player(1, home_player_2)
    home_team.add_player(2, home_player_3)
    return home_team


@pytest.fixture
def away_player_1():
    return Player(1, "Player1A", 4, 4, 4, 4, 1, 0, 40000, [])


@pytest.fixture
def away_team(away_player_1):
    away_team = Team("Away Amazons", "Amazons", 40000, 3, 3, 0, TeamType.AWAY)
    away_team.add_player(0, away_player_1)
    return away_team


@pytest.fixture
def board(home_team, away_team):
    gamestate = GameState(home_team, away_team, TeamType.HOME)
    gamestate.kickoff()
    return gamestate
