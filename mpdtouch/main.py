#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, urllib, hashlib, time
from kivy.support import install_twisted_reactor
install_twisted_reactor()
from mpd import MPDFactory
from twisted.internet import reactor
from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.adapters.models import SelectableDataItem
from kivy.clock import Clock
from kivy.core.window import Window
from utils import TimeToHMS , format_to_str,url_exists
from kivy.factory import Factory

current_song = {}

class LibraryListWidget(BoxLayout):
    pass
Factory.register('LibraryListWidget', LibraryListWidget)

class CustomListItem(SelectableDataItem):
    def __init__(self):
        super(CustomListItem, self).__init__()
        print('create')


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
        # TODO : afficher la radio ....


    def on_add_press(self):
        WA.protocol.load(self.result)
        self.dismiss()


class WidgetListButton(BoxLayout):
    pass


class SongListButton(SelectableDataItem):
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
            sources = ['Genres', 'Albums','Artists','Playlists']
            self.llw.ids.library_list.adapter.data.extend([item for item in sources])
            self.source = None

    def Get_Source(self ,adapter):
        self.genre = None
        self.album = None
        self.artist = None

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



        else:
            pass

    def get_playlist(self ,adapter):
        if adapter.selection:
            #print adapter.selection[0].text
            self.mdp = Modal_Playlist_Add_Box(adapter.selection[0].text)
            self.mdp.open()



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
            cover = 'audio-cd.png'
            for file in result:
                if cover == 'audio-cd.png':
                    cover = WA.get_cover_path(file,True)
                    #print self.llw.ids.library_list.adapter.data[i] # ... Le nom de l' album ...
                    self.llw.ids.library_list.adapter.get_view(int(i)).itemimage.source = cover
                else:
                    break
        except:
            pass

    def Scroll_Playlist(self):
        #print 'scroll'
        self.llw.ids.library_list.container.parent.scroll_to(self.llw.ids.library_list.adapter.get_view(10), padding=10, animate=True)


class Playlist(Screen):
    playlist_list = ObjectProperty()

    def __init__(self, **kwargs):
        super(Playlist, self).__init__(**kwargs)

    def on_SongListButton_press(self,*args):
        self.Color_Playlist( args[0].song)
        WA.protocol.seekid(int(args[0].song['id']), 0)



    def Color_Playlist(self,current_song):
        try:
            for i in range(0, len(self.playlist_list.adapter.data)):
                 item = self.playlist_list.adapter.get_view(int(i)).ids.itembutton
                 item.background_color = [0.0, 0.0, 0.0, 1]
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

        self.player_artist.text = format_to_str('Artist')
        self.player_genre.text = format_to_str('Genre')
        self.player_title.text = format_to_str('Title')
        self.player_album.text = format_to_str('Album')
        self.player_cover.source = 'audio-cd.png'


    def on_play_press(self):
        if self.PLAY_STATE:
            WA.protocol.pause()
            WA.PlayerControlWidget.ids.play_btn_image.source = WA.root_dir +'/textures/pause.png'
            self.PLAY_STATE = False
        else:
            self.PLAY_STATE = True
            WA.PlayerControlWidget.ids.play_btn_image.source = WA.root_dir +'/textures/play.png'
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
        if result['state'] == 'play':
            self.PLAY_STATE = True
            if result.has_key('time'):
                if result['state'] == 'play':

                    self.player_slider.max =   int( result['time'].split(':',-1)[1])
                    self.player_slider.value =  round(float(result['elapsed']))
                    self.player_song_elapsed_time.text = TimeToHMS(round(float(result['elapsed'])))
                    self.player_song_total_time.text = TimeToHMS(int( result['time'].split(':',-1)[1]))
        if result.has_key('song'):
            if  self.songid  !=  result['song']:
                self.songid  = result['song']
                #print('song changed !')

                WA.protocol.currentsong().addCallback(self.CallBack_Current_Song)

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
        #if current_song.has_key('pos'):
           # WA.Playlist_Screen.ids.playlist_list.scroll_to(max(int(current_song['pos'])-2,0))
        if current_song.has_key('artist'):
            self.player_artist.text = format_to_str(current_song['artist'])
        if current_song.has_key('genre'):
            self.player_genre.text = format_to_str(current_song['genre'])
        if current_song.has_key('title'):
            self.player_title.text = format_to_str(current_song['title'])
        if current_song.has_key('album'):
            self.player_album.text = format_to_str(current_song['album'])
        if current_song.has_key('file'):
            #print(current_song['file'])
            try:
                self.player_cover.source = WA.get_cover_path(current_song['file'],False)
            except:
                pass

    def on_connection(self, connection):
        self.print_message("connected successfully!")
        self.connection = connection


