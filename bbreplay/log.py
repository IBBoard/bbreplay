# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import re
from . import block_string_to_enum
from . import CoinToss, Role, TeamType, ScatterDirection, ActionResult


class PartialEntry:
    def combine(self, other_entry):
        raise NotImplementedError()


class TeamEntry:
    def __init__(self, team):
        self.team = team


class TeamPlayerEntry(TeamEntry):
    def __init__(self, team, player):
        super().__init__(team)
        self.player = int(player)


class MatchLogEntry:
    def __init__(self, home_name, home_abbrev, away_name, away_abbrev):
        self.home_name = home_name
        self.home_abbrev = home_abbrev
        self.away_name = away_name
        self.away_abbrev = away_abbrev

    def __repr__(self):
        return f'MatchEntry(home={self.home_name}({self.home_abbrev}, away={self.away_name}({self.away_abbrev}))'


class CoinTossLogEntry(TeamEntry):
    def __init__(self, team, choice):
        super().__init__(team)
        self.choice = CoinToss[choice.upper()]

    def __repr__(self):
        return f'CoinToss(team={self.team}, choice={self.choice})'


class RoleLogEntry(TeamEntry):
    def __init__(self, team, choice):
        super().__init__(team)
        self.choice = Role[choice.upper()]

    def __repr__(self):
        return f'Role(team={self.team}, choice={self.choice})'


class KickDirectionLogEntry(TeamPlayerEntry):
    def __init__(self, team, player, direction):
        super().__init__(team, player)
        self.direction = ScatterDirection(int(direction))

    def __repr__(self):
        # XXX Is this relative to the kick direction? i.e. rotated for the other team's kicks
        return f"KickDirection(team={self.team}, player_num={self.player}, direction={self.direction})"


class KickDistanceLogEntry(TeamPlayerEntry):
    def __init__(self, team, player, distance):
        super().__init__(team, player)
        self.distance = int(distance)

    def __repr__(self):
        return f"KickDistance(team={self.team}, player_num={self.player}, distance={self.distance})"


class BounceLogEntry:
    def __init__(self, direction):
        self.direction = ScatterDirection(int(direction))

    def __repr__(self):
        # XXX Is this relative to the kick direction? i.e. rotated for the other team's kicks
        return f"Bounce(direction={self.direction})"


class BlockLogEntry(TeamPlayerEntry, PartialEntry):
    def __init__(self, team, player):
        super().__init__(team, player)
        self.results = []

    def complete(self, results):
        self.results = results
        return self

    def __repr__(self):
        return f"Block(team={self.team}, player={self.player}, results={self.results})"


class ActionResultEntry(TeamPlayerEntry):
    def __init__(self, name, team, player, required, roll, result):
        super().__init__(team, player)
        self.__name = name
        self.required = required
        self.roll = roll
        self.result = ActionResult[result.upper()]

    def __repr__(self):
        return f"{self.__name}(team={self.team}, player={self.player}, required={self.required}, "\
               f"roll={self.roll}, result={self.result})"


