from bbreplay.log import ApothecaryLogEntry, ArmourValueRollEntry, InjuryRollEntry, TurnOverEntry, WildAnimalEntry, \
    parse_log_entry_lines


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
