from . import *
from bbreplay import ScatterDirection, TeamType, Position
from bbreplay.command import *
from bbreplay.replay import *
from bbreplay.state import EndTurn


def test_single_movement(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(0, 0), player)
    cmds = iter_([EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 1, 1])])
    events = list(replay._process_movement(player, cmds, None, board))
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
    cmds_iter = iter_(cmds)
    events = replay._process_movement(player, cmds_iter, None, board)
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
    assert not next(cmds_iter, None)


def test_move_from_prone_defender_is_not_dodge(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    defender = away_team.get_player(0)
    board.set_prone(defender)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    cmds = iter_([EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7])])
    events = replay._process_movement(player, cmds, [], board)

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(6, 7)
    assert player.position == Position(6, 7)

    assert not board.is_prone(player)
    assert not next(events, None)


def test_move_from_stupid_defender_is_not_dodge(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    defender = away_team.get_player(0)
    board.stupidity_test(defender, ActionResult.FAILURE)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    cmds = iter_([EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7])])
    events = replay._process_movement(player, cmds, [], board)

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(6, 7)
    assert player.position == Position(6, 7)

    assert not board.is_prone(player)
    assert not next(events, None)


def test_single_successful_dodge(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    defender = away_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    cmds = iter_([EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7])])
    log_entries = [
        DodgeEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.SUCCESS.name)
    ]
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.DODGE
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(6, 7)
    assert player.position == Position(6, 7)

    assert not board.is_prone(player)
    assert not next(events, None)


