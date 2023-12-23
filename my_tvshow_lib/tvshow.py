import os
import re
import tvdb_helper
import argparse
from episode import Episode
from datetime import datetime
from pathlib import Path
from helpers import *


class TVShow:
    def __init__(self, folder) -> None:
        self.folder = str(Path(folder))
        self.multimode = False
        self._determine_tvshow()

    def __str__(self) -> str:
        return f"[{self.id}] {self.name} ({self.year})"

    def _determine_tvshow(self):
        tvshow_name = Path(self.folder).parts[-1]

        if _m := re.search(r"[\(\[]((19|20)\d{2})[\)\]]", tvshow_name):
            tvshow_name = tvshow_name.replace(_m.group(0), "").strip()
            year = int(_m.group(1))
            self.id, self.name, self.year = tvdb_helper.get_show_id(
                tvshow_name, year=year
            )
        else:
            self.id, self.name, self.year = tvdb_helper.get_show_id(tvshow_name)

        return self.id

    def get_episodes(self):
        self.episodes = []
        for root, dirs, files in os.walk(self.folder):
            for fn in files:
                if not is_video_file(fn):
                    continue
                episode = Episode(os.path.join(root, fn), self.id, self.name, self.multimode)
                self.episodes.append(episode)


if __name__ == "__main__":
    # args = parse_args()
    # rename_tvshows(args.directory, args.debugmode, args.tagsonly, args.multimode)
    tv_show = TVShow("/media/falcon/Videos/TV Shows/Mr Robot/")
    tv_show.multimode = True
    tv_show.get_episodes()
    
    print(tv_show)
    for episode in tv_show.episodes:
        print(episode)
        print("")
