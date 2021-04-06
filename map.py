# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING


import argparse
import os.path
from collections import namedtuple
from bbreplay.replay import load
from bbreplay.command import SetupCommand, SetupCompleteCommand, \
    MovementCommand, BlockCommand, PushbackCommand, DodgeMoveCommand, \
    FollowUpChoiceCommand, \
    EndTurnCommand, AbandonMatchCommand
from bbreplay.teams import PlayerType


TOPLINE =    "╔═╤╗"
ENDZONE =    "╟╌┼╢"
ROW =        "║ ┆║"
HALFWAY =    "╟─┼╢"
BOTTOMLINE = "╚═╧╝"


Player = namedtuple('Player', ['team', 'number'])

def draw_filler_row(chars):
    # TODO: String builder
    row = chars[0]
    for col in range(15):
        row += chars[1] + chars[1]
        if col == 3 or col == 10:
            row += chars[2]
    row += chars[3]
    row += "\n"
    return row


def player_to_text(player):
    return chr((0x2460 if player.team == PlayerType.HOME else 0x2474) + player.number)

def draw_map(positions):
    # TODO: String builder
    map = ""
    for row in range(26):
        if row == 0:
            map += draw_filler_row(TOPLINE)
        map += ROW[0]
        for col in range(15):
            map += ROW[1]
            contents = positions.get((col, row), None)
            if contents:
                map += player_to_text(contents)
            else:
                map += ROW[1]
            if col == 3 or col == 10:
                map += ROW[2]
        map += ROW[3]
        map += "\n"
        if row == 0 or row == 24:
            map += draw_filler_row(ENDZONE)
        elif row == 12:
            map += draw_filler_row(HALFWAY)
        elif row == 25:
            map += draw_filler_row(BOTTOMLINE)
    
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

        if cmd_type is SetupCommand or cmd_type is MovementCommand or cmd_type is DodgeMoveCommand:
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
                    if y == 0 or y == 25:
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

        