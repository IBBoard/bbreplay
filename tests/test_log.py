from bbreplay import ActionResult, ScatterDirection, TeamType
from bbreplay.log import ApothecaryLogEntry, ArmourValueRollEntry, BlockLogEntry, BounceLogEntry, CatchEntry, \
    DodgeEntry, FireballEntry, FoulAppearanceEntry, GoingForItEntry, InjuryRollEntry, RerollEntry, SkillEntry, \
    TurnOverEntry, WildAnimalEntry, parse_log_entry, parse_log_entry_lines, CasualtyRollEntry


STARTING_LINE = "|  +- Enter CStateMatchTossCreateResults"
STARTING_LINES = [
    STARTING_LINE,
    "|  +- Enter CStateMatch"
]
ENDING_LINES = [
    "|  +- Exit CStateMatch"
]


def test_parse_ignores_non_gamelog_lines():
    log_lines = STARTING_LINES + \
        [
            "|  | GameLog(02): WAR #05 Pinky Injury  : 6 + 3 = 9 -> KO'd",
            "|  | GameLog(-1): WAR suffer a TURNOVER! : Knocked Down!",
            "|  | Entering CStatePlayerTeamChooseOptionalSkills, Warpstone Heat is NOT WAITING FOR player decision",
            "|  | GameLog(13): WAR call on their Apothecary to attempt to heal #05 Pinky.",
        ] \
        + ENDING_LINES
    match_log_entries = parse_log_entry_lines(log_lines)
    assert len(match_log_entries) == 3


def test_parse_apothecary_puts_turnover_at_end():
    log_lines = STARTING_LINES + \
        [
            "|  | GameLog(02): WAR #05 Pinky Armour Value  (9+) : 6 + 5 = 11 -> Success",
            "|  | GameLog(02): WAR #05 Pinky Injury  : 6 + 3 = 9 -> KO'd",
            "|  | GameLog(-1): WAR suffer a TURNOVER! : Knocked Down!",
            "|  | GameLog(13): WAR call on their Apothecary to attempt to heal #05 Pinky.",
        ] \
        + ENDING_LINES
    log_entries = iter(parse_log_entry_lines(log_lines))
    assert isinstance(next(log_entries), ArmourValueRollEntry)
    assert isinstance(next(log_entries), InjuryRollEntry)
    assert isinstance(next(log_entries), ApothecaryLogEntry)
    assert isinstance(next(log_entries), TurnOverEntry)
    assert not next(log_entries, None)


def test_bounce_does_not_happen_mid_injury():
    log_lines = STARTING_LINES + \
        [
            "|  | GameLog(02): NAG #13 Anasfynn Armour Value  (8+) : 3 + 6 = 9 -> Success",
            "|  | GameLog(02): NAG #13 Anasfynn Injury  : 5 + 5 = 10 -> Injured",
            "|  | GameLog(02): Bounce (D8) : 6",
            "|  | GameLog(02): NAG #13 Anasfynn Casualty  : Smashed Collar Bone -> Loses 1 point in Strength",
            "|  | GameLog(13): NAG call on their Apothecary to attempt to heal #13 Anasfynn.",
            "|  | GameLog(02): NAG #13 Anasfynn Casualty  : Badly Hurt -> No long term effect",
            "|  | GameLog(13): NAG The Apothecary heals #13 Anasfynn.",
            "|  | GameLog(12): WAN #07 Ebola-Gorz earns 2 SPP (Casualty)",
        ] \
        + ENDING_LINES
    log_entries = iter(parse_log_entry_lines(log_lines))
    assert isinstance(next(log_entries), ArmourValueRollEntry)
    assert isinstance(next(log_entries), InjuryRollEntry)
    assert isinstance(next(log_entries), CasualtyRollEntry)
    assert isinstance(next(log_entries), ApothecaryLogEntry)
    assert isinstance(next(log_entries), CasualtyRollEntry)
    assert isinstance(next(log_entries), BounceLogEntry)
    assert not next(log_entries, None)


