from itertools import zip_longest
import pytest
from bbreplay import TeamType, Position
from bbreplay.command import *
from bbreplay.player import Player
from bbreplay.replay import *
from bbreplay.state import GameState, EndTurn
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
    gamestate = GameState(home_team, away_team, TeamType.HOME)
    for _ in gamestate.kickoff():
        pass
    return gamestate


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
    events = replay._process_movement(player, cmds[0], iter_(cmds[1:]), None, None, board)
    end_move = Position(2, 0)
    for move in range(4):
        event = next(events)
        expected_start = positions[move]
        expected_end = positions[move + 1]
        assert isinstance(event, Movement)
        assert event.source_space == expected_start
        assert event.target_space == expected_end
        assert player.position == expected_end
    assert player.position == end_move
    assert not board.is_prone(player)
    assert not next(events, None)


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
    events = replay._process_movement(player, cmds[0], iter_(cmds[1:]), iter_(log_entries), None, board)
    end_move = Position(3, 0)

    for move in range(4):
        event = next(events)
        expected_start = positions[move]
        expected_end = positions[move + 1]
        assert isinstance(event, Movement)
        assert event.source_space == expected_start
        assert event.target_space == expected_end
        assert player.position == expected_end

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    move += 1
    expected_start = positions[move]
    expected_end = positions[move + 1]
    assert isinstance(event, Movement)
    assert event.source_space == expected_start
    assert event.target_space == expected_end

    assert player.position == end_move
    assert not board.is_prone(player)
    assert not next(events, None)


def test_going_for_it_fail_no_reroll(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(0, 0), player)
    home_id = TeamType.HOME.value
    cmds = [
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 1, 0, 0, 0, 0, 0, 1, 1]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 2, 0, 0, 0, 0, 0, 2, 2]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 3, 0, 0, 0, 0, 0, 3, 1]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 4, 0, 0, 0, 0, 0, 2, 0]),
        EndMovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 0, 0, 0, 0, 0, 0, 3, 0]),
        DeclineRerollCommand(1, 1, TeamType.HOME, 1, []),
        DiceChoiceCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 0])
    ]
    log_entries = [
        GoingForItEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        ArmourValueRollEntry(TeamType.HOME, player.number, "9+", "2", ActionResult.FAILURE.name),
        TurnOverEntry(TeamType.HOME, "Knocked Down!")
    ]
    positions = [Position(0, 0), Position(1, 1), Position(2, 2), Position(3, 1), Position(2, 0), Position(3, 0)]
    events = replay._process_movement(player, cmds[0], iter_(cmds[1:]), iter_(log_entries), None, board)
    end_move = Position(3, 0)

    for move in range(4):
        event = next(events)
        expected_start = positions[move]
        expected_end = positions[move + 1]
        assert isinstance(event, Movement)
        assert event.source_space == expected_start
        assert event.target_space == expected_end
        assert player.position == expected_end

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    move += 1
    expected_start = positions[move]
    expected_end = positions[move + 1]
    assert isinstance(event, FailedMovement)
    assert event.source_space == expected_start
    assert event.target_space == expected_end
    assert player.position == end_move
    assert board.is_prone(player)

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"


def test_going_for_it_fail_reroll(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(0, 0), player)
    home_id = TeamType.HOME.value
    cmds = [
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 1, 0, 0, 0, 0, 0, 1, 1]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 2, 0, 0, 0, 0, 0, 2, 2]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 3, 0, 0, 0, 0, 0, 3, 1]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 4, 0, 0, 0, 0, 0, 2, 0]),
        EndMovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 0, 0, 0, 0, 0, 0, 3, 0]),
        RerollCommand(1, 1, TeamType.HOME, 1, []),
        DiceChoiceCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 0])
    ]
    log_entries = [
        GoingForItEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        RerollEntry(TeamType.HOME),
        GoingForItEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        ArmourValueRollEntry(TeamType.HOME, player.number, "9+", "2", ActionResult.FAILURE.name),
        TurnOverEntry(TeamType.HOME, "Knocked Down!")
    ]
    positions = [Position(0, 0), Position(1, 1), Position(2, 2), Position(3, 1), Position(2, 0), Position(3, 0)]
    events = replay._process_movement(player, cmds[0], iter_(cmds[1:]), iter_(log_entries), None, board)
    end_move = Position(3, 0)

    for move in range(4):
        event = next(events)
        expected_start = positions[move]
        expected_end = positions[move + 1]
        assert isinstance(event, Movement)
        assert event == Movement(player, expected_start, expected_end, board)
        assert event.source_space == expected_start
        assert event.target_space == expected_end
        assert player.position == expected_end

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Reroll)
    assert event.team == player.team.team_type
    assert event.type == "Team Reroll"

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    move += 1
    expected_start = positions[move]
    expected_end = positions[move + 1]
    assert isinstance(event, FailedMovement)
    assert event.source_space == expected_start
    assert event.target_space == expected_end
    assert player.position == end_move
    assert board.is_prone(player)

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"


