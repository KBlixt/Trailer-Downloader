# get movie folder
import os
import fnmatch
import configparser

config = configparser.RawConfigParser()
config.read('config')
movie_library_dir = config.get('SETTINGS', 'MOVIE_LIBRARY')
printing = True

for movie in os.listdir(movie_library_dir):
    printing = True
    movie_dir = movie_library_dir + '/' + movie
    for file in os.listdir(movie_dir):
        if fnmatch.fnmatch(file, '*].mkv'):
            printing = False
            break
        if fnmatch.fnmatch(file, '*].mp4'):
            printing = False
            break
        if fnmatch.fnmatch(file, '*].avi'):
            printing = False
            break
        if fnmatch.fnmatch(file, '*].wmv'):
            printing = False
            break
    if printing:
        print(movie)

