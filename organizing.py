import os
import configparser
import fnmatch
import pprint
import shutil
import time

# pip install theses vvv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pytube import YouTube

# also, install FFmpeg.


def find_extra(config, extra_name, search, sort_arguments):

    print('Finding video for extra: "' + extra_name + '".')

    time.sleep(1)
    print('Loading configuration.')
    movie_library_dir = config.get('SETTINGS', 'movie_library_dir')
    google_api_key = config.get('SETTINGS', 'google_api_key')
    download_dir = config.get('SETTINGS', 'download_dir') or os.getcwd()

    time.sleep(1)
    print('Loading library.')
    library = get_library_record(movie_library_dir, config)

    time.sleep(1)
    print('finding movie to download extra for')
    movie_folder = get_movie_folder(library, list(), list(extra_name))

    config.set('LIBRARY_RECORD', movie_folder.replace(' ', '_'), str(library[movie_folder] + 1))

    time.sleep(1)
    print('finding video to download for : ' + movie_folder)
    video_to_download = get_video_to_download(movie_folder, search, sort_arguments, google_api_key)

    time.sleep(1)
    print('Downloading: "' + video_to_download['title'] + '"')
    download(video_to_download, download_dir, extra_name)

    time.sleep(1)
    print('Moving "' + extra_name + '" and cleaning up')
    move_and_cleanup(download_dir, os.path.join(movie_library_dir, movie_folder), extra_name + '.mp4')

    print('All done!')
    return True


def get_library_record(library_dir, config):

    library = dict()

    for folder_name in os.listdir(library_dir):
        if fnmatch.fnmatch(folder_name, '* (????)'):
            if not config.has_option('LIBRARY_RECORD', folder_name.replace(' ', '_')):
                new_entry = 0
            else:
                new_entry = int(config.getint('LIBRARY_RECORD', folder_name.replace(' ', '_')))

            library[folder_name] = new_entry
    return library


def get_movie_folder(earlier_tries, have, have_not):

    min_earlier_tries = 10000
    max_earlier_tries = 0

    for movie in earlier_tries:
        if earlier_tries[movie] < min_earlier_tries:
            min_earlier_tries = earlier_tries[movie]

        if earlier_tries[movie] > max_earlier_tries:
            max_earlier_tries = earlier_tries[movie]

    while True:
        for movie in earlier_tries:
            if earlier_tries[movie] > min_earlier_tries:
                continue

            for word in have:
                if word not in movie.lower():
                    continue

            for word in have_not:
                if word in movie.lower():
                    continue

            return movie

        if min_earlier_tries >= max_earlier_tries:
            break

        min_earlier_tries += 1

    raise Exception("Couldn't find a movie in the library matching the given restriction")


def get_video_to_download(movie, search_suffix, filter_arguments, google_api_key):

    def scan_response(response):

        response['max_video_resolution'] = 0

        for result in response['items']:

            time.sleep(1)
            video = YouTube(result['link'])
            result['youtube_object'] = video
            time.sleep(1)

            result['avg_rating'] = float(video.player_config_args['avg_rating'])
            result['view_count'] = int(video.player_config_args['view_count'])

            result['video_resolution'] = 0
            for stream in video.streams.filter(type='video').all():
                resolution = int(stream.resolution.replace('p', ''))
                if resolution > response['max_video_resolution']:
                    response['max_video_resolution'] = resolution
                if resolution > result['video_resolution']:
                    result['video_resolution'] = resolution

            try:
                if 'ad_preroll' in video.player_config_args:
                    result['adds_info'] = 'have adds'
                else:
                    result['adds_info'] = 'No adds'
            except ValueError:
                result['adds_info'] = 'No adds'

        return response

    def filter_response(response, arguments):

        items = list()

        for result in response['items']:

            append_video = True

            for word in arguments['video_name_must_contain']:
                if word.lower() not in result['title'].lower():
                    append_video = False

            for word in arguments['video_name_must_not_contain']:
                if word.lower() in result['title'].lower():
                    append_video = False

            if append_video:
                items.append(result)

        response.pop('items')
        response['items'] = items

        return response

    def score_response(response, scoring_arguments):

        for result in response['items']:

            result['true_rating'] = result['avg_rating'] * (1 - 1 / ((result['view_count'] / 60) ** 0.5))

            if result['video_resolution'] < 700:
                result['true_rating'] *= 0.90
                result['view_count'] *= 0.5

            for bonus in scoring_arguments['video_name_tag_bonuses']:
                for word in scoring_arguments['video_name_tag_bonuses'][bonus]:
                    if word in result['title'].lower():
                        result['true_rating'] *= bonus
                        break

        return response

    # search for movie
    search = movie.replace('(', '').replace(')', '') + ' ' + search_suffix
    service = build("customsearch", "v1", developerKey=google_api_key)
    search_response = service.cse().list(q=search, cx='015352570329068055865:ihmqj9sngga', num=6).execute()

    # deal with the response
    search_response = scan_response(search_response)
    search_response = filter_response(search_response, filter_arguments)
    search_response = score_response(search_response, filter_arguments)

    # select video
    selected_movie = None

    top_score = 0
    top_view_count = 0

    for item in search_response['items']:

        print('-----------------------------------------------------------------')
        print(item['title'])
        print(item['adds_info'])
        print(item['video_resolution'])
        print(item['link'])
        print(item['true_rating'])
        print(item['view_count'])

        if item['true_rating'] > top_score:
            top_score = item['true_rating']

    for item in search_response['items']:
        if item['true_rating'] > top_score * 0.95:
            if item['view_count'] > top_view_count:
                top_view_count = item['view_count']
                selected_movie = item

    return selected_movie


