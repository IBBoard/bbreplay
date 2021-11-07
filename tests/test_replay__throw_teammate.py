from bbreplay.log import AlwaysHungryEntry, LandingEntry, ScatterLaunchEntry, ThrowTeammateEntry
import pytest
from bbreplay import ScatterDirection, TeamType, Position
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
def home_player_2():
    return Player(2, "Player2H", 4, 4, 4, 4, 1, 0, 40000, [])


@pytest.fixture
def home_team(home_player_1, home_player_2):
    home_team = Team("Home Halflings", "Halfling", 40000, 3, 3, 0, TeamType.HOME)
    home_team.add_player(0, home_player_1)
    home_team.add_player(1, home_player_2)
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


def test_throwing_teammate_successful_landing(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    player_1.skills.append(Skills.THROW_TEAMMATE)
    board.set_position(Position(7, 12), player_1)
    player_2 = home_team.get_player(1)
    player_2.skills.append(Skills.RIGHT_STUFF)
    board.set_position(Position(7, 11), player_2)
    cmds = [
        TargetPlayerCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0, 1, 9, 18]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0, 1, 26, 0, 0, 0, 7, 11, 0, 0])
    ]
    log_entries = [
        ThrowTeammateEntry(TeamType.HOME, 1, "6+", 6, ThrowResult.INACCURATE_PASS.name),
        ScatterLaunchEntry(ScatterDirection.NW.value),
        ScatterLaunchEntry(ScatterDirection.SE.value),
        ScatterLaunchEntry(ScatterDirection.E.value),
        LandingEntry(TeamType.HOME, 2, "4+", 4, ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw_teammate(player_1, player_2, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, ThrowTeammate)
    assert event.player == player_1
    assert event.thrown_player == player_2
    assert event.target == Position(9, 18)
    assert event.result == ThrowResult.INACCURATE_PASS

    event = next(events)
    assert isinstance(event, Scatter)
    assert event.start_space == Position(9, 18)
    assert event.end_space == Position(10, 18)

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_2
    assert event.action == ActionType.LANDING
    assert event.result == ActionResult.SUCCESS

    assert player_2.position == Position(10, 18)
    assert not board.is_prone(player_2)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_throwing_teammate_failed_landing(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    player_1.skills.append(Skills.THROW_TEAMMATE)
    board.set_position(Position(7, 12), player_1)
    player_2 = home_team.get_player(1)
    player_2.skills.append(Skills.RIGHT_STUFF)
    board.set_position(Position(7, 11), player_2)
    cmds = [
        TargetPlayerCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0, 1, 9, 18]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0, 1, 26, 0, 0, 0, 7, 11, 0, 0])
    ]
    log_entries = [
        ThrowTeammateEntry(TeamType.HOME, 1, "6+", 6, ThrowResult.INACCURATE_PASS.name),
        ScatterLaunchEntry(ScatterDirection.NW.value),
        ScatterLaunchEntry(ScatterDirection.SE.value),
        ScatterLaunchEntry(ScatterDirection.E.value),
        LandingEntry(TeamType.HOME, 2, "4+", 3, ActionResult.FAILURE.name),
        ArmourValueRollEntry(player_2.team.team_type, player_2.number, "9+", "8", ActionResult.FAILURE)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw_teammate(player_1, player_2, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, ThrowTeammate)
    assert event.player == player_1
    assert event.thrown_player == player_2
    assert event.target == Position(9, 18)
    assert event.result == ThrowResult.INACCURATE_PASS

    event = next(events)
    assert isinstance(event, Scatter)
    assert event.start_space == Position(9, 18)
    assert event.end_space == Position(10, 18)

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_2
    assert event.action == ActionType.LANDING
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player_2

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player_2
    assert event.result == ActionResult.FAILURE

    assert player_2.position == Position(10, 18)
    assert board.is_prone(player_2)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_throwing_teammate_fumble_pickup_failed_landing(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    player_1.skills.append(Skills.THROW_TEAMMATE)
    board.set_position(Position(7, 12), player_1)
    player_2 = home_team.get_player(1)
    player_2.skills.append(Skills.RIGHT_STUFF)
    board.set_position(Position(7, 11), player_2)
    cmds = [
        TargetPlayerCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0, 1, 9, 18]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0, 1, 26, 0, 0, 0, 7, 11, 0, 0]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0])
    ]
    log_entries = [
        ThrowTeammateEntry(TeamType.HOME, 1, "6+", 6, ThrowResult.FUMBLE.name),
        LandingEntry(TeamType.HOME, 2, "4+", 3, ActionResult.FAILURE.name),
        ArmourValueRollEntry(player_2.team.team_type, player_2.number, "9+", "8", ActionResult.FAILURE)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw_teammate(player_1, player_2, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, ThrowTeammate)
    assert event.player == player_1
    assert event.thrown_player == player_2
    assert event.target == Position(9, 18)
    assert event.result == ThrowResult.FUMBLE

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_2
    assert event.action == ActionType.LANDING
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player_2

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player_2
    assert event.result == ActionResult.FAILURE

    assert player_2.position == Position(7, 11)
    assert board.is_prone(player_2)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_throwing_teammate_successful_always_hungry(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player_1 = home_team.get_player(0)
    player_1.skills.append(Skills.THROW_TEAMMATE)
    player_1.skills.append(Skills.ALWAYS_HUNGRY)
    board.set_position(Position(7, 12), player_1)
    player_2 = home_team.get_player(1)
    player_2.skills.append(Skills.RIGHT_STUFF)
    board.set_position(Position(7, 11), player_2)
    cmds = [
        TargetPlayerCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0, 1, 9, 18]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 1, [0, 0, 0, 1, 26, 0, 0, 0, 7, 11, 0, 0])
    ]
    log_entries = [
        AlwaysHungryEntry(TeamType.HOME, 1, "2+", 2, ActionResult.SUCCESS.name),
        ThrowTeammateEntry(TeamType.HOME, 1, "6+", 6, ThrowResult.INACCURATE_PASS.name),
        ScatterLaunchEntry(ScatterDirection.NW.value),
        ScatterLaunchEntry(ScatterDirection.SE.value),
        ScatterLaunchEntry(ScatterDirection.E.value),
        LandingEntry(TeamType.HOME, 2, "4+", 4, ActionResult.SUCCESS.name)
    ]
    cmds_iter = iter_(cmds)
    log_entries_iter = iter_(log_entries)
    events = replay._process_throw_teammate(player_1, player_2, cmds_iter, log_entries_iter, board)

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_1
    assert event.action == ActionType.ALWAYS_HUNGRY
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, ThrowTeammate)
    assert event.player == player_1
    assert event.thrown_player == player_2
    assert event.target == Position(9, 18)
    assert event.result == ThrowResult.INACCURATE_PASS

    event = next(events)
    assert isinstance(event, Scatter)
    assert event.start_space == Position(9, 18)
    assert event.end_space == Position(10, 18)

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player_2
    assert event.action == ActionType.LANDING
    assert event.result == ActionResult.SUCCESS

    assert player_2.position == Position(10, 18)
    assert not board.is_prone(player_2)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)
