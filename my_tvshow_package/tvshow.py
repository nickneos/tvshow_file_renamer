import os
import re
import json
from pathlib import Path
from my_tvshow_package import helpers, tvdb_helper
from my_tvshow_package import Episode


class TVShow:
    def __init__(self, folder) -> None:
        self.folder = str(Path(folder))
        self._determine_tvshow()

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "year": self.year,
            "folder": self.folder,
        }

    def _determine_tvshow(self):
        tvshow_name = Path(self.folder).parts[-1]
        kwargs = {}

        if _m := re.search(r"[\(\[]((19|20)\d{2})[\)\]]", tvshow_name):
            tvshow_name = tvshow_name.replace(_m.group(0), "").strip()
            kwargs["year"] = int(_m.group(1))
            
        data = tvdb_helper.find_series(tvshow_name, kwargs=kwargs)
        self.id = data.get("tvdb_id")
        self.name = data.get("name")
        self.year = data.get("year")

    def get_episodes(self):
        self.episodes = []
        for root, dirs, files in os.walk(self.folder):
            for fn in files:
                if not helpers.is_video_file(fn):
                    continue
                episode = Episode(os.path.join(root, fn), self.id)
                self.episodes.append(episode)
