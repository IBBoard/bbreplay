from bbreplay.log import ApothecaryLogEntry, ArmourValueRollEntry, InjuryRollEntry, TurnOverEntry, parse_log_entry_lines


STARTING_LINES = [
    "|  +- Enter CStateMatchTossCreateResults",
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
