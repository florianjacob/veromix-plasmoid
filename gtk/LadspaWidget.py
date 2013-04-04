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

import datetime, urllib.parse
from gi.repository import Gtk, GObject

from SliderWidget import SliderWidget
from SliderWidget import VerticalLabelSlider
from veromixcommon.LADSPAEffects import *


class LadspaWidget(SliderWidget):

    def __init__(self):
        self.number_of_siders = 0
        self.ladspa_sink_update = datetime.datetime.now()
        self.ladspa_values = None
        self.ladspa_timer_running = False
        self.module_info = None
        self.timer = None
        SliderWidget.__init__(self)
        self.init_layout()

    def init_layout(self):
        self.slider_box = Gtk.HBox(0)
        self.create_label(None)
        self.pack_start(self.label_box, False, False, 3)
        self.pack_start(self.slider_box, False, False, 0)
        self.EXPAND_CHANNELS = True

    def on_pa_data_updated(self, data):
        pass

    def _create_slider(self, title):
        slider = VerticalLabelSlider()
        slider.set_markup(title)
        self.sliders.append(slider)
        self.slider_box.pack_start(slider, False, False, 0)
        return slider

    def create_sliders(self, sink):
        self.sliders = []
        for i in range(0, self.number_of_siders):
            slider = self._create_slider("")
            slider.connect_value_changed(self.on_sliders_value_changed)

    def on_sliders_value_changed(self, widget, value, data):
        values = []
        for i in range(0,self.number_of_siders):
            values.append(self.sliders[i].get_volume())
        self._schedule_set_ladspa_sink(values)

    def set_volume(self, pa_sink_proxy):
        self._pa_sink_proxy = pa_sink_proxy

    def on_pa_module_data_updated(self, data, pa_sink_proxy):
        self.module_proxy = data
        self.module_proxy.set_pa_sink_proxy(pa_sink_proxy)
        count = self.module_proxy.get_lasapa_number_of_controls()
        if count != self.number_of_siders:
            self.number_of_siders = count
            self.remove_sliders(pa_sink_proxy)
            self.create_sliders(pa_sink_proxy)

        if self.label:
            self.label.set_markup("<b>" + self.module_proxy.get_ladspa_nice_title() + "</b>")

        for i in range(0, self.number_of_siders):
            minmax = self.module_proxy.get_ladspa_scaled_range(i)
            self.sliders[i].set_range(minmax[0], minmax[1])
            self.sliders[i].set_markup("<b>" + self.module_proxy.get_ladspa_effect_label(i) + "</b>")
            self.sliders[i].set_volume(self.module_proxy.get_ladspa_control_value_scaled(i))
        self.show_all()

    def _schedule_set_ladspa_sink(self,values):
        if self.timer != None:
            GObject.source_remove(self.timer)
        self.ladspa_values = values
        self.timer = GObject.timeout_add(1000, self._set_ladspa_sink)

    def _set_ladspa_sink(self):
        self.timer = None
        self.module_proxy.set_ladspa_sink(self.ladspa_values, self.pa_sink_proxy())

    def save_preset(self, name):
        self.module_proxy.save_preset(name)
        self.on_sliders_value_changed(None, None, None)

    def get_selected_preset(self):
        return self.module_proxy.get_ladspa_preset_name()

    def get_selected_effect(self):
        return self.module_proxy.get_ladspa_effect_name()

    def is_ladspa(self):
        return True

    def get_ladspa_master(self):
        return self.module_proxy.get_ladspa_master()
        
