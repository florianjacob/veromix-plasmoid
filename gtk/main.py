#!/usr/bin/python3
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

##
# python3-gi python3-dbus
##
import os, gettext, dbus, dbus.service
from gi.repository import Gtk, Gdk
from gettext import gettext as i18n

from Veromix import Veromix
from Indicator import Indicator
from Configuration import config
from veromixcommon.Utils import createDbusServiceDescription
from veromixcommon.LADSPAEffects import LADSPAPresetLoader

DBUS_INTERFACE = "org.veromix.gtkfrontend"

VEROMIX_BASEDIR = os.path.abspath(os.path.join(os.path.realpath(__file__), os.path.pardir))
VEROMIX_BASEDIR = os.path.abspath(os.path.join(VEROMIX_BASEDIR, os.path.pardir))
VEROMIX_SERVICE = "/dbus-service/veromix-service-glib.py"

class VeromixWindow(dbus.service.Object):

    def __init__(self, bus):
        dbus.service.Object.__init__ (self, bus, "/", DBUS_INTERFACE)

        self.window = Gtk.Window(title=i18n("Veromix"),type =Gtk.WindowType.TOPLEVEL)
        self.window.set_icon_name("veromix")
        self.window.connect('delete-event', self.on_delete_event)
        self.window.set_default_size(430, 180)

        veromix = Veromix(self.window, bus)
        self.window.add(veromix)
        self.create_indicator(veromix)
        self.window.show_all()

    @dbus.service.method (DBUS_INTERFACE, in_signature='', out_signature='')
    def show_window(self):
        self.window.present()

    def on_delete_event(self, widget, event):
        if config().get_window_exit_on_close():
            Gtk.main_quit()
        self.window.hide()
        return True

    def create_indicator(self, veromix):
        self.tray_icon = Indicator(veromix)

def init_locales():
    name = "veromix"
    directory = VEROMIX_BASEDIR + "/data/locale"
    if "usr/share/veromix" in VEROMIX_BASEDIR:
        directory = "/usr/share/locale"
    gettext.bindtextdomain(name, directory)
    gettext.textdomain(name)

if __name__ == '__main__':
    # Veromix is dedicated to my girlfriend Véronique
    init_locales()
    Gdk.set_program_class("veromix")
    if not dbus.get_default_main_loop():
        mainloop=dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    else:
        mainloop=dbus.mainloop.glib.DBusGMainLoop(set_as_default=False)
    bus = dbus.SessionBus()
    request = bus.request_name (DBUS_INTERFACE, dbus.bus.NAME_FLAG_DO_NOT_QUEUE)
    if request == dbus.bus.REQUEST_NAME_REPLY_EXISTS:
        obj = bus.get_object (DBUS_INTERFACE, "/")
        app = dbus.Interface (obj, DBUS_INTERFACE)
        app.show_window()
        Gdk.notify_startup_complete()
    else:
        createDbusServiceDescription(VEROMIX_BASEDIR + VEROMIX_SERVICE, False)
        LADSPAPresetLoader().install_ladspa_presets_if_needed()
        win = VeromixWindow(bus)
        win.show_window()
        Gtk.main()
        config().save()
