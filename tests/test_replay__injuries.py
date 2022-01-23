from . import *
from bbreplay.command import *
from bbreplay.log import CasualtyRollEntry, InjuryRollEntry
from bbreplay.replay import *


def test_armour_roll_with_casualty(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(3, 7), player)
    cmds = iter_([])
    log_entries = iter_([
        ArmourValueRollEntry(player.team.team_type, player.number, "9+", "10", ActionResult.SUCCESS),
        InjuryRollEntry(player.team.team_type, player.number, "1", InjuryRollResult.INJURED.name),
        CasualtyRollEntry(player.team.team_type, player.number, CasualtyResult.BADLY_HURT.name)
    ])
    events = replay._process_armour_roll(player, cmds, log_entries, board)

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
    assert event.result == InjuryRollResult.INJURED

    event = next(events)
    assert isinstance(event, Casualty)
    assert event.player == player
    assert event.result == CasualtyResult.BADLY_HURT

    assert board.is_prone(player)

    assert not next(cmds, None)
    assert not next(log_entries, None)
    assert not next(events, None)


def test_armour_roll_with_casualty_and_decay(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.DECAY)
    board.set_position(Position(3, 7), player)
    cmds = iter_([])
    log_entries = iter_([
        ArmourValueRollEntry(player.team.team_type, player.number, "9+", "10", ActionResult.SUCCESS),
        InjuryRollEntry(player.team.team_type, player.number, "1", InjuryRollResult.INJURED.name),
        CasualtyRollEntry(player.team.team_type, player.number, CasualtyResult.BADLY_HURT.name),
        CasualtyRollEntry(player.team.team_type, player.number, CasualtyResult.SMASHED_KNEE.name)
    ])
    events = replay._process_armour_roll(player, cmds, log_entries, board)

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
    assert event.result == InjuryRollResult.INJURED

    event = next(events)
    assert isinstance(event, Casualty)
    assert event.player == player
    assert event.result == CasualtyResult.BADLY_HURT

    event = next(events)
    assert isinstance(event, Casualty)
    assert event.player == player
    assert event.result == CasualtyResult.SMASHED_KNEE

    assert board.is_prone(player)

    assert not next(cmds, None)
    assert not next(log_entries, None)
    assert not next(events, None)
