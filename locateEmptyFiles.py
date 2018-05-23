import os
import fnmatch
import configparser

config = configparser.RawConfigParser()
config.read('config.cfg')
movie_library_dir = config.get('SETTINGS', 'MOVIE_LIBRARY')

print('---------------------------------------------')
print('---------------------------------------------')
print('Folder without a movie:')
print('---------------------------------------------')
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
print('---------------------------------------------')
print('---------------------------------------------')
print('Movies without any trailer:')
print('---------------------------------------------')
for movie in os.listdir(movie_library_dir):

    official = False
    remaster = False
    movie_dir = movie_library_dir + '/' + movie
    for file in os.listdir(movie_dir):
        if fnmatch.fnmatch(file, 'Official Trailer-trailer.mp4'):
            official = True

        if fnmatch.fnmatch(file, 'Remastered Trailer-trailer.mp4'):
            remaster = True

    if remaster and official:
        continue
    print(movie)
print('---------------------------------------------')
print('---------------------------------------------')
print('Movies without an official trailer:')
print('---------------------------------------------')
for movie in os.listdir(movie_library_dir):

    official = False
    remaster = False
    movie_dir = movie_library_dir + '/' + movie
    for file in os.listdir(movie_dir):
        if fnmatch.fnmatch(file, 'Official Trailer-trailer.mp4'):
            official = True

    if official:
        continue
    print(movie)
print('---------------------------------------------')
print('---------------------------------------------')