def test_bounce_and_catch_does_not_happen_mid_injury():
    log_lines = STARTING_LINES + \
        [
            "|  | GameLog(02): NAG #13 Anasfynn Armour Value  (8+) : 3 + 6 = 9 -> Success",
            "|  | GameLog(02): NAG #13 Anasfynn Injury  : 5 + 5 = 10 -> Injured",
            "|  | GameLog(02): Bounce (D8) : 6",
            "|  | GameLog(02): NAG #03 Gesmal Catch {AG}  (3+) : 6 Critical -> Success",
            "|  | GameLog(02): NAG #13 Anasfynn Casualty  : Smashed Collar Bone -> Loses 1 point in Strength",
            "|  | GameLog(13): NAG call on their Apothecary to attempt to heal #13 Anasfynn.",
            "|  | GameLog(02): NAG #13 Anasfynn Casualty  : Badly Hurt -> No long term effect",
            "|  | GameLog(13): NAG The Apothecary heals #13 Anasfynn.",
            "|  | GameLog(12): WAN #07 Ebola-Gorz earns 2 SPP (Casualty)",
        ] \
        + ENDING_LINES
    log_entries = iter(parse_log_entry_lines(log_lines))
    assert isinstance(next(log_entries), ArmourValueRollEntry)
    assert isinstance(next(log_entries), InjuryRollEntry)
    assert isinstance(next(log_entries), CasualtyRollEntry)
    assert isinstance(next(log_entries), ApothecaryLogEntry)
    assert isinstance(next(log_entries), CasualtyRollEntry)
    assert isinstance(next(log_entries), BounceLogEntry)
    assert isinstance(next(log_entries), CatchEntry)
    assert not next(log_entries, None)


def test_bounce_and_failed_catch_does_not_happen_mid_injury():
    log_lines = STARTING_LINES + \
        [
            "|  | GameLog(02): NAG #13 Anasfynn Armour Value  (8+) : 3 + 6 = 9 -> Success",
            "|  | GameLog(02): NAG #13 Anasfynn Injury  : 5 + 5 = 10 -> Injured",
            "|  | GameLog(02): Bounce (D8) : 6",
            "|  | GameLog(02): NAG #03 Gesmal Catch {AG}  (4+) : 3 + 0 {Bouncing Ball} = 3 -> Failure",
            "|  | GameLog(02): Bounce (D8) : 6",
            "|  | GameLog(02): NAG #13 Anasfynn Casualty  : Smashed Collar Bone -> Loses 1 point in Strength",
            "|  | GameLog(13): NAG call on their Apothecary to attempt to heal #13 Anasfynn.",
            "|  | GameLog(02): NAG #13 Anasfynn Casualty  : Badly Hurt -> No long term effect",
            "|  | GameLog(13): NAG The Apothecary heals #13 Anasfynn.",
            "|  | GameLog(12): WAN #07 Ebola-Gorz earns 2 SPP (Casualty)",
        ] \
        + ENDING_LINES
    log_entries = iter(parse_log_entry_lines(log_lines))
    assert isinstance(next(log_entries), ArmourValueRollEntry)
    assert isinstance(next(log_entries), InjuryRollEntry)
    assert isinstance(next(log_entries), CasualtyRollEntry)
    assert isinstance(next(log_entries), ApothecaryLogEntry)
    assert isinstance(next(log_entries), CasualtyRollEntry)
    assert isinstance(next(log_entries), BounceLogEntry)
    assert isinstance(next(log_entries), CatchEntry)
    assert isinstance(next(log_entries), BounceLogEntry)
    assert not next(log_entries, None)


