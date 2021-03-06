# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import argparse
import os.path
from bbreplay import Peekable, TeamType
from bbreplay.replay import create_replay


class LoggingGenrator(Peekable):
    def __init__(self, generator):
        super().__init__(generator)
        self.__i = 0

    def next(self):
        datum = super().next()
        print(f"\tConsuming {type(datum).__name__} {self.__i}: {datum}")
        self.__i += 1
        return datum


def print_team(team, debug):
    prefix = "Home" if team.team_type == TeamType.HOME else "Away"
    if debug:
        print(f"{prefix}: {team.name} ({team.race} - {team.coach_type.name.title()})")
    else:
        print(f"{prefix}: {team.name} ({team.race})")
    print(f"\t{team.team_value}TV, {team.rerolls} rerolls, {team.apothecaries} apothecaries")
    for idx, player in sorted(enumerate(team.get_players()), key=lambda x: x[1].number):
        if debug:
            print(f"\t{player.number} - {player.name} (idx {idx})")
        else:
            print(f"\t{player.number} - {player.name}")
        if player.skills:
            skill_string = ', '.join(skill.name.replace('_', ' ').title() for skill in player.skills)
            print(f"\t\t{skill_string}")
    print("\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a Blood Bowl replay file and dump internal representations')
    parser.add_argument('replay_file', metavar='replay-file', help='the replay database to parse')
    parser.add_argument('log_file', metavar='log-file', help='the replay log to parse')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='include verbose messages (including suspected network traffic)')
    parser.add_argument('--debug', action='store_true',
                        help='include debug messages to track progress')
    args = parser.parse_args()

    print(f"{os.path.basename(args.replay_file)}\n")
    replay = create_replay(args.replay_file, args.log_file)

    if args.debug:
        replay.set_generator(LoggingGenrator)

    home_team, away_team = replay.get_teams()
    print_team(home_team, args.debug)
    print_team(away_team, args.debug)

    print("\n+++ Commands")

    for i, cmd in enumerate(cmd for cmd in replay.get_commands() if args.verbose or not cmd.is_verbose):
        if args.debug:
            print(f"Command {i} - {cmd}")
        else:
            print(cmd)

    print("\n+++ Log entries")

    for i, log in enumerate(replay.get_log_entries()):
        if args.debug:
            print(f"Log {i} - {log}")
        else:
            print(log)

    print("\n+++ Events")

    for event in replay.events():
        # Fudge the output so that we're not dumping the board each time,
        # because it gets messy and unreadable
        event_details = event._asdict()
        if 'board' in event_details:
            del(event_details['board'])
        print(f"{type(event).__name__}{event_details}")
