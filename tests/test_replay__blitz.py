from bbreplay.log import BlockLogEntry, CasualtyRollEntry, InjuryRollEntry
from bbreplay import ScatterDirection, TeamType, Position
from bbreplay.command import *
from bbreplay.player import Player
from bbreplay.replay import *
from . import *


def test_blitz_pushback_followup(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME, 0, [1])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED])
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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


def test_blitz_pushback_no_followup(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME, 0, [0])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED])
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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

    assert not board.is_prone(player)
    assert not board.is_prone(opponent)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_blitz_pushback_no_followup_and_continue_move(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME, 0, [0]),
        # And step away again
        EndMovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED])
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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
    assert isinstance(event, Movement)
    assert event.player == player
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(6, 7)

    assert not board.is_prone(player)
    assert not board.is_prone(opponent)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_blitz_pushback_fend_prevents_followup(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    opponent = away_team.get_player(0)
    opponent.skills.append(Skills.FEND)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED]),
        SkillEntry(opponent.team.team_type, opponent.number, Skills.FEND.name)
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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
    assert isinstance(event, Skill)
    assert event.player == opponent
    assert event.skill == Skills.FEND

    assert player.position == Position(7, 7)
    assert opponent.position == Position(9, 8)

    assert not board.is_prone(player)
    assert not board.is_prone(opponent)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_blitz_single_destination_pushback_fend_prevents_followup(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    opponent = away_team.get_player(0)
    opponent.skills.append(Skills.FEND)
    board.set_position(Position(8, 7), opponent)
    opponent_2 = Player(2, "Player2A", 4, 4, 4, 4, 1, 0, 40000, [])
    board.set_position(Position(9, 6), opponent_2)
    opponent_3 = Player(3, "Player3A", 4, 4, 4, 4, 1, 0, 40000, [])
    board.set_position(Position(9, 7), opponent_3)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED]),
        SkillEntry(opponent.team.team_type, opponent.number, Skills.FEND.name)
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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
    assert isinstance(event, Skill)
    assert event.player == opponent
    assert event.skill == Skills.FEND

    assert player.position == Position(7, 7)
    assert opponent.position == Position(9, 8)

    assert not board.is_prone(player)
    assert not board.is_prone(opponent)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_blitz_pushback_fend_prevents_followup_then_continue_move(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    opponent = away_team.get_player(0)
    opponent.skills.append(Skills.FEND)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        # And step away again
        EndMovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED]),
        SkillEntry(opponent.team.team_type, opponent.number, Skills.FEND.name)
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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
    assert isinstance(event, Skill)
    assert event.player == opponent
    assert event.skill == Skills.FEND

    event = next(events)
    assert isinstance(event, Movement)
    assert event.player == player
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(6, 7)

    assert not board.is_prone(player)
    assert not board.is_prone(opponent)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_blitz_pushback_juggernaut_cancels_fend(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.JUGGERNAUT)
    board.set_position(Position(6, 7), player)
    opponent = away_team.get_player(0)
    opponent.skills.append(Skills.FEND)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME, 0, [1])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED])
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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

    assert player.position == Position(8, 7)
    assert opponent.position == Position(9, 8)

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
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 4, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 5, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME, 0, [1])
    ])
    log_entries = iter_([
        GoingForItEntry(player.team.team_type, player.number, "2+", "2", ActionResult.SUCCESS),
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED])
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME, 0, [1])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.DEFENDER_DOWN]),
        ArmourValueRollEntry(opponent.team.team_type, opponent.number, "9+", "8", ActionResult.FAILURE),
        BounceLogEntry(ScatterDirection.N.value)
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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


def test_blitz_ball_carrier_downed_with_following_movement(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    board.set_ball_carrier(opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME, 0, [1]),
        EndMovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 8])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.DEFENDER_DOWN]),
        ArmourValueRollEntry(opponent.team.team_type, opponent.number, "9+", "8", ActionResult.FAILURE),
        BounceLogEntry(ScatterDirection.N.value)
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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

    event = next(events)
    # Movement tests should check valid movement
    assert isinstance(event, Movement)

    assert not board.is_prone(player)
    assert board.is_prone(opponent)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_blitz_ball_carrier_downed_double_log(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    board.set_ball_carrier(opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME, 0, [1])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.DEFENDER_DOWN]),
        ArmourValueRollEntry(opponent.team.team_type, opponent.number, "9+", "8", ActionResult.FAILURE),
        # Occasionally we get two rolls and the game only honours the second
        BounceLogEntry(ScatterDirection.N.value),
        BounceLogEntry(ScatterDirection.SE.value)
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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
    assert event.scatter_direction == ScatterDirection.SE
    assert event.start_space == Position(9, 8)
    assert event.end_space == Position(10, 7)

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
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 4, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 5, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME, 0, [1])
    ])
    log_entries = iter_([
        GoingForItEntry(player.team.team_type, player.number, "2+", "2", ActionResult.SUCCESS),
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.DEFENDER_DOWN]),
        ArmourValueRollEntry(opponent.team.team_type, opponent.number, "9+", "8", ActionResult.FAILURE),
        BounceLogEntry(ScatterDirection.N.value)
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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


