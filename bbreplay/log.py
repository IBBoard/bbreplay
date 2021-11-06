# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import re
from . import enum_name_to_enum
from . import CoinToss, Role, TeamType, ScatterDirection, ActionResult, InjuryRollResult, ThrowInDirection, \
    KickoffEvent, Weather, Skills, BlockResult, ThrowResult, CasualtyResult


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


class TossRandomisationEntry:
    def __init__(self):
        self.team = None
        self.result = None

    def __repr__(self):
        return f"TossRandomisation(team={self.team}, result={self.result})"


class MatchLogEntry:
    def __init__(self, home_name, home_abbrev, away_name, away_abbrev):
        self.home_name = home_name
        self.home_abbrev = home_abbrev
        self.away_name = away_name
        self.away_abbrev = away_abbrev

    def __repr__(self):
        return f'MatchEntry(home={self.home_name} ({self.home_abbrev}), away={self.away_name} ({self.away_abbrev}))'


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


class WeatherLogEntry:
    def __init__(self, result):
        self.result = Weather[result.upper().replace(' ', '_')]

    def __repr__(self):
        return f'Weather(result={self.result})'


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


class KickoffEventLogEntry:
    def __init__(self, result):
        self.result = KickoffEvent(int(result))

    def __repr__(self):
        return f'KickoffEvent(result={self.result})'


class ThrowInDirectionLogEntry:
    def __init__(self, direction):
        # This *should* be a D6. But we've only seen values of 2 and 3 so assume it's really a D3 for now
        self.direction = ThrowInDirection(int(direction))

    def __repr__(self):
        return f"ThrowInDirection(direction={self.direction})"


class ThrowInDistanceLogEntry(TeamPlayerEntry):
    def __init__(self, distance):
        self.distance = int(distance)

    def __repr__(self):
        return f"ThrowInDistance(distance={self.distance})"


class BounceLogEntry:
    def __init__(self, direction):
        self.direction = ScatterDirection(int(direction))

    def __repr__(self):
        return f"Bounce(direction={self.direction})"


class ScatterLaunchEntry:
    def __init__(self, direction):
        self.direction = ScatterDirection(int(direction))

    def __repr__(self):
        return f"ScatterLaunchEntry(direction={self.direction})"


class BlockLogEntry(TeamPlayerEntry, PartialEntry):
    def __init__(self, team, player):
        super().__init__(team, player)
        self.results = []

    def complete(self, results):
        self.results = results
        return self

    def __repr__(self):
        return f"Block(team={self.team}, player_num={self.player}, results={self.results})"


class ActionResultEntry(TeamPlayerEntry):
    def __init__(self, name, team, player, required, roll, result):
        super().__init__(team, player)
        self.__name = name
        self.required = required
        self.roll = roll
        self.result = ActionResult[result.upper()] if isinstance(result, str) else result

    def __repr__(self):
        return f"{self.__name}(team={self.team}, player_num={self.player}, required={self.required}, "\
               f"roll={self.roll}, result={self.result})"


