#!/usr/bin/env python
# -*- coding: utf-8 -*-

from kivy.app import App
import os, urllib, hashlib, time
from kivy.support import install_twisted_reactor
install_twisted_reactor()
from mpd import MPDFactory
from twisted.internet import reactor
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.listview import ListItemButton
from kivy.adapters.models import SelectableDataItem
from kivy.clock import Clock
from kivy.core.window import Window
from utils import TimeToHMS , format_to_str,url_exists
from kivy.factory import Factory
from PIL import Image
from parsers.rssparser import  RssParser
from parsers.xfpsparser import  XspfParser
import time
import json
import alsaaudio


current_song = {}

class LibraryListWidget(BoxLayout):
    pass
Factory.register('LibraryListWidget', LibraryListWidget)

class ListItemButton1(ListItemButton):
    song = dict

class Modal_Volume(ModalView):
    def __init__(self,vol):
        super(Modal_Volume, self).__init__()
        self.vol = vol
        self.ids.volume_slider.value = self.vol

    def on_volume_slide(self):
        if WA.sound_driver == 'alsa':
            m = alsaaudio.Mixer()
            m.setvolume(int(self.ids.volume_slider.value))
        else :
            WA.protocol.setvol(int(self.ids.volume_slider.value))


class Modal_No_Connection(ModalView):
    pass


class Modal_Add_Box(ModalView):
    def __init__(self,result):
        super(Modal_Add_Box, self).__init__()
        self.result = result

    def on_play_press(self):
        WA.protocol.clear()
        for file in self.result:
            WA.protocol.add(file)
        self.dismiss()
        WA.protocol.play()
        WA.protocol.currentsong().addCallback(WA.PlayerControlWidget.CallBack_Current_Song)

    def on_add_press(self):
        for file in self.result:
            WA.protocol.add(file)
        self.dismiss()


class Modal_Playlist_Add_Box(ModalView):
    def __init__(self,result):
        super(Modal_Playlist_Add_Box, self).__init__()
        self.result = result

    def on_play_press(self):
        WA.protocol.clear()
        WA.protocol.load(self.result)
        WA.protocol.play()
        self.dismiss()


    def on_add_press(self):
        WA.protocol.load(self.result)
        self.dismiss()


class WidgetListButton(BoxLayout):
    pass


class SongListItem(SelectableDataItem):
    pass

class CustomListItem(SelectableDataItem):
    pass

class Params(Screen):
    def on_update(self):
        print 'updating DB'
        WA.protocol.update()

    def CallBack_Stats(self,result):
        #print result
        WA.ParamsControlWidget.stats.text = \
            "Uptime   : " + TimeToHMS(int(result['uptime'])) +  \
            "   -   Playtime : " + TimeToHMS(int(result['playtime'])) + '\n' + '\n' + \
            "Last Update       :  " + time.ctime(int(result['db_update'])) + '\n' + '\n' +\
            "DB Total Playtime :  " + TimeToHMS(int(result['db_playtime'])) + '\n' +  '\n'  + \
        format_to_str(result['artists']) + ' Artists, ' +  format_to_str(result['albums']) + ' Albums, ' + format_to_str(result['songs']) + ' Songs'


