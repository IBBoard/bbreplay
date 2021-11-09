from . import *
from bbreplay import ScatterDirection, TeamType, Position
from bbreplay.command import *
from bbreplay.replay import *


def test_handoff_forward_success(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    board.set_position(Position(6, 7), player_1)
    player_2 = home_team.get_player(1)
    board.set_position(Position(7, 7), player_2)
    board.set_ball_carrier(player_1)
    cmds = [
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.HOME.value, 1, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7])
    ]
    log_entries = [
        CatchEntry(TeamType.HOME, 2, "3+", "6", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw(player_1, player_2, cmds_iter, log_entries_iter, board)

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
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.HOME.value, 1, 6, 6]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 6])
    ]
    log_entries = [
        CatchEntry(TeamType.HOME, 2, "3+", "6", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw(player_1, player_2, cmds_iter, log_entries_iter, board)

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
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.HOME.value, 1, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7])
    ]
    log_entries = [
        CatchEntry(TeamType.HOME, 2, "3+", "6", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw(player_1, player_2, cmds_iter, log_entries_iter, board)

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


def test_pass_forward_success(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    board.set_position(Position(5, 7), player_1)
    player_2 = home_team.get_player(1)
    board.set_position(Position(7, 7), player_2)
    board.set_ball_carrier(player_1)
    cmds = [
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.HOME.value, 1, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        Command(1, 1, TeamType.AWAY.value, 13, [])
    ]
    log_entries = [
        ThrowEntry(TeamType.HOME, 1, "3+", "6", ThrowResult.ACCURATE_PASS.name),
        CatchEntry(TeamType.HOME, 2, "3+", "6", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw(player_1, player_2, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Pass)
    assert event.player == player_1
    assert event.target == Position(7, 7)
    assert event.result == ThrowResult.ACCURATE_PASS

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


def test_pass_forward_success_after_reroll(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    board.set_position(Position(5, 7), player_1)
    player_2 = home_team.get_player(1)
    board.set_position(Position(7, 7), player_2)
    board.set_ball_carrier(player_1)
    cmds = [
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.HOME.value, 1, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        Command(1, 1, TeamType.AWAY.value, 13, []),
        RerollCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0])
    ]
    log_entries = [
        ThrowEntry(TeamType.HOME, 1, "3+", "6", ThrowResult.ACCURATE_PASS.name),
        CatchEntry(TeamType.HOME, 2, "3+", "2", ActionResult.FAILURE.name),
        RerollEntry(TeamType.HOME),
        CatchEntry(TeamType.HOME, 2, "3+", "3", ActionResult.SUCCESS.name),
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw(player_1, player_2, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Pass)
    assert event.player == player_1
    assert event.target == Position(7, 7)
    assert event.result == ThrowResult.ACCURATE_PASS

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_2
    assert event.action == ActionType.CATCH
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Reroll)
    assert event.team == TeamType.HOME
    assert event.type == "Team Reroll"

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


def test_pass_sideways_success(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    board.set_position(Position(5, 7), player_1)
    player_2 = home_team.get_player(1)
    board.set_position(Position(5, 5), player_2)
    board.set_ball_carrier(player_1)
    cmds = [
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.HOME.value, 1, 5, 5]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 5, 5]),
        Command(1, 1, TeamType.AWAY.value, 13, [])
    ]
    log_entries = [
        ThrowEntry(TeamType.HOME, 1, "3+", "6", ThrowResult.ACCURATE_PASS.name),
        CatchEntry(TeamType.HOME, 2, "3+", "6", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw(player_1, player_2, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Pass)
    assert event.player == player_1
    assert event.target == Position(5, 5)
    assert event.result == ThrowResult.ACCURATE_PASS

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_2
    assert event.action == ActionType.CATCH
    assert event.result == ActionResult.SUCCESS

    assert board.get_ball_carrier() == player_2
    assert board.get_ball_position() == Position(5, 5)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_pass_diagonal_success(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    board.set_position(Position(5, 5), player_1)
    player_2 = home_team.get_player(1)
    board.set_position(Position(3, 3), player_2)
    board.set_ball_carrier(player_1)
    cmds = [
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.HOME.value, 1, 3, 3]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 3, 3]),
        Command(1, 1, TeamType.AWAY.value, 13, [])
    ]
    log_entries = [
        ThrowEntry(TeamType.HOME, 1, "3+", "6", ThrowResult.ACCURATE_PASS.name),
        CatchEntry(TeamType.HOME, 2, "3+", "6", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw(player_1, player_2, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Pass)
    assert event.player == player_1
    assert event.target == Position(3, 3)
    assert event.result == ThrowResult.ACCURATE_PASS

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_2
    assert event.action == ActionType.CATCH
    assert event.result == ActionResult.SUCCESS

    assert board.get_ball_carrier() == player_2
    assert board.get_ball_position() == Position(3, 3)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_pass_diagonal_failed_intercept(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    board.set_position(Position(5, 5), player_1)
    player_2 = home_team.get_player(1)
    board.set_position(Position(3, 3), player_2)
    board.set_ball_carrier(player_1)
    opponent = away_team.get_player(0)
    board.set_position(Position(4, 4), opponent)
    cmds = [
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.HOME.value, 1, 3, 3]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 3, 3]),
        InterceptCommand(1, 1, TeamType.AWAY.value, 13, [1])
    ]
    log_entries = [
        CatchEntry(TeamType.AWAY, 1, "3+", "2", ActionResult.FAILURE.name),
        ThrowEntry(TeamType.HOME, 1, "3+", "6", ThrowResult.ACCURATE_PASS.name),
        CatchEntry(TeamType.HOME, 2, "3+", "6", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw(player_1, player_2, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Interception)
    assert event.player == opponent
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Pass)
    assert event.player == player_1
    assert event.target == Position(3, 3)
    assert event.result == ThrowResult.ACCURATE_PASS

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_2
    assert event.action == ActionType.CATCH
    assert event.result == ActionResult.SUCCESS

    assert board.get_ball_carrier() == player_2
    assert board.get_ball_position() == Position(3, 3)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_pass_diagonal_successful_intercept(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    board.set_position(Position(5, 5), player_1)
    player_2 = home_team.get_player(1)
    board.set_position(Position(3, 3), player_2)
    board.set_ball_carrier(player_1)
    opponent = away_team.get_player(0)
    board.set_position(Position(4, 4), opponent)
    cmds = [
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.HOME.value, 1, 3, 3]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 3, 3]),
        InterceptCommand(1, 1, TeamType.AWAY.value, 13, [1])
    ]
    log_entries = [
        CatchEntry(TeamType.AWAY, 1, "3+", "3", ActionResult.SUCCESS.name),
        TurnOverEntry(TeamType.HOME, "Lost the ball!")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw(player_1, player_2, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Interception)
    assert event.player == opponent
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Lost the ball!"

    assert board.get_ball_carrier() == opponent
    assert board.get_ball_position() == Position(4, 4)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_stupid_player_pass_with_success(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    player_1.skills.append(Skills.REALLY_STUPID)
    board.set_position(Position(5, 7), player_1)
    player_2 = home_team.get_player(1)
    board.set_position(Position(7, 7), player_2)
    board.set_ball_carrier(player_1)
    cmds = [
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.HOME.value, 1, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        Command(1, 1, TeamType.AWAY.value, 13, [])
    ]
    log_entries = [
        StupidEntry(TeamType.HOME, 1, "4+", "4", ActionResult.SUCCESS.name),
        ThrowEntry(TeamType.HOME, 1, "3+", "6", ThrowResult.ACCURATE_PASS.name),
        CatchEntry(TeamType.HOME, 2, "3+", "6", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw(player_1, player_2, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_1
    assert event.action == ActionType.REALLY_STUPID
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, Pass)
    assert event.player == player_1
    assert event.target == Position(7, 7)
    assert event.result == ThrowResult.ACCURATE_PASS

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


def test_stupid_player_pass_with_failure(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    player_1.skills.append(Skills.REALLY_STUPID)
    board.set_position(Position(5, 7), player_1)
    player_2 = home_team.get_player(1)
    board.set_position(Position(7, 7), player_2)
    board.set_ball_carrier(player_1)
    cmds = [
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.HOME.value, 1, 3, 3]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0])
    ]
    log_entries = [
        StupidEntry(TeamType.HOME, 1, "4+", "3", ActionResult.FAILURE.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw(player_1, player_2, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_1
    assert event.action == ActionType.REALLY_STUPID
    assert event.result == ActionResult.FAILURE

    assert board.get_ball_carrier() == player_1
    assert board.get_ball_position() == Position(5, 7)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_dumpoff_does_not_allow_reroll(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(5, 7), player)
    board.set_ball_carrier(player)
    player_2 = home_team.get_player(1)
    board.set_position(Position(7, 7), player_2)
    cmds = iter_([
        # Dumpoff is consumed in the block rolling function
        # DumpOffCommand(1, 1, TeamType.AWAY, 0, []),
        ThrowCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 7, 7]),
        InterceptCommand(1, 1, TeamType.AWAY.value, 0, [TeamType.HOME.value, 0, 0])
    ])
    log_entries = iter_([
        ThrowEntry(player.team.team_type, player.number, "3+", "3", ThrowResult.ACCURATE_PASS.name),
        CatchEntry(player_2.team.team_type, player_2.number, "4+", "3", ActionResult.FAILURE.name),
        BounceLogEntry(ScatterDirection.N.value)
    ])
    events = replay._process_pass(player, cmds, log_entries, board, False)

    event = next(events)
    assert isinstance(event, Pass)
    assert event.player == player
    assert event.target == Position(7, 7)

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.CATCH
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.scatter_direction == ScatterDirection.N
    assert event.start_space == Position(7, 7)
    assert event.end_space == Position(7, 8)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)
