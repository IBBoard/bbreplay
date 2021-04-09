# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import re
from . import block_string_to_enum
from . import CoinToss, Role, TeamType, ScatterDirection


class MatchLogEntry:
    def __init__(self, home_name, home_abbrev, away_name, away_abbrev):
        self.home_name = home_name
        self.home_abbrev = home_abbrev
        self.away_name = away_name
        self.away_abbrev = away_abbrev
    
    def __repr__(self):
        return f'MatchEntry(home={self.home_name}({self.home_abbrev}, away={self.away_name}({self.away_abbrev}))'


class CoinTossLogEntry:
    def __init__(self, team, choice):
        self.team = team
        self.choice = CoinToss[choice.upper()]
    
    def __repr__(self):
        return f'CoinToss(team={self.team}, choice={self.choice})'


class RoleLogEntry:
    def __init__(self, team, choice):
        self.team = team
        self.choice = Role[choice.upper()]
    
    def __repr__(self):
        return f'Role(team={self.team}, choice={self.choice})'


class KickDirectionLogEntry:
    def __init__(self, team, player, direction):
        self.team = team
        self.player = int(player)
        self.direction = ScatterDirection(int(direction))

    def __repr__(self):
        # XXX Is this relative to the kick direction? i.e. rotated for the other team's kicks
        return f"KickDirection(team={self.team}, player_num={self.player}, direction={self.direction})"


class KickDistanceLogEntry:
    def __init__(self, team, player, distance):
        self.team = team
        self.player = int(player)
        self.distance = int(distance)
    
    def __repr__(self):
        return f"KickDistance(team={self.team}, player_num={self.player}, distance={self.distance})"


class BounceLogEntry:
    def __init__(self, direction):
        self.direction = ScatterDirection(int(direction))

    def __repr__(self):
        # XXX Is this relative to the kick direction? i.e. rotated for the other team's kicks
        return f"Bounce(direction={self.direction})"


TEAM = "([A-Z0-9]+)"

gamelog_re = re.compile('GameLog\(-?[0-9]+\): (.*)')
block_dice_re = re.compile('^\[[^\]]+\]( - \[[^\]]+\])*')
teams_re = re.compile(f"([^\()]+)\({TEAM}\) vs ([^\)]+)\({TEAM}\)")
coin_toss_re = re.compile(f"{TEAM} choose (Heads|Tails)")
role_re = re.compile(f"{TEAM} choose to (Kick|Receive)")
kick_direction_re = re.compile(f"{TEAM} #([0-9]+).* Kick-off Direction \(D8\) : ([1-8])")
kick_distance_re = re.compile(f"{TEAM} #([0-9]+).* Kick-off Distance \(D6\) : (?:[1-6] / 2 {{Kick\}} -> )?([1-6])$")
ball_bounce_re = re.compile("Bounce \(D8\) : ([1-8])")
block_re = re.compile(f"{TEAM} \(([0-9]+)\).*(Block)  Result:")
block_dice_choice_re = re.compile(f"{TEAM} #([0-9]+).* chooses : (Pushed|Defender Stumbles|Defender Down|Both Down|Attacker Down)")
gfi_re = re.compile(f"{TEAM} #([0-9]+).* (Going for it) .* (Success|Failure)")
pickup_re = re.compile(f"{TEAM} #([0-9]+).* (Pick-up) {{AG}} .* (Success|Failure)")
dodge_re = re.compile(f"{TEAM} #([0-9]+).* (Dodge) {{AG}} .* (Success|Failure)")
reroll_re = re.compile(f"{TEAM} use a (re-roll)")
turnover_re = re.compile(f"{TEAM} suffer a (TURNOVER!) : (.*)")
other_success_failure_re = re.compile(f"{TEAM} #([0-9]+) .* ([A-Z][a-z]+)(?: {{[A-Z]+}})? +\([0-9]+\+\).* (Success|Failure)")

turn_regexes = [
    (block_re, None),
    (block_dice_choice_re, None),
    (pickup_re, None),
    (dodge_re, None),
    (gfi_re, None),
    (reroll_re, None),
    (turnover_re, None),
    (teams_re, MatchLogEntry),
    (coin_toss_re, CoinTossLogEntry),
    (role_re, RoleLogEntry),
    (kick_direction_re, KickDirectionLogEntry),
    (kick_distance_re, KickDistanceLogEntry),
    (ball_bounce_re, BounceLogEntry),
    (other_success_failure_re, None)
]

def parse_log_entry(log_entry, home_abbrev, away_abbrev):
    if not log_entry:
        return None

    for re, constructor in turn_regexes:
        result = re.match(log_entry)
        if result:
            groups = list(result.groups())
            if groups[0] == home_abbrev:
                groups[0] = TeamType.HOME
            elif groups[0] == away_abbrev:
                groups[0] = TeamType.AWAY

            return constructor(*groups) if constructor else groups


def parse_block_result(block_entry, pending_block):
    block_results = [block_string_to_enum(block_string.strip(' []')) for block_string in block_entry.split('-')]
    return (*pending_block, block_results)

def parse_log_entries(log_path):
    log_entries = []
    pending_block = None
    home_abbrev = None
    away_abbrev = None
    with open(log_path, 'r') as f:
        for line in f:
            line = line.strip()
            result = gamelog_re.search(line)
            if result:
                log_entry = parse_log_entry(result.group(1), home_abbrev, away_abbrev)
                if not log_entry:
                    # Some even we don't care about yet, so skip it
                    continue
                elif isinstance(log_entry, list) and len(log_entry) == 3 and log_entry[2] == 'Block': # XXX Ugly kludge
                    pending_block = log_entry
                else:
                    if not home_abbrev and isinstance(log_entry, MatchLogEntry):
                        home_abbrev = log_entry.home_abbrev
                        away_abbrev = log_entry.away_abbrev
                    log_entries.append(log_entry)
            else:
                result = block_dice_re.search(line)
                if result:
                    block_result = parse_block_result(result.group(0), pending_block)
                    log_entries.append(block_result)
    return log_entries
