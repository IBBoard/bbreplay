# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import argparse
import os.path
from bbreplay.replay import Replay
from bbreplay.command import NetworkCommand


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a Blood Bowl replay file.')
    parser.add_argument('replay_file', metavar='replay-file', help='the replay database to parse')
    parser.add_argument('log_file', metavar='log-file', help='the replay log to parse')
    parser.add_argument('--verbose', '-v', action='store_true', help='include verbose messages (including suspected network traffic)')
    args = parser.parse_args()

    print(f"{os.path.basename(args.replay_file)}")
    replay = Replay(args.replay_file, args.log_file)
    home_team, away_team = replay.get_teams()
    print(f"Home: {home_team.name} ({home_team.race})")
    print(f"Away: {away_team.name} ({away_team.race})")

    print("+++ Events")

    for event in replay.events():
        print(event)

    print("+++ Commands")

    for cmd in replay.get_commands():
        if args.verbose or not cmd.is_verbose:
            print(cmd)

    print("+++ Log entries")

    for log in replay.get_log_entries():
        print(log)
    