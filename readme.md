# TV Show File Renamer

Renames TV Show media files using information from thetvdb.com.

## Requirements
- `api_key.txt` file in root directory which contains your api key from [thetvdb.com](https://thetvdb.com/api-information)

## Usage

```sh
python tvshow_file_renamer.py [-h] [-f format-string] [-d] directory
```

| Positional Arguments | Description                                                                                  |
| -------------------- | -------------------------------------------------------------------------------------------- |
| `directory`          | Full path of TV show directory. Assumes all files under this directory relate to one tv show |

| Options                                   |                                                                                                                                               |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `-h`, `--help`                            | show this help message and exit                                                                                                               |
| `-f`, `--filename_format` `format-string` | The filename format to rename the files to. eg: `--filename_format "{show_name} ({show_year}) S{season_no}E{episode_no} {episode_name}{ext}"` |
| `-d`, `--debugmode`                       | Enables debug mode. In debug mode, renamed filenames are printed to screen but are not actually renamed on the disk                           |