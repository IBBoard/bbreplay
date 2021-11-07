from . import *
from bbreplay import Position, ScatterDirection, ThrowInDirection
from bbreplay.log import ThrowInDirectionLogEntry, ThrowInDistanceLogEntry, BounceLogEntry, TurnOverEntry
from bbreplay.replay import Bounce, Replay, ThrowIn


def test_throwin_direction_downfield(board):
    home_team, away_team = board.teams
    player = home_team.get_player(0)
    board.set_position(Position(7, 12), player)
    replay = Replay(home_team, away_team, [], [])
    board.set_ball_position(Position(0, 7))
    board.setup_complete()
    cmds = [
    ]
    log_entries = [
        BounceLogEntry(ScatterDirection.W.value),
        ThrowInDirectionLogEntry(ThrowInDirection.DOWN_PITCH.value),
        ThrowInDistanceLogEntry(3),
        BounceLogEntry(ScatterDirection.W.value),
        TurnOverEntry(TeamType.AWAY, "Fumble")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_ball_movement(log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(0, 7)
    assert event.end_space == Position(-1, 7)

    event = next(events)
    assert isinstance(event, ThrowIn)
    assert event.start_space == Position(0, 7)
    assert event.end_space == Position(3, 4)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(3, 4)
    assert event.end_space == Position(2, 4)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert isinstance(next(log_entries_iter), TurnOverEntry)


def test_throwin_direction_upfield(board):
    home_team, away_team = board.teams
    player = home_team.get_player(0)
    board.set_position(Position(7, 12), player)
    replay = Replay(home_team, away_team, [], [])
    board.set_ball_position(Position(0, 7))
    board.setup_complete()
    cmds = [
    ]
    log_entries = [
        BounceLogEntry(ScatterDirection.W.value),
        ThrowInDirectionLogEntry(ThrowInDirection.UP_PITCH.value),
        ThrowInDistanceLogEntry(3),
        BounceLogEntry(ScatterDirection.W.value),
        TurnOverEntry(TeamType.AWAY, "Fumble")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_ball_movement(log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(0, 7)
    assert event.end_space == Position(-1, 7)

    event = next(events)
    assert isinstance(event, ThrowIn)
    assert event.start_space == Position(0, 7)
    assert event.end_space == Position(3, 10)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(3, 10)
    assert event.end_space == Position(2, 10)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert isinstance(next(log_entries_iter), TurnOverEntry)


def test_throwin_direction_across_field(board):
    home_team, away_team = board.teams
    player = home_team.get_player(0)
    board.set_position(Position(7, 12), player)
    replay = Replay(home_team, away_team, [], [])
    board.set_ball_position(Position(0, 7))
    board.setup_complete()
    cmds = [
    ]
    log_entries = [
        BounceLogEntry(ScatterDirection.W.value),
        ThrowInDirectionLogEntry(ThrowInDirection.CENTRE.value),
        ThrowInDistanceLogEntry(3),
        BounceLogEntry(ScatterDirection.W.value),
        TurnOverEntry(TeamType.AWAY, "Fumble")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_ball_movement(log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(0, 7)
    assert event.end_space == Position(-1, 7)

    event = next(events)
    assert isinstance(event, ThrowIn)
    assert event.start_space == Position(0, 7)
    assert event.end_space == Position(3, 7)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(3, 7)
    assert event.end_space == Position(2, 7)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert isinstance(next(log_entries_iter), TurnOverEntry)


def test_throwin_direction_downfield_with_downfield_play(board):
    home_team, away_team = board.teams
    player = home_team.get_player(0)
    board.set_position(Position(7, 13), player)
    replay = Replay(home_team, away_team, [], [])
    board.set_ball_position(Position(0, 7))
    board.setup_complete()
    cmds = [
    ]
    log_entries = [
        BounceLogEntry(ScatterDirection.W.value),
        ThrowInDirectionLogEntry(ThrowInDirection.DOWN_PITCH.value),
        ThrowInDistanceLogEntry(3),
        BounceLogEntry(ScatterDirection.W.value),
        TurnOverEntry(TeamType.AWAY, "Fumble")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_ball_movement(log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(0, 7)
    assert event.end_space == Position(-1, 7)

    event = next(events)
    assert isinstance(event, ThrowIn)
    assert event.start_space == Position(0, 7)
    assert event.end_space == Position(3, 10)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(3, 10)
    assert event.end_space == Position(2, 10)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert isinstance(next(log_entries_iter), TurnOverEntry)


def test_throwin_direction_upfield_with_downfield_play(board):
    home_team, away_team = board.teams
    player = home_team.get_player(0)
    board.set_position(Position(7, 13), player)
    replay = Replay(home_team, away_team, [], [])
    board.set_ball_position(Position(0, 7))
    board.setup_complete()
    cmds = [
    ]
    log_entries = [
        BounceLogEntry(ScatterDirection.W.value),
        ThrowInDirectionLogEntry(ThrowInDirection.UP_PITCH.value),
        ThrowInDistanceLogEntry(3),
        BounceLogEntry(ScatterDirection.W.value),
        TurnOverEntry(TeamType.AWAY, "Fumble")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_ball_movement(log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(0, 7)
    assert event.end_space == Position(-1, 7)

    event = next(events)
    assert isinstance(event, ThrowIn)
    assert event.start_space == Position(0, 7)
    assert event.end_space == Position(3, 4)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(3, 4)
    assert event.end_space == Position(2, 4)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert isinstance(next(log_entries_iter), TurnOverEntry)


def test_throwin_direction_across_field_with_downfield_play(board):
    home_team, away_team = board.teams
    player = home_team.get_player(0)
    board.set_position(Position(7, 13), player)
    replay = Replay(home_team, away_team, [], [])
    board.set_ball_position(Position(0, 7))
    board.setup_complete()
    cmds = [
    ]
    log_entries = [
        BounceLogEntry(ScatterDirection.W.value),
        ThrowInDirectionLogEntry(ThrowInDirection.CENTRE.value),
        ThrowInDistanceLogEntry(3),
        BounceLogEntry(ScatterDirection.W.value),
        TurnOverEntry(TeamType.AWAY, "Fumble")
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_ball_movement(log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(0, 7)
    assert event.end_space == Position(-1, 7)

    event = next(events)
    assert isinstance(event, ThrowIn)
    assert event.start_space == Position(0, 7)
    assert event.end_space == Position(3, 7)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(3, 7)
    assert event.end_space == Position(2, 7)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert isinstance(next(log_entries_iter), TurnOverEntry)
