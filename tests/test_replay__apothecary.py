from bbreplay import TeamType, Position
from bbreplay.command import *
from bbreplay.log import *
from bbreplay.replay import *
from . import *


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


def test_apothecary_not_available(board):
    # Zero apothecaries is the default, but be explicit
    board.apothecaries[TeamType.HOME.value] = 0
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


def test_apothecary_not_used_for_stunned(board):
    board.apothecaries[TeamType.HOME.value] = 1
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    cmds = iter_([
    ])
    log_entries = iter_([
        InjuryRollEntry(player.team.team_type, player.number, "1", InjuryRollResult.STUNNED.name)
    ])
    events = replay._process_injury_roll(player, cmds, log_entries, board)

    event = next(events)
    assert isinstance(event, InjuryRoll)
    assert event.player == player
    assert event.result == InjuryRollResult.STUNNED

    assert not board.is_injured(player)
    assert player.position == Position(6, 7)
    assert board.get_position(Position(6, 7)) == player

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


# TODO: Test apothecary followed by TurnOver
