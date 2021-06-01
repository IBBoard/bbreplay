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