def test_bug8_blitz_into_ball_with_false_double_bounce(board):
    # A bounce to an occupied square without a catch has to indicate a dud scatter
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(6, 7), player)
    player_2 = Player(2, "Player2H", 4, 4, 4, 4, 1, 0, 40000, [])
    home_team.add_player(1, player_2)
    board.set_position(Position(10, 9), player_2)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    board.set_ball_position(Position(9, 8))
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME, 0, [1])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.DEFENDER_DOWN]),
        ArmourValueRollEntry(opponent.team.team_type, opponent.number, "9+", "8", ActionResult.FAILURE),
        BounceLogEntry(ScatterDirection.NE.value),
        BounceLogEntry(ScatterDirection.N.value)
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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
    assert board.get_ball_position() == Position(9, 9)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_gfi_blitz_ball_carrier_with_dumpoff_to_noone_downed(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(3, 7), player)
    opponent = away_team.get_player(0)
    opponent.skills.append(Skills.DUMP_OFF)
    board.set_position(Position(8, 7), opponent)
    board.set_ball_carrier(opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 4, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 5, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DumpOffCommand(1, 1, TeamType.AWAY, 0, []),
        ThrowCommand(1, 1, TeamType.AWAY.value, 0, [TeamType.AWAY.value, 0, 10, 10]),
        Command(1, 1, TeamType.HOME, 0, []),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME, 0, [1])
    ])
    log_entries = iter_([
        ThrowEntry(opponent.team.team_type, opponent.number, "3+", "3", ThrowResult.ACCURATE_PASS.name),
        BounceLogEntry(ScatterDirection.N.value),
        GoingForItEntry(player.team.team_type, player.number, "2+", "2", ActionResult.SUCCESS),
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.DEFENDER_DOWN]),
        ArmourValueRollEntry(opponent.team.team_type, opponent.number, "9+", "8", ActionResult.FAILURE)
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

    event = next(events)
    assert isinstance(event, Blitz)
    assert event.blitzing_player == player
    assert event.blitzed_player == opponent

    for _ in range(4):
        event = next(events)
        # Movement tests should check valid movement
        assert isinstance(event, Movement)

    event = next(events)
    assert isinstance(event, Pass)
    assert event.player == opponent
    assert event.target == Position(10, 10)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.scatter_direction == ScatterDirection.N
    assert event.start_space == Position(10, 10)
    assert event.end_space == Position(10, 11)

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

    assert not board.is_prone(player)
    assert board.is_prone(opponent)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_gfi_blitz_ball_carrier_with_dumpoff_to_noone_fails_gfi_bug(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(3, 7), player)
    opponent = away_team.get_player(0)
    opponent.skills.append(Skills.DUMP_OFF)
    board.set_position(Position(8, 7), opponent)
    board.set_ball_carrier(opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 4, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 5, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DumpOffCommand(1, 1, TeamType.AWAY, 0, []),
        ThrowCommand(1, 1, TeamType.AWAY.value, 0, [TeamType.AWAY.value, 0, 10, 10]),
        Command(1, 1, TeamType.HOME, 0, []),
        RerollCommand(1, 1, TeamType.HOME, 1, [])
    ])
    log_entries = iter_([
        ThrowEntry(opponent.team.team_type, opponent.number, "3+", "3", ThrowResult.ACCURATE_PASS.name),
        BounceLogEntry(ScatterDirection.N.value),
        GoingForItEntry(player.team.team_type, player.number, "2+", "2", ActionResult.FAILURE),
        RerollEntry(TeamType.HOME),
        GoingForItEntry(player.team.team_type, player.number, "2+", "2", ActionResult.SUCCESS),
        # This GFI shouldn't happen, but it does!
        GoingForItEntry(player.team.team_type, player.number, "2+", "2", ActionResult.FAILURE),
        ArmourValueRollEntry(player.team.team_type, player.number, "9+", "8", ActionResult.FAILURE),
        TurnOverEntry(player.team.team_type, "Knocked Down!")
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

    event = next(events)
    assert isinstance(event, Blitz)
    assert event.blitzing_player == player
    assert event.blitzed_player == opponent

    for _ in range(4):
        event = next(events)
        # Movement tests should check valid movement
        assert isinstance(event, Movement)

    event = next(events)
    assert isinstance(event, Pass)
    assert event.player == opponent
    assert event.target == Position(10, 10)

    event = next(events)
    assert isinstance(event, Bounce)
    assert event.scatter_direction == ScatterDirection.N
    assert event.start_space == Position(10, 10)
    assert event.end_space == Position(10, 11)

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Reroll)
    assert event.team == player.team.team_type
    assert event.type == "Team Reroll"

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.result == ActionResult.SUCCESS

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"

    assert board.is_prone(player)
    assert not board.is_prone(opponent)

    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_gfi_blitz_failure_with_casualty(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(3, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    board.set_ball_carrier(opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 4, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 5, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        RerollCommand(1, 1, TeamType.HOME, 1, []),
        ApothecaryCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0])
    ])
    log_entries = iter_([
        GoingForItEntry(player.team.team_type, player.number, "2+", "2", ActionResult.FAILURE),
        RerollEntry(TeamType.HOME),
        GoingForItEntry(player.team.team_type, player.number, "2+", "2", ActionResult.FAILURE),
        ArmourValueRollEntry(player.team.team_type, player.number, "9+", "10", ActionResult.SUCCESS),
        InjuryRollEntry(player.team.team_type, player.number, "1", InjuryRollResult.INJURED.name),
        CasualtyRollEntry(player.team.team_type, player.number, CasualtyResult.BADLY_HURT.name),
        TurnOverEntry(player.team.team_type, "Knocked Down!")
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Reroll)
    assert event.team == player.team.team_type
    assert event.type == "Team Reroll"

    event = next(events)
    assert isinstance(event, Action)
    assert event.action == ActionType.GOING_FOR_IT
    assert event.result == ActionResult.FAILURE

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
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"

    assert board.is_prone(player)
    assert not board.is_prone(opponent)

    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_frenzy_blitz_beyond_gfi_limit(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.FRENZY)
    board.set_position(Position(2, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 3, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 4, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 5, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8])
    ])
    log_entries = iter_([
        # Movement GFI action
        GoingForItEntry(player.team.team_type, player.number, "2+", "2", ActionResult.SUCCESS),
        # Blocking GFI action
        GoingForItEntry(player.team.team_type, player.number, "2+", "2", ActionResult.SUCCESS),
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED])
        # We can't Frenzy and follow-up because we ran out of GFI
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_blitz_with_juggernaut_stopping_both_down(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.JUGGERNAUT)
    board.set_position(Position(6, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        JuggernautChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 1]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        FollowUpChoiceCommand(1, 1, TeamType.HOME, 0, [1])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.BOTH_DOWN]),
        SkillEntry(player.team.team_type, player.number, Skills.JUGGERNAUT.name)
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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
    assert event.dice == [BlockResult.BOTH_DOWN]
    # We still get a BOTH DOWN result, but then we use the skill and do the pushback
    assert event.result == BlockResult.BOTH_DOWN

    event = next(events)
    assert isinstance(event, Skill)
    assert event.player == player
    assert event.skill == Skills.JUGGERNAUT

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


