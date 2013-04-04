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
from gi.repository.GdkPixbuf import Pixbuf

class MuteButton(Gtk.Fixed):

    ICON_HEIGHT = 36

    def __init__(self):
        Gtk.Fixed.__init__(self)
        self._image_name = None
        self.image = Gtk.Image()
        self.muted_image = Gtk.Image()
        self.muted_image.set_from_icon_name("gtk-close", Gtk.IconSize.MENU)
        
        self.mute = Gtk.ToggleButton()
        self.mute.set_can_focus(False)
        self.mute.set_relief(Gtk.ReliefStyle.NONE)
        self.mute.set_image_position(1)

        self.mute.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.COPY)
        self.mute.drag_source_add_text_targets()

        self.set_size_request(self.ICON_HEIGHT,self.ICON_HEIGHT)
        self.mute.set_size_request(self.ICON_HEIGHT,self.ICON_HEIGHT)
        
        self.put(self.mute, 0, 0)
        
    def set_active(self, aboolean):
        if aboolean:
            pos = self.ICON_HEIGHT - Gtk.icon_size_lookup(Gtk.IconSize.MENU)[1]
            if self.muted_image not in self.get_children():
                self.put(self.muted_image, pos, pos)
            self.muted_image.show()
        else:
            if self.muted_image in self.get_children():
                self.muted_image.hide()
        self.mute.set_active(aboolean)

    def set_image_name(self, name):
        if self._image_name != name:
            self.image.set_from_icon_name(name, Gtk.IconSize.BUTTON)
            self.mute.set_image(self.image)

    def connect_clicked(self, function):
        # 'clicked' would have the right behaviour for drag and drop but 
        # it is also triggered when the state changes (via context-menu or external event)
        self.mute.connect("button-release-event", function)

    def connect_drag(self, function):
        self.mute.connect("drag-data-get", function)

