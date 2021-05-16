from bbreplay.log import BlockLogEntry
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


def test_blitz_pushback_followup(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        # The TargetPlayerCommand is what triggers the call to _process_block
        # TargetPlayerCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, …, TeamType.AWAY.value, 0]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME.value, 0, [1])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED])
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, None, board)

    event = next(events)
    assert isinstance(event, Blitz)
    assert event.blitzing_player == player
    assert event.blitzed_player == opponent

    event = next(events)
    # Movement tests should check valid movement
    assert isinstance(event, Movement)

    event = next(events)
    assert isinstance(event, Block)
    assert event.blocking_player == player
    assert event.blocked_player == opponent
    assert event.dice == [BlockResult.PUSHED]
    assert event.result == BlockResult.PUSHED

    event = next(events)
    assert isinstance(event, Pushback)
    assert event.pushing_player == player
    assert event.pushed_player == opponent
    assert event.source_space == Position(8, 7)
    assert event.taget_space == Position(9, 8)

    event = next(events)
    assert isinstance(event, FollowUp)
    assert event.following_player == player
    assert event.followed_player == opponent
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(8, 7)

    assert not board.is_prone(player)
    assert not board.is_prone(opponent)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_gfi_blitz_pushback_followup(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(3, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        # The TargetPlayerCommand is what triggers the call to _process_block
        # TargetPlayerCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, …, TeamType.AWAY.value, 0]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 4, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 5, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME.value, 0, [1])
    ])
    log_entries = iter_([
        GoingForItEntry(player.team.team_type, player.number, "2+", "2", ActionResult.SUCCESS),
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED])
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, None, board)

    event = next(events)
    assert isinstance(event, Blitz)
    assert event.blitzing_player == player
    assert event.blitzed_player == opponent

    for _ in range(4):
        event = next(events)
        # Movement tests should check valid movement
        assert isinstance(event, Movement)

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, Block)
    assert event.blocking_player == player
    assert event.blocked_player == opponent
    assert event.dice == [BlockResult.PUSHED]
    assert event.result == BlockResult.PUSHED

    event = next(events)
    assert isinstance(event, Pushback)
    assert event.pushing_player == player
    assert event.pushed_player == opponent
    assert event.source_space == Position(8, 7)
    assert event.taget_space == Position(9, 8)

    event = next(events)
    assert isinstance(event, FollowUp)
    assert event.following_player == player
    assert event.followed_player == opponent
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(8, 7)

    assert not board.is_prone(player)
    assert not board.is_prone(opponent)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_blitz_ball_carrier_downed(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    board.set_ball_carrier(opponent)
    cmds = iter_([
        # The TargetPlayerCommand is what triggers the call to _process_block
        # TargetPlayerCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, …, TeamType.AWAY.value, 0]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME.value, 0, [1])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.DEFENDER_DOWN]),
        ArmourValueRollEntry(opponent.team.team_type, opponent.number, "9+", "8", ActionResult.FAILURE),
        BounceLogEntry(ScatterDirection.N.value)
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, None, board)

    event = next(events)
    assert isinstance(event, Blitz)
    assert event.blitzing_player == player
    assert event.blitzed_player == opponent

    event = next(events)
    # Movement tests should check valid movement
    assert isinstance(event, Movement)

    event = next(events)
    assert isinstance(event, Block)
    assert event.blocking_player == player
    assert event.blocked_player == opponent
    assert event.dice == [BlockResult.DEFENDER_DOWN]
    assert event.result == BlockResult.DEFENDER_DOWN

    event = next(events)
    assert isinstance(event, Pushback)
    assert event.pushing_player == player
    assert event.pushed_player == opponent
    assert event.source_space == Position(8, 7)
    assert event.taget_space == Position(9, 8)

    event = next(events)
    assert isinstance(event, FollowUp)
    assert event.following_player == player
    assert event.followed_player == opponent
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(8, 7)

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == opponent

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == opponent
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.scatter_direction == ScatterDirection.N
    assert event.start_space == Position(9, 8)
    assert event.end_space == Position(9, 9)

    assert not board.is_prone(player)
    assert board.is_prone(opponent)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_gfi_blitz_ball_carrier_downed(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(3, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    board.set_ball_carrier(opponent)
    cmds = iter_([
        # The TargetPlayerCommand is what triggers the call to _process_block
        # TargetPlayerCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, …, TeamType.AWAY.value, 0]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 4, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 5, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        MovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME.value, 0, [1])
    ])
    log_entries = iter_([
        GoingForItEntry(player.team.team_type, player.number, "2+", "2", ActionResult.SUCCESS),
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.DEFENDER_DOWN]),
        ArmourValueRollEntry(opponent.team.team_type, opponent.number, "9+", "8", ActionResult.FAILURE),
        BounceLogEntry(ScatterDirection.N.value)
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, None, board)

    event = next(events)
    assert isinstance(event, Blitz)
    assert event.blitzing_player == player
    assert event.blitzed_player == opponent

    for _ in range(4):
        event = next(events)
        # Movement tests should check valid movement
        assert isinstance(event, Movement)

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, Block)
    assert event.blocking_player == player
    assert event.blocked_player == opponent
    assert event.dice == [BlockResult.DEFENDER_DOWN]
    assert event.result == BlockResult.DEFENDER_DOWN

    event = next(events)
    assert isinstance(event, Pushback)
    assert event.pushing_player == player
    assert event.pushed_player == opponent
    assert event.source_space == Position(8, 7)
    assert event.taget_space == Position(9, 8)

    event = next(events)
    assert isinstance(event, FollowUp)
    assert event.following_player == player
    assert event.followed_player == opponent
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(8, 7)

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == opponent

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == opponent
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.scatter_direction == ScatterDirection.N
    assert event.start_space == Position(9, 8)
    assert event.end_space == Position(9, 9)

    assert not board.is_prone(player)
    assert board.is_prone(opponent)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)
