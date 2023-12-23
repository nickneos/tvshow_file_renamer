import re
import tvdb_helper
from datetime import datetime
from pathlib import Path
from helpers import *

PATTERN = r"s(\d{1,2})(?:\s|\-)?[ex]\s?(\d{1,2})"
PATTERN_MULTI = r"s(\d{1,2})(?:\s|\-)?[ex]\s?(\d{1,2})(\s?\-?\s?[ex]?(\d{1,2}))?"


class Episode:
    def __init__(self, path, show_id, show_name, multimode=False) -> None:
        self.path = path
        self.show_id = show_id
        self.show_name = show_name
        self.filename = Path(path).name
        self._get_info(multimode)

    def __str__(self) -> str:
        txt = f"Path: {self.path}\n"
        txt += f"Season: {self.season}\nEpisode: {self.episode}\n"
        txt += f"Name: {self.name}\n"
        txt += f"Overview: {self.overview}\n"
        txt += f"Aired: {self.aired}\n"
        return txt

    def _get_info(self, multimode=False):
        pattern = PATTERN_MULTI if multimode else PATTERN
        match = re.findall(pattern, self.filename, re.IGNORECASE)

        if len(match) <= 0:
            self.season = None
            self.episode = None
            self.aired = None
            self.name = None
            self.overview = None
            return

        elif len(match) == 1:
            self.season = int(match[0][0])
            # this is for multi episode files
            # eg. "S01E01-03"
            if not multimode:
                self.episode = int(match[0][1])
            elif match[0][3] == "":
                self.episode = int(match[0][1])
            else:
                self.episode = [int(match[0][1]), int(match[0][3])]
        else:
            # also for multi episode files
            # eg. "1x01 & 1x02 & 1x03"
            self.season = delist_if_needed([int(x[0]) for x in match])
            self.episode = delist_if_needed([int(x[1]) for x in match])

            # shouldn't have multi seasons in one file
            if type(self.season) is list:
                raise ("Multiple seasons detected in one file?")

        # multi episodes will be a list.
        # make single episodes into a list as well
        episode = self.episode if type(self.episode) is list else [self.episode]
        aired = []
        name = []
        overview = []
        # loop through list of episode numbers and get info for each episode
        for ep in episode:
            info = tvdb_helper.get_episode_details(self.show_id, self.season, ep)
            if info:
                aired.append(info[0])
                name.append(info[1])
                overview.append(info[2])

        self.aired = delist_if_needed(aired)
        self.name = delist_if_needed(name)
        self.overview = delist_if_needed(overview)
