print('Starting script.')
import os
import configparser
import fnmatch
import pprint
import time

# pip install theses vvv
from googleapiclient.discovery import build
import pafy




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
    def score_video(result, start_score, sort_arguments):
        score = start_score

        for word in sort_arguments['must_contain']:
            if word not in result['title'].lower():
                return 0

        for word in sort_arguments['must_not_contain']:
            if word in result['title'].lower():
                return 0

        for bonus in sort_arguments['bonuses_and_penalties']:
            for word in sort_arguments['bonuses_and_penalties'][bonus]:
                if word in result['title'].lower():
                    score += bonus
                    break

    # search for movie
    search = movie.replace('(', '').replace(')', '') + ' ' + added_search_term

    service = build("customsearch", "v1", developerKey=google_api_key)
    response = service.cse().list(q=search, cx='015352570329068055865:ihmqj9sngga', num=10).execute()
    top_score = 0
    score = 5
    selected_movie = None
    for result in response['items']:
        print(result['title'])
        print(result['link'])
        score_video(result, score, sort_arguments)
        print(score)
        score -= 1
        if score > top_score:
            top_score = score
            selected_movie = result
    if selected_movie is None:
        raise Exception("Didn't find a good video match for the movie using given sort_arguments")
    return selected_movie['link']


def download(youtube_source_url, download_dir, file_name):
    return True


def move_and_cleanup(source_dir, file_name,  target_dir):
    return True


def get_official_trailer(config):
    # Video constrains:

    must_contain = ['trailer']
    must_not_contain = []
    bonuses_and_penalties = {2: ['hd', '1080', '...'],
                             4: ['official'],
                             -10: ['teaser']}
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
    print('Movie to process: ' + movie_folder)
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
