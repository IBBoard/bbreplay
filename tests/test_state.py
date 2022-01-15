from bbreplay import TeamType
from bbreplay.log import *
from bbreplay.command import *
from bbreplay.player import Player
from bbreplay.replay import *
from . import *


def test_leader_reroll_added_once_per_half(board):
    home_team, _ = board.teams
    player = home_team.get_player(0)
    player.skills.append(Skills.LEADER)
    board.set_position(Position(1, 1), player)
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 4
    board.kickoff()
    board.touchdown(player)
    board.end_turn(TeamType.HOME)
    board.prepare_setup()
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 4


def test_leader_reroll_not_added_when_not_used_and_player_not_deployed(board):
    home_team, _ = board.teams
    player = home_team.get_player(0)
    player.skills.append(Skills.LEADER)
    board.set_position(Position(1, 1), player)
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 4
    board.kickoff()
    board.touchdown(player)
    board.end_turn(TeamType.HOME)
    board.prepare_setup()
    board.set_position(OFF_PITCH_POSITION, player)
    board.setup_complete()
    assert not board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 3


def test_leader_reroll_not_readded_after_use(board):
    home_team, _ = board.teams
    player = home_team.get_player(0)
    player.skills.append(Skills.LEADER)
    board.set_position(Position(1, 1), player)
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 4
    board.kickoff()
    board.use_leader_reroll(TeamType.HOME, player)
    board.touchdown(player)
    board.end_turn(TeamType.HOME)
    board.prepare_setup()
    board.setup_complete()
    assert not board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 3


def test_leader_reroll_readded_in_second_half(board):
    home_team, _ = board.teams
    player = home_team.get_player(0)
    player.skills.append(Skills.LEADER)
    board.set_position(Position(1, 1), player)
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 4
    board.kickoff()
    board.end_turn(TeamType.HOME)
    board.start_turn(TeamType.AWAY)
    board.end_turn(TeamType.AWAY)
    # And the other seven turns
    for _ in range(7):
        for team_type in [TeamType.HOME, TeamType.AWAY]:
            board.start_turn(team_type)
            board.end_turn(team_type)
    board.halftime()
    board.prepare_setup()
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 4


def test_leader_reroll_readded_with_second_leader(board):
    home_team, _ = board.teams
    player = home_team.get_player(0)
    player.skills.append(Skills.LEADER)
    board.set_position(Position(1, 1), player)
    extra_player = Player(2, "Player2H", 4, 4, 4, 4, 1, 0, 40000, [Skills.LEADER])
    home_team.add_player(1, extra_player)
    board.set_position(Position(2, 2), extra_player)
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 4
    board.kickoff()
    board.use_leader_reroll(TeamType.HOME, player)
    board.touchdown(player)
    board.end_turn(TeamType.HOME)
    board.prepare_setup()
    board.setup_complete()
    assert board.has_leader_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 4


def test_rerolls_regen_at_halftime(board):
    home_team, _ = board.teams
    player = home_team.get_player(0)
    board.setup_complete()
    assert board.rerolls[TeamType.HOME.value] == 3
    board.kickoff()
    board.use_reroll(TeamType.HOME)
    assert board.rerolls[TeamType.HOME.value] == 2
    board.touchdown(player)
    board.end_turn(TeamType.HOME)
    board.prepare_setup()
    board.setup_complete()
    board.kickoff()
    assert board.rerolls[TeamType.HOME.value] == 2
    board.end_turn(TeamType.AWAY)
    # And the other seven turns
    for _ in range(7):
        for team_type in [TeamType.HOME, TeamType.AWAY]:
            board.start_turn(team_type)
            board.end_turn(team_type)
    board.halftime()
    board.prepare_setup()
    board.setup_complete()
    assert board.rerolls[TeamType.HOME.value] == 3
