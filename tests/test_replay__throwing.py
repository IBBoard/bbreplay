import pytest
from bbreplay import ScatterDirection, TeamType, Position
from bbreplay import player
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
def home_player_2():
    return Player(2, "Player2H", 4, 4, 4, 4, 1, 0, 40000, [])


@pytest.fixture
def home_team(home_player_1, home_player_2):
    home_team = Team("Home Halflings", "Halfling", 40000, 3, 3, 0, TeamType.HOME)
    home_team.add_player(0, home_player_1)
    home_team.add_player(1, home_player_2)
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


def test_handoff_forward_success(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    board.set_position(Position(6, 7), player_1)
    player_2 = home_team.get_player(1)
    board.set_position(Position(7, 7), player_2)
    board.set_ball_carrier(player_1)
    cmds = [
        # TargetPlayerCommand was already consumed in the main turn processing loop
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7])
    ]
    log_entries = [
        CatchEntry(TeamType.HOME, 2, "3+", "6", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw(player_1, player_2, cmds_iter, log_entries_iter, None, board)

    event = next(events)
    assert isinstance(event, Handoff)
    assert event.player == player_1
    assert event.target == player_2

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_2
    assert event.action == ActionType.CATCH
    assert event.result == ActionResult.SUCCESS

    assert board.get_ball_carrier() == player_2
    assert board.get_ball_position() == Position(7, 7)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_handoff_sideways_success(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    board.set_position(Position(6, 7), player_1)
    player_2 = home_team.get_player(1)
    board.set_position(Position(6, 6), player_2)
    board.set_ball_carrier(player_1)
    cmds = [
        # TargetPlayerCommand was already consumed in the main turn processing loop
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 6])
    ]
    log_entries = [
        CatchEntry(TeamType.HOME, 2, "3+", "6", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw(player_1, player_2, cmds_iter, log_entries_iter, None, board)

    event = next(events)
    assert isinstance(event, Handoff)
    assert event.player == player_1
    assert event.target == player_2

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_2
    assert event.action == ActionType.CATCH
    assert event.result == ActionResult.SUCCESS

    assert board.get_ball_carrier() == player_2
    assert board.get_ball_position() == Position(6, 6)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_handoff_diagonal_success(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    board.set_position(Position(6, 6), player_1)
    player_2 = home_team.get_player(1)
    board.set_position(Position(7, 7), player_2)
    board.set_ball_carrier(player_1)
    cmds = [
        # TargetPlayerCommand was already consumed in the main turn processing loop
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7])
    ]
    log_entries = [
        CatchEntry(TeamType.HOME, 2, "3+", "6", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw(player_1, player_2, cmds_iter, log_entries_iter, None, board)

    event = next(events)
    assert isinstance(event, Handoff)
    assert event.player == player_1
    assert event.target == player_2

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_2
    assert event.action == ActionType.CATCH
    assert event.result == ActionResult.SUCCESS

    assert board.get_ball_carrier() == player_2
    assert board.get_ball_position() == Position(7, 7)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)
