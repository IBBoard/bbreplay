from bbreplay import TeamType
from bbreplay.log import *
from bbreplay.command import *
from bbreplay.player import Player
from bbreplay.replay import *
from . import *


def test_no_reroll_with_no_options(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    while board.can_reroll(TeamType.HOME):
        board.use_reroll(TeamType.HOME)
    actions, new_result = replay._process_action_reroll(None, None, player, board)

    assert actions == []
    assert new_result is None


def test_reroll_with_failed_loner(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.LONER)
    cmds = [
        RerollCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
    ]
    log_entries = [
        SkillRollEntry(TeamType.HOME, 1, Skills.LONER.name, "4+", "3", ActionResult.FAILURE.name),
        RerollEntry(TeamType.HOME)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    actions, new_result = replay._process_action_reroll(cmds_iter, log_entries_iter, player, board)

    assert len(actions) == 2
    loner = actions[0]
    assert isinstance(loner, SkillRoll)
    assert loner.player == player
    assert loner.skill == Skills.LONER
    assert loner.result == ActionResult.FAILURE

    event = actions[1]
    assert isinstance(event, Reroll)
    assert event.team == TeamType.HOME

    assert new_result is None


def test_skip_reroll_with_loner(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.LONER)
    cmds = [
        DeclineRerollCommand(1, 1, TeamType.HOME, 0, []),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
    ]
    log_entries = [
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    actions, new_result = replay._process_action_reroll(cmds_iter, log_entries_iter, player, board)

    assert len(actions) == 0
    assert new_result is None


def test_reroll_with_success_on_successful_loner(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.LONER)
    cmds = [
        RerollCommand(1, 1, TeamType.HOME, 1, [])
    ]
    log_entries = [
        SkillRollEntry(TeamType.HOME, 1, Skills.LONER.name, "4+", "4", ActionResult.SUCCESS.name),
        RerollEntry(TeamType.HOME),
        DodgeEntry(TeamType.HOME, 1, "2+", "2", ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    actions, new_result = replay._process_action_reroll(cmds_iter, log_entries_iter, player, board)

    assert len(actions) == 2
    loner = actions[0]
    assert isinstance(loner, SkillRoll)
    assert loner.player == player
    assert loner.skill == Skills.LONER
    assert loner.result == ActionResult.SUCCESS

    event = actions[1]
    assert isinstance(event, Reroll)
    assert event.team == player.team.team_type
    assert event.type == "Team Reroll"

    assert new_result is ActionResult.SUCCESS


def test_reroll_with_failure_on_successful_loner(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.LONER)
    cmds = [
        RerollCommand(1, 1, TeamType.HOME, 1, [])
    ]
    log_entries = [
        SkillRollEntry(TeamType.HOME, 1, Skills.LONER.name, "4+", "4", ActionResult.SUCCESS.name),
        RerollEntry(TeamType.HOME),
        DodgeEntry(TeamType.HOME, 1, "2+", "1", ActionResult.FAILURE.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    actions, new_result = replay._process_action_reroll(cmds_iter, log_entries_iter, player, board)

    assert len(actions) == 2
    loner = actions[0]
    assert isinstance(loner, SkillRoll)
    assert loner.player == player
    assert loner.skill == Skills.LONER
    assert loner.result == ActionResult.SUCCESS

    event = actions[1]
    assert isinstance(event, Reroll)
    assert event.team == player.team.team_type
    assert event.type == "Team Reroll"

    assert new_result is ActionResult.FAILURE


def test_skill_reroll_not_allowed_with_cancelling_skill(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.DODGE)
    board.set_position(Position(12, 12), player)
    opponent = away_team.get_player(0)
    opponent.skills.append(Skills.TACKLE)
    board.set_position(Position(13, 13), opponent)

    cmds = [
        RerollCommand(1, 1, TeamType.HOME, 1, [])
    ]
    log_entries = [
        RerollEntry(TeamType.HOME),
        DodgeEntry(TeamType.HOME, 1, "2+", "1", ActionResult.FAILURE.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    actions, new_result = replay._process_action_reroll(cmds_iter, log_entries_iter, player, board,
                                                        reroll_skill=Skills.DODGE, cancelling_skill=Skills.TACKLE)

    event = actions[0]
    assert isinstance(event, Reroll)
    assert event.team == player.team.team_type
    assert event.type == "Team Reroll"

    assert new_result == ActionResult.FAILURE


def test_leader_reroll_on_sucessful_loner(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.LONER)
    home_player_leader = Player(2, "Player2H", 4, 4, 4, 4, 1, 0, 40000, [Skills.LEADER])
    home_team.add_player(1, home_player_leader)
    board.set_position(Position(1, 1), home_player_leader)
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    cmds = [
        RerollCommand(1, 1, TeamType.HOME, 1, [])
    ]
    log_entries = [
        LeaderRerollEntry(TeamType.HOME, 2),
        SkillRollEntry(TeamType.HOME, 1, Skills.LONER.name, "4+", 6, ActionResult.SUCCESS.name),
        DodgeEntry(TeamType.HOME, 1, "2+", "1", ActionResult.FAILURE.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    actions, new_result = replay._process_action_reroll(cmds_iter, log_entries_iter, player, board)
    events = iter(actions)

    event = next(events)
    assert isinstance(event, SkillRoll)
    assert event.player == player
    assert event.skill == Skills.LONER
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, Reroll)
    assert event.team == player.team.team_type
    assert event.type == "Leader Reroll"

    assert not board.has_leader_reroll(TeamType.HOME)

    assert new_result is ActionResult.FAILURE


def test_leader_reroll_on_failed_loner(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.LONER)
    home_player_leader = Player(2, "Player2H", 4, 4, 4, 4, 1, 0, 40000, [Skills.LEADER])
    home_team.add_player(1, home_player_leader)
    board.set_position(Position(1, 1), home_player_leader)
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    cmds = [
        RerollCommand(1, 1, TeamType.HOME, 1, [])
    ]
    log_entries = [
        LeaderRerollEntry(TeamType.HOME, 2),
        SkillRollEntry(TeamType.HOME, 1, Skills.LONER.name, "4+", 3, ActionResult.FAILURE.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    actions, new_result = replay._process_action_reroll(cmds_iter, log_entries_iter, player, board)
    events = iter(actions)

    event = next(events)
    assert isinstance(event, SkillRoll)
    assert event.player == player
    assert event.skill == Skills.LONER
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Reroll)
    assert event.team == player.team.team_type
    assert event.type == "Leader Reroll"

    assert not board.has_leader_reroll(TeamType.HOME)

    assert new_result is None
