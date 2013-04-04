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

from gi.repository import Gtk, Gdk

from GPulseAudioProxy import PulseAudio
from ContextMenu import ContextMenu
from SortedChannelBox import SortedChannelBox
from Configuration import config

class Veromix(Gtk.VBox):

    def __init__(self, window, dbus):
        Gtk.VBox.__init__(self, window)
        self.window = window
        self.pa = PulseAudio(self, dbus)

        self.create_sinks()
        self.launch_pa()
        self.init_mpris2()

    def launch_pa(self):

        self.pa.connect_veromix_service()
        # FIXME: singleton initialization
        ContextMenu.get_instance(self)

        self.pa.connect("on_sink_info", self.sink_box.on_sink_info)
        self.pa.connect("on_sink_remove", self.sink_box.on_sink_remove)

        self.pa.connect("on_sink_input_info", self.sink_box.on_sink_input_info)
        self.pa.connect("on_sink_input_remove", self.sink_box.on_sink_remove)

        self.pa.connect("on_source_info", self.source_box.on_source_info)
        self.pa.connect("on_source_remove", self.source_box.on_sink_remove)

        self.pa.connect("on_source_output_info", self.source_box.on_source_output_info)
        self.pa.connect("on_source_output_remove", self.source_box.on_sink_remove)

        self.pa.connect("on_module_info", self.sink_box.on_module_info)

        self.pa.connect("on_volume_meter_sink", self.sink_box.on_volume_meter_sink)
        self.pa.connect("on_volume_meter_sink_input", self.sink_box.on_volume_meter_sink_input)
        self.pa.connect("on_volume_meter_source", self.source_box.on_volume_meter_source)

        self.pa.connect("mpris2_player_added", self.sink_box.on_media_player_added)
        self.pa.connect("mpris2_player_removed", self.sink_box.on_media_player_removed)

        self.pa.requestInfo()

    def init_mpris2(self):
        if not config().get_media_player_enabled():
            return self
        self.pa.enable_mpris2()
        for controller in self.pa.get_mpris2_players():
            v = controller.get_name()
#            if self.in_mediaplayer_blacklist(v):
#                return
            self.sink_box.on_media_player_added(None, controller.get_name(), controller)

    def create_sinks(self):
        self.veromix_sinks = Gtk.VBox()

        self.source_box = SortedChannelBox()
        self.veromix_sinks.pack_start(self.source_box, False, True, 0)
        self.source_box.connect("veromix-resize", self._do_resize)

        self.sink_box = SortedChannelBox()
        self.veromix_sinks.pack_start(self.sink_box, False, True, 0)
        self.sink_box.connect("veromix-resize", self._do_resize)

        spacer = Gtk.HBox()
        self.veromix_sinks.pack_start(spacer,True,True,0)

        self.scroll = Gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        self.scroll.set_policy(1, 1)
        self.scroll.add_with_viewport(self.veromix_sinks)
        self.scroll.set_border_width(5)

#        self.expander = Gtk.Expander(label="Outputs")
#        self.expander.set_expanded(True)
#        self.expander.add(self.scroll)
#        self.pack_start(self.expander, True, True, 0)

        self.pack_start(self.scroll, True, True, 0)

    def get_default_sink(self):
        return self.sink_box.get_default_sink()

    def get_sink_widgets(self):
        return self.sink_box.get_sinks()

    def pa_proxy(self):
        return self.pa

    def query_application(self, app_info, default_icon=None):
        # FIXME
        return default_icon

    def _do_resize(self, event):
        previous_policy = self.scroll.get_policy()
        # Disable scrolling:
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
        # See what changed:
        desired = self.scroll.size_request()
        toplevel = self.scroll.get_toplevel()
        new_size = toplevel.size_request()
        # Reenable scrolling:
        self.scroll.set_policy(*previous_policy)
        default_size = self.window.get_default_size()
        self.window.resize(max(new_size.width, default_size[0]), max(new_size.height, default_size[1]))

