# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import argparse
import os.path
from bbreplay.replay import Replay
from bbreplay.command import NetworkCommand


def logging_generator(data):
    for i, datum in enumerate(data):
        print(f"\tConsuming {type(datum).__name__} {i}: {datum}")
        yield datum


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a Blood Bowl replay file and dump internal representations')
    parser.add_argument('replay_file', metavar='replay-file', help='the replay database to parse')
    parser.add_argument('log_file', metavar='log-file', help='the replay log to parse')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='include verbose messages (including suspected network traffic)')
    parser.add_argument('--debug', action='store_true',
                        help='include debug messages to track progress')
    args = parser.parse_args()

    print(f"{os.path.basename(args.replay_file)}")
    replay = Replay(args.replay_file, args.log_file)

    if args.debug:
        replay.set_generator(logging_generator)

    home_team, away_team = replay.get_teams()
    print(f"Home: {home_team.name} ({home_team.race})")
    print(f"Away: {away_team.name} ({away_team.race})")

    print("\n+++ Commands")

    for cmd in replay.get_commands():
        if args.verbose or not cmd.is_verbose:
            print(cmd)

    print("\n+++ Log entries")

    for log in replay.get_log_entries():
        print(log)

    print("\n+++ Events")

    for event in replay.events():
        # Fudge the output so that we're not dumping the board each time,
        # because it gets messy and unreadable
        event_details = event._asdict()
        if 'board' in event_details:
            del(event_details['board'])
        print(f"{type(event).__name__}{event_details}")
