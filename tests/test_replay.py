from itertools import zip_longest
import pytest
from bbreplay import TeamType, Position
from bbreplay.command import *
from bbreplay.player import Player
from bbreplay.replay import *
from bbreplay.state import GameState
from bbreplay.teams import Team


@pytest.fixture
def home_player_1():
    return Player(1, "Player1H", 4, 4, 4, 4, 1, 0, 40000, [])


@pytest.fixture
def home_team(home_player_1):
    home_team = Team("Home Halflings", "Halfling", 40000, 3, 3, TeamType.HOME)
    home_team.add_player(0, home_player_1)
    return home_team


@pytest.fixture
def away_player_1():
    return Player(1, "Player1A", 4, 4, 4, 4, 1, 0, 40000, [])


@pytest.fixture
def away_team(away_player_1):
    away_team = Team("Away Amazons", "Amazons", 40000, 3, 3, TeamType.AWAY)
    away_team.add_player(0, away_player_1)
    return away_team


@pytest.fixture
def board(home_team, away_team):
    return GameState(home_team, away_team, home_team)


def test_single_movement(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(0, 0), player)
    cmd = EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 1, 1])
    events = list(replay._process_movement(player, cmd, [], None, None, board))
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, Movement)
    assert event.source_space == Position(0, 0)
    assert event.target_space == Position(1, 1)
    assert player.position == Position(1, 1)


def test_multi_movement(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(0, 0), player)
    cmds = [
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 1, 1]),
        MovementCommand(1, 1, TeamType.HOME.value, 1, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 2, 2]),
        MovementCommand(1, 1, TeamType.HOME.value, 2, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 3, 1]),
        EndMovementCommand(1, 1, TeamType.HOME.value, 3, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 2, 0])
    ]
    positions = [Position(0, 0), Position(1, 1), Position(2, 2), Position(3, 1), Position(2, 0)]
    events = replay._process_movement(player, cmds[0], (cmd for cmd in cmds[1:]), None, None, board)
    for event, expected_start, expected_end in zip_longest(events, positions[:-1], positions[1:], fillvalue=None):
        assert isinstance(event, Movement)
        assert event.source_space == expected_start
        assert event.target_space == expected_end
        assert player.position == expected_end


def test_going_for_it_success(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(0, 0), player)
    cmds = [
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 1, 1]),
        MovementCommand(1, 1, TeamType.HOME.value, 1, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 2, 2]),
        MovementCommand(1, 1, TeamType.HOME.value, 2, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 3, 1]),
        MovementCommand(1, 1, TeamType.HOME.value, 3, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 2, 0]),
        EndMovementCommand(1, 1, TeamType.HOME.value, 4, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 3, 0])
    ]
    log_entries = [
        GoingForItEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.SUCCESS.name)
    ]
    positions = [Position(0, 0), Position(1, 1), Position(2, 2), Position(3, 1), Position(2, 0), Position(3, 0)]
    events = replay._process_movement(player, cmds[0], (cmd for cmd in cmds[1:]), iter(log_entries), None, board)
    move = 0
    for seq, event in enumerate(events):
        expected_start = positions[move]
        expected_end = positions[move + 1]
        if seq == 4:
            assert isinstance(event, Action)
            assert event.action == ActionType.GOING_FOR_IT
            assert event.result == ActionResult.SUCCESS
        else:
            assert isinstance(event, Movement)
            assert event.source_space == expected_start
            assert event.target_space == expected_end
            assert player.position == expected_end
            move += 1


def test_going_for_it_fail_no_reroll(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(0, 0), player)
    cmds = [
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 1, 1]),
        MovementCommand(1, 1, TeamType.HOME.value, 1, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 2, 2]),
        MovementCommand(1, 1, TeamType.HOME.value, 2, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 3, 1]),
        MovementCommand(1, 1, TeamType.HOME.value, 3, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 2, 0]),
        EndMovementCommand(1, 1, TeamType.HOME.value, 4, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 3, 0])
    ]
    log_entries = [
        GoingForItEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        ArmourValueRollEntry(TeamType.HOME, player.number, "9+", "2", ActionResult.FAILURE.name),
        TurnOverEntry(TeamType.HOME, "Knocked Down!")
    ]
    positions = [Position(0, 0), Position(1, 1), Position(2, 2), Position(3, 1), Position(2, 0), Position(3, 0)]
    events = replay._process_movement(player, cmds[0], (cmd for cmd in cmds[1:]), iter(log_entries), None, board)
    end_move = Position(2, 0)
    move = 0
    for seq, event in enumerate(events):
        expected_start = positions[move]
        expected_end = positions[move + 1]
        if seq == 4:
            assert isinstance(event, Action)
            assert event.action == ActionType.GOING_FOR_IT
            assert event.result == ActionResult.FAILURE
        elif seq == 5:
            assert isinstance(event, FailedMovement)
            assert event.source_space == expected_start
            assert event.target_space == expected_end
            assert player.position == end_move
            assert board.is_prone(player)
            move += 1
        else:
            assert isinstance(event, Movement)
            assert event.source_space == expected_start
            assert event.target_space == expected_end
            assert player.position == expected_end
            move += 1