def test_blitz_with_declined_juggernaut_not_stopping_both_down(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.JUGGERNAUT)
    board.set_position(Position(6, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        JuggernautChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.BOTH_DOWN]),
        ArmourValueRollEntry(player.team.team_type, player.number, "9+", "8", ActionResult.FAILURE),
        ArmourValueRollEntry(opponent.team.team_type, opponent.number, "9+", "8", ActionResult.FAILURE),
        TurnOverEntry(player.team.team_type, "Knocked Down!")
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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
    assert event.dice == [BlockResult.BOTH_DOWN]
    assert event.result == BlockResult.BOTH_DOWN

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == opponent

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == opponent
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"

    assert board.is_prone(player)
    assert board.is_prone(opponent)

    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_blitz_with_frenzied_gfi(board):
    # The first block may be within movement, but the second block may need a GFI roll
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.FRENZY)
    board.set_position(Position(4, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 5, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 1, [0, 1, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 10, 7])
    ])
    log_entries = iter_([
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED]),
        SkillEntry(player.team.team_type, player.number, Skills.FRENZY.name),
        GoingForItEntry(player.team.team_type, player.number, "2+", 2, ActionResult.SUCCESS),
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.DEFENDER_STUMBLES]),
        ArmourValueRollEntry(opponent.team.team_type, opponent.number, "10+", 8, ActionResult.FAILURE)
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

    event = next(events)
    assert isinstance(event, Blitz)
    assert event.blitzing_player == player
    assert event.blitzed_player == opponent

    for _ in range(3):
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

    event = next(events)
    assert isinstance(event, Skill)
    assert event.player == player
    assert event.skill == Skills.FRENZY

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player
    assert event.action == ActionType.GOING_FOR_IT
    assert event.result == ActionResult.SUCCESS

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
    assert event.source_space == Position(9, 8)
    assert event.taget_space == Position(10, 7)

    event = next(events)
    assert isinstance(event, FollowUp)
    assert event.following_player == player
    assert event.followed_player == opponent
    assert event.source_space == Position(8, 7)
    assert event.target_space == Position(9, 8)

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == opponent

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == opponent
    assert event.result == ActionResult.FAILURE

    assert not board.is_prone(player)
    assert board.is_prone(opponent)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_blitz_with_double_frenzied_gfi(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    player.skills.append(Skills.FRENZY)
    board.set_position(Position(3, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 4, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 5, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 6, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 7, 7]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 9, 8]),
        DiceChoiceCommand(1, 1, TeamType.HOME, 1, [0, 1, 0]),
        PushbackCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 10, 7])
    ])
    log_entries = iter_([
        GoingForItEntry(player.team.team_type, player.number, "2+", 2, ActionResult.SUCCESS),
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.PUSHED]),
        SkillEntry(player.team.team_type, player.number, Skills.FRENZY.name),
        GoingForItEntry(player.team.team_type, player.number, "2+", 2, ActionResult.SUCCESS),
        BlockLogEntry(player.team.team_type, player.number).complete([BlockResult.DEFENDER_STUMBLES]),
        ArmourValueRollEntry(opponent.team.team_type, opponent.number, "10+", 8, ActionResult.FAILURE)
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

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
    assert event.player == player
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

    event = next(events)
    assert isinstance(event, Skill)
    assert event.player == player
    assert event.skill == Skills.FRENZY

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player
    assert event.action == ActionType.GOING_FOR_IT
    assert event.result == ActionResult.SUCCESS

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
    assert event.source_space == Position(9, 8)
    assert event.taget_space == Position(10, 7)

    event = next(events)
    assert isinstance(event, FollowUp)
    assert event.following_player == player
    assert event.followed_player == opponent
    assert event.source_space == Position(8, 7)
    assert event.target_space == Position(9, 8)

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == opponent

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == opponent
    assert event.result == ActionResult.FAILURE

    assert not board.is_prone(player)
    assert board.is_prone(opponent)

    assert not next(events, None)
    assert not next(cmds, None)
    assert not next(log_entries, None)


