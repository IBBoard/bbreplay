#! /bin/bash

bb_base=~/.local/share/Steam/steamapps/compatdata/216890/pfx/drive_c/
bb_log=${bb_base}users/steamuser/My\ Documents/BloodBowlChaos/BB_Chaos000.log

# NOTE: Original and Legendary editions will have different IDs and slightly different log names
last_replay=$(grep "Open database.*Replay.*\.db" "${bb_log}" | tail -n1 | cut -f2- -d/ | sed 's/\r//')
last_replay_file=${last_replay##*/}
mkdir -p temp/
cp "${bb_log}" "temp/${last_replay_file/.db}.log"
cp "${bb_base}${last_replay}" "temp/${last_replay_file}"