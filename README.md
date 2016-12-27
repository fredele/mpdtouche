# mpdtouch

It's another mpd client for touchscreens. Written in python with Kivy and Twisted.
You can navigate your mpd music collection by genre , artist, album.

I do not know if the touchscreen would really work with it, i  don't have one.

Mostly, it's a proof-of-concept. **DO NOT USE IT** for production or as your regular playback software.
Many improvements could be done, but I think that I will not pursue this task : it works well enough for my use.

There can be various issues, I only spent 5 days to write it, and I'm satisfied for the result given the work.
I had in mind to build a headless music player with a touchscreen, so I tried to make a GUI for mpd : here it is.

This code should be easely accessible for beginners to hack around.
To run tha app, launch main.py with python (2.7).

A web server must run to serve the covers (named "folder.jpg") placed in the same directory as the audio files.
This could be done with apache or ngingx or whatever with only one config file.

Maybe will there be someone who will get inspired ... (?)

Some screenshots :

![Screenshot](https://github.com/fredele/mpdtouche/blob/master/Screenshots/screenshot1.png?raw=true)

![Screenshot](https://github.com/fredele/mpdtouche/blob/master/Screenshots/screenshot2.png?raw=true)

![Screenshot](https://github.com/fredele/mpdtouche/blob/master/Screenshots/screenshot3.png?raw=true)

![Screenshot](https://github.com/fredele/mpdtouche/blob/master/Screenshots/screenshot4.png?raw=true)

