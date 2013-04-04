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


import os, configparser

from veromixcommon.Utils import _XDG_CONFIG_DIR, createDirectory

__config_instance = None

def config():
    global __config_instance
    if __config_instance == None:
        __config_instance = VeromixConfiguration()
    return __config_instance

class VeromixConfiguration:
    _FILENAME = _XDG_CONFIG_DIR + "/veromix.conf"

    def __init__(self):
        self.section = 'UI'
        self._load()

    def _load(self):
        self._config = configparser.ConfigParser()
        self._config[self.section] = {}
        if os.path.exists(self._FILENAME):
            self._config.read(self._FILENAME)
        if len(self._config.sections()) == 0:
            self._config[self.section] = {}

    def save(self):
        createDirectory(_XDG_CONFIG_DIR)
        with open(self._FILENAME, 'w') as configfile:
            self._config.write(configfile)

    def _get(self, key, default):
        if key not in self._config[self.section]:
            self._config[self.section][key] = str(default)
        if type(default) == bool:
            return self._config[self.section].getboolean(key)
        if type(default) == int:
            return self._config[self.section].getint(key)
        return self._config[self.section][key]

    def get_window_exit_on_close(self):
        return self._get('exit_on_close', True)

    def get_indicator_type(self):
        self._config[self.section]['#indicator_type'] = 'None|GtkStatusIcon|AppIndicator'
        return self._get('indicator_type', 'AppIndicator')

    def get_media_player_enabled(self):
        return self._get('media_player_enable', True)