def download(youtube_video, download_dir, file_name):
    def get_best_adaptive_audio_stream(stream_list):

        max_bit_rate = 0
        top_audio_stream = None
        preferable_max_bit_rate = 0
        preferable_top_audio_stream = None

        for audio_stream in stream_list.streams.filter(type='audio', progressive=False).all():

            if audio_stream.is_progressive \
                    or audio_stream.resolution != '0p' \
                    or audio_stream.video_codec != 'unknown':
                continue

            bit_rate = int(audio_stream.abr.replace('kbps', ''))

            if bit_rate > max_bit_rate:
                max_bit_rate = bit_rate
                top_audio_stream = audio_stream

            if bit_rate > preferable_max_bit_rate and 'mp4a' in audio_stream.audio_codec.lower():
                preferable_max_bit_rate = bit_rate
                preferable_top_audio_stream = audio_stream

        if preferable_max_bit_rate * 1.7 > max_bit_rate:
            return preferable_top_audio_stream
        else:
            return top_audio_stream

    def get_best_adaptive_video_stream(stream_list):

        max_resolution = 0
        top_video_stream = None
        preferable_max_resolution = 0
        preferable_top_video_stream = None

        for video_stream in stream_list.streams.filter(type='video').all():

            if video_stream.is_progressive \
                    or video_stream.abr != '25kbps' \
                    or video_stream.audio_codec != 'unknown':
                continue

            resolution = int(video_stream.resolution.replace('p', ''))

            if resolution > max_resolution:
                max_resolution = resolution
                top_video_stream = video_stream

            if resolution > 1080:
                continue

            if resolution > preferable_max_resolution and 'avc' in video_stream.video_codec.lower():
                preferable_max_resolution = resolution
                preferable_top_video_stream = video_stream

        if preferable_max_resolution == max_resolution:
            return preferable_top_video_stream
        else:
            return top_video_stream

    def get_best_progressive_stream(stream_list):

        max_resolution = 0
        selected_stream = None

        for progressive_stream in stream_list.streams.filter(progressive=True).all():

            resolution = int(progressive_stream.resolution.replace('p', ''))

            if resolution > max_resolution:
                max_resolution = resolution

        max_score = 0
        for progressive_stream in stream_list.streams.filter().all():

            score = 0
            resolution = int(progressive_stream.resolution.replace('p', ''))
            bit_rate = int(progressive_stream.abr.replace('kbps', ''))

            if resolution == max_resolution:
                score += 10000
            if 'avc' in progressive_stream.video_codec.lower():
                score += 1000
            if 'mp4a' in progressive_stream.audio_codec.lower():
                score += bit_rate * 1.7
            else:
                score += bit_rate

            if score > max_score:
                max_score = score
                selected_stream = progressive_stream

        return selected_stream

    def download_adaptive_streams(video_stream, audio_stream, target_dir, target_file_name):

        video_stream.download(target_dir, 'video')
        audio_stream.download(target_dir, 'audio')

        if 'avc' in video_stream.video_codec.lower():
            video_encode_parameters = 'copy'
        else:
            video_encode_parameters = 'libx264 -preset slow -crf 18'

        if 'mp4a' in audio_stream.audio_codec.lower():
            audio_encode_parameters = 'copy'
        else:
            audio_encode_parameters = 'aac -strict -2 -b:a 128k'

        os.system('ffmpeg -i "' + os.path.join(target_dir, 'video') + '".* '
                         '-i "' + os.path.join(target_dir, 'audio') + '".* '
                         '-c:v ' + video_encode_parameters + ' '
                         '-c:a ' + audio_encode_parameters + ' '
                         '-threads 4 '
                         '"' + os.path.join(target_dir, target_file_name + '.mp4') + '" -y')

    def download_progressive_streams(progressive_stream, target_dir, target_file_name):

        print('Picked the progressive stream.')

        if progressive_stream.subtype.lower() == 'mp4':
            progressive_stream.download(target_dir, target_file_name)
            return
        else:
            progressive_stream.download(target_dir, 'progressive')

        if 'avc' in progressive_stream.video_codec.lower():
            video_encode_parameters = 'copy'
        else:
            video_encode_parameters = 'libx264 -preset slow -crf 18'

        if 'mp4a' in progressive_stream.audio_codec.lower():
            audio_encode_parameters = 'copy'
        else:
            audio_encode_parameters = 'aac -strict -2 -b:a 128k'

        os.system('ffmpeg -i "' + os.path.join(target_dir, 'progressive') + '".* '
                         '-c:v ' + video_encode_parameters + ' '
                         '-c:a ' + audio_encode_parameters + ' '
                         '-threads 4 '
                         '"' + os.path.join(target_dir, target_file_name + '.mp4') + '" -y')

    # decide adaptive streams to get
    video = youtube_video['youtube_object']
    for stream in video.streams.all():

        if stream.abr is None:
            stream.abr = '25kbps'
        if stream.audio_codec is None:
            stream.audio_codec = 'unknown'
        if stream.resolution is None:
            stream.resolution = '0p'
        if stream.video_codec is None:
            stream.video_codec = 'unknown'
    print('---------------------------------------------------------------------------------------------------')
    print(pprint.pprint(video.streams.all()))
    print('---------------------------------------------------------------------------------------------------')
    best_audio_stream = get_best_adaptive_audio_stream(video)
    best_video_stream = get_best_adaptive_video_stream(video)
    best_progressive_stream = get_best_progressive_stream(video)
    print(pprint.pprint(best_progressive_stream))
    print(pprint.pprint(best_video_stream))
    print(pprint.pprint(best_audio_stream))
    print('---------------------------------------------------------------------------------------------------')

    if 'mp4a' in best_audio_stream.audio_codec.lower():
        best_audio_stream.abr = int(best_audio_stream.abr.replace('kbps', '')) * 1.7
    if 'mp4a' in best_progressive_stream.audio_codec.lower():
        best_progressive_stream.abr = int(best_progressive_stream.abr.replace('kbps', '')) * 1.7

    # decide to get adaptive or progressive
    if int(best_video_stream.resolution.replace('p', '')) > int(best_progressive_stream.resolution.replace('p', '')):
        print('Picked the adaptive streams because of higher video resolution.')
        download_adaptive_streams(best_video_stream, best_audio_stream, download_dir, file_name)

    elif 'avc' not in best_progressive_stream.video_codec.lower() and 'avc' in best_video_stream.video_codec.lower():
        print('Picked the adaptive streams because of better video codec.')
        download_adaptive_streams(best_video_stream, best_audio_stream, download_dir, file_name)

    elif best_audio_stream.abr > best_progressive_stream.abr * 0.9:
        print('Picked the adaptive streams because of better audio.')
        download_adaptive_streams(best_video_stream, best_audio_stream, download_dir, file_name)

    else:
        download_progressive_streams(best_progressive_stream, download_dir, file_name)

    return