class Library(Screen):
    artist = None
    album = None
    genre = None
    source = 'a'
    def Set_Sources(self):
        if self.source != None:
            WA.Library_Screen.ids.library_widget.clear_widgets()
            self.llw = LibraryListWidget()
            WA.Library_Screen.ids.library_widget.add_widget(self.llw)
            WA.Library_Screen.ids.title.text = 'Sources'
            self.llw.ids.library_list.adapter.bind(on_selection_change=self.Get_Source)
            sources = ['Genres', 'Albums','Artists','Playlists','Podcasts','Radios']
            self.llw.ids.library_list.adapter.data.extend([item for item in sources])
            self.source = None

    def Get_Source(self ,adapter):
        self.genre = None
        self.album = None
        self.artist = None
        self.podcast = None
        self.radio = None
        if adapter.selection:
            self.source = adapter.selection[0].text

            if self.source == 'Genres':
               WA.protocol.list('genre').addCallback(WA.LibraryControlWidget.Callback_Set_Widget)

            if self.source == 'Albums':
                WA.protocol.list('album').addCallback(WA.LibraryControlWidget.Callback_Set_Widget)
            if self.source == 'Artists':
                WA.protocol.list('artist').addCallback(WA.LibraryControlWidget.Callback_Set_Widget)
            if self.source == 'Playlists':
                WA.protocol.listplaylists().addCallback(WA.LibraryControlWidget.Callback_Set_Widget)
            if self.source == 'Podcasts':
                WA.LibraryControlWidget.Callback_Set_Widget('[]')
            if self.source == 'Radios':
                WA.LibraryControlWidget.Callback_Set_Widget('[]')
    def Back(self):
        if self.source == 'Genres':
            if self.genre != None and self.artist != None :     #and self.album == None
                self.album = None
                self.artist = None
                WA.protocol.list('artist', 'genre', self.genre).addCallback(self.Callback_Set_Widget)

            elif self.genre != None and self.artist == None :   #and self.album == None
                self.genre = None
                WA.protocol.list('genre').addCallback(self.Callback_Set_Widget)
            else:
                self.Set_Sources()

        elif self.source == 'Albums':
            self.Set_Sources()

        elif self.source == 'Artists':
            if  self.artist == None:
                self.Set_Sources()
            else :
                WA.protocol.list('artist').addCallback(WA.LibraryControlWidget.Callback_Set_Widget)
                self.artist = None

        elif self.source == 'Playlists':
            self.Set_Sources()

        elif self.source == 'Podcasts':
            if self.podcast == None :
                self.Set_Sources()
            else :
                self.podcast = None
                self.Callback_Set_Widget('')

        elif self.source == 'Radios':
            self.Set_Sources()
        else:
            pass

    def Callback_Set_Widget(self, result):
        result = [item for item in result if item != '']
        if self.source == 'Genres':
            if self.genre  == None and self.artist  == None and self.album  == None:
                self.llw = None
                #print('Genre selection')
                WA.Library_Screen.ids.library_widget.clear_widgets()
                self.llw = LibraryListWidget()
                WA.Library_Screen.ids.library_widget.add_widget(self.llw)
                WA.Library_Screen.ids.title.text = 'Genre'
                self.llw.ids.library_list.adapter.bind(on_selection_change=self.get_artists_from_genre )
                self.llw.ids.library_list.adapter.data.extend([item for item in result])

            if self.genre  != None and self.artist  == None and self.album  == None:
                self.llw = None
                #print('Artist selection')url
                WA.Library_Screen.ids.library_widget.clear_widgets()
                self.llw = LibraryListWidget()
                WA.Library_Screen.ids.library_widget.add_widget(self.llw)
                WA.Library_Screen.ids.title.text = self.genre + ' Artists'
                self.llw.ids.library_list.adapter.bind(on_selection_change=self.get_albums_from_artist )
                self.llw.ids.library_list.adapter.data.extend([item for item in result])

            if self.genre  != None and self.artist  != None and self.album  == None:
                self.llw = None
                #print('Album selection')
                WA.Library_Screen.ids.library_widget.clear_widgets()
                self.llw = LibraryListWidget()
                WA.Library_Screen.ids.library_widget.add_widget(self.llw)
                WA.Library_Screen.ids.title.text = self.artist  + ' Albums'
                self.llw.ids.library_list.adapter.bind(on_selection_change=self.get_files_from_album )
                try:
                    i = 0
                    for album in result :
                        self.llw.ids.library_list.adapter.data.extend([album])
                        WA.protocol.list('file', 'album', album, 'artist', self.artist, 'genre', self.genre).addCallback(self.Set_album_covers,i)
                        i +=1
                except:
                    pass

        elif  self.source == 'Albums':
            self.llw = None
            #print('Albums selection')
            WA.Library_Screen.ids.library_widget.clear_widgets()
            self.llw = LibraryListWidget()
            WA.Library_Screen.ids.library_widget.add_widget(self.llw)
            WA.Library_Screen.ids.title.text = 'Albums'
            self.llw.ids.library_list.adapter.bind(on_selection_change=self.get_files_from_album)
            try:
                i = 0
                for album in result:
                    self.llw.ids.library_list.adapter.data.extend([album])
                    WA.protocol.list('file', 'album', album).addCallback( self.Set_album_covers, i)
                    i += 1
            except:
                pass

        elif  self.source == 'Artists':
            if self.artist == None:
                self.llw = None
                #print('Artists selection')
                WA.Library_Screen.ids.library_widget.clear_widgets()
                self.llw = LibraryListWidget()
                WA.Library_Screen.ids.library_widget.add_widget(self.llw)
                WA.Library_Screen.ids.title.text = 'Artists'
                self.llw.ids.library_list.adapter.bind(on_selection_change=self.get_albums_from_artist)
                self.llw.ids.library_list.adapter.data.extend([album for album in result])
            else:
                self.llw = None
                #print('Albums selection')
                WA.Library_Screen.ids.library_widget.clear_widgets()
                self.llw = LibraryListWidget()
                WA.Library_Screen.ids.library_widget.add_widget(self.llw)
                WA.Library_Screen.ids.title.text = 'Albums'
                self.llw.ids.library_list.adapter.bind(on_selection_change=self.get_files_from_album)
                i = 0
                for album in result:
                    self.llw.ids.library_list.adapter.data.extend([album])
                    WA.protocol.list('file', 'album', album).addCallback(self.Set_album_covers, i)
                    i += 1

        elif self.source == 'Playlists':
            WA.Library_Screen.ids.library_widget.clear_widgets()
            self.llw = LibraryListWidget()
            WA.Library_Screen.ids.library_widget.add_widget(self.llw)
            WA.Library_Screen.ids.title.text = 'Playlists'
            #print result
            self.llw.ids.library_list.adapter.data.extend([playlist for playlist in result])
            self.llw.ids.library_list.adapter.bind(on_selection_change=self.get_playlist)

        elif self.source == 'Podcasts':
            with open(WA.root_dir + '/podcasts/podcasts.json') as data:
                jsondata = json.load(data)
                WA.Library_Screen.ids.library_widget.clear_widgets()
                self.llw = LibraryListWidget()
                WA.Library_Screen.ids.library_widget.add_widget(self.llw)
                WA.Library_Screen.ids.title.text = 'Podcasts'
                self.llw.ids.library_list.adapter.data.extend([podcast for podcast in jsondata["podcasts"]])
                self.llw.ids.library_list.adapter.bind(on_selection_change=self.get_podcast)

        elif self.source == 'Radios':
            g = XspfParser()
            g.parseFile(WA.root_dir + '/radios/radios.xspf')
            radios = g.getResult()
            for radio in radios['tracklist']:
                m = hashlib.md5()
                m.update(radio['location'])
                WA.cache_file = WA.cache_dir + m.hexdigest() + '.jpg'
                if  os.path.isfile(WA.cache_file):
                    pass
                else:
                    if radio.has_key('image'):
                        if url_exists(radio['image']):
                            urllib.urlretrieve(radio['image'], WA.cache_file)

            WA.Library_Screen.ids.library_widget.clear_widgets()
            self.llw = LibraryListWidget()
            WA.Library_Screen.ids.library_widget.add_widget(self.llw)
            WA.Library_Screen.ids.title.text = 'Radios'
            self.llw.ids.library_list.adapter.data.extend([radio for radio in radios['tracklist']])
            self.llw.ids.library_list.adapter.bind(on_selection_change=self.get_radio)

        else:
            pass

    def get_playlist(self ,adapter):
        if adapter.selection:
            #print adapter.selection[0].text
            self.mdp = Modal_Playlist_Add_Box(adapter.selection[0].text)
            self.mdp.open()

    def get_radio(self ,adapter):
        if adapter.selection:
            WA.protocol.stop()
            WA.protocol.clear()
            WA.protocol.add(adapter.selection[0].song['location'])
            WA.protocol.play()
            WA.Player_Screen.Clear_Screen()
            WA.sm.goto_Player()
            WA.Player_Screen.ids.player_album.text =  adapter.selection[0].text
            WA.Player_Screen.ids.player_title.text = ''
            WA.Player_Screen.ids.player_artist.text = ''
            WA.Player_Screen.ids.player_genre.text = ''
            if adapter.selection[0].song.has_key('image'):
                WA.Player_Screen.ids.player_cover.source = WA.get_cover_path(adapter.selection[0].song['image'], True)

    def get_podcast(self ,adapter):
        if adapter.selection:
            self.podcast = adapter.selection[0].text
            content =  urllib.urlopen(adapter.selection[0].song['feedurl'])
            res = RssParser()
            res.parseFile(content)
            resdict = res.getResult()
            items = resdict['items']
            self.llw = None
            WA.Library_Screen.ids.library_widget.clear_widgets()
            self.llw = LibraryListWidget()
            WA.Library_Screen.ids.library_widget.add_widget(self.llw)
            WA.Library_Screen.ids.title.text = 'Podcast : ' + adapter.selection[0].text
            self.llw.ids.library_list.adapter.bind(on_selection_change=self.set_podcast)
            self.llw.ids.library_list.adapter.data.extend([item for item in items ])
            res = None
            content = None

    def set_podcast(self ,adapter):
        if adapter.selection:
            WA.Library_Screen.ids.library_widget.clear_widgets()
            WA.protocol.stop()
            WA.protocol.clear()
            WA.protocol.add(str(adapter.selection[0].song['guid']))
            WA.protocol.play()
            WA.Player_Screen.Clear_Screen()
            WA.sm.goto_Player()
            WA.Player_Screen.ids.player_album.text =  adapter.selection[0].text
            WA.Player_Screen.ids.player_title.text = ''
            WA.Player_Screen.ids.player_artist.text = ''
            WA.Player_Screen.ids.player_genre.text = ''

    def get_artists_from_genre(self ,adapter):
        if adapter.selection:
            self.genre = adapter.selection[0].text
            WA.protocol.list('artist', 'genre', self.genre).addCallback(self.Callback_Set_Widget)
            #self.adapter.bind(on_selection_change=self.llw.on_selection_change)

    def get_albums_from_artist(self ,adapter):
        if adapter.selection:
            self.artist = adapter.selection[0].text
            if self.genre  != None:
                WA.protocol.list('album', 'artist', self.artist ,'genre' ,self.genre).addCallback(self.Callback_Set_Widget)
            else:
                WA.protocol.list('album', 'artist', self.artist).addCallback(self.Callback_Set_Widget)

    def get_files_from_album(self ,adapter):
        if adapter.selection:
            self.album = adapter.selection[0].text
            if   self.artist != None and self.genre != None :
                WA.protocol.list('file', 'album',self.album , 'artist', self.artist ,'genre' ,self.genre).addCallback(self.Get_files)
            else:
                WA.protocol.list('file', 'album', self.album ).addCallback(self.Get_files)

    def Get_files(self, result):
        #print('Get files')
        self.md = Modal_Add_Box(result)
        self.md.open()

    def Set_album_covers(self,result,i):
        try:
            cover =  WA.root_dir +'/textures/audio-cd.png'
            for file in result:
                if cover ==  WA.root_dir +'/textures/audio-cd.png':
                    cover = WA.get_cover_path(file,True)
                    #print self.llw.ids.library_list.adapter.data[i] # ... Le nom de l' album ...
                    self.llw.ids.library_list.adapter.get_view(int(i)).itemimage.source = cover
                else:
                    break
        except:
            cover == WA.root_dir + '/textures/audio-cd.png'

    def Scroll_Playlist(self):
        #print 'scroll'
        self.llw.ids.library_list.container.parent.scroll_to(self.llw.ids.library_list.adapter.get_view(10), padding=10, animate=True)


