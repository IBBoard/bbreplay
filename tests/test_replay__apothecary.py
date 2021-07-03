import pytest
from bbreplay import TeamType, Position
from bbreplay.command import *
from bbreplay.log import *
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


def test_apothecary_recovers_casualty(board):
    board.apothecaries[TeamType.HOME.value] = 1
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    board.set_injured(player)
    cmds = iter_([
        ApothecaryCommand(1, 1, TeamType.HOME, 1, [0, 0, 1]),
        ApothecaryChoiceCommand(1, 1, TeamType.HOME, 1, [0, 0, CasualtyResult.BADLY_HURT.value])
    ])
    log_entries = iter_([
        ApothecaryLogEntry(player.team.team_type, player.number),
        CasualtyRollEntry(player.team.team_type, player.number, CasualtyResult.BADLY_HURT.name)
    ])
    events = replay._process_apothecary(player, InjuryRollResult.INJURED, CasualtyResult.DEAD, cmds, log_entries, board)

    event = next(events)
    assert isinstance(event, Apothecary)
    assert event.player == player
    assert event.new_injury == InjuryRollResult.INJURED
    assert event.casualty == CasualtyResult.BADLY_HURT

    event = next(events)
    assert isinstance(event, Casualty)
    assert event.player == player
    assert event.result == CasualtyResult.BADLY_HURT

    assert not board.is_injured(player)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_apothecary_reduces_casualty(board):
    board.apothecaries[TeamType.HOME.value] = 1
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    board.set_injured(player)
    cmds = iter_([
        ApothecaryCommand(1, 1, TeamType.HOME, 1, [0, 0, 1]),
        ApothecaryChoiceCommand(1, 1, TeamType.HOME, 1, [0, 0, CasualtyResult.BROKEN_RIBS.value])
    ])
    log_entries = iter_([
        ApothecaryLogEntry(player.team.team_type, player.number),
        CasualtyRollEntry(player.team.team_type, player.number, CasualtyResult.BROKEN_RIBS.name)
    ])
    events = replay._process_apothecary(player, InjuryRollResult.INJURED, CasualtyResult.DEAD, cmds, log_entries, board)

    event = next(events)
    assert isinstance(event, Apothecary)
    assert event.player == player
    assert event.new_injury == InjuryRollResult.INJURED
    assert event.casualty == CasualtyResult.BROKEN_RIBS

    event = next(events)
    assert isinstance(event, Casualty)
    assert event.player == player
    assert event.result == CasualtyResult.BROKEN_RIBS

    assert board.is_injured(player)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_apothecary_reduces_KO(board):
    board.apothecaries[TeamType.HOME.value] = 1
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    cmds = iter_([
        ApothecaryCommand(1, 1, TeamType.HOME, 1, [0, 0, 1])
    ])
    log_entries = iter_([
        ApothecaryLogEntry(player.team.team_type, player.number)
    ])
    events = replay._process_apothecary(player, InjuryRollResult.KO, CasualtyResult.NONE, cmds, log_entries, board)

    event = next(events)
    assert isinstance(event, Apothecary)
    assert event.player == player
    assert event.new_injury == InjuryRollResult.STUNNED
    assert event.casualty == CasualtyResult.NONE

    event = next(events)
    assert isinstance(event, InjuryRoll)
    assert event.player == player
    assert event.result == InjuryRollResult.STUNNED

    assert not board.is_injured(player)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_apothecary_declined(board):
    board.apothecaries[TeamType.HOME.value] = 1
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    board.set_injured(player)
    cmds = iter_([
        ApothecaryCommand(1, 1, TeamType.HOME, 1, [0, 0, 0])
    ])
    log_entries = iter_([
    ])
    events = replay._process_apothecary(player, InjuryRollResult.INJURED, CasualtyResult.DEAD, cmds, log_entries, board)

    assert board.is_injured(player)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


# TODO: Test apothecary followed by TurnOver
