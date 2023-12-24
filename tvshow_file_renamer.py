import os
import csv
import argparse
from datetime import datetime
from pathlib import Path
from my_tvshow_package import TVShow, Episode

DEFAULT_RENAME_FORMAT = (
    "{show_name} ({show_year}) S{season_no}E{episode_no} {episode_name}{ext}"
)


def rename_tvshows(folder, format, test_run=False):
    """
    Loops through `folder` and renames any video files
    with "S01E01" naming convention.

    If `test_run` is set `True`, this will only log
    to console. Rename operations are not run
    """
    tv_show = TVShow(folder)
    tv_show.get_episodes()

    # loop through each file to be renamed
    for episode in tv_show.episodes:
        # get details
        new_filename = rename_episode_file(episode, format)
        testing_tag = "[TEST ONLY] " if test_run else ""

        # rename tv show file
        print(f'{testing_tag}Renaming "{episode.path}" --> "{new_filename}"')
        if not test_run:
            os.rename(episode.path, new_filename)
            log_to_csv(episode.path, new_filename, "test_runs.csv")
        else:
            log_to_csv(episode.path, new_filename, "test_runs.csv")


def rename_episode_file(episode: Episode, format: str):
    """
    Renames the `episode` filename to the new `format` string
    """
    # handle multi ep numbers
    if type(episode.episode) is list:
        ep = "E".join([f"{e:02}" for e in episode.episode])
    else:
        ep = f"{episode.episode:02}"

    # handle multi ep titles
    if type(episode.name) is list:
        ep_title = "~~".join(episode.name)
    else:
        ep_title = episode.name if episode.name else ""

    # construct new filename
    new_filename = (
        format.replace("{show_name}", episode.show_name)
        .replace("{show_year}", episode.show_year)
        .replace("{season_no}", f"{episode.season:02}")
        .replace("{episode_no}", ep)
        .replace("{episode_name}", ep_title)
        .replace("{ext}", Path(episode.path).suffix)
    )

    return os.path.join(Path(episode.path).parent, new_filename)


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


def parse_args():
    # cli arguments
    parser = argparse.ArgumentParser(description="Renames TV Shows")
    parser.add_argument("directory", help="full path of TV show directory")
    parser.add_argument("-f", "--filename_format", default=DEFAULT_RENAME_FORMAT)
    parser.add_argument("-d", "--debugmode", action="store_true", help="for debugging")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    rename_tvshows(args.directory, args.filename_format, args.debugmode)

