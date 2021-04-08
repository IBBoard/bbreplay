# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING


import argparse
import os.path
from collections import namedtuple
from bbreplay import TeamType, PITCH_LENGTH, PITCH_WIDTH, TOP_ENDZONE_IDX, BOTTOM_ENDZONE_IDX, \
    LAST_COLUMN_IDX, LEFT_WIDEZONE_IDX, RIGHT_WIDEZONE_IDX, AFTER_HALFWAY_IDX, BEFORE_HALFWAY_IDX
from bbreplay.replay import Replay, SetupComplete, Kickoff
from bbreplay.player import Ball
from bbreplay.command import SetupCommand, SetupCompleteCommand, \
    MovementCommand, BlockCommand, PushbackCommand, EndMovementCommand, \
    FollowUpChoiceCommand, \
    EndTurnCommand, AbandonMatchCommand


TOPLINE =      "╔═╤╤╗"
ENDZONE =      "╟╍┿╋╢"
ROW =          "║ ┆┇║"
ROW_AFTER =    "╟╌┼╂╢"
HALFWAY_LINE = "╟━┿╋╢"
BOTTOMLINE =   "╚═╧╧╝"


def draw_filler_row(chars):
    # TODO: String builder
    row = "   " + chars[0]
    for col in range(PITCH_WIDTH):
        row += chars[1] * 3
        if col == LEFT_WIDEZONE_IDX or col == RIGHT_WIDEZONE_IDX - 1:
            row += chars[3]
        elif col == LAST_COLUMN_IDX:
            row += chars[4]
        else:
            row += chars[2]
    row += "\n"
    return row


def object_to_text(obj):
    if not obj:
        return ROW[1] * 3
    elif isinstance(obj, Ball):
        return ROW[1] + "B" + ROW[1]  # "🏈" is too wide ☹
    else:
        # TODO: Put the ball in the first space if it's being carried!
        return ROW[1] + player_to_text(obj) + ROW[1]

def player_to_text(player):
    return chr((0x2460 if player.team.team_type == TeamType.HOME else 0x2474) + player.number - 1)

def draw_map(board):
    # TODO: String builder
    map = ""
    for row, row_data in enumerate(board):
        if row == 0:
            map += "    "  # Three spaces for numbering, plus one for the border
            for col in range(PITCH_WIDTH):
                map += f"{col:^4}"
            map += "\n"
            map += draw_filler_row(TOPLINE)
        map += f"{row:^3}"
        map += ROW[0]
        for col, contents in enumerate(row_data):
            map += object_to_text(contents)
            if col == LEFT_WIDEZONE_IDX or col == RIGHT_WIDEZONE_IDX - 1:
                map += ROW[3]
            elif col == LAST_COLUMN_IDX:
                map += ROW[4]
            else:
                map += ROW[2]
        map += "\n"
        if row == TOP_ENDZONE_IDX:
            map += draw_filler_row(ENDZONE)
        elif row == BEFORE_HALFWAY_IDX:
            map += draw_filler_row(HALFWAY_LINE)
        elif row == BOTTOM_ENDZONE_IDX:
            map += draw_filler_row(BOTTOMLINE)
        elif row == BOTTOM_ENDZONE_IDX - 1:
            map += draw_filler_row(ENDZONE)
        else:
            map += draw_filler_row(ROW_AFTER)
    
    return map


def print_team(team):
    prefix = "Home" if team.team_type == TeamType.HOME else "Away"
    print(f"{prefix}: {team.name} ({team.race})")
    for player in sorted(team.get_players(), key=lambda p: p.number):
        print(f"\t{player_to_text(player)} - {player.name}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Map the player positions in a Blood Bowl replay file.')
    parser.add_argument('replay_file', metavar='replay-file', help='the replay database to parse')
    parser.add_argument('log_file', metavar='log-file', help='the replay log to parse')
    args = parser.parse_args()

    print(f"{os.path.basename(args.replay_file)}")
    replay = Replay(args.replay_file, args.log_file)
    home_team, away_team = replay.get_teams()

    print_team(home_team)
    print_team(away_team)

    coords_to_players = {}
    players_to_coords = {}
    turn = 0

    for event in replay.events():
        event_type = type(event)
        if event_type is SetupComplete:
            print("\nSetup")
            print(draw_map(event.board))
        elif event_type is Kickoff:
            print("\nKickoff")
            print(draw_map(event.board))

        