class PickupEntry(ActionResultEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__("Pickup", team, player, required, roll, result)


class DodgeEntry(ActionResultEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__("Dodge", team, player, required, roll, result)


class ArmourValueRollEntry(ActionResultEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__("ArmourValueRoll", team, player, required, roll, result)


class GoingForItEntry(ActionResultEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__("GoingForIt", team, player, required, roll, result)


class StupidEntry(ActionResultEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__("Stupid", team, player, required, roll, result)


class DodgeSkillEntry:
    def __init__(self, team, player):
        self.team = team
        self.player = player

    def __repr__(self):
        return f'DodgeSkill(team={self.team}, player={self.player})'


class RerollEntry(TeamEntry):
    def __init__(self, team):
        super().__init__(team)

    def __repr__(self):
        return f'Reroll(team={self.team})'


# This could be a TeamPlayerEntry but it's more important that we treat it like a RerollEntry
class LeaderRerollEntry(RerollEntry):
    def __init__(self, team, player):
        super().__init__(team)
        self.player = player

    def __repr__(self):
        return f'Reroll(team={self.team}, player={self.player})'


def create_other_entry(team, player, action, required, roll, result):
    if action == "Stupid":
        return StupidEntry(team, player, required, roll, result)
    elif action == "Value":
        return ArmourValueRollEntry(team, player, required, roll, result)
    else:
        return action, team, player, required, roll, result


TEAM = "([A-Z0-9]+)"

gamelog_re = re.compile('GameLog\\(-?[0-9]+\\): (.*)')
block_dice_re = re.compile('^\\[[^\\]]+\\]( - \\[[^\\]]+\\])*')
teams_re = re.compile(f"([^\\()]+)\\({TEAM}\\) vs ([^\\)]+)\\({TEAM}\\)")
coin_toss_re = re.compile(f"{TEAM} choose (Heads|Tails)")
role_re = re.compile(f"{TEAM} choose to (Kick|Receive)")
kick_direction_re = re.compile(f"{TEAM} #([0-9]+).* Kick-off Direction \\(D8\\) : ([1-8])")
kick_distance_re = re.compile(f"{TEAM} #([0-9]+).* Kick-off Distance \\(D6\\) : (?:[1-6] / 2 {{Kick}} -> )?([1-6])$")
ball_bounce_re = re.compile("Bounce \\(D8\\) : ([1-8])")
block_re = re.compile(f"{TEAM} \\(([0-9]+)\\).*Block  Result:")
block_dice_choice_re = re.compile(f"{TEAM} #([0-9]+).* chooses : "
                                  "(Pushed|Defender Stumbles|Defender Down|Both Down|Attacker Down)")
gfi_re = re.compile(f"{TEAM} #([0-9]+).* Going for it +\(([0-9]+\+)\) : ([0-9]+) -> .* (Success|Failure)")
pickup_re = re.compile(f"{TEAM} #([0-9]+).* Pick-up {{AG}} +\(([0-9]+\+)\) : .*([0-9]+)(?: Critical)? ->"
                       " (Success|Failure)")
dodge_re = re.compile(f"{TEAM} #([0-9]+).* Dodge {{AG}} +\(([0-9]+\+)\) : .*([0-9]+)(?: Critical)? -> "
                      "(Success|Failure)")
dodge_skill_re = re.compile(f"{TEAM} #([0-9]+).* uses Dodge")
reroll_re = re.compile(f"{TEAM} use a re-roll")
leader_reroll_re = re.compile(f"{TEAM} #([0-9]+).* uses Leader")
turnover_re = re.compile(f"{TEAM} suffer a (TURNOVER!) : (.*)")
other_success_failure_re = re.compile(f"{TEAM} #([0-9]+) .* ([A-Z][a-z]+)(?: {{[A-Z]+}})? +\\(([0-9]+\\+)\\) :"
                                      " .* ([0-9]+)(?: Critical)? -> (Success|Failure)")

turn_regexes = [
    (block_re, BlockLogEntry),
    (pickup_re, PickupEntry),
    (dodge_re, DodgeEntry),
    (dodge_skill_re, DodgeSkillEntry),
    (gfi_re, GoingForItEntry),
    (reroll_re, RerollEntry),
    (leader_reroll_re, LeaderRerollEntry),
    (turnover_re, None),
    (teams_re, MatchLogEntry),
    (coin_toss_re, CoinTossLogEntry),
    (role_re, RoleLogEntry),
    (kick_direction_re, KickDirectionLogEntry),
    (kick_distance_re, KickDistanceLogEntry),
    (ball_bounce_re, BounceLogEntry),
    (other_success_failure_re, create_other_entry)
]


def parse_log_entry(log_entry, home_abbrev, away_abbrev):
    if not log_entry:
        return None

    for regex, constructor in turn_regexes:
        result = regex.match(log_entry)
        if result:
            groups = list(result.groups())
            if groups[0] == home_abbrev:
                groups[0] = TeamType.HOME
            elif groups[0] == away_abbrev:
                groups[0] = TeamType.AWAY
            return constructor(*groups) if constructor else groups


def parse_log_entries(log_path):
    log_entries = []
    partial_entry = None
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
                elif isinstance(log_entry, PartialEntry):
                    partial_entry = log_entry
                else:
                    if not home_abbrev and isinstance(log_entry, MatchLogEntry):
                        home_abbrev = log_entry.home_abbrev
                        away_abbrev = log_entry.away_abbrev
                    if partial_entry:
                        log_entry = partial_entry.complete(log_entry)
                        partial_entry = None
                    log_entries.append(log_entry)
            else:
                result = block_dice_re.search(line)
                if result:
                    block_dice = [block_string_to_enum(block_string.strip(' []'))
                                  for block_string in result.group(0).split('-')]
                    block_result = partial_entry.complete(block_dice)
                    log_entries.append(block_result)
                    partial_entry = None
    return log_entries
