import pytest
from bbreplay import TeamType
from bbreplay.log import *
from bbreplay.command import *
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
    home_team = Team("Home Halflings", "Halfling", 40000, 3, 3, TeamType.HOME)
    home_team.add_player(0, home_player_1)
    return home_team


@pytest.fixture
def away_player_1():
    return Player(1, "Player1A", 4, 4, 4, 4, 1, 0, 40000, [])


@pytest.fixture
def away_team(away_player_1):
    away_team = Team("Away Amazons", "Amazons", 40000, 3, 3, TeamType.AWAY)
    away_team.add_player(0, away_player_1)
    return away_team


@pytest.fixture
def board(home_team, away_team):
    gamestate = GameState(home_team, away_team, TeamType.HOME)
    for _ in gamestate.kickoff():
        pass
    return gamestate


def test_no_reroll_with_no_options(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.rerolls[TeamType.HOME.value] = 0
    actions, new_result = replay._process_action_reroll(None, None, player, board)

    assert actions == []
    assert new_result is None


def test_reroll_with_failed_loner(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.LONER)
    cmds = [
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
    ]
    log_entries = [
        SkillRollEntry(TeamType.HOME, 1, Skills.LONER.name, "4+", "3", ActionResult.FAILURE.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    actions, new_result = replay._process_action_reroll(cmds_iter, log_entries_iter, player, board)

    assert len(actions) == 1
    loner = actions[0]
    assert isinstance(loner, SkillRoll)
    assert loner.player == player
    assert loner.skill == Skills.LONER
    assert loner.result == ActionResult.FAILURE

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