def test_going_for_it_fail_success_on_reroll(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(0, 0), player)
    home_id = TeamType.HOME.value
    cmds = [
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 1, 0, 0, 0, 0, 0, 1, 1]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 2, 0, 0, 0, 0, 0, 2, 2]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 3, 0, 0, 0, 0, 0, 3, 1]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 4, 0, 0, 0, 0, 0, 2, 0]),
        EndMovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 0, 0, 0, 0, 0, 0, 3, 0]),
        RerollCommand(1, 1, TeamType.HOME, 1, [])
    ]
    log_entries = [
        GoingForItEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        RerollEntry(TeamType.HOME),
        GoingForItEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.SUCCESS.name)
    ]
    positions = [Position(0, 0), Position(1, 1), Position(2, 2), Position(3, 1), Position(2, 0), Position(3, 0)]
    events = replay._process_movement(player, cmds[0], iter_(cmds[1:]), iter_(log_entries), None, board)
    end_move = Position(3, 0)

    for move in range(4):
        event = next(events)
        expected_start = positions[move]
        expected_end = positions[move + 1]
        assert isinstance(event, Movement)
        assert event.source_space == expected_start
        assert event.target_space == expected_end
        assert player.position == expected_end

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Reroll)
    assert event.team == player.team.team_type
    assert event.type == "Team Reroll"

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.player == player
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    move += 1
    expected_start = positions[move]
    expected_end = positions[move + 1]
    assert isinstance(event, Movement)
    assert event.source_space == expected_start
    assert event.target_space == expected_end
    assert player.position == expected_end

    assert player.position == end_move
    assert not board.is_prone(player)

    assert not next(events, None)


def test_going_for_it_fail_first_success_on_reroll(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(0, 0), player)
    home_id = TeamType.HOME.value
    cmds = [
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 1, 0, 0, 0, 0, 0, 1, 1]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 2, 0, 0, 0, 0, 0, 2, 2]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 3, 0, 0, 0, 0, 0, 3, 1]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 4, 0, 0, 0, 0, 0, 2, 0]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 4, 0, 0, 0, 0, 0, 3, 0]),
        EndMovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 0, 0, 0, 0, 0, 0, 4, 1]),
        RerollCommand(1, 1, TeamType.HOME, 1, [])
    ]
    log_entries = [
        GoingForItEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        RerollEntry(TeamType.HOME),
        GoingForItEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.SUCCESS.name),
        GoingForItEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.SUCCESS.name)
    ]
    positions = [Position(0, 0), Position(1, 1), Position(2, 2), Position(3, 1), Position(2, 0), Position(3, 0),
                 Position(4, 1)]
    events = replay._process_movement(player, cmds[0], iter_(cmds[1:]), iter_(log_entries), None, board)
    end_move = Position(4, 1)

    for move in range(4):
        event = next(events)
        expected_start = positions[move]
        expected_end = positions[move + 1]
        assert isinstance(event, Movement)
        assert event.source_space == expected_start
        assert event.target_space == expected_end
        assert player.position == expected_end

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Reroll)
    assert event.team == player.team.team_type
    assert event.type == "Team Reroll"

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.player == player
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    move += 1
    expected_start = positions[move]
    expected_end = positions[move + 1]
    assert isinstance(event, Movement)
    assert event.source_space == expected_start
    assert event.target_space == expected_end
    assert player.position == expected_end

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.player == player
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    move += 1
    expected_start = positions[move]
    expected_end = positions[move + 1]
    assert isinstance(event, Movement)
    assert event.source_space == expected_start
    assert event.target_space == expected_end
    assert player.position == expected_end

    assert player.position == end_move
    assert not board.is_prone(player)

    assert not next(events, None)


def test_going_for_it_twice_fail_first_no_reroll(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(0, 0), player)
    home_id = TeamType.HOME.value
    cmds = [
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 1, 0, 0, 0, 0, 0, 1, 1]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 2, 0, 0, 0, 0, 0, 2, 2]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 3, 0, 0, 0, 0, 0, 3, 1]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 4, 0, 0, 0, 0, 0, 2, 0]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 4, 0, 0, 0, 0, 0, 3, 0]),
        EndMovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 0, 0, 0, 0, 0, 0, 4, 1]),
        DeclineRerollCommand(1, 1, TeamType.HOME, 1, []),
        DiceChoiceCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 0])
    ]
    log_entries = [
        GoingForItEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        ArmourValueRollEntry(TeamType.HOME, player.number, "9+", "2", ActionResult.FAILURE.name),
        TurnOverEntry(TeamType.HOME, "Knocked Down!")
    ]
    positions = [Position(0, 0), Position(1, 1), Position(2, 2), Position(3, 1), Position(2, 0), Position(3, 0),
                 Position(4, 1)]
    events = replay._process_movement(player, cmds[0], iter_(cmds[1:]), iter_(log_entries), None, board)
    end_move = Position(3, 0)

    for move in range(4):
        event = next(events)
        expected_start = positions[move]
        expected_end = positions[move + 1]
        assert isinstance(event, Movement)
        assert event.source_space == expected_start
        assert event.target_space == expected_end
        assert player.position == expected_end

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    for move in range(4, 6):
        event = next(events)
        expected_start = positions[move]
        expected_end = positions[move + 1]
        assert isinstance(event, FailedMovement)
        assert event.source_space == expected_start
        assert event.target_space == expected_end
        assert player.position == end_move
        assert board.is_prone(player)

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"


