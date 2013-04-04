# -*- coding: utf-8 -*-
# Copyright (C) 2012 Nik Lutz <nik.lutz@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import signal
import dbus.mainloop.glib
#from PyQt4.QtCore import *
from gi.repository import GObject

from veromixcommon.PulseProxyObjects import *
from Mpris2MediaPlayerGtk import Mpris2MediaPlayerGtk

def SIGNAL(name):
    return name

class PulseAudio(GObject.GObject):

    __gsignals__ = {
        'on_sink_info': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'on_sink_remove': (GObject.SIGNAL_RUN_FIRST, None, (int,)),
        'on_sink_input_info': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'on_sink_input_remove': (GObject.SIGNAL_RUN_FIRST, None, (int,)),

        'on_source_info': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'on_source_remove': (GObject.SIGNAL_RUN_FIRST, None, (int,)),
        'on_source_output_info': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'on_source_output_remove': (GObject.SIGNAL_RUN_FIRST, None, (int,)),

        'on_card_info': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'on_card_remove': (GObject.SIGNAL_RUN_FIRST, None, (int,)),

        'on_module_info': (GObject.SIGNAL_RUN_FIRST, None, (object,)),

        'on_volume_meter_sink_input': (GObject.SIGNAL_RUN_FIRST, None, (int, float,)),
        'on_volume_meter_source': (GObject.SIGNAL_RUN_FIRST, None, (int, float,)),
        'on_volume_meter_sink': (GObject.SIGNAL_RUN_FIRST, None, (int, float,)),

        'mpris2_player_added': (GObject.SIGNAL_RUN_FIRST, None, (str, object,)),
        'mpris2_player_removed': (GObject.SIGNAL_RUN_FIRST, None, (str, object,)),
    }

    def __init__(self, parent, dbus=None):
        GObject.GObject.__init__(self)
        self.REQUIRED_SERVICE_VERSION = 15
        if dbus == None:
            if not dbus.get_default_main_loop():
                mainloop=dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            else:
                mainloop=dbus.mainloop.glib.DBusGMainLoop(set_as_default=False)
            self.bus = dbus.SessionBus()
        else:
            self.bus = dbus
        self.veromix = parent

    def connect_veromix_service(self):
        if  self.getMixer().veromix_service_version() != self.REQUIRED_SERVICE_VERSION:
            try:
                self.getMixer().veromix_service_quit()
                if  self.getMixer().veromix_service_version() != self.REQUIRED_SERVICE_VERSION:
                    raise NameError("Wrong server versions")
            except:
                raise NameError("Wrong server versions")

        self.bus.add_signal_receiver(self.on_sink_input_info,
                dbus_interface="org.veromix.notification",
                signal_name="sink_input_info")

        self.bus.add_signal_receiver(self.on_sink_info,
                dbus_interface="org.veromix.notification",
                signal_name="sink_info")

        self.bus.add_signal_receiver(self.on_source_output_info,
                dbus_interface="org.veromix.notification",
                signal_name="source_output_info")

        self.bus.add_signal_receiver(self.on_source_info,
                dbus_interface="org.veromix.notification",
                signal_name="source_info")

        self.bus.add_signal_receiver(self.on_sink_input_remove,
                dbus_interface="org.veromix.notification",
                signal_name="sink_input_remove")

        self.bus.add_signal_receiver(self.on_sink_remove,
                dbus_interface="org.veromix.notification",
                signal_name="sink_remove")

        self.bus.add_signal_receiver(self.on_source_remove,
                dbus_interface="org.veromix.notification",
                signal_name="source_remove")

        self.bus.add_signal_receiver(self.on_source_output_remove,
                dbus_interface="org.veromix.notification",
                signal_name="source_output_remove")

        self.bus.add_signal_receiver(self.on_volume_meter_sink_input,
                dbus_interface="org.veromix.notification",
                signal_name="volume_meter_sink_input")

        self.bus.add_signal_receiver(self.on_volume_meter_source,
                dbus_interface="org.veromix.notification",
                signal_name="volume_meter_source")

        self.bus.add_signal_receiver(self.on_volume_meter_sink,
                dbus_interface="org.veromix.notification",
                signal_name="volume_meter_sink")

        self.bus.add_signal_receiver(self.on_card_info,
                dbus_interface="org.veromix.notification",
                signal_name="card_info")

        self.bus.add_signal_receiver(self.on_card_remove,
                dbus_interface="org.veromix.notification",
                signal_name="card_remove")

        self.bus.add_signal_receiver(self.on_module_info,
                dbus_interface="org.veromix.notification",
                signal_name="module_info")

    def enable_mpris2(self):
        self.bus.add_signal_receiver(self.on_name_owner_changed,
                                    signal_name="NameOwnerChanged")

    def disable_mpris2(self):
        self.bus.remove_signal_receiver(self.on_name_owner_changed,
                                    signal_name="NameOwnerChanged")

    def on_name_owner_changed(self, val, val1=None, val2=None):
        if "org.mpris.MediaPlayer2" in val:
            if val in self.bus.list_names():
                self.emit("mpris2_player_added", str(val), Mpris2MediaPlayerGtk(str(val), self))
            else:
                self.emit("mpris2_player_removed", str(val), Mpris2MediaPlayerGtk(str(val), self))

    def connect_mpris2_player(self, callback, name):
        self.bus.add_signal_receiver(callback,
                dbus_interface="org.freedesktop.DBus.Properties",
                signal_name="PropertiesChanged",
                bus_name=name)

    def disconnect_mpris2_player(self, callback, name):
        self.bus.remove_signal_receiver(callback,
                dbus_interface="org.freedesktop.DBus.Properties",
                signal_name="PropertiesChanged",
                bus_name=name)

    def get_mpris2_players(self):
        collection = []
        for val in self.bus.list_names() :
            if "org.mpris.MediaPlayer2" in val:
                collection.append(Mpris2MediaPlayerGtk(str(val), self))
        return collection

    def getMixer(self):
        pa_obj  = self.bus.get_object("org.veromix.pulseaudio.glib","/org/veromix/pulseaudio")
        return dbus.Interface(pa_obj, 'org.veromix.pulseaudio')

    def get_mpris2_object(self, destination):
        return  self.bus.get_object(destination, '/org/mpris/MediaPlayer2')

    def getNowPlaying(self, destination):
        pa_obj = self.get_mpris2_object(destination)
        return dbus.Interface(pa_obj, 'org.mpris.MediaPlayer2.Player')

    def getNowPlayingProperty(self, destination, name):
        pa_obj = self.get_mpris2_object(destination)
        props = dbus.Interface(pa_obj, 'org.freedesktop.DBus.Properties')
        return props.Get('org.mpris.MediaPlayer2.Player', name)

    def on_sink_input_info(self, index, name, muted, volume, props):
        sink = SinkInputInfo(self, index, name, muted, volume, props)
        self.emit("on_sink_input_info", sink)

    def on_sink_info(self, index, name, muted, volume, props, ports, active_port):
        sink = SinkInfo(self, index, name, muted, volume, props, ports, active_port)
        self.emit("on_sink_info", sink)

    def on_source_output_info(self, index, name, props):
        sink = SourceOutputInfo(self, index, name, True, {"left":0, "right":0}, props)
        self.emit("on_source_output_info", sink)

    def on_source_info(self, index, name, muted, volume, props, ports, active_port):
        sink = SourceInfo(self, index, name, muted, volume, props, ports, active_port)
        self.emit("on_source_info", sink)

    def on_sink_input_remove(self, index):
        self.emit("on_sink_input_remove", index)

    def on_sink_remove(self, index):
        self.emit("on_sink_remove", index)

    def on_source_remove(self, index):
        self.emit("on_source_remove", index)

    def on_source_output_remove(self, index):
        self.emit("on_source_output_remove", index)

    def on_volume_meter_sink_input(self, index, value):
        self.emit("on_volume_meter_sink_input", index, value)

    def on_volume_meter_sink(self, index, value):
        self.emit("on_volume_meter_sink", index, value)

    def on_volume_meter_source(self, index, value):
        self.emit("on_volume_meter_source", index, value)

    def on_card_info(self, index, name, properties, active_profile_name, profiles_dict):
        info = CardInfo(index, name, properties, active_profile_name, profiles_dict)
        self.emit("on_card_info", info)

    def on_card_remove(self, index):
        self.emit("on_card_remove", index)
    # calls

    def set_card_profile(self, index, value):
        self.getMixer().set_card_profile(index, value)

    def set_sink_input_volume(self, index, vol):
        try:
            self.getMixer().sink_input_volume(index,vol)
        except(Exception, e):
            print ("dbus connection not ready: ")

    def set_sink_input_mute(self, index, mute):
        self.getMixer().sink_input_mute(index,mute)

    def sink_input_kill(self, index):
        self.getMixer().sink_input_kill(index)

    def set_sink_volume(self, index, vol):
        self.getMixer().sink_volume(index,vol)

    def set_sink_mute(self, index, mute):
        self.getMixer().sink_mute(index,mute)

    def set_sink_port(self, index, portstr):
        self.getMixer().sink_port(index,portstr)

    def set_default_sink(self, index):
        self.getMixer().set_default_sink(index)

    def create_combined_sink(self, first_sink_index, second_sink_index):
        self.getMixer().create_combined_sink(int(first_sink_index), int(second_sink_index))

    def set_source_volume(self, index, vol):
        self.getMixer().source_volume(index,vol)

    def set_source_mute(self, index, mute):
        self.getMixer().source_mute(index,mute)

    def set_source_port(self, index, portstr):
        self.getMixer().source_port(index,portstr)

    def set_default_source(self, index):
        self.getMixer().set_default_source(index)

    def move_sink_input(self, sink, output):
        self.getMixer().move_sink_input(sink, output)

    def move_source_output(self, sink, output):
        self.getMixer().move_source_output(sink, output)

    def toggle_monitor_of_sink(self, sink_index, named):
        self.getMixer().toggle_monitor_of_sink(sink_index, named)

    def toggle_monitor_of_sinkinput(self, sinkinput_index, sink_index, named):
        self.getMixer().toggle_monitor_of_sinkinput(sinkinput_index, sink_index, named)

    def toggle_monitor_of_source(self, source_index, named):
        self.getMixer().toggle_monitor_of_source(source_index, named)

    def set_ladspa_sink(self, sink_index, module_index, parameters):
        self.getMixer().set_ladspa_sink(sink_index, module_index, parameters)

    def remove_ladspa_sink(self, sink_index):
        self.getMixer().remove_ladspa_sink(sink_index)

    def remove_combined_sink(self, sink_index):
        self.getMixer().remove_combined_sink(sink_index)

    def on_module_info(self, index, name, argument, n_used, auto_unload):
        info = ModuleInfo(index, name, argument, n_used, auto_unload)
        self.emit("on_module_info",info)

    # FIXME

    def nowplaying_next(self, destination):
        self.getNowPlaying(str(destination)).Next()

    def nowplaying_prev(self, destination):
        self.getNowPlaying(str(destination)).Previous()

    def nowplaying_pause(self, destination):
        self.getNowPlaying(str(destination)).Pause()

    def nowplaying_play(self, destination):
        self.getNowPlaying(str(destination)).Play()

    def mpris2_get_position(self, destination):
        return self.getNowPlayingProperty(str(destination), "Position")

    def mpris2_set_position(self, destination, position):
        self.getNowPlaying(str(destination)).Seek(long(position))

    def mpris2_get_metadata(self, destination):
        return self.getNowPlayingProperty(str(destination), "Metadata")

    def mpris2_get_playback_status(self, destination):
        return self.getNowPlayingProperty(str(destination), "PlaybackStatus")

    def requestInfo(self):
        try:
            self.getMixer().requestInfo()
        except(Exception, e):
            print ("dbus connection not ready: ", e)

    def set_autostart_meters(self, aboolean):
        self.getMixer().set_autostart_meters(aboolean)