class ScreenManager(ScreenManager):
    def goto_Playlist(self):
        WA.protocol.playlistinfo().addCallback(WA.PlayerControlWidget.CallBack_playlist)
        WA.protocol.currentsong().addCallback(WA.PlayerControlWidget.CallBack_Current_Song)
        self.current = 'Playlist'

    def goto_Player(self):
        self.current = 'Player'

    def goto_Library(self):
        self.current = 'Library'

    def goto_Params(self):
        self.current = 'Params'
        WA.protocol.stats().addCallback(WA.ParamsControlWidget.CallBack_Stats)


class MpdtouchApp(App):
    Schedule_time = 1
    protocol = None
    connection_status = False
    No_Connection = False

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
                    'text':
                        format_to_str(data_item['file'])

                    }


    def library_converter(self,index, data_item):
        #print data_item
        if isinstance(data_item, basestring):
            return {'is_selected': False, 'text': data_item, 'source': 'audio-cd.png'}
        if isinstance(data_item, dict) and data_item.has_key('playlist'):
            return {'is_selected': False, 'text': data_item['playlist'], 'source': 'audio-cd.png'}

    def get_cover_path(self,filepath,cache):
        try:
            dir_path = urllib.quote(os.path.dirname(filepath.encode('UTF-8')))
            url = WA.cover_base_url + dir_path + '/folder.jpg'
            m = hashlib.md5()
            m.update(url)
            cache_file = self.cache_dir + m.hexdigest()+'.jpg'
            if os.path.isfile(cache_file) and cache ==True :
                #print 'get cached file ...'
                return cache_file
            else:
                if url_exists(url):
                    urllib.urlretrieve(url, cache_file)
                    #print 'get from Web server ...'
                    return url
                else:
                    return 'audio-cd.png'
        except:
            return 'audio-cd.png'


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
    }
    ]"""
                                )

    def build_config(self, config):
        # Set default configuration
        config.setdefaults('Cover', {'baseurl': 'http://covers.fr/'} )
        config.setdefaults('Cover', {'cache_dir': os.getenv("HOME") + '/.cache/thumbnails/large/'})
        config.setdefaults('mpd', {'port': '6600'})
        config.setdefaults('mpd', {'host': '127.0.0.1'})

    def build(self):
        # Get configuration
        self.cover_base_url = self.config.getdefault("Cover", "baseurl", "http://covers.fr/")
        self.cache_dir = self.config.getdefault("Cover", "cache_dir", os.getenv("HOME") + '/.cache/thumbnails/large/')
        self.mpd_port = self.config.getdefault("mpd", "port", "6600")
        self.mpd_host = self.config.getdefault("mpd", "host", "127.0.0.1")

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
        self.PlayerControlWidget.ids.player_cover.source = 'audio-cd.png'
        Clock.schedule_interval(self.schedule_tick, self.Schedule_time)
        coef = 0.71
        Window.size = (800 * coef, 480 * coef)
        #self._keyboard = Window.request_keyboard(self._keyboard_closed, self.sm, 'text')
        #self._keyboard.bind(on_key_down=self._on_keyboard_down)
        return self.sm

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