def test_going_for_it_twice_fail_second_no_reroll(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(0, 0), player)
    home_id = TeamType.HOME.value
    cmds = [
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 1, 0, 0, 0, 0, 0, 1, 1]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 2, 0, 0, 0, 0, 0, 2, 2]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 3, 0, 0, 0, 0, 0, 3, 1]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 4, 0, 0, 0, 0, 0, 2, 0]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 4, 0, 0, 0, 0, 0, 3, 0]),
        EndMovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 0, 0, 0, 0, 0, 0, 4, 1]),
        DeclineRerollCommand(1, 1, TeamType.HOME, 1, []),
        DiceChoiceCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 0])
    ]
    log_entries = [
        GoingForItEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.SUCCESS.name),
        GoingForItEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        ArmourValueRollEntry(TeamType.HOME, player.number, "9+", "2", ActionResult.FAILURE.name),
        TurnOverEntry(TeamType.HOME, "Knocked Down!")
    ]
    positions = [Position(0, 0), Position(1, 1), Position(2, 2), Position(3, 1), Position(2, 0), Position(3, 0),
                 Position(4, 1)]
    events = replay._process_movement(player, cmds[0], iter_(cmds[1:]), iter_(log_entries), None, board)
    end_move = Position(4, 1)

    for move in range(4):
        event = next(events)
        expected_start = positions[move]
        expected_end = positions[move + 1]
        assert isinstance(event, Movement)
        assert event.source_space == expected_start
        assert event.target_space == expected_end
        assert player.position == expected_end

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.player == player
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    move += 1
    expected_start = positions[move]
    expected_end = positions[move + 1]
    assert isinstance(event, Movement)
    assert event.source_space == expected_start
    assert event.target_space == expected_end
    assert player.position == expected_end

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    move += 1
    expected_start = positions[move]
    expected_end = positions[move + 1]
    assert isinstance(event, FailedMovement)
    assert event.source_space == expected_start
    assert event.target_space == expected_end
    assert player.position == end_move
    assert board.is_prone(player)

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"


def test_going_for_it_twice_fail_second_success_on_reroll(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(0, 0), player)
    home_id = TeamType.HOME.value
    cmds = [
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 1, 0, 0, 0, 0, 0, 1, 1]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 2, 0, 0, 0, 0, 0, 2, 2]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 3, 0, 0, 0, 0, 0, 3, 1]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 4, 0, 0, 0, 0, 0, 2, 0]),
        MovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 4, 0, 0, 0, 0, 0, 3, 0]),
        EndMovementCommand(1, 1, TeamType.HOME, 1, [home_id, 0, 0, 0, 0, 0, 0, 0, 4, 1]),
        RerollCommand(1, 1, TeamType.HOME, 1, [])
    ]
    log_entries = [
        GoingForItEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.SUCCESS.name),
        GoingForItEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        RerollEntry(TeamType.HOME),
        GoingForItEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.SUCCESS.name)
    ]
    positions = [Position(0, 0), Position(1, 1), Position(2, 2), Position(3, 1), Position(2, 0), Position(3, 0),
                 Position(4, 1)]
    events = replay._process_movement(player, cmds[0], iter_(cmds[1:]), iter_(log_entries), None, board)
    end_move = Position(4, 1)

    for move in range(4):
        event = next(events)
        expected_start = positions[move]
        expected_end = positions[move + 1]
        assert isinstance(event, Movement)
        assert event.source_space == expected_start
        assert event.target_space == expected_end
        assert player.position == expected_end

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.player == player
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    move += 1
    expected_start = positions[move]
    expected_end = positions[move + 1]
    assert isinstance(event, Movement)
    assert event.source_space == expected_start
    assert event.target_space == expected_end
    assert player.position == expected_end

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Reroll)
    assert event.team == player.team.team_type
    assert event.type == "Team Reroll"

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.player == player
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    move += 1
    expected_start = positions[move]
    expected_end = positions[move + 1]
    assert isinstance(event, Movement)
    assert event.source_space == expected_start
    assert event.target_space == expected_end
    assert player.position == expected_end
    assert player.position == end_move
    assert not board.is_prone(player)

    assert not next(events, None)
