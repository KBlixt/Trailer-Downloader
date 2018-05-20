import os
import configparser
import fnmatch
import pprint
import time

# pip install theses vvv
from googleapiclient.discovery import build
from pytube import YouTube


class ExtraDownloader:
    def __init__(self, config_file='config'):
        self.config_file = config_file
        self.config = configparser.RawConfigParser()
        self.config.read(config_file)
        self.movie_name = ''
        self.movie_dir = ''
        self.movie_library_dir = self.config.get('SETTINGS', 'MOVIE_LIBRARY')
        self.directory_breaker = '/'
        self.google_api_key = self.config.get('SETTINGS', 'google_api_key')
        self.official_exists = False
        self.remastered_exists = False
        self.run()

        self.temp_path = None
        self.audio_stream = None
        self.audio_stream_path = None
        self.video_stream = None
        self.video_stream_path = None
        self.full_stream = None
        self.full_stream_path = None
        self.post_process_recode_audio = None
        self.post_process_recode_video = None
        self.count = 0

    def run(self):

        for i in range(2):
            if self.find_movie_name():
                if not self.official_exists:
                    self.download_extra('Official')
                    self.count += 1
                if not self.remastered_exists:
                    self.download_extra('Remaster')
                    self.count += 1
            if self.count > 45:
                break
        return

    def find_movie_name(self, limit):

        # get movie folder
        for movie in os.listdir(self.movie_library_dir):
            self.official_exists = False
            self.remastered_exists = False
            if fnmatch.fnmatch(movie, '* (????)'):

                self.movie_dir = self.movie_library_dir + self.directory_breaker + movie
                for file in os.listdir(self.movie_dir):
                    if 'Official Trailer-trailer' in file:
                        self.official_exists = True
                        break
                for file in os.listdir(self.movie_dir):
                    if 'Remastered Trailer-trailer' in file:
                        self.remastered_exists = True
                        break

                if self.remastered_exists and self.official_exists:
                    continue

                dir_config_name = movie.replace(' ', '_')
                try:
                    earlier_tries = self.config.getint('LIBRARY_RECORD', dir_config_name)
                except configparser.NoOptionError:
                    earlier_tries = 0
                if earlier_tries > limit:
                    continue
                if self.official_exists and 0 != limit:
                    continue
                earlier_tries += 1

                self.config.set('LIBRARY_RECORD', dir_config_name, str(earlier_tries))
                updated_config_file = open(self.config_file, 'w')
                self.config.write(updated_config_file)
                updated_config_file.close()
                self.movie_name = movie
                return True

        return False

        # go through them all, locate first movie without a trailer

        # parse the name for the movie name
        pass

    def download_extra(self, extra_name):

        # search for movie
        search = self.movie_name.replace('(', '').replace(')', '')
        search = search + ' ' + extra_name + ' Trailer'
        print(search)
        service = build("customsearch", "v1", developerKey=self.google_api_key)
        res = service.cse().list(q=search, cx='015352570329068055865:ihmqj9sngga', num=3).execute()

        download_name = ''
        for result in res['items']:
            print(result['title'])
            print(result['link'])

            if extra_name.lower() in result['title'].lower():

                download_name = result['link']

                break

        # download movie
        # example vid: https://www.youtube.com/watch?v=3WAOxKOmR90
        # https://www.youtube.com/watch?v=IUDTlvagjJA
        if download_name == '':
            return False
        yt = YouTube(download_name)
        pprint.pprint(yt.streams.all())
        pprint.pprint(yt.streams.filter(type='audio').all())

        self.audio_stream = (extra_name + '-audio')
        self.audio_stream_path = os.getcwd() + self.directory_breaker + self.audio_stream
        self.video_stream = (extra_name + '-video')
        self.video_stream_path = os.getcwd() + self.directory_breaker + self.video_stream
        self.full_stream = (extra_name + '-full')
        self.full_stream_path = os.getcwd() + self.directory_breaker + self.full_stream
        self.temp_path = os.getcwd()

        max_res = 0
        for stream in yt.streams.filter(type='video').all():
            if int(stream.resolution.replace('p', '')) > max_res:
                max_res = int(stream.resolution.replace('p', ''))
        max_res_str = str(max_res) + 'p'

        stream_with_max_abr = None
        max_abr = 0
        for stream in yt.streams.all():
            try:
                bit_rate = int(stream.abr.replace('kbps', ''))
                print(stream.itag + ':' + stream.abr)
            except AttributeError:
                continue
            if fnmatch.fnmatch(stream.audio_codec, '*mp4a*'):
                bit_rate = bit_rate * 1.85
            if bit_rate > max_abr:
                max_abr = bit_rate
                stream_with_max_abr = stream
        max_abr_str = stream_with_max_abr.abr

        available_video_streams = list()
        preferable_video_streams = list()
        for video_stream in yt.streams.filter(resolution=max_res_str).all():
            available_video_streams.append(video_stream)
            if fnmatch.fnmatch(video_stream.video_codec.lower(), '*avc*'):
                preferable_video_streams.append(video_stream)

        available_audio_streams = list()
        preferable_audio_streams = list()
        for audio_stream in yt.streams.filter(abr=max_abr_str).all():
            available_audio_streams.append(audio_stream)
            if fnmatch.fnmatch(audio_stream.audio_codec.lower(), '*mp4a*'):
                preferable_audio_streams.append(audio_stream)
        print(0)

        ########################################################################
        for video_stream in preferable_video_streams:
            for audio_stream in preferable_audio_streams:
                if audio_stream.itag == video_stream.itag:
                    print(video_stream.itag)
                    print(audio_stream.itag)
                    video_stream.download(self.temp_path, self.full_stream)
                    time.sleep(2)
                    os.system('ffmpeg -i "' + self.full_stream_path + '".* '
                              '-c:v copy '
                              '-c:a copy '
                              '-threads 4 '
                              '"' + self.full_stream_path + '"-rename.mp4')

                    self.move_extra(extra_name)
                    return True

        for video_stream in preferable_video_streams:
            for audio_stream in preferable_audio_streams:
                if audio_stream.is_adaptive and video_stream.is_adaptive:
                    print(video_stream.itag)
                    print(audio_stream.itag)
                    video_stream.download(self.temp_path, self.video_stream)
                    audio_stream.download(self.temp_path, self.audio_stream)
                    os.system('ffmpeg -i "' + self.video_stream_path + '".* '
                              '-i "' + self.audio_stream_path + '".* '
                              '-c:v copy '
                              '-c:a copy '
                              '-threads 4 '
                              '"' + self.full_stream_path + '"-rename.mp4')
                    self.move_extra(extra_name)
                    return True

        for video_stream in preferable_video_streams:
            for audio_stream in available_audio_streams:
                if audio_stream.itag == video_stream.itag:
                    print(video_stream.itag)
                    print(audio_stream.itag)
                    video_stream.download(self.temp_path, self.full_stream)
                    os.system('ffmpeg -i "' + self.full_stream_path + '".* '
                              '-c:v copy '
                              '-c:a aac -strict -2 -b:a 128k '
                              '-threads 4 '
                              '"' + self.full_stream_path + '"-rename.mp4')
                    self.move_extra(extra_name)
                    return True

        for video_stream in preferable_video_streams:
            for audio_stream in available_audio_streams:
                if audio_stream.is_adaptive and video_stream.is_adaptive:
                    print(video_stream.itag)
                    print(audio_stream.itag)
                    video_stream.download(self.temp_path, self.video_stream)
                    audio_stream.download(self.temp_path, self.audio_stream)
                    os.system('ffmpeg -i "' + self.video_stream_path + '".* '
                              '-i "' + self.audio_stream_path + '".* '
                              '-c:v copy '
                              '-c:a aac -strict -2 -b:a 128k '
                              '-threads 4 '
                              '"' + self.full_stream_path + '"-rename.mp4')
                    self.move_extra(extra_name)
                    return True

        for video_stream in available_video_streams:
            for audio_stream in preferable_audio_streams:
                if audio_stream.itag == video_stream.itag:
                    print(video_stream.itag)
                    print(audio_stream.itag)
                    video_stream.download(self.temp_path, self.full_stream)
                    os.system('ffmpeg -i "' + self.full_stream_path + '".* '
                              '-c:v libx264 -preset slow -crf 18 '
                              '-c:a copy '
                              '-threads 4 '
                              '"' + self.full_stream_path + '"-rename.mp4')
                    self.move_extra(extra_name)
                    return True

        for video_stream in available_video_streams:
            for audio_stream in preferable_audio_streams:
                if audio_stream.is_adaptive and video_stream.is_adaptive:
                    print(video_stream.itag)
                    print(audio_stream.itag)
                    video_stream.download(self.temp_path, self.video_stream)
                    audio_stream.download(self.temp_path, self.audio_stream)
                    os.system('ffmpeg -i "' + self.video_stream_path + '".* '
                              '-i "' + self.audio_stream_path + '".* '
                              '-c:v libx264 -preset slow -crf 18 '
                              '-c:a copy '
                              '-threads 4 '
                              '"' + self.full_stream_path + '"-rename.mp4')
                    self.move_extra(extra_name)
                    return True

        for video_stream in available_video_streams:
            for audio_stream in available_audio_streams:
                if audio_stream.itag == video_stream.itag:
                    print(video_stream.itag)
                    print(audio_stream.itag)
                    video_stream.download(self.temp_path, self.full_stream)
                    os.system('ffmpeg -i "' + self.full_stream_path + '".* '
                              '-c:v libx264 -preset slow -crf 18 '
                              '-c:a aac -strict -2 -b:a 128k '
                              '-threads 4 '
                              '"' + self.full_stream_path + '"-rename.mp4')
                    self.move_extra(extra_name)
                    return True

        for video_stream in available_video_streams:
            for audio_stream in available_audio_streams:
                if audio_stream.is_adaptive and video_stream.is_adaptive:
                    print(video_stream.itag)
                    print(audio_stream.itag)
                    video_stream.download(self.temp_path, self.video_stream)
                    audio_stream.download(self.temp_path, self.audio_stream)
                    os.system('ffmpeg -i "' + self.video_stream_path + '".* '
                              '-i "' + self.audio_stream_path + '".* '
                              '-c:v libx264 -preset slow -crf 18 '
                              '-c:a aac -strict -2 -b:a 128k '
                              '-threads 4 '
                              '"' + self.full_stream_path + '"-rename.mp4')
                    self.move_extra(extra_name)
                    return True

    def move_extra(self, extra_name):
        # move the movie to the movie directory it belongs to.
        if extra_name == 'Official':
            os.system('mv "' + self.full_stream_path + '-rename.mp4" "'
                      + self.movie_dir + self.directory_breaker + extra_name + ' Trailer-trailer.mp4"')
        elif extra_name == 'Remaster':
            os.system('mv "' + self.full_stream_path + '-rename.mp4" "'
                      + self.movie_dir + self.directory_breaker + '-' + extra_name + 'ed Trailer-trailer.mp4"')

        os.system('rm "' + self.video_stream_path + '".*')
        os.system('rm "' + self.audio_stream_path + '".*')


run = ExtraDownloader()
