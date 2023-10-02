import os
import re
import sys
from datetime import datetime
from unicodedata import normalize


PATTERN = r"s?(\d{1,2})\s?[ex]\s?(\d{1,3})(\s?\-?\s?[ex]?(\d{1,3}))?"

def is_video_file(file):
    extensions = [".avi", ".mp4", ".mkv"]

    for ext in extensions:
        if file.endswith(ext):
            return True
    return False


def all_equal(list):
    return all(x == list[0] for x in list)


def get_tvshow_metadata(file):
    match = re.findall(PATTERN, file, re.IGNORECASE)

    if len(match) <= 0:
        return None, None
    elif len(match) == 1:
        s = match[0][0]
        # this is for multi episode files
        # eg. "S01E01-03"
        if match[0][3] == "":
            e = match[0][1]
        else:
            e = [match[0][1], match[0][3]]
    else:
        # also for multi episode files
        # eg. "1x01 & 1x02 & 1x03"
        s = [int(x[0]) for x in match]
        e = [int(x[1]) for x in match]

        # shouldn't have multi seasons in one file
        if all_equal(s):
            s = s[0]
        else:
            raise("Multiple seasons detected in one file?")
        # if list with same values, "unlist" it
        if all_equal(e):
            e = e[0]

    return s, e


def build_rename_info(folder):
    tvshow_dicts = []

    # walk through folder
    for root, dirs, files in os.walk(folder):
        for f in files:
            if is_video_file(f):
                # build tv info to dictionary
                season, episode = get_tvshow_metadata(f)
                dict = {
                    "file": os.path.join(root, f),
                    "season": season,
                    "episode": episode,
                }
                # append to list
                tvshow_dicts.append(dict)

    # generate renamed files
    for dict in tvshow_dicts:
        # season number as 0 padded string
        s = f"{dict['season']:02}"

        # episode number as 0 padded string
        # also handle multi episodes
        if type(dict["episode"]) is list:
            e = f"{min(dict['episode']):02}-E{max(dict['episode']):02}"
        else:
            e = f"{dict['episode']:02}"

        # generate new filename
        new_filename = re.sub(
            PATTERN, f"S{s}E{e}", dict["file"], count=1, flags=re.IGNORECASE
        )
        # remove repeating episode tags
        # eg. when original file was like "1x01 & 1x02"
        new_filename = re.sub(
            r"\s?\&\s?" + PATTERN, "", new_filename, flags=re.IGNORECASE
        )
        # add renamed filename to dictionary
        dict["rename_to"] = new_filename

    return tvshow_dicts


def log_to_csv(orig_file, renamed_file, csv_file="history.csv"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not os.path.exists(csv_file):
        with open(csv_file, "w") as f:
            f.write("ts, original_filename, new_filename\n")

    with open(csv_file, "a") as f:
        f.write(f"{ts}, {orig_file}, {renamed_file}\n")


def rename_tvshows(folder, test_run=False):
    rename_info = build_rename_info(folder)
    # with open("rename_info.json", "w") as f:
    #     f.write(json.dumps(rename_info, indent=2))

    for file in rename_info:
        file_from = file["file"]
        file_to = file["rename_to"]
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        testing_tag = "[TEST ONLY] " if test_run else ""

        # skip if no change in filename
        if file_from == file_to:
            continue

        # rename tv show file
        print(f'{ts}: {testing_tag}Renaming "{file_from}" --> "{file_to}"')
        if not test_run:
            os.rename(file_from, file_to)
            log_to_csv(file_from, file_to)


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
