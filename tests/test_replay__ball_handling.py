from bbreplay.log import FireballEntry, InjuryRollEntry
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


def test_pickup_success(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    board.set_ball_position(Position(7, 7))
    cmds = [
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7])
    ]
    log_entries = [
        PickupEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.SUCCESS.name)
    ]
    cmd = cmds[0]
    cmds_iter = iter_(cmds[1:])
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmd, cmds_iter, log_entries_iter, None, board)

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(6, 7)
    assert event.target_space == Position(7, 7)

    event = next(events)
    assert isinstance(event, Pickup)
    assert event.player == player
    assert event.position == Position(7, 7)
    assert event.result == ActionResult.SUCCESS

    assert board.get_ball_carrier() == player
    assert board.get_ball_position() == Position(7, 7)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_pickup_failure(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    board.set_ball_position(Position(7, 7))
    cmds = [
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
    ]
    log_entries = [
        PickupEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        BounceLogEntry(ScatterDirection.NW.value),
        TurnOverEntry(TeamType.HOME, "Pick-up failed!")
    ]
    cmd = cmds[0]
    cmds_iter = iter_(cmds[1:])
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmd, cmds_iter, log_entries_iter, None, board)

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(6, 7)
    assert event.target_space == Position(7, 7)

    event = next(events)
    assert isinstance(event, Pickup)
    assert event.player == player
    assert event.position == Position(7, 7)
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.start_space == Position(7, 7)
    assert event.end_space == Position(6, 8)
    assert event.scatter_direction == ScatterDirection.NW

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Pick-up failed!"

    assert board.get_ball_carrier() is None
    assert board.get_ball_position() == Position(6, 8)

    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)


def test_bounce_from_spell(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_ball_carrier(player)
    cmd = SpellCommand(1, 1, TeamType.AWAY.value, 0, [TeamType.AWAY.value, 0, 255, 7, 7])
    log_entries = [
        FireballEntry(TeamType.HOME, 1, "4+", "4", ActionResult.SUCCESS.name),
        ArmourValueRollEntry(TeamType.HOME, 1, "8+", "9", ActionResult.SUCCESS.name),
        InjuryRollEntry(TeamType.HOME, 1, "6", InjuryRollResult.STUNNED.name),
        BounceLogEntry(ScatterDirection.NW.value)
    ]
    log_entries_iter = iter_(log_entries)
    events = replay._process_spell(cmd, log_entries_iter, board)

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


def test_bounce_from_spell_with_multiple_hits(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(7, 7), player)
    board.set_ball_carrier(player)
    player_2 = Player(2, "Player2H", 4, 4, 4, 4, 1, 0, 40000, [])
    home_team.add_player(1, player_2)
    board.set_position(Position(6, 6), player_2)
    cmd = SpellCommand(1, 1, TeamType.AWAY.value, 0, [TeamType.AWAY.value, 0, 255, 7, 7])
    log_entries = [
        FireballEntry(TeamType.HOME, 1, "4+", "4", ActionResult.SUCCESS.name),
        ArmourValueRollEntry(TeamType.HOME, 1, "8+", "9", ActionResult.SUCCESS.name),
        InjuryRollEntry(TeamType.HOME, 1, "6", InjuryRollResult.STUNNED.name),
        FireballEntry(TeamType.HOME, 2, "4+", "4", ActionResult.FAILURE.name),
        BounceLogEntry(ScatterDirection.NW.value)
    ]
    log_entries_iter = iter_(log_entries)
    events = replay._process_spell(cmd, log_entries_iter, board)

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
    cmd = SpellCommand(1, 1, TeamType.AWAY.value, 0, [TeamType.AWAY.value, 0, 255, 7, 7])
    log_entries = [
        FireballEntry(TeamType.HOME, 1, "4+", "4", ActionResult.SUCCESS.name),
        ArmourValueRollEntry(TeamType.HOME, 1, "8+", "9", ActionResult.SUCCESS.name),
        InjuryRollEntry(TeamType.HOME, 1, "6", InjuryRollResult.STUNNED.name),
        FireballEntry(TeamType.HOME, 2, "4+", "4", ActionResult.SUCCESS.name),
        ArmourValueRollEntry(TeamType.HOME, 2, "8+", "9", ActionResult.FAILURE.name),
        BounceLogEntry(ScatterDirection.SW.value),
        BounceLogEntry(ScatterDirection.E.value)
    ]
    log_entries_iter = iter_(log_entries)
    events = replay._process_spell(cmd, log_entries_iter, board)

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


def test_pickup_success_with_sure_hands(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.SURE_HANDS)
    board.set_position(Position(6, 7), player)
    board.set_ball_position(Position(7, 7))
    cmds = [
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7])
    ]
    log_entries = [
        PickupEntry(TeamType.HOME, player.number, "2+", "1", ActionResult.FAILURE.name),
        SkillEntry(TeamType.HOME, player.number, Skills.SURE_HANDS.name),
        PickupEntry(TeamType.HOME, player.number, "2+", "2", ActionResult.SUCCESS.name)
    ]
    cmd = cmds[0]
    cmds_iter = iter_(cmds[1:])
    log_entries_iter = iter_(log_entries)
    events = replay._process_movement(player, cmd, cmds_iter, log_entries_iter, None, board)

    event = next(events)
    assert isinstance(event, Movement)
    assert event.source_space == Position(6, 7)
    assert event.target_space == Position(7, 7)

    event = next(events)
    assert isinstance(event, Pickup)
    assert event.player == player
    assert event.position == Position(7, 7)
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Reroll)
    assert event.team == TeamType.HOME
    assert event.type == Skills.SURE_HANDS.name.title()

    event = next(events)
    assert isinstance(event, Pickup)
    assert event.player == player
    assert event.position == Position(7, 7)
    assert event.result == ActionResult.SUCCESS

    assert board.get_ball_carrier() == player
    assert board.get_ball_position() == Position(7, 7)

    assert not next(events, None)
    assert not next(cmds_iter, None)
    assert not next(log_entries_iter, None)
