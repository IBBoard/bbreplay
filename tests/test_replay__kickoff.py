from . import *
from bbreplay import ScatterDirection, TeamType, Position, Weather
from bbreplay.command import *
from bbreplay.log import KickDirectionLogEntry, KickDistanceLogEntry, KickoffEventLogEntry, WeatherLogEntry
from bbreplay.replay import *


def test_normal_kick(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    cmds = iter_([
        SetupCompleteCommand(1, 0, TeamType.AWAY.value, 0, []),
        SetupCompleteCommand(1, 0, TeamType.HOME.value, 0, []),
        KickoffCommand(1, 0, TeamType.AWAY.value, 0, [8, 15]),
        PreKickoffCompleteCommand(1, 0, TeamType.HOME.value, 0, [TeamType.HOME.value])
    ])
    log_entries = iter_([
        KickDirectionLogEntry(TeamType.AWAY.name, "1", ScatterDirection.S.value),
        KickDistanceLogEntry(TeamType.AWAY.name, "1", 1),
        KickoffEventLogEntry(KickoffEvent.CHEERING_FANS.value),
        BounceLogEntry(ScatterDirection.N.value)
    ])
    events = replay._process_kickoff(cmds, log_entries, board)

    event = next(events)
    assert isinstance(event, TeamSetupComplete)
    assert event.team == TeamType.AWAY

    event = next(events)
    assert isinstance(event, TeamSetupComplete)
    assert event.team == TeamType.HOME

    event = next(events)
    assert isinstance(event, SetupComplete)

    event = next(events)
    assert isinstance(event, Kickoff)
    assert event.target == Position(8, 15)
    assert event.scatter_direction == ScatterDirection.S
    assert event.scatter_distance == 1
    assert board.get_ball_position() == Position(8, 14)

    event = next(events)
    assert isinstance(event, KickoffEventTuple)
    assert event.result == KickoffEvent.CHEERING_FANS

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.scatter_direction == ScatterDirection.N
    assert event.start_space == Position(8, 14)
    assert event.end_space == Position(8, 15)

    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_normal_kick_very_sunny(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    cmds = iter_([
        SetupCompleteCommand(1, 0, TeamType.AWAY.value, 0, []),
        SetupCompleteCommand(1, 0, TeamType.HOME.value, 0, []),
        KickoffCommand(1, 0, TeamType.AWAY.value, 0, [8, 15]),
        PreKickoffCompleteCommand(1, 0, TeamType.HOME.value, 0, [TeamType.HOME.value])
    ])
    log_entries = iter_([
        KickDirectionLogEntry(TeamType.AWAY.name, "1", ScatterDirection.S.value),
        KickDistanceLogEntry(TeamType.AWAY.name, "1", 1),
        KickoffEventLogEntry(KickoffEvent.CHANGING_WEATHER.value),
        WeatherLogEntry(Weather.VERY_SUNNY.name),
        BounceLogEntry(ScatterDirection.N.value),
        BounceLogEntry(ScatterDirection.E.value)
    ])
    events = replay._process_kickoff(cmds, log_entries, board)

    event = next(events)
    assert isinstance(event, TeamSetupComplete)
    assert event.team == TeamType.AWAY

    event = next(events)
    assert isinstance(event, TeamSetupComplete)
    assert event.team == TeamType.HOME

    event = next(events)
    assert isinstance(event, SetupComplete)

    event = next(events)
    assert isinstance(event, Kickoff)
    assert event.target == Position(8, 15)
    assert event.scatter_direction == ScatterDirection.S
    assert event.scatter_distance == 1
    assert board.get_ball_position() == Position(8, 14)

    event = next(events)
    assert isinstance(event, KickoffEventTuple)
    assert event.result == KickoffEvent.CHANGING_WEATHER

    event = next(events)
    assert isinstance(event, WeatherTuple)
    assert event.result == Weather.VERY_SUNNY

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.scatter_direction == ScatterDirection.N
    assert event.start_space == Position(8, 14)
    assert event.end_space == Position(8, 15)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.scatter_direction == ScatterDirection.E
    assert event.start_space == Position(8, 15)
    assert event.end_space == Position(9, 15)

    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_touchback_for_off_pitch_kick(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    cmds = iter_([
        SetupCompleteCommand(1, 0, TeamType.AWAY.value, 0, []),
        SetupCompleteCommand(1, 0, TeamType.HOME.value, 0, []),
        KickoffCommand(1, 0, TeamType.AWAY.value, 0, [0, 0]),  # Kick right into the corner,
        PreKickoffCompleteCommand(1, 0, TeamType.HOME.value, 0, [TeamType.HOME.value]),
        TouchbackCommand(1, 0, TeamType.HOME.value, 0, [TeamType.HOME.value, 0])
    ])
    log_entries = iter_([
        KickDirectionLogEntry(TeamType.AWAY.name, "1", ScatterDirection.SW.value),
        KickDistanceLogEntry(TeamType.AWAY.name, "1", 6),
        KickoffEventLogEntry(KickoffEvent.CHEERING_FANS.value),
        BounceLogEntry(ScatterDirection.NW.value)
    ])
    events = replay._process_kickoff(cmds, log_entries, board)

    event = next(events)
    assert isinstance(event, TeamSetupComplete)
    assert event.team == TeamType.AWAY

    event = next(events)
    assert isinstance(event, TeamSetupComplete)
    assert event.team == TeamType.HOME

    event = next(events)
    assert isinstance(event, SetupComplete)

    event = next(events)
    assert isinstance(event, Kickoff)
    assert event.target == Position(0, 0)
    assert event.scatter_direction == ScatterDirection.SW
    assert event.scatter_distance == 6
    assert board.get_ball_position().is_offpitch()

    event = next(events)
    assert isinstance(event, KickoffEventTuple)
    assert event.result == KickoffEvent.CHEERING_FANS

    event = next(events)
    assert isinstance(event, Touchback)
    assert event.player == player

    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_touchback_for_off_pitch_bounce(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    cmds = iter_([
        SetupCompleteCommand(1, 0, TeamType.AWAY.value, 0, []),
        SetupCompleteCommand(1, 0, TeamType.HOME.value, 0, []),
        KickoffCommand(1, 0, TeamType.AWAY.value, 0, [1, 1]),  # Kick right into the corner,
        PreKickoffCompleteCommand(1, 0, TeamType.HOME.value, 0, [TeamType.HOME.value]),
        TouchbackCommand(1, 0, TeamType.HOME.value, 0, [TeamType.HOME.value, 0])
    ])
    log_entries = iter_([
        KickDirectionLogEntry(TeamType.AWAY.name, "1", ScatterDirection.SW.value),
        KickDistanceLogEntry(TeamType.AWAY.name, "1", 1),
        KickoffEventLogEntry(KickoffEvent.CHEERING_FANS.value),
        BounceLogEntry(ScatterDirection.S.value)
    ])
    events = replay._process_kickoff(cmds, log_entries, board)

    event = next(events)
    assert isinstance(event, TeamSetupComplete)
    assert event.team == TeamType.AWAY

    event = next(events)
    assert isinstance(event, TeamSetupComplete)
    assert event.team == TeamType.HOME

    event = next(events)
    assert isinstance(event, SetupComplete)

    event = next(events)
    assert isinstance(event, Kickoff)
    assert event.target == Position(1, 1)
    assert event.scatter_direction == ScatterDirection.SW
    assert event.scatter_distance == 1
    assert board.get_ball_position() == Position(0, 0)

    event = next(events)
    assert isinstance(event, KickoffEventTuple)
    assert event.result == KickoffEvent.CHEERING_FANS

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.scatter_direction == ScatterDirection.S
    assert event.start_space == Position(0, 0)
    assert event.end_space.is_offpitch()

    event = next(events)
    assert isinstance(event, Touchback)
    assert event.player == player

    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_touchback_for_own_half_kick(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    cmds = iter_([
        SetupCompleteCommand(1, 0, TeamType.AWAY.value, 0, []),
        SetupCompleteCommand(1, 0, TeamType.HOME.value, 0, []),
        KickoffCommand(1, 0, TeamType.AWAY.value, 0, [8, 13]),
        PreKickoffCompleteCommand(1, 0, TeamType.HOME.value, 0, [TeamType.HOME.value]),
        TouchbackCommand(1, 0, TeamType.HOME.value, 0, [TeamType.HOME.value, 0])
    ])
    log_entries = iter_([
        KickDirectionLogEntry(TeamType.AWAY.name, "1", ScatterDirection.S.value),
        KickDistanceLogEntry(TeamType.AWAY.name, "1", 1),
        KickoffEventLogEntry(KickoffEvent.CHEERING_FANS.value),
        BounceLogEntry(ScatterDirection.W.value)
    ])
    events = replay._process_kickoff(cmds, log_entries, board)

    event = next(events)
    assert isinstance(event, TeamSetupComplete)
    assert event.team == TeamType.AWAY

    event = next(events)
    assert isinstance(event, TeamSetupComplete)
    assert event.team == TeamType.HOME

    event = next(events)
    assert isinstance(event, SetupComplete)

    event = next(events)
    assert isinstance(event, Kickoff)
    assert event.target == Position(8, 13)
    assert event.scatter_direction == ScatterDirection.S
    assert event.scatter_distance == 1
    assert board.get_ball_position() == Position(8, 12)

    event = next(events)
    assert isinstance(event, KickoffEventTuple)
    assert event.result == KickoffEvent.CHEERING_FANS

    event = next(events)
    assert isinstance(event, Touchback)
    assert event.player == player

    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_touchback_for_own_half_kick_other_direction(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    cmds = iter_([
        SetupCompleteCommand(1, 0, TeamType.AWAY.value, 0, []),
        SetupCompleteCommand(1, 0, TeamType.HOME.value, 0, []),
        KickoffCommand(1, 0, TeamType.AWAY.value, 0, [8, 12]),
        PreKickoffCompleteCommand(1, 0, TeamType.HOME.value, 0, [TeamType.HOME.value]),
        TouchbackCommand(1, 0, TeamType.HOME.value, 0, [TeamType.HOME.value, 0])
    ])
    log_entries = iter_([
        KickDirectionLogEntry(TeamType.AWAY.name, "1", ScatterDirection.N.value),
        KickDistanceLogEntry(TeamType.AWAY.name, "1", 1),
        KickoffEventLogEntry(KickoffEvent.CHEERING_FANS.value),
        BounceLogEntry(ScatterDirection.W.value)
    ])
    events = replay._process_kickoff(cmds, log_entries, board)

    event = next(events)
    assert isinstance(event, TeamSetupComplete)
    assert event.team == TeamType.AWAY

    event = next(events)
    assert isinstance(event, TeamSetupComplete)
    assert event.team == TeamType.HOME

    event = next(events)
    assert isinstance(event, SetupComplete)

    event = next(events)
    assert isinstance(event, Kickoff)
    assert event.target == Position(8, 12)
    assert event.scatter_direction == ScatterDirection.N
    assert event.scatter_distance == 1
    assert board.get_ball_position() == Position(8, 13)

    event = next(events)
    assert isinstance(event, KickoffEventTuple)
    assert event.result == KickoffEvent.CHEERING_FANS

    event = next(events)
    assert isinstance(event, Touchback)
    assert event.player == player

    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_riot_at_start_of_first_half_rolls_forwards(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    cmds = iter_([])
    log_entries = iter_([
        KickoffEventLogEntry(KickoffEvent.RIOT.value)
    ])
    events = replay._process_kickoff_event(cmds, log_entries, board)

    assert board.turn == 1

    event = next(events)
    assert isinstance(event, KickoffEventTuple)
    assert event.result == KickoffEvent.RIOT

    event = next(events)
    assert isinstance(event, StartTurn)

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Riot!"

    event = next(events)
    assert isinstance(event, StartTurn)

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Riot!"

    # Check that we're out of events before checking board turn so that we
    # continue executing the rest of the `end_turn()` function after the `yield`
    assert not next(events, None)
    assert board.turn == 2

    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_riot_at_start_of_second_half_rolls_forwards(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    cmds = iter_([])
    log_entries = iter_([
        KickoffEventLogEntry(KickoffEvent.RIOT.value)
    ])
    events = replay._process_kickoff_event(cmds, log_entries, board)

    board.kickoff()

    for _ in range(8):
        board.start_turn(board.receiving_team)
        board.end_turn(board.receiving_team)
        board.start_turn(board.kicking_team)
        board.end_turn(board.kicking_team)

    assert board.turn == 9

    event = next(events)
    assert isinstance(event, KickoffEventTuple)
    assert event.result == KickoffEvent.RIOT

    event = next(events)
    assert isinstance(event, StartTurn)

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Riot!"

    event = next(events)
    assert isinstance(event, StartTurn)

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Riot!"

    # Check that we're out of events before checking board turn so that we
    # continue executing the rest of the `end_turn()` function after the `yield`
    assert not next(events, None)
    assert board.turn == 10

    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_riot_at_end_of_first_half_rolls_backwards(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    cmds = iter_([])
    log_entries = iter_([
        KickoffEventLogEntry(KickoffEvent.RIOT.value)
    ])
    events = replay._process_kickoff_event(cmds, log_entries, board)

    board.kickoff()

    for _ in range(7):
        board.start_turn(board.receiving_team)
        board.end_turn(board.receiving_team)
        board.start_turn(board.kicking_team)
        board.end_turn(board.kicking_team)

    # In the board game the tracker moves when the player starts their turn
    # which is after the kick-off, but we count turns slightly differently
    # and already consider it to be turn 8
    assert board.turn == 8

    event = next(events)
    assert isinstance(event, KickoffEventTuple)
    assert event.result == KickoffEvent.RIOT

    # Check that we're out of events before checking board turn so that we
    # continue executing the rest of the `end_turn()` function after the `yield`
    assert not next(events, None)
    assert board.turn == 7

    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_riot_at_end_of_second_half_rolls_backwards(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    cmds = iter_([])
    log_entries = iter_([
        KickoffEventLogEntry(KickoffEvent.RIOT.value)
    ])
    events = replay._process_kickoff_event(cmds, log_entries, board)

    board.kickoff()

    for _ in range(15):
        board.start_turn(board.receiving_team)
        board.end_turn(board.receiving_team)
        board.start_turn(board.kicking_team)
        board.end_turn(board.kicking_team)

    assert board.turn == 16

    event = next(events)
    assert isinstance(event, KickoffEventTuple)
    assert event.result == KickoffEvent.RIOT

    # Check that we're out of events before checking board turn so that we
    # continue executing the rest of the `end_turn()` function after the `yield`
    assert not next(events, None)
    assert board.turn == 15

    assert not next(cmds, None)
    assert not next(log_entries, None)

