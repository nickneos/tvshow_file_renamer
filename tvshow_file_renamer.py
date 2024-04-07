import os
import csv
import argparse
from datetime import datetime
from pathlib import Path

# custom modules
from my_tvshow_package.tvshow import TVShow
from my_tvshow_package.episode import Episode

DEFAULT_RENAME_FORMAT = (
    "S{season_no}E{episode_no} - {episode_name}{ext}"
)


def rename_tvshow_episodes(tvshow_folder, format, test_run=False):
    """
    Loops through `tvshow_folder` and renames the video files
    according to `format`

    If `test_run` is set `True`, this will only log to console.
    Rename operations are not run
    """
    tv_show = TVShow(tvshow_folder)
    tv_show.get_episodes()

    # loop through each episode video file to be renamed
    for episode in tv_show.episodes:
        # get details
        new_filename = rename_episode_file(episode, format)
        testing_tag = "[TEST ONLY] " if test_run else ""

        # skip over if no new filename generated
        if not new_filename:
            print(f'{testing_tag}Skipping "{episode.path}"')
            continue

        # rename tv show file
        print(f'{testing_tag}Renaming "{episode.path}" --> "{new_filename}"')
        if not test_run:
            os.makedirs(os.path.dirname(new_filename), exist_ok=True)
            os.rename(episode.path, new_filename)
            log_to_csv(episode.path, new_filename)
        else:
            log_to_csv(episode.path, new_filename, "test_runs.csv")


def rename_episode_file(episode: Episode, fmt: str):
    """
    Renames the `episode` filename to the new `fmt` string
    """
    # handle multi episode numbers
    # eg. S01E01E02
    try:
        if type(episode.episode) is list:
            ep = "E".join([f"{e:02}" for e in episode.episode])
        else:
            ep = f"{episode.episode:02}"

        # handle multi ep titles
        if type(episode.name) is list:
            ep_title = "~~".join(episode.name)
        else:
            ep_title = episode.name if episode.name else ""
    except TypeError:
        return None

    # construct new filename
    new_filename = episode.top_level_folder.replace(
        Path(episode.top_level_folder).parts[-1],
        f"{episode.show_name} ({episode.show_year})/Season {episode.season}/",
    )
    new_filename = new_filename + (
        fmt.replace("{show_name}", episode.show_name)
        .replace("{show_year}", episode.show_year)
        .replace("{season_no}", f"{episode.season:02}")
        .replace("{episode_no}", ep)
        .replace("{episode_name}", ep_title)
        .replace("{ext}", Path(episode.path).suffix)
    )

    return new_filename


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
    parser = argparse.ArgumentParser(
        description="Renames TV Show media files using information from thetvdb.com"
    )
    parser.add_argument(
        "directory",
        help="Full path of TV show directory. Assumes all files under this directory relate to one tv show",
    )
    parser.add_argument(
        "-f",
        "--filename-format",
        default=DEFAULT_RENAME_FORMAT,
        metavar="format-string",
        help='Example: "{show_name} ({show_year}) S{season_no}E{episode_no} {episode_name}{ext}"',
    )
    parser.add_argument(
        "-t",
        "--test-mode",
        action="store_true",
        help="Enables test mode. In test mode, renamed filenames are printed to screen but are not actually renamed on the disk",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    rename_tvshow_episodes(args.directory, args.filename_format, args.test_mode)