def move_and_cleanup(source_dir, target_dir, file_name):

    # moving file
    shutil.move(os.path.join(source_dir, file_name), os.path.join(target_dir, file_name))

    # deleting downloaded files

    for folder_name in os.listdir(source_dir):
        if fnmatch.fnmatch(folder_name, 'audio.*'):
            os.remove(os.path.join(source_dir, folder_name))
        if fnmatch.fnmatch(folder_name, 'video.*'):
            os.remove(os.path.join(source_dir, folder_name))
        if fnmatch.fnmatch(folder_name, 'progressive.*'):
            os.remove(os.path.join(source_dir, folder_name))


def get_official_trailer(config):
    #################################################################
    # Video constrains:
    extra_name = 'Official Trailer-trailer'
    search_suffix = ' Trailer'
    video_name_must_contain = ['trailer']
    video_name_must_not_contain = ['Side-by-Side', 'Side by Side', 'SidebySide']
    video_name_tag_bonuses = {
        1.01: ['official'],
        0.99: ['preview', 'teaser']
    }

    #################################################################

    filter_arguments = {'video_name_must_contain': video_name_must_contain,
                        'video_name_must_not_contain': video_name_must_not_contain,
                        'video_name_tag_bonuses': video_name_tag_bonuses}

    find_extra(config, extra_name, search_suffix, filter_arguments)


def get_remastered_trailer(config):

    #################################################################
    # Video constrains:
    extra_name = 'Remastered Trailer-trailer'
    search_suffix = ' Trailer'
    video_name_must_contain = ['trailer', 'remaster']
    video_name_must_not_contain = ['teaser', 'preview']
    #################################################################

    sort_arguments = {'video_name_must_contain': video_name_must_contain,
                      'video_name_must_not_contain': video_name_must_not_contain}

    find_extra(config, extra_name, search_suffix, sort_arguments)


config_file = 'config'
conf = configparser.ConfigParser()

for i in range(97):
    try:
        conf.read(config_file)

        get_official_trailer(conf)

        with open('config', 'w') as new_config_file:
            conf.write(new_config_file)
            new_config_file.close()

        time.sleep(150)
    except HttpError as e:
        print(e)
        break
    except KeyError as eeee:
        print(eeee)
    time.sleep(10)
