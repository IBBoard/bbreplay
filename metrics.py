# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import argparse
import glob
import json
import os.path
import sqlite3
import sys
from pathlib import Path
from bbreplay import TeamType
from bbreplay.command import create_commands
from bbreplay.log import parse_log_entries
from bbreplay.replay import Replay
from bbreplay.teams import create_team


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a batch of Blood Bowl replay files to calculate'
                                                 ' coverage/completeness metrics')
    parser.add_argument('replays_dir', metavar='replays-dir', help='input directory of replays and logs')
    parser.add_argument('--output', '-o', help='output file for metrics (otherwise prints to stdout)')
    args = parser.parse_args()

    total_commands = 0
    total_processed = 0
    results = {}

    for db_path in glob.glob(os.path.join(args.replays_dir, '*.db')):
        log_path = Path(db_path).with_suffix('.log')
        if not log_path.exists():
            print(f"Found replay file with no matching log - {db_path}", sys.stderr)
            continue

        # Duplicate the `create_replay()` function because we need to wrap the commands
        db = sqlite3.connect(db_path)
        home_team = create_team(db, TeamType.HOME)
        away_team = create_team(db, TeamType.AWAY)

        commands = create_commands(db)
        log_entries = parse_log_entries(log_path)
        num_commands = len(commands)
        total_commands += num_commands

        # Wrap commands in an iter so we can track how far the process got
        commands = iter(commands)
        replay = Replay(home_team, away_team, commands, log_entries)

        i = 0

        try:
            replay.validate()
            # We can't just do len() because it might throw an exception
            # But we don't care about the content, just the number
            for _ in replay.events():
                i += 1
        except:  # noqa: E722 - we explicitly don't want to stop on anything
            pass
        finally:
            num_commands_processed = num_commands - len(list(commands))
            total_processed += num_commands_processed
            results[db_path] = {
                "commands": num_commands,
                "events": i,
                "processed": num_commands_processed
            }

    metrics = {
        'total_commands': total_commands,
        'total_processed': total_processed,
        'results': results
    }

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(metrics, f)
    else:
        print(json.dumps(metrics, indent=4, sort_keys=True))
