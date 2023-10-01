import os
import re
import sys
from datetime import datetime
from unicodedata import normalize


def is_video_file(file):
    extensions = [".avi", ".mp4", ".mkv"]

    for ext in extensions:
        if file.endswith(ext):
            return True
    return False


def all_equal(list):
    return all(x == list[0] for x in list)


def get_tvshow_metadata(file):
    pattern = r"s?s?(\d{1,2})\s?[ex]\s?(\d{1,3})"
    match = re.findall(pattern, file, re.IGNORECASE)

    if len(match) <= 0:
        return None, None
    elif len(match) == 1:
        return int(match[0][0]), int(match[0][1])
    else:
        s = [int(x[0]) for x in match]
        e = [int(x[1]) for x in match]

        if all_equal(s):
            s = s[0]
        if all_equal(e):
            e = e[0]

        return s, e


def build_rename_info(folder):
    tvshow_info = []

    for root, dirs, files in os.walk(folder):
        for f in files:
            if is_video_file(f):
                season, episode = get_tvshow_metadata(f)
                dict = {
                    "file": os.path.join(root, f),
                    "season": season,
                    "episode": episode,
                }
                tvshow_info.append(dict)

    for show in tvshow_info:
        s = f"{show['season']:02}"
        if type(show["episode"]) is list:
            e = f"{min(show['episode']):02}-{max(show['episode']):02}"
        else:
            e = f"{show['episode']:02}"

        pattern = r"s?s?\d{1,2}\s?[ex]\s?\d{1,3}(s?\s?\&\s?s?\d{1,2}\s?[ex]\s?\d{1,3})*"
        new_filename = re.sub(
            pattern, f"S{s}E{e}", show["file"], count=1, flags=re.IGNORECASE
        )
        show["rename_to"] = new_filename

    return tvshow_info


def log_to_csv(orig_file, renamed_file, csv_file="history.csv"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not os.path.exists(csv_file):
        with open(csv_file, "w") as f:
            f.write("ts, original_filename, new_filename\n")

    with open(csv_file, "a") as f:
        f.write(f"{ts}, {orig_file}, {renamed_file}\n")


def rename_tvshows(folder):
    rename_info = build_rename_info(folder)
    # with open("rename_info.json", "w") as f:
    #     f.write(json.dumps(rename_info, indent=2))

    for file in rename_info:
        file_from = file["file"]
        file_to = file["rename_to"]

        if file_from == file_to:
            continue

        # rename tv show file
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{ts}: Renaming {file_from} to {file_to}")
        os.rename(file_from, file_to)
        log_to_csv(file_from, file_to)


if __name__ == "__main__":
    try:
        for i, arg in enumerate(sys.argv):
            if arg in ["-f", "--folder"]:
                rename_tvshows(sys.argv[i+1])
    except IndexError:
        print("I'll document usage later")
