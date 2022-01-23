from . import *
from bbreplay.command import *
from bbreplay.replay import *


def test_turnover_by_timeout_after_movement(board):
    home_team, away_team = board.teams
    replay = Replay(home_team, away_team, [], [])
    player = home_team.get_player(0)
    board.set_position(Position(0, 0), player)
    opponent = away_team.get_player(0)
    board.set_position(Position(7, 7), opponent)
    cmds = iter_([
        EndMovementCommand(1, 1, TeamType.HOME.value, 0, [TeamType.HOME.value, 0, 0, 0, 0, 0, 0, 0, 1, 1]),
        EndMovementCommand(1, 1, TeamType.AWAY.value, 0, [TeamType.AWAY.value, 0, 0, 0, 0, 0, 0, 0, 8, 8])
    ])
    log_entries = iter_([
        TurnOverEntry(TeamType.HOME, "Time limit exceeded!")
    ])
    events = replay._process_turn(cmds, log_entries, TeamType.HOME, board)

    event = next(events)
    assert isinstance(event, StartTurn)

    event = next(events)
    assert isinstance(event, Movement)

    event = next(events)
    assert isinstance(event, EndTurn)
    assert event.reason == "Time limit exceeded!"

    cmd = next(cmds)
    assert isinstance(cmd, EndMovementCommand)
    assert cmd.team == TeamType.AWAY

    assert not next(events, None)
    assert not next(log_entries, None)
