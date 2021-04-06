# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING


import argparse
import os.path
from collections import namedtuple
from bbreplay.replay import load
from bbreplay.command import SetupCommand, SetupCompleteCommand, \
    MovementCommand, BlockCommand, PushbackCommand, EndMovementCommand, \
    FollowUpChoiceCommand, \
    EndTurnCommand, AbandonMatchCommand
from bbreplay.teams import TeamType


TOPLINE =      "╔═╤╤╗"
ENDZONE =      "╟╍┿╋╢"
ROW =          "║ ┆┇║"
ROW_AFTER =    "╟╌┼╂╢"
HALFWAY_LINE = "╟━┿╋╢"
BOTTOMLINE =   "╚═╧╧╝"

PITCH_LENGTH = 26
PITCH_WIDTH = 15
TOP_ENDZONE = 0
BOTTOM_ENDZONE = PITCH_LENGTH - 1
LEFT_WIDEZONE = 3 # Note: zero-based indexing
RIGHT_WIDEZONE = 10
HALFWAY = PITCH_LENGTH // 2 - 1
LAST_COLUMN = PITCH_WIDTH - 1


Player = namedtuple('Player', ['team', 'number'])

def draw_filler_row(chars):
    # TODO: String builder
    row = "   " + chars[0]
    for col in range(PITCH_WIDTH):
        row += chars[1] * 3
        if col == LEFT_WIDEZONE or col == RIGHT_WIDEZONE:
            row += chars[3]
        elif col == LAST_COLUMN:
            row += chars[4]
        else:
            row += chars[2]
    row += "\n"
    return row


def player_to_text(player):
    return chr((0x2460 if player.team == TeamType.HOME else 0x2474) + player.number)

def draw_map(positions):
    # TODO: String builder
    map = ""
    for row in range(PITCH_LENGTH):
        if row == 0:
            map += "    "  # Three spaces for numbering, plus one for the border
            for col in range(PITCH_WIDTH):
                map += f"{col:^4}"
            map += "\n"
            map += draw_filler_row(TOPLINE)
        map += f"{row:^3}"
        map += ROW[0]
        for col in range(PITCH_WIDTH):
            map += ROW[1]
            contents = positions.get((col, row), None)
            if contents:
                map += player_to_text(contents)
            else:
                map += ROW[1]
            map += ROW[1]
            if col == LEFT_WIDEZONE or col == RIGHT_WIDEZONE:
                map += ROW[3]
            elif col == LAST_COLUMN:
                map += ROW[4]
            else:
                map += ROW[2]
        map += "\n"
        if row == TOP_ENDZONE:
            map += draw_filler_row(ENDZONE)
        elif row == HALFWAY:
            map += draw_filler_row(HALFWAY_LINE)
        elif row == BOTTOM_ENDZONE:
            map += draw_filler_row(BOTTOMLINE)
        elif row == BOTTOM_ENDZONE - 1:
            map += draw_filler_row(ENDZONE)
        else:
            map += draw_filler_row(ROW_AFTER)
    
    return map


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Map the player positions in a Blood Bowl replay file.')
    parser.add_argument('replay_file', metavar='replay-file', help='the replay to parse')
    parser.add_argument('--verbose', '-v', action='store_true', help='include verbose messages (including suspected network traffic)')
    args = parser.parse_args()

    print(f"{os.path.basename(args.replay_file)}")
    replay = load(args.replay_file)
    home_team, away_team = replay.get_teams()
    print(f"Home: {home_team.name} ({home_team.race})")
    print(f"Away: {away_team.name} ({away_team.race})")

    coords_to_players = {}
    players_to_coords = {}
    setups = 0
    turn = 0
    block_target_coords = None
    blocker = None
# FIXME: Crash because player is out of position (12,13, not 12,12)
# Traceback (most recent call last):
#  File "map.py", line 121, in <module>
#    player = coords_to_players[block_target_coords]
#KeyError: (12, 12)
#
# Failed move in cmd_type=33 due to Beast's tentacles?

    for cmd in replay.get_commands():
        cmd_type = type(cmd)

        if cmd_type is SetupCommand or cmd_type is MovementCommand or cmd_type is EndMovementCommand:
            player = Player(cmd.team, cmd.player_idx)
            if player in players_to_coords:
                old_coords = players_to_coords[player]
                del(coords_to_players[old_coords])
            else:
                old_coords = None
            coords = (cmd.x, cmd.y)

            if coords in coords_to_players:
                swapped_player = coords_to_players[coords]
                print(f"Swapping players {player} & {swapped_player}")
                if old_coords:
                    coords_to_players[old_coords] = swapped_player
                    players_to_coords[swapped_player] = old_coords
                else:
                    print(f"Removing {swapped_player} from {players_to_coords[swapped_player]}")
                    del(players_to_coords[swapped_player])

            coords_to_players[coords] = player
            players_to_coords[player] = coords
        elif cmd_type is BlockCommand:
            blocker = Player(cmd.team, cmd.player_idx)
            block_target_coords = (cmd.x, cmd.y)
        elif cmd_type is FollowUpChoiceCommand:
            if cmd.choice:
                old_coords = players_to_coords[blocker]
                del(coords_to_players[old_coords])
                players_to_coords[blocker] = block_target_coords
                coords_to_players[block_target_coords] = blocker
        elif cmd_type is PushbackCommand:
            player = coords_to_players[block_target_coords]
            if block_target_coords in coords_to_players:
                del(coords_to_players[block_target_coords])
            coords = (cmd.x, cmd.y)
            coords_to_players[coords] = player
            players_to_coords[player] = coords
        elif cmd_type is SetupCompleteCommand:
            setups += 1
            if setups % 2 == 0:
                substitute_coords = []
                for coords in coords_to_players:                    
                    _, y = coords
                    if y == TOP_ENDZONE or y == BOTTOM_ENDZONE:
                        substitute_coords.append(coords)
                
                for coords in substitute_coords:
                    player = coords_to_players[coords]
                    del(coords_to_players[coords])
                    del(players_to_coords[player])
                print("Setup")
                print(draw_map(coords_to_players))
        elif cmd_type is EndTurnCommand or cmd_type is AbandonMatchCommand:
            turn += 1
            print(f"End of Turn {(turn//2)+1} - {cmd.team}")
            print(draw_map(coords_to_players))

        