class Playlist(Screen):
    playlist_list = ObjectProperty()

    def __init__(self, **kwargs):
        super(Playlist, self).__init__(**kwargs)

    def on_SongListItem_press(self,*args):
        self.Color_Playlist( args[0].song)
        WA.protocol.seekid(int(args[0].song['id']), 0)



    def Color_Playlist(self,current_song):
        for i in range(0, len(self.playlist_list.adapter.data)):
            item = self.playlist_list.adapter.get_view(int(i)).ids.itembutton
            item.background_color = [0.0, 0.0, 0.0, 1]
            item.selected_color = [0.0, 0.0, 0.0, 1]
            item.deselected_color = [0.0, 0.0, 0.0, 1]
        try:
            if current_song.has_key('pos'):
                item = self.playlist_list.adapter.get_view(int(current_song['pos'])).ids.itembutton
                if item is not None:
                     item.background_color = (0.8, 0.8, 0.8, 1)
        except:
            pass

    def Clear_Playlist(self):
        WA.protocol.clear()
        WA.PlayerControlWidget.on_stop_press()
        WA.protocol.playlistinfo().addCallback(WA.PlayerControlWidget.CallBack_playlist)


class Player(Screen):
    PLAY_STATE = False
    Player_cover = ObjectProperty()
    player_slider = ObjectProperty()
    player_artist = ObjectProperty()
    player_album = ObjectProperty()
    player_title = ObjectProperty()
    player_genre = ObjectProperty()
    player_song_elapsed_time = ObjectProperty()
    player_song_total_time = ObjectProperty()
    play_btn = ObjectProperty()
    songid = '-1'


    def __init__(self, **kwargs):
        super(Player, self).__init__(**kwargs)

    def Clear_Screen(self):
        self.player_slider.max = 0
        self.player_slider.value = 0
        self.player_song_elapsed_time.text = TimeToHMS(0)
        self.player_song_total_time.text = TimeToHMS(0)

        self.player_artist.text = format_to_str('')
        self.player_genre.text = format_to_str('')
        self.player_title.text = format_to_str('')
        self.player_album.text = format_to_str('')
        self.player_cover.source =  WA.root_dir +'/textures/audio-cd.png'




    def on_play_press(self):
        if self.PLAY_STATE:
            WA.protocol.pause()
            #WA.PlayerControlWidget.ids.play_btn_image.source = WA.root_dir +'/textures/pause.png'
            self.PLAY_STATE = False
        else:
            self.PLAY_STATE = True
            #WA.PlayerControlWidget.ids.play_btn_image.source = WA.root_dir +'/textures/play.png'
            WA.protocol.play().addCallback(self.CallBack_Play)
        WA.protocol.currentsong().addCallback(self.CallBack_Current_Song)


    def on_stop_press(self):
        self.PLAY_STATE = False
        WA.protocol.stop().addCallback(self.CallBack_Stop)
        WA.protocol.currentsong().addCallback(self.CallBack_Current_Song)
        self.Clear_Screen()

    def on_previous_press(self):
        self.player_slider.value = 0
        WA.protocol.previous()


    def on_next_press(self):
        self.player_slider.value = 0
        WA.protocol.next()

    def on_player_slider_touch_move(self):
        #val =int((self.player_slider.value))
        #WA.protocol.seekcur(val)
        pass

    def Callback_Status(self, result):
        try:
            if result['state'] == 'play':
                if result.has_key('time'):
                    if result['state'] == 'play':
                        self.player_slider.max =   int( result['time'].split(':',-1)[1])
                        self.player_slider.value =  round(float(result['elapsed']))
                        self.player_song_elapsed_time.text = TimeToHMS(round(float(result['elapsed'])))
                        self.player_song_total_time.text = TimeToHMS(int( result['time'].split(':',-1)[1]))
                        self.play_btn_image.source =  WA.root_dir + "/textures/play.png"
            elif result['state'] == 'pause':
                self.play_btn_image.source = WA.root_dir + "/textures/pause.png"
            if result.has_key('song'):
                if  self.songid  !=  result['song']:
                    self.songid  = result['song']
                    #print('song changed !')

                    WA.protocol.currentsong().addCallback(self.CallBack_Current_Song)

            if result.has_key('volume'):
                self.volume  = result['volume']


        except:
            pass

    def on_volume_press(self):
        if WA.sound_driver == 'alsa':
            m = alsaaudio.Mixer()
            self.volume = m.getvolume()[0]
        self.md = Modal_Volume( self.volume)
        self.md.open()

    def CallBack_Play(self,result):
        pass

    def CallBack_Stop(self, result):
        self.player_slider.value = 0

    def CallBack_Previous(self, result):
        pass

    def CallBack_Next(self, result):
        pass

    def CallBack_playlist(self, result):
        WA.Playlist_Screen.ids.playlist_list.adapter.data = []
        WA.Playlist_Screen.ids.playlist_list.adapter.data.extend([song for song in result])

    def CallBack_Current_Song(self, result):
        current_song  = result.copy()
        if current_song.has_key('time'):
            self.player_slider.max = int(current_song['time'])
            WA.PlaylistControlWidget.Color_Playlist(current_song)

        if current_song.has_key('album'):
            self.player_album.text = format_to_str(current_song['album'])
        elif current_song.has_key('file'):
            self.player_album.text = WA.get_title_from_stream(format_to_str(current_song['file']))
        else:
            self.player_album.text = ''

        if current_song.has_key('genre'):
            self.player_genre.text = format_to_str(current_song['genre'])
        else:
            self.player_genre.text =''
        if current_song.has_key('title'):
            self.player_title.text = format_to_str(current_song['title'])
        else:
            self.player_title.text = ''
        if current_song.has_key('artist'):
            self.player_artist.text = format_to_str(current_song['artist'])
        else:
            self.player_artist.text = ''
        if current_song.has_key('file'):
            try:
                self.player_cover.source = WA.get_cover_path(current_song['file'],False)
            except:
                pass
        WA.PlaylistControlWidget.Color_Playlist(current_song )

    def on_connection(self, connection):
        self.print_message("connected successfully!")
        self.connection = connection


