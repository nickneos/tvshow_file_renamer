import re
import json
from pathlib import Path

# my modules
from .tvdb_helper import get_episode_details, get_series_details
from .helpers import delist_if_needed

PATTERN = r"(?:s|season)\s?(\d{1,2})(?:e|episode|x)(\d{1,2})(?:(?:e|episode|x|\-)(\d{1,2}))?(?:(?:e|episode|x|\-)(\d{1,2}))?"


class Episode:
    def __init__(self, path, show_id, top_level_folder) -> None:
        self.path = path
        self.show_id = show_id
        self.top_level_folder = top_level_folder
        # self.show_name =
        # self.show_year =
        self.filename = Path(path).name
        self._get_tvdb_info()

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self):
        return vars(self)

    def _get_tvdb_info(self):
        # get series info
        series_info = get_series_details(self.show_id)
        self.show_name = series_info["name"]
        self.show_year = series_info["year"]

        # get episode info
        match = re.findall(PATTERN, self.filename, re.IGNORECASE)

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
            # eg. "S01E01E02"
            self.episode = delist_if_needed(
                [int(ep) for ep in match[0][1:] if ep.strip() != ""]
            )
        else:
            # also for multi episode files but with season repeater
            # eg. "S01E01 & S01E02 and S01E03"
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
            ep_info = get_episode_details(self.show_id, self.season, ep)
            if ep_info:
                aired.append(ep_info["aired"])
                name.append(ep_info["name"])
                overview.append(ep_info["overview"])

        self.aired = delist_if_needed(aired)
        self.name = delist_if_needed(name)
        self.overview = delist_if_needed(overview)
