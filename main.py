import os
import re
import csv
import tvdb_helper
import argparse
from datetime import datetime
from pathlib import Path


PATTERN = r"s(\d{1,2})(?:\s|\-)?[ex]\s?(\d{1,2})"
PATTERN_MULTI = r"s(\d{1,2})(?:\s|\-)?[ex]\s?(\d{1,2})(\s?\-?\s?[ex]?(\d{1,2}))?"
VIDEO_EXTS = [".avi", ".mp4", ".mkv"]


def rename_tvshows(folder, test_run=False, tags_only=True, multimode=False):
    """
    Loops through `folder` and renames any video files
    with "S01E01" naming convention.

    If `test_run` is set `True`, this will only log
    to console. Rename operations are not run
    """
    rename_info = rename_generator(folder, tags_only, multimode)

    # loop through each file to be renamed
    for i, file in enumerate(rename_info):
        # get details
        file_from = file["filename"]
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


def rename_generator(folder, tags_only=False, multimode=False):
    rename_info = []

    # get all episodes in folder recursively
    episodes_data = episode_list_with_metadata(folder, multimode=multimode)

    for ep in episodes_data:
        s = ep.get("season")
        e = ep.get("episode")
        fn = ep.get("file")
        ext = Path(fn).suffix
        show_name = ep.get("tvshow_name")
        year = ep.get("year")
        episode_name = ep.get("episode_name")
        aired = ep.get("aired")
        pattern = PATTERN_MULTI if multimode else PATTERN

        if not s:
            continue
        if not e:
            continue

        # handle multi episodes
        if multimode and type(e) is list:
            e = f"{min(e):02}-E{max(e):02}"

        # generate new file name
        if tags_only:
            new_filename = (
                f"{show_name} ({year}) - S{s:02}E{e:02}{ext}"
            )
            # remove repeating episode tags
            # eg. when original file was like "1x01 & 1x02"
            if multimode:
                new_filename = re.sub(
                    r"\s?\&\s?" + pattern, "", new_filename, flags=re.IGNORECASE
                )
        else:
            new_filename = (
                f"{show_name} ({year}) - S{s:02}E{e:02} - {episode_name}{ext}"
            )
        
        new_filename = os.path.join(Path(fn).parent, new_filename)

        # skip over if no change in filename
        if fn.lower() == new_filename.lower():
            continue

        rename_info.append({"filename": fn, "rename_to": new_filename})

    return rename_info


def episode_list_with_metadata(folder, include_tvdb_info=True, multimode=False):
    """
    Return list of dictionaries for each episode nested
    under `folder`.

    If `include_tvdb_info` = `True`, includes additional
    episode information from tvdb.

    """
    tvshow_dicts = []
    prev_show = None

    # walk through folder
    for root, dirs, files in os.walk(folder):
        for fn in files:
            if not is_video_file(fn):
                continue

            full_file_path = os.path.join(root, fn)

            # build tv info to dictionary
            season, episode = extract_s_e_from_filename(fn, multimode)

            if season is None or episode is None:
                continue

            # build dict and add to list
            dict = {
                "season": season,
                "episode": episode,
                "file": full_file_path,
            }

            # get episode title and other details
            if include_tvdb_info:
                show_name, year = determine_tvshow_from_path(full_file_path)
                if show_name != prev_show:
                    # update show_id
                    if year:
                        show_id, show_name, year = tvdb_helper.get_show_id(
                            show_name, year=year
                        )
                    else:
                        show_id, show_name, year = tvdb_helper.get_show_id(show_name)

                dict["tvshow_name"] = show_name
                dict["year"] = year

                # multi episodes will be a list.
                # make single episodes into a list as well
                episode = [episode] if type(episode) is not list else episode
                ep_info = []
                # loop through list of episode numbers and get info for each episode
                for ep in episode:
                    ep_info.append(tvdb_helper.get_episode_details(show_id, season, ep))

                # add info to dict
                ep_info = [x for x in ep_info if x is not None]
                if len(ep_info) > 0:
                    if len(ep_info) == 1:
                        dict["aired"] = ep_info[0][0]
                        dict["episode_name"] = ep_info[0][1]
                        dict["overview"] = ep_info[0][2]
                    else:
                        dict["aired"] = [x[0] for x in ep_info if x]
                        dict["episode_name"] = [x[1] for x in ep_info if x]
                        dict["overview"] = [x[2] for x in ep_info if x]

            # add to list
            tvshow_dicts.append(dict)

            # keep for next iteration
            prev_show = show_name

    return tvshow_dicts


def extract_s_e_from_filename(file, multimode):
    """Returns season number and episode number for given video `file`"""
    pattern = PATTERN_MULTI if multimode else PATTERN
    match = re.findall(pattern, file, re.IGNORECASE)

    if len(match) <= 0:
        return None, None
    
    elif len(match) == 1:
        s = int(match[0][0])
        # this is for multi episode files
        # eg. "S01E01-03"
        if not multimode:
            e = int(match[0][1])  
        elif match[0][3] == "":
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


def determine_tvshow_from_path(path):
    for parent in Path(path).parents:
        try:
            _, folder = str(parent).replace("\\", "/").rsplit("/", maxsplit=1)
        except:
            return None, None

        if re.search(r"(season|series)[\s\.\_\-]{0,2}\d{1,2}", folder, re.IGNORECASE):
            continue

        tvshow_name = folder.strip()
        break

    year_match = re.search(r"[\(\[]((19|20)\d{2})[\)\]]", tvshow_name)
    if year_match:
        tvshow_name = tvshow_name.replace(year_match.group(0), "").strip()
        return tvshow_name, int(year_match.group(1))
    else:
        return tvshow_name, None


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


def is_video_file(file):
    """Checks if `file` is a video file"""
    for ext in VIDEO_EXTS:
        if file.endswith(ext):
            return True
    return False


def all_equal(list):
    """Checks if all items in `list` are of the same value"""
    return all(x == list[0] for x in list)


def parse_args():
    # cli arguments
    parser = argparse.ArgumentParser(description="Renames TV Shows")
    parser.add_argument("directory", help="full path of TV show directory")
    parser.add_argument(
        "-t", "--tagsonly", action="store_true", help="rename using tags only"
    )
    parser.add_argument("-m", "--multimode", action="store_true", help="folder contains multi-episodes")
    parser.add_argument("-d", "--debugmode", action="store_true", help="for debugging")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    rename_tvshows(args.directory, args.debugmode, args.tagsonly, args.multimode)
