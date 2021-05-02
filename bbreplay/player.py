# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

from . import prefix_for_teamtype, PlayerStatus, Skills, OFF_PITCH_POSITION


MA_TO_STAT = {
    33: 4,
    41: 5,
    50: 6,
    58: 7,
    66: 8
}

ST_AG_TO_STAT = {
    16: 1,
    33: 2,
    50: 3,
    60: 4,  # Yes, two values for 4!
    66: 4,
    70: 5,
    83: 5
}

AV_TO_STAT = {
    58: 7,
    72: 8,
    83: 9
}


class Positionable:
    def __init__(self):
        self.position = OFF_PITCH_POSITION

    def is_on_pitch(self):
        return self.position != OFF_PITCH_POSITION


class Player(Positionable):
    def __init__(self, team, db_id, number, name, move, strength, agility, armour_value, level, spp, value, db):
        super().__init__()
        self.__dbid = db_id
        self.team = team
        self.number = number
        self.name = name
        self.MA = MA_TO_STAT[int(float(move))]
        self.ST = ST_AG_TO_STAT[int(float(strength))]
        self.AG = ST_AG_TO_STAT[int(float(agility))]
        self.AV = AV_TO_STAT[int(float(armour_value))]
        self.level = level
        self.SPP = spp
        self.value = value
        self.status = PlayerStatus.OKAY
        self.__db = db
        self.__skills = None

    @property
    def skills(self):
        if self.__skills is None:
            self.__skills = []
            table_prefix = prefix_for_teamtype(self.team.team_type)
            cur = self.__db.cursor()
            type_skills = cur.execute(f'SELECT idSkill_Listing, description FROM {table_prefix}_Player_Listing player '
                                      f'INNER JOIN {table_prefix}_Player_Type_Skills type_skills '
                                      'ON player.idPlayer_Types = type_skills.idPlayer_Types '
                                      f'WHERE player.ID = {self.__dbid} ')

            for skill_row in type_skills:
                try:
                    self.__skills.append(Skills(skill_row[0]))
                except ValueError as ex:
                    raise ValueError(f"Unidentified skill {skill_row[0]} ({skill_row[1]}) for {self.team.name} player "
                                     f"#{self.number} {self.name}") from ex

            learned_skills = cur.execute(f'SELECT idSkill_Listing FROM {table_prefix}_Player_Skills '
                                         f'WHERE idPlayer_Listing = {self.__dbid}')

            for skill_row in learned_skills:
                try:
                    self.__skills.append(Skills(skill_row[0]))
                except ValueError as ex:
                    raise ValueError(f"Unidentified learned skill {skill_row[0]} for {self.team.name} player "
                                     f"#{self.number} {self.name}") from ex
            cur.close()
        return self.__skills

    def __repr__(self):
        return f"Player(number={self.number}, name={self.name}, " \
               f"level={self.level}, spp={self.SPP}, value={self.value}, {self.position})"
