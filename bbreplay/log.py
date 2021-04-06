# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import re
from . import block_string_to_enum


TEAM = "([A-Z0-9]+)"

gamelog_re = re.compile('GameLog\(-?[0-9]+\): (.*)')
block_dice_re = re.compile('^\[[^\]]+\]( - \[[^\]]+\])*')
teams_re = re.compile(f"([^\()]+)\({TEAM}\) vs ([^\)]+)\({TEAM}\)")
coin_toss_re = re.compile(f"{TEAM} choose (Heads|Tails)")
role_re = re.compile(f"{TEAM} choose to (Kick|Receive)")
kick_direction_re = re.compile(f"{TEAM}.* (Kick-off Direction) \(D8\) : ([1-8])")
kick_distance_re = re.compile(f"{TEAM}.* (Kick-off Distance) \(D6\) : (?: [1-6] / 2 {{Kick\}} -> )([1-6])")
ball_bounce_re = re.compile("(Bounce) \(D8\) : ([1-8])")
block_re = re.compile(f"{TEAM} \(([0-9]+)\).*(Block)  Result:")
block_dice_choice_re = re.compile(f"{TEAM} #([0-9]+).* chooses : (Pushed|Defender Stumbles|Defender Down|Both Down|Attacker Down)")
gfi_re = re.compile(f"{TEAM} #([0-9]+).* Going for it .* (Success|Failure)")
pickup_re = re.compile(f"{TEAM} #([0-9]+).* Pick-up {{AG}} .* (Success|Failure)")
dodge_re = re.compile(f"{TEAM} #([0-9]+).* Dodge {{AG}} .* (Success|Failure)")
reroll_re = re.compile(f"{TEAM} use a re-roll")
turnover_re = re.compile(f"{TEAM} suffer a (TURNOVER!) : (.*)")
other_success_failure_re = re.compile(f"{TEAM} #([0-9]+) .* ([A-Z][a-z]+)(?: {{[A-Z]+}})? +\([0-9]+\+\).* (Success|Failure)")

turn_regexes = [
    block_re,
    block_dice_choice_re,
    pickup_re,
    dodge_re,
    gfi_re,
    reroll_re,
    turnover_re,
    teams_re,
    coin_toss_re,
    role_re,
    kick_direction_re,
    kick_distance_re,
    ball_bounce_re,
    other_success_failure_re
]

def parse_log_entry(log_entry):
    if not log_entry:
        return None

    for re in turn_regexes:
        result = re.match(log_entry)
        if result:
            return result.groups()


def parse_block_result(block_entry, pending_block):
    block_results = [block_string_to_enum(block_string.strip(' []')) for block_string in block_entry.split('-')]
    return (*pending_block, block_results)

def parse_log_entries(log_path):
    log_entries = []
    pending_block = None
    with open(log_path, 'r') as f:
        for line in f:
            result = gamelog_re.search(line)
            if result:
                log_entry = parse_log_entry(result.group(1))
                if not log_entry:
                    # Some even we don't care about yet, so skip it
                    continue
                elif len(log_entry) == 3 and log_entry[2] == 'Block':
                    pending_block = log_entry
                else:
                    log_entries.append(log_entry)
            else:
                result = block_dice_re.search(line)
                if result:
                    block_result = parse_block_result(result.group(0), pending_block)
                    log_entries.append(block_result)
    print(log_entries)
    return log_entries
