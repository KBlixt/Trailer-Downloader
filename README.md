# Trailer-Downloader

This script will go through your movie library and search for a trailer on youtube and download the best one (hopefully).
The script requires that you have a ordered library. Most preferably if you've named them "movie_name year".
Using parentheses or brackets around the year is alright.

The reason for this is that it will use the folder name to search for movies on google.

Rough explanation of the search method:
It will look at the rating for each movie (the blue bar by the thumbs up/down) and adjust it by how manny views it have.
hen the script will download the trailer with the most views that are within 5% of the highest rated video in the search.
it also take into consideration the resolution of the video somewhat.

it will put the trailer in the movie folder and call it "Official Trailer-trailer.mp4"


### Installation

You install it by downloading the script to anywhere and set up a config file. you can use the empty one provided and
rename it to "config.cfg".

Read and configure the config file. it's fairly straight forward. all you really have to do is point to the movie 
library and you're good to go, the rest is optional really unless your movies have a different name pattern.

you'll also need 2 python packages:

```sh
pip install pytube
pip install google
```

Then you can run it with python3.6 or python2.7 it will run until you stop it:

```sh
python3 /path/to/script/Trailer-Downloader-36
```
Or:
```sh
python /path/to/script/Trailer-Downloader-27
```

### folder naming scheme required for the script:

movie_name release_year

"movie_name" is the name of the movie and "release_year" is the year the movie was released.
".", "-" and "\_" as delimiters in stead of spaces is ok. 
parenthesis and square brackets will be removed entirely.

### FFmpeg and encoding

if you want to get 1080p streams then you'll have to get FFmpeg. this is because for some reason youtube stores their
audio/video streams separately for some reason. if this is enable then the script will make sure that you end up with a
trailer that uses h.264 and AAC in a mp4 container. it might encode if it finds higher resolutions that isn't in h.264.

install by

```sh
sudo apt-get update
sudo apt-get dist-upgrade
sudo apt-get install ffmpeg
```

### expanding the script

This script could probably be used to download other extras like interviews and behind the scenes. but I don't
need that for now. 

I made the script mainly for usage within plex. so turning it into some kind of plex plugin or hooking it up against the
plex Database would probably enhance the capabilities. like not searching by folder name and actually get the popper name.
