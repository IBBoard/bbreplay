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

BOARD_COLOUR = "\u001b[48:5:22;38:5:255m"
HOME_TEAM_COLOUR = "\u001b[38:5:220m"
AWAY_TEAM_COLOUR = "\u001b[38:5:196m"
BALL_COLOUR = "\u001b[38:5:94m"
PIECE_RESET = "\u001b[38:5:255m"
ROW_RESET = "\u001b[0m"


def draw_filler_row(chars, pretty):
    # TODO: String builder
    row = "   "
    if pretty:
        row += BOARD_COLOUR
    row += chars[0]
    for col in range(PITCH_WIDTH):
        row += chars[1] * 3
        if col == LEFT_WIDEZONE_IDX or col == RIGHT_WIDEZONE_IDX - 1:
            row += chars[3]
        elif col == LAST_COLUMN_IDX:
            row += chars[4]
        else:
            row += chars[2]

    if pretty:
        row += ROW_RESET

    row += "\n"
    return row


def object_to_text(obj, pretty):
    if not obj:
        return ROW[1] * 3
    elif isinstance(obj, Ball):
        ball = "●" if not pretty else BALL_COLOUR + "●" + PIECE_RESET  # "🏈" is too wide to align properly☹
        return ROW[1] + ball + ROW[1]  
    else:
        # TODO: Put the ball in the first space if it's being carried!
        return ROW[1] + player_to_text(obj, pretty) + ROW[1]

def player_to_text(player, pretty):
    team_type = player.team.team_type
    player_char = chr((0x2460 if team_type == TeamType.HOME else 0x2474) + player.number - 1)
    if pretty:
        # TODO: Can we pull this from the team? Relies on 24-bit terminals
        colour = HOME_TEAM_COLOUR if team_type == TeamType.HOME else AWAY_TEAM_COLOUR
        player_char = colour + player_char + PIECE_RESET
    return player_char

def draw_map(board, pretty):
    # TODO: String builder
    map = ""
    for row, row_data in enumerate(board):
        if row == 0:
            map += "    "  # Three spaces for numbering, plus one for the border
            for col in range(PITCH_WIDTH):
                map += f"{col:^4}"
            map += "\n"
            map += draw_filler_row(TOPLINE, pretty)
        map += f"{row:^3}"
        map += BOARD_COLOUR
        map += ROW[0]
        for col, contents in enumerate(row_data):
            map += object_to_text(contents, pretty)
            if col == LEFT_WIDEZONE_IDX or col == RIGHT_WIDEZONE_IDX - 1:
                map += ROW[3]
            elif col == LAST_COLUMN_IDX:
                map += ROW[4]
            else:
                map += ROW[2]
        map += ROW_RESET + "\n"
        if row == TOP_ENDZONE_IDX:
            map += draw_filler_row(ENDZONE, pretty)
        elif row == BEFORE_HALFWAY_IDX:
            map += draw_filler_row(HALFWAY_LINE, pretty)
        elif row == BOTTOM_ENDZONE_IDX:
            map += draw_filler_row(BOTTOMLINE, pretty)
        elif row == BOTTOM_ENDZONE_IDX - 1:
            map += draw_filler_row(ENDZONE, pretty)
        else:
            map += draw_filler_row(ROW_AFTER, pretty)

    return map


def print_team(team, pretty):
    prefix = "Home" if team.team_type == TeamType.HOME else "Away"
    print(f"{prefix}: {team.name} ({team.race})")
    for player in sorted(team.get_players(), key=lambda p: p.number):
        print(f"\t{BOARD_COLOUR} {player_to_text(player, pretty)} {ROW_RESET}- {player.name}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Map the player positions in a Blood Bowl replay file.')
    parser.add_argument('replay_file', metavar='replay-file', help='the replay database to parse')
    parser.add_argument('log_file', metavar='log-file', help='the replay log to parse')
    parser.add_argument('--pretty', action='store_true', help='Use ANSII colours for the map')
    args = parser.parse_args()

    print(f"{os.path.basename(args.replay_file)}")
    replay = Replay(args.replay_file, args.log_file)
    home_team, away_team = replay.get_teams()

    print_team(home_team, args.pretty)
    print_team(away_team, args.pretty)

    coords_to_players = {}
    players_to_coords = {}
    turn = 0

    for event in replay.events():
        event_type = type(event)
        if event_type is SetupComplete:
            print("\nSetup")
            print(draw_map(event.board, args.pretty))
        elif event_type is Kickoff:
            print("\nKickoff")
            print(draw_map(event.board, args.pretty))

        