from bbreplay import ScatterDirection
from bbreplay.log import ApothecaryLogEntry, ArmourValueRollEntry, BounceLogEntry, FireballEntry, InjuryRollEntry, \
    TurnOverEntry, WildAnimalEntry, parse_log_entry_lines, CasualtyRollEntry


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
            "|  | GameLog(-1): WAR suffer a TURNOVER! : Knocked Down!",
            "|  | Entering CStatePlayerTeamChooseOptionalSkills, Warpstone Heat is NOT WAITING FOR player decision",
            "|  | GameLog(13): WAR call on their Apothecary to attempt to heal #05 Pinky.",
        ] \
        + ENDING_LINES
    match_log_entries = parse_log_entry_lines(log_lines)
    assert len(match_log_entries) == 1
    assert len(match_log_entries[0]) == 2


def test_parse_apothecary_puts_turnover_at_end():
    log_lines = STARTING_LINES + \
        [
            "|  | GameLog(02): WAR #05 Pinky Armour Value  (9+) : 6 + 5 = 11 -> Success",
            "|  | GameLog(02): WAR #05 Pinky Injury  : 6 + 3 = 9 -> KO'd",
            "|  | GameLog(-1): WAR suffer a TURNOVER! : Knocked Down!",
            "|  | GameLog(13): WAR call on their Apothecary to attempt to heal #05 Pinky.",
        ] \
        + ENDING_LINES
    log_entries = iter(parse_log_entry_lines(log_lines)[0])
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
    log_entries = iter(parse_log_entry_lines(log_lines)[0])
    assert isinstance(next(log_entries), ArmourValueRollEntry)
    assert isinstance(next(log_entries), InjuryRollEntry)
    assert isinstance(next(log_entries), CasualtyRollEntry)
    assert isinstance(next(log_entries), ApothecaryLogEntry)
    assert isinstance(next(log_entries), CasualtyRollEntry)
    assert isinstance(next(log_entries), BounceLogEntry)


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
    all_log_entries = iter(parse_log_entry_lines(log_lines))
    log_entries = next(all_log_entries)
    print(log_entries)
    assert len(log_entries) == 1
    assert isinstance(log_entries[0], TurnOverEntry)

    log_entries = next(all_log_entries)
    assert len(log_entries) == 1
    assert isinstance(log_entries[0], WildAnimalEntry)

    assert not next(all_log_entries, None)


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
    all_log_entries = iter(parse_log_entry_lines(log_lines))
    log_entries = next(all_log_entries)
    print(log_entries)
    assert len(log_entries) == 7
    assert isinstance(log_entries[0], FireballEntry)
    assert isinstance(log_entries[1], ArmourValueRollEntry)
    assert isinstance(log_entries[2], InjuryRollEntry)
    assert isinstance(log_entries[3], FireballEntry)
    assert isinstance(log_entries[4], ArmourValueRollEntry)
    assert isinstance(log_entries[5], BounceLogEntry)
    assert log_entries[5].direction == ScatterDirection(3)
    assert isinstance(log_entries[6], BounceLogEntry)
    assert log_entries[6].direction == ScatterDirection(7)

    assert not next(all_log_entries, None)
