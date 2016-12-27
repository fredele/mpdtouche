from setuptools import setup
import sys, os

version = '0.1'

setup(	name='mpdtouch',
	version=version,
	author='fredele',
	author_email='frederic.klieber@gmail.com',
	include_package_data=True,
	url='https://github.com/fredele',
	description="A mpd clienttouchscreen",
	long_description=open("README.txt").read(),
	install_requires=[   "kivy", "twisted" ],
	data_files=[ ('', ['__main__.py','utils.py','mpd.py','window.kv','window.ini','audio-cd.png' ])],

	keywords='mpd touchscreen',
	license='MIT',
      )