def test_bug17_failed_dodge_on_blitz(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(7, 7), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(8, 7), opponent)
    cmds = iter_([
        TargetPlayerCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0,  TeamType.AWAY.value, 0, 8, 7]),
        MovementCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 8]),
        TargetSpaceCommand(1, 1, TeamType.HOME, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 8, 7]),
        RerollCommand(1, 1, TeamType.HOME, 1, [])
    ])
    log_entries = iter_([
        DodgeEntry(player.team.team_type, player.number, "6+", "2", ActionResult.FAILURE),
        RerollEntry(TeamType.HOME),
        DodgeEntry(player.team.team_type, player.number, "6+", "2", ActionResult.FAILURE),
        ArmourValueRollEntry(player.team.team_type, player.number, "9+", "8", ActionResult.FAILURE),
        TurnOverEntry(player.team.team_type, "Knocked Down!")
    ])
    events = replay._process_block(player, opponent, cmds, log_entries, board)

    event = next(events)
    assert isinstance(event, Blitz)
    assert event.blitzing_player == player
    assert event.blitzed_player == opponent

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player
    assert event.action == ActionType.DODGE
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, Reroll)
    assert event.team == player.team.team_type

    event = next(events)
    assert isinstance(event, Action)
    assert event.player == player
    assert event.action == ActionType.DODGE
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, PlayerDown)
    assert event.player == player

    event = next(events)
    assert isinstance(event, ArmourRoll)
    assert event.player == player
    assert event.result == ActionResult.FAILURE

    event = next(events)
    assert isinstance(event, FailedMovement)
    assert event.player == player
    assert event.source_space == Position(7, 7)
    assert event.target_space == Position(8, 8)

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Knocked Down!"

    assert board.is_prone(player)
    assert not board.is_prone(opponent)

    assert not next(cmds, None)
    assert not next(log_entries, None)
    assert not next(events, None)