def test_turnover_gets_cleared():
    log_lines = [
        STARTING_LINE,
        "|  +- Enter CStateMatchActionTT",
        "|  |",
        "|  | Release CStateMatchSelectTT",
        "|  | GameLog(-1): ORK suffer a TURNOVER! : Knocked Down!",
        "|  | Init CStateMatchSelectTT",
        "|  |",
        "|  +- Exit CStateMatchActionTT"
        "|",
        "|",
        "|  +- Enter CStateMatchActionTT",
        "|  |",
        "|  | Release CStateMatchSelectTT",
        "|  | GameLog(02): WAR #05 Pinky Wild Animal  (4+) : 2 -> Failure",
        "|  | Init CStateMatchSelectTT",
        "|  |",
        "|  +- Exit CStateMatchActionTT"
    ]
    log_entries = iter(parse_log_entry_lines(log_lines))
    assert isinstance(next(log_entries), TurnOverEntry)
    assert isinstance(next(log_entries), WildAnimalEntry)
    assert not next(log_entries, None)


def test_spell_ball_bounce_gets_rearranged():
    log_lines = [
        STARTING_LINE,
        "|  +- Enter CStateMatchWizardUseSpellTT",
        "|  | GameLog(02): ORK #03 Roknast Fireball (4+) : 5 -> Success",
        "|  | GameLog(02): ORK #03 Roknast Armour Value  (10+) : 4 + 6 = 10 -> Success",
        "|  | GameLog(02): ORK #03 Roknast Injury  : 1 + 4 + 1 {Mighty Blow} = 6 -> Stunned",
        "|  | GameLog(02): Bounce (D8) : 3",
        "|  | GameLog(02): ORK #10 Granik Fireball (4+) : 6 -> Success",
        "|  | GameLog(02): ORK #10 Granik Armour Value  (10+) : 5 + 3 = 8 -> Failure",
        "|  +- Exit CStateMatchWizardUseSpellTT",
        "|  +- Enter CStateMatchSelectTT",
        "|  | Release CStateMatchWizardUseSpellTT",
        "|  | GameLog(02): Bounce (D8) : 7",
        "|  | GameLog(00): WAR #05 Pinky uses Blitz!",
        "|  |",
        "|  +- Exit CStateMatchSelectTT",
    ]
    log_entries = parse_log_entry_lines(log_lines)
    print(log_entries)
    assert isinstance(log_entries[0], FireballEntry)
    assert isinstance(log_entries[1], ArmourValueRollEntry)
    assert isinstance(log_entries[2], InjuryRollEntry)
    assert isinstance(log_entries[3], FireballEntry)
    assert isinstance(log_entries[4], ArmourValueRollEntry)
    assert isinstance(log_entries[5], BounceLogEntry)
    assert log_entries[5].direction == ScatterDirection(3)
    assert isinstance(log_entries[6], BounceLogEntry)
    assert log_entries[6].direction == ScatterDirection(7)


