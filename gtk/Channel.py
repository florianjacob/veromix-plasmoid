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

import re
from gi.repository import Gtk, Gdk
from gi.repository.GdkPixbuf import Pixbuf

from SliderWidget import SliderWidget
from LadspaWidget import LadspaWidget
from ContextMenu import ContextMenu
from MuteButton import MuteButton
from veromixcommon.MediaPlayer import MediaPlayer


DRAG_ACTION = Gdk.DragAction.COPY
(TARGET_ENTRY_TEXT, TARGET_ENTRY_PIXBUF) = range(2)

class Channel(Gtk.Alignment):

    ICON_HEIGHT = 36

    def __init__(self):
        Gtk.Alignment.__init__(self)
        #self.set_homogeneous(False)
        self._init()
        self.set_size_request(self.ICON_HEIGHT, self.ICON_HEIGHT)

    def _init(self):
        self.frame = Gtk.Frame()
        self.hbox = Gtk.HBox()
        self._create()
        self._pack_contents()
        self._pack_frame()

    def _pack_contents(self):
        self.mute_box.pack_start(self.mute, False, True, 2)
        self.mute_box.pack_start(Gtk.HBox(), True, True, 0)
        self.menu_box.pack_start(self.menu_button, False, True, 2)
        self.menu_box.pack_start(Gtk.HBox(), True, True, 0)

        self.hbox.pack_start(self.mute_box, False, True, 2)
        self.hbox.pack_start(self.slider,True,True,5)
        self.hbox.pack_start(self.menu_box,False,False, 2)

    def _pack_frame(self):
        self.frame.add(self.hbox)
        self.add(self.frame)
        self.connect("button-press-event", self.on_button_press_event)

    def _create(self):
        self._create_mute()
        self._create_slider()
        self._create_menu_button()

    def _create_menu_button(self):
        self.menu_box=Gtk.VBox()
        self.menu_button = Gtk.ToggleButton()
        self.menu_button.set_relief(Gtk.ReliefStyle.NONE)
        self.menu_button.set_can_focus(False)
        self.menu_button.add(Gtk.Arrow(Gtk.ArrowType.DOWN, Gtk.ShadowType.NONE))
        self.menu_button.connect("released", self.show_popupmenu)
        self.menu_button.set_size_request(-1, self.ICON_HEIGHT)

    def on_menu_button_released(self, widget):
        self.menu_button.set_active(False)

    def _create_mute(self):
        self.mute_box = Gtk.VBox()
        self.mute = MuteButton()
        self.mute.connect_clicked(self.on_mute_clicked)

    def _create_slider(self):
        self.slider = SliderWidget()

    def show_popupmenu(self, widget, button=0, time=0):
        self.menu = Gtk.Menu()
        self.menu.connect("selection-done", self.on_menu_button_released)
        instance = ContextMenu.get_instance()
        instance.populate_menu(self.pa_sink_proxy(), self.menu, self.slider)
        self.menu.show_all()
        self.menu.popup(None, None, None, None, 0, 0)
        return False

    def on_button_press_event(self, widget, event):
        if (event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3):
            self.show_popupmenu(event.button, event.time)
            return True # event has been handled

    def on_mute_clicked(self, button, event):
        # catch drag and drop:
        if (Gdk.EventType.BUTTON_RELEASE and (event.x != 0.0 and event.y != 0.0)):
            self.pa_sink_proxy().toggle_mute()
            return True
        return False

    def pa_sink_proxy(self):
        return self._pa_sink

    def on_pa_data_updated(self, data):
        self._pa_sink = data

        self.slider.set_volume(data)
        self.mute.set_active(data.isMuted())
        self.mute.set_image_name(data.get_nice_icon())

    def step_volume(self, up):
        self.slider.step_volume(up)

    def toggle_mute(self):
        self.pa_sink_proxy().toggle_mute()

    def on_pa_module_data_updated(self, data):
        pass

class SinkChannel(Channel):

    def _init(self):
        Channel._init(self)
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], DRAG_ACTION)
        self.drag_dest_add_text_targets()
        self.connect("drag-data-received", self.on_drag_data_received)

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        if info == TARGET_ENTRY_TEXT:
            match =  re.match("veromix://sink_input_index:(\d*)", data.get_text())
            if match:
                self.pa_sink_proxy().move_sink_input(match.group(1))

