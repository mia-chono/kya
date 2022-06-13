from dotenv import dotenv_values

import re
import requests
from fftools import FFmpeg
from fftools import utils as ffmpeg_utils
from crunchy_api import CrunchyApi

config = dotenv_values()


def get_episode_id(ep_url: str) -> str:
    return re.search(r"/[A-Z]\w+", ep_url).group(0)[1:]


def download_file(file_url: str, output_file_path: str = "subs.ass") -> None:
    r = requests.get(file_url)
    with open(output_file_path, 'wb') as f:
        f.write(r.content)


if __name__ == '__main__':
    url = 'https://beta.crunchyroll.com/fr/watch/GJWU25K3X/untitled'

    cr = CrunchyApi(
        basic_token=config.get('BASIC_TOKEN'),
        username=config.get('USERNAME'),
        password=config.get('PASSWORD')
    )
    cr.is_episode_link(url)
    id = get_episode_id(url)
    cr.login()
    ep = cr.get_episode(id)
    stream = cr.get_streams(ep)

    download_file(stream.subtitles['fr-FR'].url or stream.subtitles['en-US'].url)
    ffmpeg = FFmpeg()
    (
        ffmpeg
        .add_stream(stream.streams.adaptive_dash[''].url)
        .add_command('-c:v copy -c:a aac -c copy "./temp_video.mp4"')
        .run(monitor=ffmpeg_utils.basic_monitor)
    )

    # create a mkv file from the mp4 file and the subtitles
    ffmpeg.commands.clear()
    (
        ffmpeg
        .add_files(['./temp_video.mp4', './subs.ass'])
        .add_commands(['-map',
                       '0',
                       '-map',
                       '1',
                       '-metadata:s:v:0',
                       'title=Crunchyroll',
                       '-metadata:s:a:0',
                       'language=jpn',
                       '-metadata:s:a:0',
                       'title=Japonais',
                       '-metadata:s:a:0',
                       'language=jpn',
                       '-metadata:s:a:0',
                       'title=Japonais',
                       '-metadata:s:s:0',
                       'language=fre',
                       '-metadata:s:s:0',
                       'title=Français',
                       '-disposition:s:s:0',
                       'default',
                       '-c',
                       'copy',
                       '"video.mkv"'
                       ])
        .run(monitor=ffmpeg_utils.basic_monitor)
    )