def test_bug16_log_entry_merging_around_cinematics():
    log_lines = [
        STARTING_LINE,
        "|  +- Enter CStateMatchActionTT",
        "|  |",
        "|  | Release CStateMatchSelectTT",
        "|  | GameLog(02): ORK #10 Granik Going for it  (2+) : 4 -> Success",
        "|  | GameLog(02): ORK (10) Granik Block  Result:",
        "[Defender Down] - [Pushed]",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Warpstone Heat is WAITING FOR player decision",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Orkington Red Skullz is WAITING FOR player decision",
        "|  | GameLog(02): ORK #10 Granik chooses : Defender Down",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Orkington Red Skullz is NOT WAITING FOR player decision",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Warpstone Heat is NOT WAITING FOR player decision",
        "|  | GameLog(11): WAR #01 Thekit uses Fend.",
        "|  | GameLog(02): WAR #01 Thekit Injury  : 3 + 1 = 4 -> Stunned",
        "|  | Init CStateMatchSelectTT",
        "|  |",
        "|  +- Exit CStateMatchActionTT",
        "|",
        "|",
        "|  +- Enter CStateMatchSelectTT",
        "|  |",
        "|  | Contexts : GLOBAL(1)GUI(1)CAMERA(1)MATCH(1)PLAYERTEAMHUMAN(2)",
        "|  | Contexts : GLOBAL(1)GUI(1)MATCH(1)PLAYERTEAMHUMAN(2)",
        "|  | Contexts : GLOBAL(1)GUI(1)CAMERA(1)MATCH(1)PLAYERTEAMHUMAN(2)",
        "|  | Contexts : GLOBAL(1)GUI(1)MATCH(1)PLAYERTEAMHUMAN(2)",
        "|  | Contexts : GLOBAL(1)GUI(1)CAMERA(1)MATCH(1)PLAYERTEAMHUMAN(2)",
        "|  | Contexts : GLOBAL(1)GUI(1)CAMERA(1)CAMERAMATCHTV(1)MATCH(1)PLAYERTEAMHUMAN(2)",
        "|  |",
        "|  +- Exit CStateMatchSelectTT",
        "|",
        "|",
        "|  +- Enter CStateMatchActionTT",
        "|  |",
        "|  | Release CStateMatchSelectTT",
        "|  | GameLog(02): ORK #10 Granik Going for it  (2+) : 2 -> Success",
        "|  | Init CStateMatchSelectTT",
        "|  |",
        "|  +- Exit CStateMatchActionTT"
    ]
    log_entries = iter(parse_log_entry_lines(log_lines))
    assert isinstance(next(log_entries), GoingForItEntry)
    assert isinstance(next(log_entries), BlockLogEntry)
    assert isinstance(next(log_entries), SkillEntry)
    assert isinstance(next(log_entries), InjuryRollEntry)
    assert isinstance(next(log_entries), GoingForItEntry)
    assert not next(log_entries, None)


def test_bug16_turnover_does_not_get_merged_or_lost():
    log_lines = [
        STARTING_LINE,
        "|  +- Enter CStateMatchActionTT",
        "|  |",
        "|  | Release CStateMatchSelectTT",
        "|  | GameLog(02): ORK (10) Granik Block  Result:",
        "[Defender Down] - [Pushed]",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Warpstone Heat is WAITING FOR player decision",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Orkington Red Skullz is WAITING FOR player decision",
        "|  | GameLog(02): ORK #10 Granik chooses : Defender Down",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Orkington Red Skullz is NOT WAITING FOR player decision",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Warpstone Heat is NOT WAITING FOR player decision",
        "|  | GameLog(02): WAR #08 Slukch Armour Value  (9+) : 2 + 2 = 4 -> Failure",
        "|  | Init CStateMatchSelectTT",
        "|  |",
        "|  +- Exit CStateMatchActionTT",
        "|",
        "|",
        "|  +- Enter CStateMatchSelectTT",
        "|  |",
        "|  | GameLog(-1): ORK suffer a TURNOVER! : Time limit exceeded!",
        "|  | Init CStateMatchTurnoverTT",
        "|  |",
        "|  +- Exit CStateMatchSelectTT",
        "|",
        "|",
        "|  +- Enter CStateMatchTurnoverTT",
        "|  |",
        "|  |",
        "|  +- Exit CStateMatchTurnoverTT"
    ]
    log_entries = iter(parse_log_entry_lines(log_lines))
    assert isinstance(next(log_entries), BlockLogEntry)
    assert isinstance(next(log_entries), ArmourValueRollEntry)
    assert isinstance(next(log_entries), TurnOverEntry)
    assert not next(log_entries, None)


