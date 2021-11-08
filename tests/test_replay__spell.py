from . import *
from bbreplay.log import BlockLogEntry, FireballEntry, InjuryRollEntry
from bbreplay import ScatterDirection, TeamType, Position
from bbreplay.command import *
from bbreplay.player import Player
from bbreplay.replay import *


def test_bounce_from_spell(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_ball_carrier(player)
    cmds = [SpellCommand(1, 1, TeamType.AWAY.value, 0, [TeamType.AWAY.value, 0, 255, 7, 7])]
    log_entries = [
        FireballEntry(TeamType.HOME, 1, "4+", "4", ActionResult.SUCCESS.name),
        ArmourValueRollEntry(TeamType.HOME, 1, "8+", "9", ActionResult.SUCCESS.name),
        InjuryRollEntry(TeamType.HOME, 1, "6", InjuryRollResult.STUNNED.name),
        BounceLogEntry(ScatterDirection.NW.value)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_spell(cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Spell)
    assert event.target == Position(7, 7)
    assert event.spell == "Fireball"

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player
    assert event.action == ActionType.SPELL_HIT
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, InjuryRoll)
    assert event.player == player
    assert event.result == InjuryRollResult.STUNNED

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(7, 7)
    assert event.end_space == Position(6, 8)
    assert event.scatter_direction == ScatterDirection.NW

    assert board.get_ball_carrier() is None
    assert board.get_ball_position() == Position(6, 8)

    assert not next(events, None)
    assert not next(log_entries_iter, None)


def test_no_hits_with_spell(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_ball_carrier(player)
    cmds = [SpellCommand(1, 1, TeamType.AWAY.value, 0, [TeamType.AWAY.value, 0, 255, 7, 7])]
    log_entries = [
        FireballEntry(TeamType.HOME, 1, "4+", "3", ActionResult.FAILURE.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_spell(cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Spell)
    assert event.target == Position(7, 7)
    assert event.spell == "Fireball"

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player
    assert event.action == ActionType.SPELL_HIT
    assert event.result == ActionResult.FAILURE

    assert board.get_ball_carrier() == player

    assert not next(events, None)
    assert not next(log_entries_iter, None)


def test_bounce_from_spell_with_multiple_hits(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_ball_carrier(player)
    player_2 = Player(2, "Player2H", 4, 4, 4, 4, 1, 0, 40000, [])
    home_team.add_player(1, player_2)
    board.set_position(Position(6, 6), player_2)
    cmds = [SpellCommand(1, 1, TeamType.AWAY.value, 0, [TeamType.AWAY.value, 0, 255, 7, 7])]
    log_entries = [
        FireballEntry(TeamType.HOME, 1, "4+", "4", ActionResult.SUCCESS.name),
        ArmourValueRollEntry(TeamType.HOME, 1, "8+", "9", ActionResult.SUCCESS.name),
        InjuryRollEntry(TeamType.HOME, 1, "6", InjuryRollResult.STUNNED.name),
        FireballEntry(TeamType.HOME, 2, "4+", "4", ActionResult.FAILURE.name),
        BounceLogEntry(ScatterDirection.NW.value)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_spell(cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Spell)
    assert event.target == Position(7, 7)
    assert event.spell == "Fireball"

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player
    assert event.action == ActionType.SPELL_HIT
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, InjuryRoll)
    assert event.player == player
    assert event.result == InjuryRollResult.STUNNED

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_2
    assert event.action == ActionType.SPELL_HIT
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(7, 7)
    assert event.end_space == Position(6, 8)
    assert event.scatter_direction == ScatterDirection.NW

    assert board.get_ball_carrier() is None
    assert board.get_ball_position() == Position(6, 8)

    assert not next(events, None)
    assert not next(log_entries_iter, None)


def test_bounce_from_spell_with_bounce_off_prone(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_ball_carrier(player)
    player_2 = Player(2, "Player2H", 4, 4, 4, 4, 1, 0, 40000, [])
    home_team.add_player(1, player_2)
    board.set_position(Position(6, 6), player_2)
    cmds = [SpellCommand(1, 1, TeamType.AWAY.value, 0, [TeamType.AWAY.value, 0, 255, 7, 7])]
    log_entries = [
        FireballEntry(TeamType.HOME, 1, "4+", "4", ActionResult.SUCCESS.name),
        ArmourValueRollEntry(TeamType.HOME, 1, "8+", "9", ActionResult.SUCCESS.name),
        InjuryRollEntry(TeamType.HOME, 1, "6", InjuryRollResult.STUNNED.name),
        FireballEntry(TeamType.HOME, 2, "4+", "4", ActionResult.SUCCESS.name),
        ArmourValueRollEntry(TeamType.HOME, 2, "8+", "9", ActionResult.FAILURE.name),
        BounceLogEntry(ScatterDirection.SW.value),
        BounceLogEntry(ScatterDirection.E.value)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_spell(cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Spell)
    assert event.target == Position(7, 7)
    assert event.spell == "Fireball"

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player
    assert event.action == ActionType.SPELL_HIT
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, InjuryRoll)
    assert event.player == player
    assert event.result == InjuryRollResult.STUNNED

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_2
    assert event.action == ActionType.SPELL_HIT
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player_2

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player_2
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(7, 7)
    assert event.end_space == Position(6, 6)
    assert event.scatter_direction == ScatterDirection.SW

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(6, 6)
    assert event.end_space == Position(7, 6)
    assert event.scatter_direction == ScatterDirection.E

    assert board.get_ball_carrier() is None
    assert board.get_ball_position() == Position(7, 6)

    assert not next(events, None)
    assert not next(log_entries_iter, None)


def test_spell_does_not_consume_following_events(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_ball_carrier(player)
    cmds = [SpellCommand(1, 1, TeamType.AWAY.value, 0, [TeamType.AWAY.value, 0, 255, 7, 7])]
    log_entries = [
        FireballEntry(TeamType.HOME, 1, "4+", "4", ActionResult.SUCCESS.name),
        ArmourValueRollEntry(TeamType.HOME, 1, "8+", "9", ActionResult.SUCCESS.name),
        InjuryRollEntry(TeamType.HOME, 1, "6", InjuryRollResult.STUNNED.name),
        BounceLogEntry(ScatterDirection.NW.value),
        BlockLogEntry(TeamType.HOME, 2)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_spell(cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Spell)
    assert event.target == Position(7, 7)
    assert event.spell == "Fireball"

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player
    assert event.action == ActionType.SPELL_HIT
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, InjuryRoll)
    assert event.player == player
    assert event.result == InjuryRollResult.STUNNED

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(7, 7)
    assert event.end_space == Position(6, 8)
    assert event.scatter_direction == ScatterDirection.NW

    assert board.get_ball_carrier() is None
    assert board.get_ball_position() == Position(6, 8)

    assert not next(events, None)
    assert isinstance(next(log_entries_iter), BlockLogEntry)
