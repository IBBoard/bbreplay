from . import *
from bbreplay import ScatterDirection, TeamType, Position
from bbreplay.command import *
from bbreplay.replay import *


def test_pickup_success(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    board.set_ball_position(Position(7, 7))
    cmds = [
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7])
    ]
    log_entries = [
        PickupEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(6, 7)
    assert event.target_space == Position(7, 7)

    event = next(events)
    assert isinstance(event, Pickup)
    assert event.player == player
    assert event.position == Position(7, 7)
    assert event.result == ActionResult.SUCCESS

    assert board.get_ball_carrier() == player
    assert board.get_ball_position() == Position(7, 7)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_pickup_success_then_trip_on_GFI(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    board.set_ball_position(Position(7, 7))
    cmds = [
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 9, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 10, 7]),
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 11, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
    ]
    log_entries = [
        PickupEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.SUCCESS.name),
        GoingForItEntry(player.team.team_type, player.number, "2+", "1", ActionResult.FAILURE),
        ArmourValueRollEntry(TeamType.HOME, player.number, "10", "7", ActionResult.FAILURE.name),
        BounceLogEntry(ScatterDirection.NW.value),
        TurnOverEntry(TeamType.HOME, "Knocked Down!")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(6, 7)
    assert event.target_space == Position(7, 7)

    event = next(events)
    assert isinstance(event, Pickup)
    assert event.player == player
    assert event.position == Position(7, 7)
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(8, 7)

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(8, 7)
    assert event.target_space == Position(9, 7)

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(9, 7)
    assert event.target_space == Position(10, 7)

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, FailedMovement)
    assert event.source_space == Position(10, 7)
    assert event.target_space == Position(11, 7)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(11, 7)
    assert event.end_space == Position(10, 8)
    assert event.scatter_direction == ScatterDirection.NW

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.team == player.team.team_type
    assert event.reason == "Knocked Down!"

    event = next(events)
    assert isinstance(event, StartTurn)

    assert not board.get_ball_carrier()
    assert board.get_ball_position() == Position(10, 8)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_pickup_failure(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    board.set_ball_position(Position(7, 7))
    cmds = [
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
    ]
    log_entries = [
        PickupEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        BounceLogEntry(ScatterDirection.NW.value),
        TurnOverEntry(TeamType.HOME, "Pick-up failed!")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(6, 7)
    assert event.target_space == Position(7, 7)

    event = next(events)
    assert isinstance(event, Pickup)
    assert event.player == player
    assert event.position == Position(7, 7)
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(7, 7)
    assert event.end_space == Position(6, 8)
    assert event.scatter_direction == ScatterDirection.NW

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Pick-up failed!"

    assert board.get_ball_carrier() is None
    assert board.get_ball_position() == Position(6, 8)

    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_bounce_on_gfi(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(2, 7), player)
    board.set_ball_carrier(player)
    cmds = [
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 3, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 4, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 5, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
    ]
    log_entries = [
        GoingForItEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        ArmourValueRollEntry(TeamType.HOME, player.number, "10", "7", ActionResult.FAILURE.name),
        BounceLogEntry(ScatterDirection.NW.value),
        TurnOverEntry(TeamType.HOME, "Knocked Down!")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)

    for i in range(4):
        event = next(events)
        assert isinstance(event, Movement)
        assert event.source_space == Position(2 + i, 7)
        assert event.target_space == Position(3 + i, 7)

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, FailedMovement)
    assert event.source_space == Position(6, 7)
    assert event.target_space == Position(7, 7)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(7, 7)
    assert event.end_space == Position(6, 8)
    assert event.scatter_direction == ScatterDirection.NW

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"

    assert board.get_ball_carrier() is None
    assert board.get_ball_position() == Position(6, 8)

    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_pickup_success_with_sure_hands(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.SURE_HANDS)
    board.set_position(Position(6, 7), player)
    board.set_ball_position(Position(7, 7))
    cmds = [
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7])
    ]
    log_entries = [
        PickupEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        SkillEntry(TeamType.HOME, player.number, Skills.SURE_HANDS.name),
        PickupEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(6, 7)
    assert event.target_space == Position(7, 7)

    event = next(events)
    assert isinstance(event, Pickup)
    assert event.player == player
    assert event.position == Position(7, 7)
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Reroll)
    assert event.team == TeamType.HOME
    assert event.type == Skills.SURE_HANDS.name.title()

    event = next(events)
    assert isinstance(event, Pickup)
    assert event.player == player
    assert event.position == Position(7, 7)
    assert event.result == ActionResult.SUCCESS

    assert board.get_ball_carrier() == player
    assert board.get_ball_position() == Position(7, 7)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)
