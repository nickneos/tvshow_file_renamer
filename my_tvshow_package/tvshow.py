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
        if tvshow_name.lower().startswith("season"):
            tvshow_name = Path(self.folder).parts[-2]
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
        
        for f in Path(self.folder).rglob("*.*"):
            # for fn in files:
            if not helpers.is_video_file(f.name):
                continue
            if Path(self.folder).parts[-1].lower().startswith("season"):
                top_level_folder = Path(self.folder).parent.as_posix()
            episode = Episode(f.as_posix(), self.id, top_level_folder)
            self.episodes.append(episode)