def test_bug16_do_not_merge_consecutive_blocks():
    log_lines = [
        STARTING_LINE,
        "|  +- Enter CStateMatchActionTT",
        "|  |",
        "|  | Release CStateMatchSelectTT",
        "|  | Contexts : GLOBAL(1)GUI(1)CAMERA(1)CAMERAMATCHDEFAULT(1)MATCH(1)PLAYERTEAMHUMAN(1)",
        "|  | GameLog(02): NAG #03 Gesmal Foul Appearance  (2+) : 3 -> Success",
        "|  | GameLog(02): NAG (03) Gesmal Block  Result:",
        "[Pushed] - [Pushed]",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Boil-ton Wanderers is WAITING FOR player decision",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Naggarothi  Nightmares is WAITING FOR player decision",
        "|  | GameLog(02): NAG #03 Gesmal chooses : Pushed",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Boil-ton Wanderers is NOT WAITING FOR player decision",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Naggarothi  Nightmares is NOT WAITING FOR player decision",
        "|  | Contexts : GLOBAL(1)GUI(1)CAMERA(1)CAMERAMATCHDEFAULT(1)MATCH(1)PLAYERTEAMHUMAN(1)PLAYERTEAMSINGLEACTION",
        "|  | Contexts : GLOBAL(1)GUI(1)CAMERA(1)CAMERAMATCHDEFAULT(1)MATCH(1)PLAYERTEAMHUMAN(1)",
        "|  | GameLog(02): WAN #13 Athamme Tubercu Injury  : 2 + 4 = 6 -> Stunned",
        "|  | Init CStateMatchSelectTT",
        "|  | Contexts : GLOBAL(1)GUI(1)CAMERA(1)CAMERAMATCHDEFAULT(1)MATCH(1)PLAYERTEAMHUMAN(1)PLAYERTEAMGAMEPLAYTT",
        "|  |",
        "|  +- Exit CStateMatchActionTT",
        "|",
        "|",
        "|  +- Enter CStateMatchSelectTT",
        "|  |",
        "|  | Contexts : GLOBAL(1)GUI(1)CAMERA(1)MATCH(1)PLAYERTEAMHUMAN(1)PLAYERTEAMGAMEPLAYTT(1)",
        "|  | Contexts : GLOBAL(1)GUI(1)MATCH(1)PLAYERTEAMHUMAN(1)PLAYERTEAMGAMEPLAYTT(1)",
        "|  | Contexts : GLOBAL(1)GUI(1)CAMERA(1)MATCH(1)PLAYERTEAMHUMAN(1)PLAYERTEAMGAMEPLAYTT(1)",
        "|  | Contexts : GLOBAL(1)GUI(1)MATCH(1)PLAYERTEAMHUMAN(1)PLAYERTEAMGAMEPLAYTT(1)",
        "|  | Contexts : GLOBAL(1)GUI(1)CAMERA(1)MATCH(1)PLAYERTEAMHUMAN(1)PLAYERTEAMGAMEPLAYTT(1)",
        "|  | Contexts : GLOBAL(1)GUI(1)CAMERA(1)CAMERAMATCHDEFAULT(1)MATCH(1)PLAYERTEAMHUMAN(1)PLAYERTEAMGAMEPLAYTT",
        "|  |",
        "|  +- Exit CStateMatchSelectTT",
        "|",
        "|",
        "|  +- Enter CStateMatchActionTT",
        "|  |",
        "|  | Release CStateMatchSelectTT",
        "|  | Contexts : GLOBAL(1)GUI(1)CAMERA(1)CAMERAMATCHDEFAULT(1)MATCH(1)PLAYERTEAMHUMAN(1)",
        "|  | GameLog(02): NAG #02 Elthlaen Foul Appearance  (2+) : 3 -> Success",
        "|  | GameLog(02): NAG (02) Elthlaen Block  Result:",
        "[Attacker Down]",
        "|  | GameLog(08): NAG use a re-roll for #02 Elthlaen  (Left : 1/2)",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Boil-ton Wanderers is WAITING FOR player decision",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Naggarothi  Nightmares is WAITING FOR player decision",
        "|  | GameLog(02): NAG (02) Elthlaen Block  Result:",
        "[Attacker Down]",
        "|  | GameLog(02): NAG #02 Elthlaen chooses : Attacker Down",
        "|  | GameLog(02): NAG #02 Elthlaen Armour Value  (9+) : 3 + 4 = 7 -> Failure",
        "|  | GameLog(-1): NAG suffer a TURNOVER! : Knocked Down!",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Boil-ton Wanderers is NOT WAITING FOR player decision",
        "|  | Entering CStatePlayerTeamChooseOptionalSkills, Naggarothi  Nightmares is NOT WAITING FOR player decision",
        "|  | Init CStateMatchSelectTT",
        "|  | Contexts : GLOBAL(1)GUI(1)CAMERA(1)CAMERAMATCHDEFAULT(1)MATCH(1)PLAYERTEAMHUMAN(1)PLAYERTEAMGAMEPLAYTT",
        "|  |",
        "|  +- Exit CStateMatchActionTT"
    ]
    log_entries = iter(parse_log_entry_lines(log_lines))
    assert isinstance(next(log_entries), FoulAppearanceEntry)
    assert isinstance(next(log_entries), BlockLogEntry)
    assert isinstance(next(log_entries), InjuryRollEntry)
    assert isinstance(next(log_entries), FoulAppearanceEntry)
    assert isinstance(next(log_entries), BlockLogEntry)
    assert isinstance(next(log_entries), RerollEntry)
    assert isinstance(next(log_entries), BlockLogEntry)
    assert isinstance(next(log_entries), ArmourValueRollEntry)
    assert isinstance(next(log_entries), TurnOverEntry)
    assert not next(log_entries, None)


