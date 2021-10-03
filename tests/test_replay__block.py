from bbreplay.log import BlockLogEntry
import pytest
from bbreplay import TeamType, Position
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


def test_pushback_against_fend(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(7, 7), player)
    opponent = away_team.get_player(0)
    opponent.skills.append(Skills.FEND)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        # The TargetPlayerCommand is what triggers the call to _process_block
        # TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, …, TeamType.AWAY.value, 0]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED]),
        SkillEntry(opponent.team.team_type, opponent.number, "Fend")
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, None, board)

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
    assert isinstance(event, Skill)
    assert event.player == opponent
    assert event.skill == Skills.FEND

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_frenzy_with_double_pushback(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.FRENZY)
    board.set_position(Position(7, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        # The TargetPlayerCommand is what triggers the call to _process_block
        # TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, …, TeamType.AWAY.value, 0]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 10, 7])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED]),
        SkillEntry(player.team.team_type, player.number, "Frenzy"),
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED])
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, None, board)

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

    event = next(events)
    assert isinstance(event, Skill)
    assert event.player == player
    assert event.skill == Skills.FRENZY

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
    assert event.source_space == Position(9, 8)
    assert event.taget_space == Position(10, 7)

    event = next(events)
    assert isinstance(event, FollowUp)
    assert event.following_player == player
    assert event.followed_player == opponent
    assert event.source_space == Position(8, 7)
    assert event.target_space == Position(9, 8)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_frenzy_with_first_block_down(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.FRENZY)
    board.set_position(Position(7, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        # The TargetPlayerCommand is what triggers the call to _process_block
        # TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, …, TeamType.AWAY.value, 0]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.DEFENDER_DOWN]),
        ArmourValueRollEntry(opponent.team.team_type, opponent.number, "9+", "8", ActionResult.FAILURE)
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, None, board)

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

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_frenzy_against_dodge(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.FRENZY)
    board.set_position(Position(7, 7), player)
    opponent = away_team.get_player(0)
    opponent.skills.append(Skills.DODGE)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        # The TargetPlayerCommand is what triggers the call to _process_block
        # TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, …, TeamType.AWAY.value, 0]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 10, 7])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.DEFENDER_STUMBLES]),
        SkillEntry(opponent.team.team_type, opponent.number, "Dodge"),
        SkillEntry(player.team.team_type, player.number, "Frenzy"),
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED])
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, None, board)

    event = next(events)
    assert isinstance(event, Block)
    assert event.blocking_player == player
    assert event.blocked_player == opponent
    assert event.dice == [BlockResult.DEFENDER_STUMBLES]
    assert event.result == BlockResult.DEFENDER_STUMBLES

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
    assert isinstance(event, DodgeBlock)
    assert event.blocking_player == player
    assert event.blocked_player == opponent

    event = next(events)
    assert isinstance(event, Skill)
    assert event.player == player
    assert event.skill == Skills.FRENZY

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
    assert event.source_space == Position(9, 8)
    assert event.taget_space == Position(10, 7)

    event = next(events)
    assert isinstance(event, FollowUp)
    assert event.following_player == player
    assert event.followed_player == opponent
    assert event.source_space == Position(8, 7)
    assert event.target_space == Position(9, 8)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_frenzy_against_block(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.FRENZY)
    player.skills.append(Skills.BLOCK)
    board.set_position(Position(7, 7), player)
    opponent = away_team.get_player(0)
    opponent.skills.append(Skills.BLOCK)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        # The TargetPlayerCommand is what triggers the call to _process_block
        # TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, …, TeamType.AWAY.value, 0]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 7])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.BOTH_DOWN]),
        SkillEntry(player.team.team_type, player.number, "Block"),
        SkillEntry(opponent.team.team_type, opponent.number, "Block"),
        SkillEntry(player.team.team_type, player.number, "Frenzy"),
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED])
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, None, board)

    event = next(events)
    assert isinstance(event, Block)
    assert event.blocking_player == player
    assert event.blocked_player == opponent
    assert event.dice == [BlockResult.BOTH_DOWN]
    assert event.result == BlockResult.BOTH_DOWN

    event = next(events)
    assert isinstance(event, BlockBothDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, BlockBothDown)
    assert event.player == opponent

    event = next(events)
    assert isinstance(event, Skill)
    assert event.player == player
    assert event.skill == Skills.FRENZY

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
    assert event.taget_space == Position(9, 7)

    event = next(events)
    assert isinstance(event, FollowUp)
    assert event.following_player == player
    assert event.followed_player == opponent
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(8, 7)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_team_reroll_on_block_dice(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(7, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    board.setup_complete()
    cmds = iter_([
        # The TargetPlayerCommand is what triggers the call to _process_block
        # TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, …, TeamType.AWAY.value, 0]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        RerollCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME, 0, [1])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.BOTH_DOWN]),
        RerollEntry(TeamType.HOME),
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED]),
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, None, board)

    event = next(events)
    assert isinstance(event, Reroll)
    assert event.team == TeamType.HOME

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


def test_leader_reroll_on_block_dice(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.LEADER)
    board.set_position(Position(7, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    board.setup_complete()
    cmds = iter_([
        # The TargetPlayerCommand is what triggers the call to _process_block
        # TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, …, TeamType.AWAY.value, 0]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        RerollCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME, 0, [1])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.BOTH_DOWN]),
        LeaderRerollEntry(TeamType.HOME, 1),
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED]),
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, None, board)

    event = next(events)
    assert isinstance(event, Reroll)
    assert event.team == TeamType.HOME

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
