import pytest
from bbreplay import TeamType
from bbreplay.log import *
from bbreplay.command import *
from bbreplay.player import Player
from bbreplay.replay import *
from bbreplay.state import GameState
from bbreplay.teams import Team


def iter_(iterable):
    for item in iterable:
        print(f"Consuming {type(item).__module__}.{item}")
        yield item


@pytest.fixture
def home_player_1():
    return Player(1, "Player1H", 4, 4, 4, 4, 1, 0, 40000, [])


@pytest.fixture
def home_team(home_player_1):
    home_team = Team("Home Halflings", "Halfling", 40000, 3, 3, 0, TeamType.HOME)
    home_team.add_player(0, home_player_1)
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
    for _ in gamestate.kickoff():
        pass
    return gamestate


def test_leader_reroll_added_once_per_half(board):
    home_team, _ = board.teams
    player = home_team.get_player(0)
    player.skills.append(Skills.LEADER)
    board.set_position(Position(1, 1), player)
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 4
    [x for x in board.kickoff()]
    board.touchdown(player)
    [x for x in board.end_turn(TeamType.HOME, "reason")]
    board.prepare_setup()
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 4


def test_leader_reroll_not_added_when_not_used_and_player_not_deployed(board):
    home_team, _ = board.teams
    player = home_team.get_player(0)
    player.skills.append(Skills.LEADER)
    board.set_position(Position(1, 1), player)
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 4
    [x for x in board.kickoff()]
    board.touchdown(player)
    [x for x in board.end_turn(TeamType.HOME, "reason")]
    board.prepare_setup()
    board.set_position(OFF_PITCH_POSITION, player)
    board.setup_complete()
    assert not board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 3


def test_leader_reroll_not_readded_after_use(board):
    home_team, _ = board.teams
    player = home_team.get_player(0)
    player.skills.append(Skills.LEADER)
    board.set_position(Position(1, 1), player)
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 4
    [x for x in board.kickoff()]
    board.use_leader_reroll(TeamType.HOME, player)
    board.touchdown(player)
    [x for x in board.end_turn(TeamType.HOME, "reason")]
    board.prepare_setup()
    board.setup_complete()
    assert not board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 3


def test_leader_reroll_readded_in_second_half(board):
    home_team, _ = board.teams
    player = home_team.get_player(0)
    player.skills.append(Skills.LEADER)
    board.set_position(Position(1, 1), player)
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 4
    [x for x in board.kickoff()]
    [x for x in board.end_turn(TeamType.HOME, "reason")]
    [x for x in board.start_turn(TeamType.AWAY)]
    [x for x in board.end_turn(TeamType.AWAY, "reason")]
    # And the other seven turns
    for _ in range(7):
        for team_type in [TeamType.HOME, TeamType.AWAY]:
            [x for x in board.start_turn(team_type)]
            [x for x in board.end_turn(team_type, "reason")]
    board.halftime()
    board.prepare_setup()
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 4