def test_single_failed_dodge(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    defender = away_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    cmds = [
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        DeclineRerollCommand(1, 1, TeamType.HOME, 1, []),
        DiceChoiceCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0])
    ]
    log_entries = [
        DodgeEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.FAILURE.name),
        ArmourValueRollEntry(TeamType.HOME, player.number, "9+", "2", ActionResult.FAILURE.name),
        TurnOverEntry(TeamType.HOME, "Knocked Down!")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.DODGE
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, FailedMovement)
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(6, 7)
    assert player.position == Position(6, 7)
    assert board.is_prone(player)

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_single_failed_dodge_with_ball(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    defender = away_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    board.set_ball_carrier(player)
    cmds = [
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        DeclineRerollCommand(1, 1, TeamType.HOME, 1, []),
        DiceChoiceCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0])
    ]
    log_entries = [
        DodgeEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.FAILURE.name),
        ArmourValueRollEntry(TeamType.HOME, player.number, "9+", "2", ActionResult.FAILURE.name),
        BounceLogEntry(ScatterDirection.SE.value),
        TurnOverEntry(TeamType.HOME, "Knocked Down!")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.DODGE
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, FailedMovement)
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(6, 7)
    assert player.position == Position(6, 7)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(6, 7)
    assert event.end_space == Position(7, 6)
    assert event.scatter_direction == ScatterDirection.SE
    assert board.is_prone(player)

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_single_failed_dodge_into_ball(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    defender = away_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    board.set_ball_position(Position(6, 7))
    cmds = [
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        DeclineRerollCommand(1, 1, TeamType.HOME, 1, []),
        DiceChoiceCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0])
    ]
    log_entries = [
        DodgeEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.FAILURE.name),
        ArmourValueRollEntry(TeamType.HOME, player.number, "9+", "2", ActionResult.FAILURE.name),
        BounceLogEntry(ScatterDirection.S.value),
        TurnOverEntry(TeamType.HOME, "Knocked Down!")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.DODGE
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.scatter_direction == ScatterDirection.S
    assert event.start_space == Position(6, 7)
    assert event.end_space == Position(6, 6)

    event = next(events)
    assert isinstance(event, FailedMovement)
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(6, 7)
    assert player.position == Position(6, 7)
    assert board.is_prone(player)

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_single_failed_dodge_with_more_moves(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    defender = away_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    cmds = [
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 5, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 4, 7]),
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 3, 7]),
        DeclineRerollCommand(1, 1, TeamType.HOME, 1, []),
        DiceChoiceCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0])
    ]
    positions = [Position(7, 7), Position(6, 7), Position(5, 7), Position(4, 7), Position(3, 7)]
    log_entries = [
        DodgeEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.FAILURE.name),
        ArmourValueRollEntry(TeamType.HOME, player.number, "9+", "2", ActionResult.FAILURE.name),
        TurnOverEntry(TeamType.HOME, "Knocked Down!")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)
    end_move = Position(6, 7)

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.DODGE
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    for move in range(4):
        event = next(events)
        expected_start = positions[move]
        expected_end = positions[move + 1]
        assert isinstance(event, FailedMovement)
        assert event.source_space == expected_start
        assert event.target_space == expected_end

    assert board.is_prone(player)
    assert player.position == end_move

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_standup_is_not_dodge(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_prone(player)
    defender = away_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    cmds = [
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7])
    ]
    cmds_iter = iter_(cmds)
    events = replay._process_movement(player, cmds_iter, [], board)

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(7, 7)
    assert player.position == Position(7, 7)
    assert not board.is_prone(player)

    assert not next(events, None)
    assert not next(cmds_iter, None)


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
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)
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
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


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
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)
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
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_going_for_it_fail_with_ball(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(0, 0), player)
    board.set_ball_carrier(player)
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
        BounceLogEntry(ScatterDirection.E.value),
        TurnOverEntry(TeamType.HOME, "Knocked Down!")
    ]
    positions = [Position(0, 0), Position(1, 1), Position(2, 2), Position(3, 1), Position(2, 0), Position(3, 0)]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)
    end_move = Position(3, 0)

    for move in range(4):
        event = next(events)
        expected_start = positions[move]
        expected_end = positions[move + 1]
        assert isinstance(event, Movement)
        assert event.source_space == expected_start
        assert event.target_space == expected_end
        assert player.position == expected_end
    move += 1

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
    expected_start = positions[move]
    move += 1
    expected_end = positions[move]
    assert isinstance(event, FailedMovement)
    assert event.source_space == expected_start
    assert event.target_space == expected_end
    assert player.position == end_move
    assert board.is_prone(player)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == positions[move]
    assert event.end_space == positions[move].add(1, 0)
    assert event.scatter_direction == ScatterDirection.E

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


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
        RerollCommand(1, 1, TeamType.HOME, 1, [])
    ]
    log_entries = [
        GoingForItEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        RerollEntry(TeamType.HOME),
        GoingForItEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        ArmourValueRollEntry(TeamType.HOME, player.number, "9+", "2", ActionResult.FAILURE.name),
        TurnOverEntry(TeamType.HOME, "Knocked Down!")
    ]
    positions = [Position(0, 0), Position(1, 1), Position(2, 2), Position(3, 1), Position(2, 0), Position(3, 0)]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)
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
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


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
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)
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
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


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
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)
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
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


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
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)
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
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


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
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)
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
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


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
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)
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
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_single_failed_tentacled(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    defender = away_team.get_player(0)
    defender.skills.append(Skills.TENTACLES)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    cmds = [
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        DeclineRerollCommand(1, 1, TeamType.HOME, 1, []),
        DiceChoiceCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0])
    ]
    log_entries = [
        TentacledEntry(TeamType.HOME, player.number, TeamType.AWAY, defender.number,
                       "7+", "2", ActionResult.FAILURE.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Tentacle)
    assert event.dodging_player == player
    assert event.tentacle_player == defender
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, FailedMovement)
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(6, 7)
    assert player.position == Position(7, 7)
    assert not board.is_prone(player)

    assert not next(events, None)


def test_standup_is_not_tentacled(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_prone(player)
    defender = away_team.get_player(0)
    defender.skills.append(Skills.TENTACLES)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    cmds = [
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7])
    ]
    cmds_iter = iter_(cmds)
    events = replay._process_movement(player, cmds_iter, [], board)

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(7, 7)
    assert player.position == Position(7, 7)
    assert not board.is_prone(player)

    assert not next(events, None)


def test_move_from_prone_defender_is_not_tentacled(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    defender = away_team.get_player(0)
    board.set_prone(defender)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    defender.skills.append(Skills.TENTACLES)
    cmds = iter_([EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7])])
    events = replay._process_movement(player, cmds, [], board)

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(6, 7)
    assert player.position == Position(6, 7)

    assert not board.is_prone(player)
    assert not next(events, None)


