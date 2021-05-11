# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING


import argparse
import os.path
import time
from bbreplay import TeamType, Position, PITCH_LENGTH, PITCH_WIDTH, NEAR_ENDZONE_IDX, FAR_ENDZONE_IDX, \
    LAST_COLUMN_IDX, LEFT_WIDEZONE_IDX, RIGHT_WIDEZONE_IDX, BEFORE_HALFWAY_IDX
from bbreplay.replay import create_replay, TeamSetupComplete, SetupComplete, Kickoff, EndTurn, KickoffEventTuple, \
    WeatherTuple, FailedMovement


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

SLEEP_TIME = 0.2


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


def player_to_text(player, pretty, board=None):
    team_type = player.team.team_type
    if pretty:
        # TODO: Can we pull this from the team? Relies on 24-bit terminals
        colour = HOME_TEAM_COLOUR if team_type == TeamType.HOME else AWAY_TEAM_COLOUR
    if board and board.get_ball_position() == player.position:
        if pretty:
            player_str = BALL_COLOUR + "●" + colour
        else:
            player_str = "●"
    else:
        player_str = ROW[1]
    player_str += chr((0x2460 if team_type == TeamType.HOME else 0x2474) + player.number - 1)
    if board and board.is_prone(player):
        player_str += "🡻"
    else:
        player_str += ROW[1]
    if pretty:
        player_str = colour + player_str + PIECE_RESET
    return player_str


def draw_map(board, pretty):
    # TODO: String builder
    map = ""
    has_ball_carrier = board.get_ball_carrier() is not None
    ball_position = board.get_ball_position()
    for row in range(PITCH_LENGTH - 1, -1, -1):
        row_data = board[row]
        if row == NEAR_ENDZONE_IDX:
            map += draw_filler_row(ENDZONE, pretty)
        elif row == BEFORE_HALFWAY_IDX:
            map += draw_filler_row(HALFWAY_LINE, pretty)
        elif row == FAR_ENDZONE_IDX:
            map += draw_filler_row(TOPLINE, pretty)
        elif row == FAR_ENDZONE_IDX - 1:
            map += draw_filler_row(ENDZONE, pretty)
        else:
            map += draw_filler_row(ROW_AFTER, pretty)
        map += f"{row:^3}"
        if pretty:
            map += BOARD_COLOUR
        map += ROW[0]
        for col in range(PITCH_WIDTH):
            player = row_data[col]
            if player:
                map += player_to_text(player, pretty, board)
            elif not has_ball_carrier and ball_position == Position(col, row):
                ball = ROW[1] + "●" + ROW[1]  # "🏈" is too wide to align properly☹
                map += ball if not pretty else BALL_COLOUR + ball + PIECE_RESET
            else:
                map += ROW[1] * 3

            if col == LEFT_WIDEZONE_IDX or col == RIGHT_WIDEZONE_IDX - 1:
                map += ROW[3]
            elif col == LAST_COLUMN_IDX:
                map += ROW[4]
            else:
                map += ROW[2]
        if pretty:
            map += ROW_RESET
        map += "\n"
        if row == 0:
            map += draw_filler_row(BOTTOMLINE, pretty)
            map += "    "  # Three spaces for numbering, plus one for the border
            for col in range(PITCH_WIDTH):
                map += f"{col:^4}"
            map += "\n"
    return map


def print_team(team, pretty):
    prefix = "Home" if team.team_type == TeamType.HOME else "Away"
    print(f"{prefix}: {team.name} ({team.race})")
    for player in sorted(team.get_players(), key=lambda p: p.number):
        if pretty:
            print(f"\t{BOARD_COLOUR} {player_to_text(player, pretty)} {ROW_RESET}- {player.name}")
        else:
            print(f"\t{player_to_text(player, pretty)} - {player.name}")


def reset_console():
    # Add the rows for the lines, the numbers, and the title
    print(f"\u001b[1000D\u001b[{PITCH_LENGTH*2+4}A", end="")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Map the player positions in a Blood Bowl replay file each turn.')
    parser.add_argument('replay_file', metavar='replay-file', help='the replay database to parse')
    parser.add_argument('log_file', metavar='log-file', help='the replay log to parse')
    parser.add_argument('--pretty', action='store_true', help='Use ANSII colours for the map')
    parser.add_argument('--animate', action='store_true',
                        help='Use ANSII commands to animate move-by-move. Requires --pretty')
    parser.add_argument('--from', dest='from_turn', type=int, default=0, help='turn number to map from')
    args = parser.parse_args()

    print(f"{os.path.basename(args.replay_file)}")
    replay = create_replay(args.replay_file, args.log_file)
    home_team, away_team = replay.get_teams()

    print_team(home_team, args.pretty)
    print_team(away_team, args.pretty)

    coords_to_players = {}
    players_to_coords = {}
    turn = 0
    board = None

    max_title_length = len("End of turn 16 - ") + max(len(home_team.name), len(away_team.name))

    def print_title(text):
        if args.pretty and args.animate:
            print(text, end="")
            print(" " * (max_title_length - len(text)))
        else:
            print("\n", text)

    needs_reset = args.from_turn <= 1

    try:
        for event in replay.events():
            event_type = type(event)
            if event_type in [KickoffEventTuple, WeatherTuple, FailedMovement, TeamSetupComplete]:
                continue
            if args.pretty and args.animate and board and board.turn >= args.from_turn:
                if needs_reset:
                    time.sleep(SLEEP_TIME)
                    reset_console()
                else:
                    needs_reset = True
            if hasattr(event, 'board'):
                board = event.board
            if board and board.turn < args.from_turn:
                continue
            if event_type is SetupComplete:
                print_title("Setup")
                print(draw_map(event.board, args.pretty))
                if args.pretty and args.animate:
                    time.sleep(SLEEP_TIME * 10)
            elif event_type is Kickoff:
                print_title("Kickoff")
                print(draw_map(event.board, args.pretty))
                if args.pretty and args.animate:
                    time.sleep(SLEEP_TIME * 10)
            elif event_type is EndTurn:
                print_title(f'End of Turn {event.number} - {replay.get_team(event.team).name}')
                print(draw_map(event.board, args.pretty))
                if args.pretty and args.animate:
                    time.sleep(SLEEP_TIME * 10)
            elif args.pretty and args.animate and board:
                print_title(f"Turn {board.turn} - {board.turn_team.name}")
                print(draw_map(board, args.pretty))
    except Exception as ex:
        print("\nLast positions")
        print(draw_map(board, args.pretty))
        raise ex
