import os
import re
import sys
import csv
from datetime import datetime
from pathlib import Path


PATTERN = r"s?(\d{1,2})\s?[ex]\s?(\d{1,2})(\s?\-?\s?[ex]?(\d{1,2}))?"
VIDEO_EXTS = [".avi", ".mp4", ".mkv"]


def is_video_file(file):
    """Checks if `file` is a video file"""
    for ext in VIDEO_EXTS:
        if file.endswith(ext):
            return True
    return False


def all_equal(list):
    """Checks if all items in `list` are of the same value"""
    return all(x == list[0] for x in list)


def get_tvshow_metadata(file):
    """Returns season number and episode number for given video `file`"""
    match = re.findall(PATTERN, file, re.IGNORECASE)

    if len(match) <= 0:
        return None, None
    elif len(match) == 1:
        s = int(match[0][0])
        # this is for multi episode files
        # eg. "S01E01-03"
        if match[0][3] == "":
            e = int(match[0][1])
        else:
            e = [int(match[0][1]), int(match[0][3])]
    else:
        # also for multi episode files
        # eg. "1x01 & 1x02 & 1x03"
        s = [int(x[0]) for x in match]
        e = [int(x[1]) for x in match]

        # shouldn't have multi seasons in one file
        if all_equal(s):
            s = s[0]
        else:
            raise ("Multiple seasons detected in one file?")
        # if list with same values, "unlist" it
        if all_equal(e):
            e = e[0]

    return s, e


def build_rename_info(folder):
    """
    Loops through `folder` recursively building a list of
    dictionaries with rename info for each video file
    """
    tvshow_dicts = []

    # walk through folder
    for root, dirs, files in os.walk(folder):
        for fn in files:
            if not is_video_file(fn):
                continue

            # build tv info to dictionary
            season, episode = get_tvshow_metadata(fn)

            # generate renamed files
            try:
                # season number as 0 padded string
                s = f"{season:02}"

                # episode number as 0 padded string
                # also handle multi episodes
                if type(episode) is list:
                    e = f"{min(episode):02}-E{max(episode):02}"
                else:
                    e = f"{episode:02}"
            except TypeError:
                continue

            # generate new filename
            new_filename = re.sub(
                PATTERN, f"S{s}E{e}", fn, count=1, flags=re.IGNORECASE
            )
            # remove repeating episode tags
            # eg. when original file was like "1x01 & 1x02"
            new_filename = re.sub(
                r"\s?\&\s?" + PATTERN, "", new_filename, flags=re.IGNORECASE
            )

            # skip over if no change filename
            if fn.lower() == new_filename.lower():
                continue

            # build dict and add to list
            dict = {
                "season": season,
                "episode": episode,
                "file": os.path.join(root, fn),
                "rename_to": os.path.join(root, new_filename),
            }
            tvshow_dicts.append(dict)

    return tvshow_dicts


def log_to_csv(orig_file, renamed_file, csv_file="history.csv"):
    """creates a log entry to csv"""
    fieldnames = ["ts", "folder", "original_filename", "new_filename"]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {
        "ts": ts,
        "folder": Path(orig_file).parent,
        "original_filename": Path(orig_file).name,
        "new_filename": Path(renamed_file).name,
    }

    # begin csv file if doesnt exist
    if not os.path.exists(csv_file):
        with open(csv_file, "w", encoding="UTF8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    # append entry to csv
    with open(csv_file, "a", encoding="UTF8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(row)


def rename_tvshows(folder, test_run=False):
    """
    Loops through `folder` and renames any video files
    with "S01E01" naming convention.

    If `test_run` is set `True`, this will only log
    to console. Rename operations are not run
    """

    # get renaming details
    rename_info = build_rename_info(folder)

    # loop through each file to be renamed
    for i, file in enumerate(rename_info):
        # get details
        file_from = file["file"]
        file_to = file["rename_to"]
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        testing_tag = "[TEST ONLY] " if test_run else ""

        # rename tv show file
        print(f'{ts}: [{i}] {testing_tag}Renaming "{file_from}" --> "{file_to}"')
        if not test_run:
            os.rename(file_from, file_to)
            log_to_csv(file_from, file_to)
        else:
            log_to_csv(file_from, file_to, "test_runs.csv")


if __name__ == "__main__":
    try:
        # look through cli arguments
        for i, arg in enumerate(sys.argv):
            # option -f, --folder
            # calls rename_tvshows()
            if arg in ["-f", "--folder"]:
                test_run = False
                for arg in sys.argv:
                    if arg in ["-t", "--test-run"]:
                        test_run = True
                rename_tvshows(sys.argv[i + 1], test_run=test_run)

    except IndexError:
        print("I'll document usage later")