class SinkInputChannel(Channel):

    def _init(self):
        Channel._init(self)
        self.set_padding(0, 0, self.ICON_HEIGHT / 2, 0)
        self.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [], DRAG_ACTION)
        self.drag_source_add_text_targets()
        self.connect("drag-data-get", self.on_drag_data_get)
        self.mute.connect_drag(self.on_drag_data_get)

    def on_drag_data_get(self, widget, drag_context, data, info, time):
        data.set_text("veromix://sink_input_index:"+str(self.pa_sink_proxy().get_index()), -1)

class SourceChannel(Channel):

    def _init(self):
        Channel._init(self)

class SourceOutputChannel(Channel):

    def _init(self):
        Channel._init(self)
        self.set_padding(0, 0, self.ICON_HEIGHT / 2, 0)

class LadspaChannel(SinkChannel):

    def _create_slider(self):
        self.slider = LadspaWidget()

    def on_pa_module_data_updated(self, data):
        self.slider.on_pa_module_data_updated(data, self.pa_sink_proxy())

class MediaPlayerChannel(Channel):

    def __init__(self,name, controller):
        Channel.__init__(self)
        self._pa_sink = controller
        self.controller = controller
        self.controller.connect("data_updated", self.controller_data_updated)
        self.controller_data_updated(None)
        self.set_padding(0, 0, self.ICON_HEIGHT / 2, 0)

    def controller_data_updated(self, widget):
        if self.controller.state() == MediaPlayer.Playing:
            self.play.set_from_icon_name("player_stop", Gtk.IconSize.BUTTON)
        else:
            self.play.set_from_icon_name("player_play", Gtk.IconSize.BUTTON)

        p = self.controller.artwork()
        if p:
            q = p.get_pixbuf().scale_simple(self.ICON_HEIGHT * 2, self.ICON_HEIGHT * 2, 0)
            self.cover.set_from_pixbuf(q)
        else:
            self.cover.set_from_icon_name(self.controller.get_application_name(), Gtk.IconSize.DND)

    def on_pa_data_updated(self, data):
        pass

    def _pack_contents(self):
        prev_box = Gtk.VBox()
        prev_box.pack_start(Gtk.HBox(), True,True, 0)
        prev_box.pack_start(self.prev, False,False, 0)

        next_box = Gtk.VBox()
        next_box.pack_start(Gtk.HBox(), True,True, 0)
        next_box.pack_start(self.next, False,False, 0)

        self.hbox.pack_start(Gtk.HBox(), True, True, 0)
        self.hbox.pack_start(prev_box, False,False, 0)
        self.hbox.pack_start(self.event_box, False,False, 0)
        self.hbox.pack_start(next_box, False,False, 0)
        self.hbox.pack_start(Gtk.HBox(), True, True, 0)

    def _create(self):
        self.cover = Gtk.Image()
        self.cover.set_size_request(self.ICON_HEIGHT * 2, self.ICON_HEIGHT * 2)

        self.play = Gtk.Image()
        self.play.set_size_request(self.ICON_HEIGHT, self.ICON_HEIGHT)
        self.play.set_from_icon_name("player_stop", Gtk.IconSize.BUTTON)

        self.prev = self._create_button("player_rew", self.on_prev_clicked)
        self.next = self._create_button("player_fwd", self.on_next_clicked)

        self.fixed = Gtk.Fixed()
        self.fixed.add(self.cover)
        self.fixed.put(self.play, int(self.ICON_HEIGHT/2), self.ICON_HEIGHT)

        self.event_box = Gtk.EventBox()
        self.event_box.add(self.fixed)
        self.event_box.show_all()
        self.event_box.connect("button_press_event", self.on_play_clicked)

    def _create_button(self, image_name, callback):
        button = Gtk.Button()
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_can_focus(False)
        img = Gtk.Image()
        img.set_from_icon_name(image_name, Gtk.IconSize.BUTTON)
        button.set_image(img)
        button.set_size_request(self.ICON_HEIGHT,self.ICON_HEIGHT)
        button.connect("clicked", callback)
        return button

    def on_play_clicked(self, widget, data):
        if self.controller.state() == MediaPlayer.Playing:
            self.controller.pause()
        else:
            self.controller.play()

    def on_prev_clicked(self, widget):
        self.controller.prev_track()

    def on_next_clicked(self, widget):
        self.controller.next_track()

