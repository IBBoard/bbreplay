# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import argparse
import os.path
from bbreplay.replay import load
from bbreplay.command import NetworkCommand


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a Blood Bowl replay file.')
    parser.add_argument('replay_file', metavar='replay-file', help='the replay to parse')
    parser.add_argument('--verbose', '-v', action='store_true', help='include verbose messages (including suspected network traffic)')
    args = parser.parse_args()

    print(f"{os.path.basename(args.replay_file)}")
    replay = load(args.replay_file)
    home_team, away_team = replay.get_teams()
    print(f"Home: {home_team.name} ({home_team.race})")
    print(f"Away: {away_team.name} ({away_team.race})")

    for cmd in replay.get_commands():
        if args.verbose or not cmd.is_verbose:
            print(cmd)
    