class PickupEntry(ActionResultEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__("Pickup", team, player, required, roll, result)


class CatchEntry(ActionResultEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__("Catch", team, player, required, roll, result)


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


class WildAnimalEntry(ActionResultEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__("Wild Animal", team, player, required, roll, result)


class FoulAppearanceEntry(ActionResultEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__("FoulAppearance", team, player, required, roll, result)


class KORecoveryEntry(ActionResultEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__("KORecovery", team, player, required, roll, result)


class SpellEntry(ActionResultEntry):
    def __init__(self, name, team, player, required, roll, result):
        super().__init__(name, team, player, required, roll, result)
        self.spell_type = name


class FireballEntry(SpellEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__("Fireball", team, player, required, roll, result)


class TentacleUseEntry(PartialEntry):
    def __init__(self, team, player):
        self.team = team
        self.player = int(player)

    def complete(self, other_event):
        return TentacledEntry(other_event.team, other_event.player, self.team, self.player,
                              other_event.required, other_event.roll, other_event.result)


class TentacledRollEntry(ActionResultEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__("TentacledRoll", team, player, required, roll, result)


class TentacledEntry(ActionResultEntry):
    def __init__(self, team, player, attacking_team, attacking_player, required, roll, result):
        super().__init__("Tentacled", team, player, required, roll, result)
        self.attacking_team = attacking_team
        self.attacking_player = attacking_player

    def __repr__(self):
        return f"Tentacled(team={self.team}, player_num={self.player}, " \
               f"attacking_team={self.attacking_team}, attacking_player_num={self.attacking_player}, " \
               f"required={self.required}, roll={self.roll}, result={self.result})"


class LeapEntry(ActionResultEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__("Leap", team, player, required, roll, result)


class ThrowEntry(TeamPlayerEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__(team, player)
        self.required = required
        self.roll = int(roll)
        self.result = enum_name_to_enum(result, ThrowResult)

    def __repr__(self):
        return f"Throw(team={self.team}, player_num={self.player}, required={self.required}, roll={self.roll}, " \
               f"result={self.result})"


class ThrowTeammateEntry(TeamPlayerEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__(team, player)
        self.required = required
        self.roll = int(roll)
        self.result = enum_name_to_enum(result, ThrowResult)

    def __repr__(self):
        return f"ThrowTeammate(team={self.team}, player_num={self.player}, required={self.required}, " \
               f"roll={self.roll}, result={self.result})"


class LandingEntry(ActionResultEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__("Landing", team, player, required, roll, result)


class AlwaysHungryEntry(ActionResultEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__("AlwaysHungry", team, player, required, roll, result)


class SkillEntry(TeamPlayerEntry):
    def __init__(self, team, player, skill):
        super().__init__(team, player)
        self.skill = enum_name_to_enum(skill, Skills)

    def __repr__(self):
        return f'Skill(team={self.team}, player_num={self.player}, skill={self.skill})'


def create_skill_roll_entry(skill):
    def __create_skill_roll_entry(team, player, required, roll, result):
        return SkillRollEntry(team, player, skill.name, required, roll, result)
    return __create_skill_roll_entry


class SkillRollEntry(TeamPlayerEntry):
    def __init__(self, team, player, skill, required, roll, result):
        super().__init__(team, player)
        self.skill = enum_name_to_enum(skill, Skills)
        self.required = required
        self.roll = roll
        self.result = ActionResult[result.upper()]

    def __repr__(self):
        return f"SkillRoll(team={self.team}, player_num={self.player}, skill={self.skill}, " \
               f"required={self.required}, roll={self.roll}, result={self.result})"


class RerollEntry(TeamEntry):
    def __init__(self, team):
        super().__init__(team)

    def __repr__(self):
        return f'Reroll(team={self.team})'


# This could be a TeamPlayerEntry but it's more important that we treat it like a RerollEntry
class LeaderRerollEntry(RerollEntry):
    def __init__(self, team, player):
        super().__init__(team)
        self.player = int(player)

    def __repr__(self):
        return f'LeaderReroll(team={self.team}, player_num={self.player})'


# This could be a ActionResultEntry but it's more important that we treat it like a RerollEntry
class ProRerollEntry(RerollEntry):
    def __init__(self, team, player, required, roll, result):
        super().__init__(team)
        self.player = int(player)
        self.required = required
        self.roll = roll
        self.result = ActionResult[result.upper()]

    def __repr__(self):
        return f"ProReroll(team={self.team}, player_num={self.player}, required={self.required}, "\
               f"roll={self.roll}, result={self.result})"


class InjuryRollEntry(TeamPlayerEntry):
    def __init__(self, team, player, roll, result):
        super().__init__(team, player)
        self.roll = roll
        self.result = InjuryRollResult[result.upper()]

    def __repr__(self):
        return f"InjuryRoll(team={self.team}, player_num={self.player}, roll={self.roll}, result={self.result})"


class CasualtyRollEntry(TeamPlayerEntry):
    def __init__(self, team, player, result):
        super().__init__(team, player)
        self.result = enum_name_to_enum(result, CasualtyResult)

    def __repr__(self):
        return f"CasualtyRoll(team={self.team}, player_num={self.player}, result={self.result})"


class ApothecaryLogEntry(TeamPlayerEntry):
    def __init__(self, team, player):
        super().__init__(team, player)

    def __repr__(self):
        return f"Apothecary(team={self.team}, player_num={self.player})"


class TurnOverEntry(TeamEntry):
    def __init__(self, team, reason):
        super().__init__(team)
        self.reason = reason

    def __repr__(self):
        return f'TurnOver(team={self.team}, reason={self.reason})'


OTHER_ENTRY_MAP = {
    "Animal": WildAnimalEntry,
    "Appearance": FoulAppearanceEntry,
    "Catch": CatchEntry,
    "Fireball": FireballEntry,
    "KO": KORecoveryEntry,
    "Leap": LeapEntry,
    "Loner": create_skill_roll_entry(Skills.LONER),
    "Stupid": StupidEntry,
    "Tentacles": TentacledRollEntry,
    "Value": ArmourValueRollEntry,
    "Land": LandingEntry,
    "Hungry": AlwaysHungryEntry,
}


def create_other_entry(team, player, action, required, roll, result):
    if action in OTHER_ENTRY_MAP:
        return OTHER_ENTRY_MAP[action](team, player, required, roll, result)
    else:
        return action, team, player, required, roll, result


TEAM = "([A-Z0-9]+)"
PLAYER = "#([0-9]+) .*"
TEAM_PLAYER = f"{TEAM} {PLAYER}"

toss_randomisation_team_re = re.compile('Team   : ([01])')
toss_randomisation_result_re = re.compile('Result : ([01])')
gamelog_re = re.compile('GameLog\\(-?[0-9]+\\): (.*)')
block_dice_re = re.compile('^\\[[^\\]]+\\]( - \\[[^\\]]+\\])*')
teams_re = re.compile(f"([^\\()]+)\\({TEAM}\\) vs ([^\\)]+)\\({TEAM}\\)")
coin_toss_re = re.compile(f"{TEAM} choose (Heads|Tails)")
role_re = re.compile(f"{TEAM} choose to (Kick|Receive)")
kick_direction_re = re.compile(f"{TEAM_PLAYER} Kick-off Direction \\(D8\\) : ([1-8])")
kick_distance_re = re.compile(f"{TEAM_PLAYER} Kick-off Distance \\(D6\\) : (?:[1-6] / 2 {{Kick}} -> )?([0-6])$")
ball_bounce_re = re.compile("Bounce \\(D8\\) : ([1-8])")
scatter_launch_re = re.compile("Scatter Launch \\(D8\\) : ([1-8])")
block_re = re.compile(f"{TEAM} \\(([0-9]+)\\).*Block  Result:")
block_dice_choice_re = re.compile(f"{TEAM_PLAYER} chooses : "
                                  "(Pushed|Defender Stumbles|Defender Down|Both Down|Attacker Down)")
gfi_re = re.compile(f"{TEAM_PLAYER} Going for it +\\((2\\+|3\\+ Blizzard)\\) : ([0-9]+) -> (Success|Failure)")
pickup_re = re.compile(f"{TEAM_PLAYER} Pick-up {{AG}} +\\(([0-9]+\\+)\\) : .*([0-9]+)(?: Critical)? ->"
                       " (Success|Failure)")
throw_re = re.compile(f"{TEAM_PLAYER} Launch {{AG}} +\\(([0-9]+\\+)\\) : .*([0-9]+)(?: Critical)? ->"
                      " (Fumble|(?:Inaccurate|Accurate) pass)!")
throw_teammate_re = re.compile(f"{TEAM_PLAYER} Throw Team-Mate {{AG}} +\\(([0-9]+\\+)\\) : .*([0-9]+)(?: Critical)? ->"
                               " (Fumble|Inaccurate pass)!")  # Throwing teammates is never accurate, even Crits
dodge_re = re.compile(f"{TEAM_PLAYER} Dodge {{(?:AG|ST)}} +\\(([0-9]+\\+)\\) : .*([0-9]+)(?: Critical)? -> "
                      "(Success|Failure)")
# We're specific about skills because some like Horns and Stunty aren't important to us and just change roll results
skill_re = re.compile(f"{TEAM_PLAYER} uses (Dodge|Block|Diving Tackle|Fend|Frenzy|Sure Hands|Juggernaut)")
pro_reroll_re = re.compile(f"{TEAM_PLAYER} Pro +\\(([0-9]+\\+)\\) : ([0-9]+) -> (Success|Failure)")
tentacle_use_re = re.compile(f"{TEAM_PLAYER} uses Tentacles")
reroll_re = re.compile(f"{TEAM} use a re-roll")
leader_reroll_re = re.compile(f"{TEAM_PLAYER} uses Leader")
turnover_re = re.compile(f"{TEAM} suffer a TURNOVER! : (.*)")
other_success_failure_re = re.compile(f"{TEAM} #([0-9]+) .* ([A-Z][A-Za-z]+)(?: {{[A-Z]+}})? +\\(([0-9]+\\+)\\) :"
                                      ".* ([0-9]+)(?: Critical)? -> (Success|Failure)")
injury_roll_re = re.compile(f"{TEAM_PLAYER} = ([0-9]+) -> (Stunned|KO|Injured)")
casualty_roll_re = re.compile(f"{TEAM_PLAYER} Casualty  : (.*) -> .*")
throw_in_direction_re = re.compile("Throw-in Direction \\(D6\\) : ([1-6]+)")
throw_in_distance_re = re.compile("Throw-in Distance \\(2D6\\) : ([0-9]+)")
kickoff_event_re = re.compile("Kick-Off Table: ([0-9]+)\\. .*")
weather_re = re.compile("Weather Table: [1-6] \\+ [1-6] = [0-9]+\\. (.*)")
apothecary_re = re.compile(f"{TEAM} call on their Apothecary to attempt to heal {PLAYER}.")

turn_regexes = [
    (block_re, BlockLogEntry),
    (pickup_re, PickupEntry),
    (throw_re, ThrowEntry),
    (dodge_re, DodgeEntry),
    (skill_re, SkillEntry),
    (gfi_re, GoingForItEntry),
    (reroll_re, RerollEntry),
    (leader_reroll_re, LeaderRerollEntry),
    (pro_reroll_re, ProRerollEntry),
    (injury_roll_re, InjuryRollEntry),
    (casualty_roll_re, CasualtyRollEntry),
    (turnover_re, TurnOverEntry),
    (tentacle_use_re, TentacleUseEntry),
    (teams_re, MatchLogEntry),
    (coin_toss_re, CoinTossLogEntry),
    (role_re, RoleLogEntry),
    (kick_direction_re, KickDirectionLogEntry),
    (kick_distance_re, KickDistanceLogEntry),
    (throw_in_direction_re, ThrowInDirectionLogEntry),
    (throw_in_distance_re, ThrowInDistanceLogEntry),
    (ball_bounce_re, BounceLogEntry),
    (scatter_launch_re, ScatterLaunchEntry),
    (throw_teammate_re, ThrowTeammateEntry),
    (other_success_failure_re, create_other_entry),
    (kickoff_event_re, KickoffEventLogEntry),
    (weather_re, WeatherLogEntry),
    (apothecary_re, ApothecaryLogEntry)
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
    with open(log_path, 'r') as f:
        return parse_log_entry_lines(f)


def parse_log_entry_lines(lines):
    log_entries = []
    partial_entry = None
    home_abbrev = None
    away_abbrev = None
    event_entries = []
    match_started = False
    in_block = False
    in_select_block = False
    block_has_lines = False
    all_contexts = False
    empty_prev_action = False
    may_merge = False
    toss_randomisation = TossRandomisationEntry()
    turnover_log_entry = None
    is_spell = False
    was_spell = False

    for line in lines:
        line = line.strip()
        if not match_started:
            if line == "|  +- Enter CStateMatchTossCreateResults":
                match_started = True
            else:
                continue
        if line == "|  |":
            continue
        if line.startswith("|  +- Enter CStateMatch"):
            in_block = True
            block_has_lines = False
            in_select_block = line == "|  +- Enter CStateMatchSelectTT"
            may_merge = all_contexts
            all_contexts = in_select_block
            was_spell = is_spell
            is_spell = line.endswith("CStateMatchWizardUseSpellTT")
            continue
        elif line.startswith("|  +- Exit CStateMatch"):
            in_block = False
            all_contexts = all_contexts and block_has_lines
            if is_spell:
                i = 0
                max_i = len(event_entries)
                # We need to move the bounces to the end, because the game logs the bounce before logging
                # that an adjacent player has *also* been flattened, which would give a second bounce
                # instead of a catch if we processed it straight away
                while i < max_i:
                    if isinstance(event_entries[i], BounceLogEntry):
                        event_entries.append(event_entries.pop(i))
                        max_i -= 1
                    else:
                        i += 1

            if turnover_log_entry:
                event_entries.append(turnover_log_entry)
                turnover_log_entry = None
            if may_merge and not empty_prev_action:
                # Bug 16 - merge log entries for a player when they're split by cinematics
                # But don't merge with kickoff bounces
                log_entries[-1].extend(event_entries)
            elif event_entries:
                empty_prev_action = False
                log_entries.append(event_entries)
            elif line == "|  +- Exit CStateMatchActionTT":
                empty_prev_action = True
            event_entries = []
            continue
        elif not in_block:
            continue

        block_has_lines = True

        if in_select_block and all_contexts and not line.startswith("|  | Contexts : "):
            all_contexts = False

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
                if isinstance(log_entry, TurnOverEntry):
                    turnover_log_entry = log_entry
                elif was_spell:
                    if isinstance(log_entry, BounceLogEntry):
                        log_entries[-1].append(log_entry)
                    else:
                        was_spell = False
                elif (isinstance(log_entry, CasualtyRollEntry) or isinstance(log_entry, ApothecaryLogEntry)) \
                        and event_entries and isinstance(event_entries[-1], BounceLogEntry):
                    event_entries.insert(-1, log_entry)
                else:
                    # XXX This is ugly and we need a better way to handle "sometimes we merge, sometimes we don't"
                    if may_merge and not event_entries and isinstance(log_entry, TeamPlayerEntry):
                        # Take the first of the last batch because it's more likely to be a player event
                        # whereas the last one might be a team event
                        prev_log_entry = log_entries[-1][0]
                        if isinstance(prev_log_entry, TeamPlayerEntry) and \
                                (log_entry.team != prev_log_entry.team or log_entry.player != prev_log_entry.player):
                            may_merge = False
                    event_entries.append(log_entry)
        else:
            result = block_dice_re.search(line)
            if result:
                block_dice = [enum_name_to_enum(block_string.strip(' []'), BlockResult)
                              for block_string in result.group(0).split('-')]
                block_result = partial_entry.complete(block_dice)
                event_entries.append(block_result)
                partial_entry = None
                continue
            result = toss_randomisation_team_re.search(line)
            if result:
                toss_randomisation.team = TeamType(int(result.group(1)))
                continue
            result = toss_randomisation_result_re.search(line)
            if result:
                toss_randomisation.result = CoinToss(int(result.group(1)))
                log_entries.append([toss_randomisation])
                continue
    return log_entries
