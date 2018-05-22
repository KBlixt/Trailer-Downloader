
import os
import configparser
import fnmatch
import pprint
import time

# pip install theses vvv
from googleapiclient.discovery import build
import pafy
from pytube import YouTube


def get_library_record(library_dir, config):
    library = dict()
    for folder_name in os.listdir(library_dir):
        if fnmatch.fnmatch(folder_name, '* (????)'):
            temp = dict()
            folder_name_in_config = folder_name.replace(' ', '_')
            temp['movie_dir'] = os.getcwd() + config.get('SETTINGS', 'system_dir_changer') + folder_name
            if not config.has_option('LIBRARY_RECORD', folder_name_in_config):
                temp['earlier_tries'] = 0
            else:
                temp['earlier_tries'] = int(config.getint('LIBRARY_RECORD', folder_name_in_config))
            library[folder_name] = temp
    return library


def get_movie_folder(library, have, have_not):
    min_earlier_tries = 10000
    max_earlier_tries = 0

    for movie in library:
        if library[movie]['earlier_tries'] < min_earlier_tries:
            min_earlier_tries = library[movie]['earlier_tries']

        if library[movie]['earlier_tries'] > max_earlier_tries:
            max_earlier_tries = library[movie]['earlier_tries']

    while True:
        for movie in library:
            if library[movie]['earlier_tries'] > min_earlier_tries:
                continue

            for word in have:
                if word not in movie.lower():
                    continue

            for word in have_not:
                if word in movie.lower():
                    continue

            return movie

        if min_earlier_tries == max_earlier_tries:
            break

        min_earlier_tries += 1

    raise Exception("Couldn't find a movie in the library matching the given restriction")


def get_video_to_download(movie, added_search_term, sort_arguments, google_api_key):

    def scan_response(response, sort_arguments):
        start_score = 10
        response['best_video_resolution'] = 480

        for result in response['items']:
            video = YouTube(result['link'])

            result['title'] = result['pagemap']['videoobject'][0]['name']
            result['scoring'] = start_score
            start_score -= 0.9

            result['true_rating'] = float(video.player_config_args['avg_rating']) \
                                    * (1 - (1 / (int(video.player_config_args['view_count']) / 2500) ** 0.5))

            try:
                t = video.player_config_args['ad_preroll']
                result['adds_info'] = 'have adds'
            except Exception:
                result['adds_info'] = 'No adds'

            for stream in video.streams.filter(type='video').all():
                result['video_resolution'] = int(stream.resolution.replace('p', ''))
                if result['video_resolution'] > response['best_video_resolution']:
                    response['best_video_resolution'] = int(stream.resolution.replace('p', ''))

        return response

    def filter_response(response, sort_arguments):

        for result in response['items']:

            for word in sort_arguments['must_contain']:
                if word not in result['title'].lower():
                    response.pop(result)

            for word in sort_arguments['must_not_contain']:
                if word in result['title'].lower():
                    response.pop(result)

            if 1.7 * result['video_resolution'] < response['max_video_resolution']:
                response.pop(result)

        return response

    def score_response(response, sort_arguments):
        response['max_true_rating'] = 0
        response['min_true_rating'] = 5
        for result in response['items']:
            if result['true_rating'] > response['max_true_rating']:
                response['max_true_rating'] = result['true_rating']
            if result['true_rating'] < response['min_true_rating']:
                response['min_true_rating'] = result['true_rating']

        for result in response['items']:
            for bonus in sort_arguments['bonuses_and_penalties']:
                for word in sort_arguments['bonuses_and_penalties'][bonus]:
                    if word in result['title'].lower():
                        result['scoring'] += bonus
                        break

            result['normalized_true_rating'] = ((result['true_rating'] - response['min_true_rating'])
                                                / (response['max_true_rating']
                                                   - response['min_true_rating'])) * 10


        return response
    # search for movie
    search = movie.replace('(', '').replace(')', '') + ' ' + added_search_term
    service = build("customsearch", "v1", developerKey=google_api_key)
    response = service.cse().list(q='The Silence of the Lambs 1991 Trailer', cx='015352570329068055865:ihmqj9sngga', num=10).execute()

    # deal with the response
    response = scan_response(response, sort_arguments)
    response = filter_response(response, sort_arguments)
    response = score_response(response, sort_arguments)

    # select video
    selected_movie = None
    top_score = 0
    print('---------------------------------------------------------')
    for result in response['items']:
        print(result['title'])
        print(result['adds_info'])
        print(result['pagemap']['videoobject'][0]['datepublished'])
        print(result['link'])
        print(result['scoring'])
        print(result['normalized_true_rating'])
        print('---------------------------------------------------------')
        if result['scoring'] > top_score:
            top_score = result['scoring']
            selected_movie = result

    if selected_movie is None:
        raise Exception("Didn't find a good video match for the movie using given sort_arguments")
    return selected_movie['link']


def download(youtube_source_url, download_dir, file_name):
    return True


def move_and_cleanup(source_dir, file_name, target_dir):
    return True


def get_official_trailer(config):
    # Video constrains:
    must_contain = ['trailer']
    must_not_contain = []
    bonuses_and_penalties = {2: ['hd', '1080'],
                             4: ['official'],
                             -10: ['teaser', 'preview']}
    sort_arguments = {'must_contain': must_contain,
                      'must_not_contain': must_not_contain,
                      'bonuses_and_penalties': bonuses_and_penalties}

    movie_library_dir = config.get('SETTINGS', 'movie_library_dir')
    download_dir = config.get('SETTINGS', 'download_dir')
    system_dir_changer = config.get('SETTINGS', 'system_dir_changer')
    google_api_key = config.get('SETTINGS', 'google_api_key')
    print('Configuration loaded')

    library = get_library_record(movie_library_dir, config)
    print('Library loaded')
    movie_folder = get_movie_folder(library, list(), list('*Official Trailer-trailer.*'))
    print('Movie-trailer to download: ' + movie_folder)
    url_to_download = get_video_to_download(movie_folder, 'Official Trailer', sort_arguments, google_api_key)
    print('Downloading: ' + url_to_download)
    download(url_to_download, download_dir, 'Official Trailer-trailer')
    print('Download complete')
    move_and_cleanup(download_dir, 'Official Trailer-trailer', movie_library_dir + system_dir_changer + movie_folder)
    print('Move and cleanup complete')
    return True


config = configparser.ConfigParser()
config.read('config')
get_official_trailer(config)
