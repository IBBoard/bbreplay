from pathlib import Path
import shutil


DRIVE_BASE = Path.home().joinpath('.local/share/Steam/steamapps/compatdata/216890/pfx/drive_c/')
BLOODBOWL_DIR = DRIVE_BASE.joinpath('users/steamuser/My Documents/BloodBowlChaos/')

OPEN_DB_PREFIX_LENGTH = 14


def get_log_lines():
    # Merge all of the logs into one
    log_files = [log_file for log_file in BLOODBOWL_DIR.glob('BB_Chaos*.log')]
    log_files.sort()
    for log in log_files:
        print(log)
        with log.open() as f:
            for line in f:
                yield line.strip()


def get_replay_path(log_line):
    path = log_line.strip("| ")[OPEN_DB_PREFIX_LENGTH:]
    return Path(path)


def copy_replay(replay_path, dest):
    relative_path = replay_path.relative_to(replay_path.parents[2])
    shutil.copy2(BLOODBOWL_DIR.joinpath(relative_path), dest)


if __name__ == '__main__':
    maybe_replay_line = False
    capture_log = False
    prev_line = None
    new_log_file = None
    replay_path = None
    target_dir = Path('temp/')
    target_dir.mkdir(exist_ok=True)

    for log_line in get_log_lines():
        if log_line.startswith("| Set match version to "):
            replay_path = get_replay_path(prev_line)
        elif log_line == "|  |  | Delete previous database if any":
            maybe_replay_line = True
        elif maybe_replay_line:
            maybe_replay_line = False
            if "Saves/Replays/Replay_" in log_line:
                replay_path = get_replay_path(log_line)
        elif replay_path:
            if not capture_log and log_line == "|  +- Enter CStateMatchTossCreateResults":
                capture_log = True
                copy_replay(replay_path, target_dir)
                new_log_file = open(target_dir.joinpath(replay_path.with_suffix('.log').name), 'w', encoding="utf-8")
            elif capture_log and log_line == "|  +- Enter CStateMatchEnd":
                capture_log = False
                new_log_file.close()
                new_log_file = None
                replay_path = None

            if capture_log:
                new_log_file.write(log_line)
                new_log_file.write('\n')
        # Else it's not interesting yet

        prev_line = log_line

    if new_log_file:
        new_log_file.close()
