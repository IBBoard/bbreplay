import pytest
from bbreplay import ScatterDirection, TeamType, Position, Weather
from bbreplay.command import *
from bbreplay.log import KickDirectionLogEntry, KickDistanceLogEntry, KickoffEventLogEntry, WeatherLogEntry
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
    return GameState(home_team, away_team, TeamType.HOME)


def test_normal_kick(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    cmds = iter_([
        SetupCompleteCommand(1, 0, TeamType.AWAY.value, 0, []),
        SetupCompleteCommand(1, 0, TeamType.HOME.value, 0, []),
        KickoffCommand(1, 0, TeamType.AWAY.value, 0, [8, 15])
    ])
    log_entries = iter_([
        [
            KickDirectionLogEntry(TeamType.AWAY.name, "1", ScatterDirection.S.value),
            KickDistanceLogEntry(TeamType.AWAY.name, "1", 1)
        ],
        [
            KickoffEventLogEntry(KickoffEvent.CHEERING_FANS.value)
        ],
        [
            BounceLogEntry(ScatterDirection.N.value)
        ]
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
    assert isinstance(event, StartTurn)
    assert event.team == TeamType.HOME

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
        KickoffCommand(1, 0, TeamType.AWAY.value, 0, [8, 15])
    ])
    log_entries = iter_([
        [
            KickDirectionLogEntry(TeamType.AWAY.name, "1", ScatterDirection.S.value),
            KickDistanceLogEntry(TeamType.AWAY.name, "1", 1)
        ],
        [
            KickoffEventLogEntry(KickoffEvent.CHANGING_WEATHER.value)
        ],
        [
            WeatherLogEntry(Weather.VERY_SUNNY.name)
        ],
        [
            BounceLogEntry(ScatterDirection.N.value),
            BounceLogEntry(ScatterDirection.E.value)
        ]
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
    assert isinstance(event, StartTurn)
    assert event.team == TeamType.HOME

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
        KickoffCommand(1, 0, TeamType.AWAY.value, 0, [0, 0]),  # Kick right into the corner
        TouchbackCommand(1, 0, TeamType.HOME.value, 0, [TeamType.HOME.value, 0])
    ])
    log_entries = iter_([
        [
            KickDirectionLogEntry(TeamType.AWAY.name, "1", ScatterDirection.SW.value),
            KickDistanceLogEntry(TeamType.AWAY.name, "1", 6)
        ],
        [
            KickoffEventLogEntry(KickoffEvent.CHEERING_FANS.value)
        ]
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
    assert board.get_ball_position() == OFF_PITCH_POSITION

    event = next(events)
    assert isinstance(event, KickoffEventTuple)
    assert event.result == KickoffEvent.CHEERING_FANS

    event = next(events)
    assert isinstance(event, StartTurn)

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
        KickoffCommand(1, 0, TeamType.AWAY.value, 0, [1, 1]),  # Kick right into the corner
        TouchbackCommand(1, 0, TeamType.HOME.value, 0, [TeamType.HOME.value, 0])
    ])
    log_entries = iter_([
        [
            KickDirectionLogEntry(TeamType.AWAY.name, "1", ScatterDirection.SW.value),
            KickDistanceLogEntry(TeamType.AWAY.name, "1", 1)
        ],
        [
            KickoffEventLogEntry(KickoffEvent.CHEERING_FANS.value)
        ],
        [
            BounceLogEntry(ScatterDirection.S.value)
        ]
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
    assert isinstance(event, StartTurn)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.scatter_direction == ScatterDirection.S
    assert event.start_space == Position(0, 0)
    assert event.end_space == OFF_PITCH_POSITION

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
        TouchbackCommand(1, 0, TeamType.HOME.value, 0, [TeamType.HOME.value, 0])
    ])
    log_entries = iter_([
        [
            KickDirectionLogEntry(TeamType.AWAY.name, "1", ScatterDirection.S.value),
            KickDistanceLogEntry(TeamType.AWAY.name, "1", 1)
        ],
        [
            KickoffEventLogEntry(KickoffEvent.CHEERING_FANS.value)
        ]
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
    assert isinstance(event, StartTurn)

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
        TouchbackCommand(1, 0, TeamType.HOME.value, 0, [TeamType.HOME.value, 0])
    ])
    log_entries = iter_([
        [
            KickDirectionLogEntry(TeamType.AWAY.name, "1", ScatterDirection.N.value),
            KickDistanceLogEntry(TeamType.AWAY.name, "1", 1)
        ],
        [
            KickoffEventLogEntry(KickoffEvent.CHEERING_FANS.value)
        ]
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
    assert isinstance(event, StartTurn)

    event = next(events)
    assert isinstance(event, Touchback)
    assert event.player == player

    assert not next(cmds, None)
    assert not next(log_entries, None)