def test_mixed_order_of_injuries():
    # Casualty rolls are separate from armour/injury rolls, which means that a "both down"
    # situation can mix them. But for simplicity/consistency, we assume they're consecutive
    # (because they are in single player situations!)
    log_lines = STARTING_LINES + \
        [
            "|  | GameLog(02): WAN #01 Joe the Indisposed Armour Value  (9+) : 5 + 6 = 11 -> Success",
            "|  | GameLog(02): WAN #01 Joe the Indisposed Injury  : 5 + 5 = 10 -> Injured",
            "|  | GameLog(02): NAG #10 Meseorl Armour Value  (9+) : 5 + 5 = 10 -> Success",
            "|  | GameLog(02): NAG #10 Meseorl Injury  : 2 + 1 = 3 -> Stunned",
            "|  | GameLog(-1): WAN suffer a TURNOVER! : Knocked Down!",
            "|  | Entering CStatePlayerTeamChooseOptionalSkills, Boil-ton Wanderers is NOT WAITING FOR player decision",
            "|  | Entering CStatePlayerTeamChooseOptionalSkills, Naggarothi  Nightmares is NOT WAITING FOR player deci",
            "|  | GameLog(02): WAN #01 Joe the Indisposed Casualty  : Badly Hurt -> No long term effect",
            "|  | GameLog(02): WAN #01 Joe the Indisposed Casualty  : Badly Hurt -> No long term effect",
            "|  | GameLog(12): NAG #10 Meseorl earns 2 SPP (Casualty)",
        ] + \
        ENDING_LINES
    log_entries = iter(parse_log_entry_lines(log_lines))
    assert isinstance(next(log_entries), ArmourValueRollEntry)
    assert isinstance(next(log_entries), InjuryRollEntry)
    assert isinstance(next(log_entries), CasualtyRollEntry)
    assert isinstance(next(log_entries), CasualtyRollEntry)
    assert isinstance(next(log_entries), ArmourValueRollEntry)
    assert isinstance(next(log_entries), InjuryRollEntry)


def test_parse_log_entries():
    lines = [
        "NAG #03 Gesmal Dodge {AG}  (3+) : 2 + 1 {Dodge} + -2 + 0 {TZ} = 0 -> Failure",
        "NAG #03 Gesmal Dodge {AG}  (3+) : 6 Critical + -2 {Diving Tackle} -> Success",
    ]
    log_entries = [parse_log_entry(line, "NAG", "WAN") for line in lines]

    assert log_entries[0] == DodgeEntry(TeamType.HOME, 3, "3+", "0", ActionResult.FAILURE.name)
    assert log_entries[1] == DodgeEntry(TeamType.HOME, 3, "3+", "6", ActionResult.SUCCESS.name)