def test_single_sucessful_break_tentacled(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    defender = away_team.get_player(0)
    defender.skills.append(Skills.TENTACLES)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    cmds = [
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7])
    ]
    log_entries = [
        TentacledEntry(TeamType.HOME, player.number, TeamType.AWAY, defender.number,
                       "7+", "7", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Tentacle)
    assert event.dodging_player == player
    assert event.tentacle_player == defender
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(6, 7)
    assert player.position == Position(6, 7)

    assert not next(events, None)


def test_single_failed_tentacled_with_more_moves(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    defender = away_team.get_player(0)
    defender.skills.append(Skills.TENTACLES)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    cmds = [
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 5, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 4, 7]),
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 3, 7]),
        DeclineRerollCommand(1, 1, TeamType.HOME, 1, []),
        DiceChoiceCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0])
    ]
    positions = [Position(7, 7), Position(6, 7), Position(5, 7), Position(4, 7), Position(3, 7)]
    log_entries = [
        TentacledEntry(TeamType.HOME, player.number, TeamType.AWAY, defender.number,
                       "7+", "2", ActionResult.FAILURE.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)
    end_move = Position(7, 7)

    event = next(events)
    assert isinstance(event, Tentacle)
    assert event.dodging_player == player
    assert event.tentacle_player == defender
    assert event.result == ActionResult.FAILURE

    for move in range(4):
        event = next(events)
        expected_start = positions[move]
        expected_end = positions[move + 1]
        assert isinstance(event, FailedMovement)
        assert event.source_space == expected_start
        assert event.target_space == expected_end

    assert player.position == end_move
    assert not board.is_prone(player)
    assert not next(events, None)


def test_leap_success(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.LEAP)
    defender = away_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    cmds = [
        # Leap shows up as two movement commands and goes through any players
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 9, 7])
    ]
    log_entries = [
        LeapEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player
    assert event.action == ActionType.LEAP
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(9, 7)
    assert player.position == Position(9, 7)

    assert not board.is_prone(player)
    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_leap_failure(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.LEAP)
    defender = away_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    cmds = [
        # Leap shows up as two movement commands and goes through any players
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 9, 7]),
        DeclineRerollCommand(1, 1, TeamType.HOME, 1, []),
        DiceChoiceCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0])
    ]
    log_entries = [
        LeapEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        ArmourValueRollEntry(TeamType.HOME, player.number, "9+", "2", ActionResult.FAILURE.name),
        TurnOverEntry(TeamType.HOME, "Knocked Down!")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player
    assert event.action == ActionType.LEAP
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, FailedMovement)
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(9, 7)
    assert player.position == Position(9, 7)
    assert board.is_prone(player)

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"

    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_leap_failure_with_more_movement(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.LEAP)
    defender = away_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_position(Position(8, 7), defender)
    cmds = [
        # Leap shows up as two movement commands and goes through any players
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 9, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 10, 7]),
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 11, 7]),
        DeclineRerollCommand(1, 1, TeamType.HOME, 1, []),
        DiceChoiceCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0])
    ]
    log_entries = [
        LeapEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        ArmourValueRollEntry(TeamType.HOME, player.number, "9+", "2", ActionResult.FAILURE.name),
        TurnOverEntry(TeamType.HOME, "Knocked Down!")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player
    assert event.action == ActionType.LEAP
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, FailedMovement)
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(9, 7)
    assert player.position == Position(9, 7)
    assert board.is_prone(player)

    event = next(events)
    assert isinstance(event, FailedMovement)
    assert event.source_space == Position(9, 7)
    assert event.target_space == Position(10, 7)
    assert player.position == Position(9, 7)
    assert board.is_prone(player)

    event = next(events)
    assert isinstance(event, FailedMovement)
    assert event.source_space == Position(10, 7)
    assert event.target_space == Position(11, 7)
    assert player.position == Position(9, 7)
    assert board.is_prone(player)

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"

    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)
