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

from gi.repository import Gtk, Gdk, GObject

from veromixcommon.MediaPlayer import *
from veromixcommon.PulseProxyObjects import AbstractSink

class Mpris2MediaPlayerGtk(GObject.GObject, Mpris2MediaPlayer, AbstractSink):

    __gsignals__ = {
        'data_updated': (GObject.SIGNAL_RUN_FIRST, None, (),),
    }

    def __init__(self, name, dbus_proxy):
        GObject.GObject.__init__(self)
        Mpris2MediaPlayer.__init__(self, name, dbus_proxy)
        self.init_connection()
        self._nice_title = name

    def signal_data_updated(self):
        self.emit("data_updated")

    def url_path_of(self, string):
        # FIXME
        return string[7:]

    def trigger_timer_callback(self, timeout, function):
        QTimer.singleShot(timeout, function)

    def create_pixmap(self, val):
        img = Gtk.Image()
        img.set_from_file(val)
        return img

    def is_media_player(self):
        return True

    def get_assotiated_sink_input(self, sink_inputs):
        name = str(self.get_application_name()).lower()
        for channel in sink_inputs:
            if str(name).lower().find(channel.pa_sink_proxy().get_nice_title()) >= 0:
                return channel
        for channel in sink_inputs:
            if str(channel.pa_sink_proxy().get_nice_title()).lower().find(name) >= 0:
                return channel
        return None