class ScreenManager(ScreenManager):
    def goto_Playlist(self):
        WA.protocol.playlistinfo().addCallback(WA.PlayerControlWidget.CallBack_playlist)
        WA.protocol.currentsong().addCallback(WA.PlayerControlWidget.CallBack_Current_Song)

        for i in range(0, len( WA.PlaylistControlWidget.ids.playlist_list.adapter.data)):
            item = WA.PlaylistControlWidget.ids.playlist_list.adapter.get_view(int(i)).ids.itembutton
            item.background_color = [0.0, 0.0, 0.0, 1]
            item.selected_color = [0.0, 0.0, 0.0, 1]
            item.deselected_color = [0.0, 0.0, 0.0, 1]
        self.current = 'Playlist'

    def goto_Player(self):
        self.current = 'Player'

    def goto_Library(self):
        WA.Library_Screen.Set_Sources()
        self.current = 'Library'

    def goto_Params(self):
        self.current = 'Params'
        WA.protocol.stats().addCallback(WA.ParamsControlWidget.CallBack_Stats)


class MpdtouchApp(App):
    Schedule_time = 1
    protocol = None
    connection_status = False
    No_Connection = False
    referenced_streams = []

    def __init__(self):
        super(MpdtouchApp, self).__init__()
        self.root_dir= os.path.dirname(os.path.realpath(__file__))
        #print self.root_dir


    def _keyboard_closed(self):
        #print('My keyboard have been closed!')
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        #print keycode

        #switch views
        if   keycode[1] == 'a':
            self.sm.goto_Player()
        elif keycode[1] == 'z':
            self.sm.goto_Playlist()
        elif keycode[1] == 'e':
            self.sm.goto_Library()
        elif keycode[1] == 'r':
            self.sm.goto_Params()
        #Player
        elif keycode[1] == 'q':
            self.PlayerControlWidget.on_previous_press()
        elif keycode[1] == 's':
            self.PlayerControlWidget.on_play_press()
        elif keycode[1] == 'd':
            self.PlayerControlWidget.on_stop_press()
        elif keycode[1] == 'f':
            self.PlayerControlWidget.on_next_press()
        return True

    def get_application_config(self):
        #   ~/.mpdtouch/config.ini
        return super(MpdtouchApp, self).get_application_config( '~/.%(appname)s/config.ini')

    def song_converter(self,index, data_item):
        if data_item.has_key('track') and data_item.has_key('title') and data_item.has_key('artist') and data_item.has_key('album'):
            return {'song': data_item,
                    'cover_source': self.get_cover_path(data_item['file'],True),
                    'text':
                        ('[b]' + str(data_item['track']) + ' - ' + format_to_str(
                            data_item['title']) + '[/b]\n       ' + '[i]' + format_to_str(
                            data_item['artist'])) + ' - ' + format_to_str(data_item['album']) + '[/i]'
                    }
        elif data_item.has_key('file'):
            return {'song': data_item,
                    'cover_source': self.get_cover_path(data_item['file'],True),
                    'text': '[b]' + WA.get_title_from_stream (format_to_str(data_item['file'])) + '[/b]'
                    }


    def library_converter(self,index, data_item):
        #print data_item
        if isinstance(data_item, basestring):
            return {'text': data_item, 'source':  WA.root_dir +'/textures/audio-cd.png', 'song': ''}
        if isinstance(data_item, dict) and data_item.has_key('playlist'):
            return { 'text': data_item['playlist'], 'source':  WA.root_dir +'/textures/audio-cd.png', 'song': ''}

        if isinstance(data_item, dict) and data_item.has_key('feedurl'):  #podcasts
            return { 'text': data_item['name'], 'source': self.get_cover_path(data_item['cover'],True), 'song' :data_item }

        if isinstance(data_item, dict) and data_item.has_key('pubDate'):  #podcast
            return { 'text': data_item['title'], 'source':  WA.root_dir +'/textures/audio-cd.png', 'song' :data_item }

        if isinstance(data_item, dict) and data_item.has_key('location'):  #radio
            if data_item.has_key('image'):
                return { 'text': data_item['title'], 'source':  self.get_cover_path(data_item['image'],True) , 'song' :data_item }
            else :
                return {'text': data_item['title'], 'source' : WA.root_dir +'/textures/audio-cd.png' ,'song': data_item}

    def get_cover_path(self,filepath,cache):
        '''
        :param filepath: a url or a local filepath
        :param cache: if True, returns the cached file, else the real url.
        :return:
        '''
        try:
            if not filepath.startswith("http"):
                dir_path = urllib.quote(os.path.dirname(filepath.encode('UTF-8')))
                url = WA.cover_base_url + dir_path + '/folder.jpg'
            elif filepath.endswith(".jpg"):
                url = filepath
            elif filepath.endswith(".mp3"):
                # stream mp3
                url = filepath
                cache = True
            else:
                url = WA.root_dir + '/textures/audio-cd.png'
            m = hashlib.md5()
            m.update(url)
            cache_file = self.cache_dir + m.hexdigest()+'.jpg'
            if os.path.isfile(cache_file) and cache ==True :
                #print 'get cached file ...'
                return cache_file
            else:
                if url_exists(url) and url.endswith(".jpg"):
                    urllib.urlretrieve(url, cache_file)
                    # create thumbnails
                    size = 128, 128
                    im = Image.open(cache_file)
                    im.thumbnail(size, Image.ANTIALIAS)
                    im.save( cache_file, "JPEG")

                    #print 'get from Web server ...'
                    return url
                else:
                    return  WA.root_dir +'/textures/audio-cd.png'
        except:
            return  WA.root_dir +'/textures/audio-cd.png'

    def read_radio(self):
        g = XspfParser()
        g.parseFile(WA.root_dir + '/radios/radios.xspf')
        radios = g.getResult()
        for radio in radios['tracklist']:
            item = {}
            if radio.has_key('title'):
                item['title'] = radio['title']
            if radio.has_key('image'):
                item['image'] = radio['image']
            if radio.has_key('location'):
                item['url']   = radio['location']
            item['type'] =  'radio'
            self.referenced_streams.append(item)
    def get_title_from_stream(self, stream):
        res = stream
        for item in self.referenced_streams:
            if item.has_key('url'):
                if item['url'] == stream:
                    res = item['title']
        return res

    def build_settings(self, settings):
        settings.add_json_panel("Settings", self.config, data="""
    [
    {"type": "string",
    "title": "Cover server",
    "section": "Cover",
    "key": "baseurl"
    },
    {"type": "string",
    "title": "Cover cache directory ",
    "section": "Cover",
    "key": "cache_dir"
    },
    {"type": "string",
    "title": "MPD Host",
    "section": "mpd",
    "key": "host"
    },
    {"type": "numeric",
    "title": "MPD Port",
    "section": "mpd",
    "key": "port"
    },
    {"type": "string",
    "title": "Sound driver:         set to 'alsa' to drive master volume or whatever to drive mpd's internal volume",
    "section": "sound",
    "key": "driver"
    }
    ]"""
                                )

    def build_config(self, config):
        # Set default configuration
        config.setdefaults('Cover', {'baseurl': 'http://covers.fr/'} )
        config.setdefaults('Cover', {'cache_dir': os.getenv("HOME") + '/.cache/thumbnails/large/'})
        config.setdefaults('mpd', {'port': '6600'})
        config.setdefaults('mpd', {'host': '127.0.0.1'})
        config.setdefaults('sound', {'driver': 'alsa'})

    def build(self):

        self.read_radio()
        # Get configuration
        self.cover_base_url = self.config.getdefault("Cover", "baseurl", "http://covers.fr/")
        self.cache_dir = self.config.getdefault("Cover", "cache_dir", os.getenv("HOME") + '/.cache/thumbnails/large/')
        self.mpd_port = self.config.getdefault("mpd", "port", "6600")
        self.mpd_host = self.config.getdefault("mpd", "host", "127.0.0.1")
        self.sound_driver = self.config.getdefault("sound", "driver", "alsa")

        self.connect_to_server()
        self.sm = ScreenManager()
        self.PlayerControlWidget = Player(name='Player')
        self.PlaylistControlWidget = Playlist(name='Playlist')
        self.LibraryControlWidget = Library(name='Library')
        self.ParamsControlWidget = Params(name='Params')
        self.sm.add_widget(self.PlayerControlWidget)
        self.sm.add_widget(self.PlaylistControlWidget)
        self.sm.add_widget(self.LibraryControlWidget)
        self.sm.add_widget(self.ParamsControlWidget )
        # Sets a convenient way to access the Screens ....
        self.Playlist_Screen =  self.sm.get_screen('Playlist')
        self.Player_Screen =  self.sm.get_screen('Player')
        self.Library_Screen = self.sm.get_screen('Library')
        self.PlayerControlWidget.ids.player_cover.source =  WA.root_dir +'/textures/audio-cd.png'
        Clock.schedule_interval(self.schedule_tick, self.Schedule_time)
        Clock.schedule_interval(self.schedule_tick_10, 10 * self.Schedule_time)
        coef = 0.71
        Window.size = (800 * coef, 480 * coef)
        #self._keyboard = Window.request_keyboard(self._keyboard_closed, self.sm, 'text')
        #self._keyboard.bind(on_key_down=self._on_keyboard_down)
        return self.sm

    def schedule_tick_10(self,dt):
        try:
            self.protocol.currentsong().addCallback(self.PlayerControlWidget.CallBack_Current_Song)
        except:
            pass

    def schedule_tick(self,dt):
        try:
            self.protocol.status().addCallback(self.PlayerControlWidget.Callback_Status)
        except:
            print('pas de connection !')
            if  self.connection_status == False:
                try:
                    self.mdc
                except:
                    self.mdc = Modal_No_Connection()
                    self.mdc.open()

    def connect_to_server(self):

        self.factory = MPDFactory()
        self.factory.connectionMade = self.connectionMade
        self.factory.connectionLost = self.connectionLost
        reactor.connectTCP(self.mpd_host,int(self.mpd_port), self.factory)

    def connectionMade(self, protocol):
        self.connection_status = True
        try:
            self.mdc
            self.mdc.dismiss()
        except:
            pass

        self.protocol = protocol
        print 'Connection made'
        self.protocol.playlistinfo().addCallback(self.PlayerControlWidget.CallBack_playlist)
        self.protocol.currentsong().addCallback(self.PlayerControlWidget.CallBack_Current_Song)
        self.protocol.status().addCallback(self.PlayerControlWidget.Callback_Status)
        self.LibraryControlWidget.Set_Sources()
        #self.protocol.list('genre').addCallback(self.LibraryControlWidget.Callback_Set_Widget)

    def connectionLost(self, protocol, reason):
        self.connection_status = False
        print 'Connection lost: %s' % reason
        print  self.connection_status

        try:
            self.mdc
        except:
            self.mdc = Modal_No_Connection()
            self.mdc.open()


if __name__ == '__main__':
    WA = MpdtouchApp()
    WA.run()



