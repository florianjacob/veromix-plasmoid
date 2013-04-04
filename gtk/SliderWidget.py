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

import re, urllib.parse
from gi.repository import Gtk, Gdk
from veromixcommon.LADSPAEffects import *

DRAG_ACTION = Gdk.DragAction.COPY
(TARGET_ENTRY_TEXT, TARGET_ENTRY_PIXBUF) = range(2)

class AbstractLabelSlider:
    # FIXME
    SLIDER_HEIGHT = 36

    def __init__(self):
        self.MAX_VOLUME = 100
        self.STEP_SIZE = -5
        self.slider_hidden = False
        self._create_label()
        self._create_slider()
        self._signal_handler = None

    def connect_value_changed(self, target):
        self._signal_handler = self.slider.connect("change-value", target)

    def disconnect_value_changed(self):
        if self._signal_handler:
            self.slider.disconnect(self._signal_handler)

    def _create_slider(self):
        self.slider = Gtk.HScale()
        self.slider.set_can_focus(False)
        #self.slider.set_slider_size_fixed(True)
        self.slider.set_draw_value(False)
        self.slider.set_value_pos(1)
        self.slider.set_range(0, self.MAX_VOLUME)
        self.slider.set_value(0)
        self.slider.set_increments(0, self.STEP_SIZE)
        self.slider.set_restrict_to_fill_level(False)
        self.slider.set_size_request(-1, self.SLIDER_HEIGHT)

    def _create_label(self):
        self.label = Gtk.Label()
        self.layout = self.label.get_layout()
        self.label.set_markup("<b>Initialg</b>g")
        self.label.set_alignment(xalign=0, yalign=0)
        self.label.set_size_request(-1, self.SLIDER_HEIGHT)

    #def show_slider_value(self):
        #self.slider.set_draw_value(True)
        #self.slider.set_value_pos(1)

    def set_volume(self, volume):
        self.slider.set_value(volume)

    def set_range(self, amin, amax):
        self.slider.set_range(amin, amax)

    def get_volume(self):
        return self.slider.get_value()

    def set_markup(self, markup):
        self.label.set_markup(markup)

    def hide_slider(self):
        if not self.slider_hidden:
            self.slider.unmap()
            self.slider_hidden = True

    def set_meter(self, value):
        self.slider.set_fill_level(value)

    def set_show_fill_level(self, value):
        if self.slider.get_show_fill_level() != value:
            self.slider.set_show_fill_level(value)
            self.slider.set_fill_level(0)

class LabelSlider(Gtk.Fixed, AbstractLabelSlider):

    def __init__(self):
        Gtk.Fixed.__init__(self)
        AbstractLabelSlider.__init__(self)
        self.init_layout()
        self.connect('size-allocate', self.on_resize)

    def init_layout(self):
        self.put(self.label,0,3)
        self.put(self.slider, 0, 0)

    def on_resize(self, widget, event):
        if event:
            # set position of slider
            event.y = event.y + self.label.get_layout().get_pixel_size()[1] * 0.4
            self.slider.size_allocate(event)

class VerticalLabelSlider(Gtk.HBox, AbstractLabelSlider):

    def __init__(self):
        Gtk.HBox.__init__(self)
        AbstractLabelSlider.__init__(self)
        self.init_layout()

    def init_layout(self):
        align = Gtk.Alignment()
        align.set_padding(20, 5, 0, 0)
        align.add(self.label)
        self.pack_start(align, False, False, 0)
        self.pack_start(self.slider, False, False, 0)

    def _create_label(self):
        LabelSlider._create_label(self)
        self.label.set_angle(90)

    def _create_slider(self):
        self.slider = Gtk.VScale()
        self.slider.set_can_focus(False)
        self.slider.set_draw_value(False)
        self.slider.set_value_pos(1)
        self.slider.set_range(0, self.MAX_VOLUME)
        self.slider.set_value(0)
        self.slider.set_increments(0, -1 * self.STEP_SIZE)
        self.slider.set_inverted(True)

class SliderWidget(Gtk.VBox):

    def __init__(self):
        Gtk.VBox.__init__(self)
        self.set_border_width(0)
        self._pa_sink_proxy = None
        self.sliders = []
        self.label = None
        self.EXPAND_CHANNELS = False

    def add_sliders(self, sink):
        if self.EXPAND_CHANNELS:
            self.create_sliders(sink)
        else:
            self.create_slider(sink)
        self.show_all()

    def remove_sliders(self, sink):
        for slider in self.sliders:
            slider.disconnect_value_changed()
            self.remove(slider)
            del slider
        self.sliders = []

    def create_label(self, sink):
        self.label_box = Gtk.EventBox()
        self.label = Gtk.Label()
        self.label_box.add(self.label)
        self.label.set_alignment(xalign=0, yalign=1)

    def create_slider(self, sink):
        if self.label:
            self.remove(self.label_box)
            del self.label
            self.label = None

        slider = self._create_slider(sink.get_nice_title_and_name())
        slider.connect_value_changed(self.on_slider_value_changed)

    def create_sliders(self, sink):
        self.create_label(sink)
        self.pack_start(self.label_box, False, False, 0)
        for channel in sink.getChannels():
            slider = self._create_slider("<b>" + channel.get_name() + "</b>")
            slider.connect_value_changed(self.on_sliders_value_changed)

    def _create_slider(self, title):
        slider = LabelSlider()
        slider.set_markup(title)
        self.sliders.append(slider)
        self.pack_start(slider, False, False, 0)
        size = slider.label.get_layout().get_pixel_size()
        slider.set_size_request(-1, size[1] * 2)
        return slider

    def pa_sink_proxy(self):
        return self._pa_sink_proxy

    def on_volume_meter_data(self, value):
        if len(self.sliders) > 0:
            self.sliders[0].set_meter(value)

    def set_volume(self, pa_sink_proxy):
        self._pa_sink_proxy = pa_sink_proxy
        nr_channels =  len(pa_sink_proxy.getChannels())
        if self.EXPAND_CHANNELS and nr_channels > 1:
            self.set_slider_values(pa_sink_proxy)
            self.label.set_markup(pa_sink_proxy.get_nice_title_and_name())
            self.sliders[0].set_show_fill_level(pa_sink_proxy.has_monitor())
        else:
            if len(self.sliders) != 1:
                self.remove_sliders(pa_sink_proxy)
                self.add_sliders(pa_sink_proxy)
            if len(self.sliders) > 0:
                if nr_channels > 0:
                    self.sliders[0].set_volume(pa_sink_proxy.get_volume())
                    self.sliders[0].set_show_fill_level(pa_sink_proxy.has_monitor())
                if nr_channels == 0:
                    self.sliders[0].hide_slider()
                self.sliders[0].set_markup(pa_sink_proxy.get_nice_title_and_name())

    def set_slider_values(self, sink):
        channels = sink.getChannels()
        if len(channels) != len(self.sliders):
            self.remove_sliders(sink)
            self.add_sliders(sink)
        for i in range(0,len(channels)):
            self.sliders[i].set_markup(channels[i].get_name()) #sink.get_nice_title_and_name())
            self.sliders[i].set_volume(channels[i].get_volume())

    def is_expanded(self):
        return self.EXPAND_CHANNELS

    def expand(self, boolean):
        self.EXPAND_CHANNELS = boolean
        self.set_volume(self._pa_sink_proxy)

    def step_volume(self, up):
#        self.pa_sink_proxy().step_volume_by(self.STEP_SIZE, up)  ## FIXME
        self.pa_sink_proxy().step_volume_by(5, up)

    def on_slider_value_changed(self, slider, scrolltype, value):
        vol = self.pa_sink_proxy().volumeDiffFor(value)
        self.pa_sink_proxy().set_volume(vol)
        return True

    def on_sliders_value_changed(self, slider, scrolltype, value):
        vol = []
        for slider in self.sliders:
            vol.append(slider.get_volume())
        self.pa_sink_proxy().set_volume(vol)
        return False

    def on_pa_module_data_updated(self, data):
        pass

    def get_selected_preset(self):
        return None

    def get_selected_effect(self):
        return None

    def is_ladspa(self):
        return False

    def get_ladspa_master(self):
        return self.pa_sink_proxy().get_ladspa_master()

    def set_ladspa_effect(self, value, master):
        parameters = ""
        preset = None
        for p in LADSPAEffects().effects():
            if p["preset_name"] == value:
                parameters = "sink_name=" + urllib.parse.quote(p["name"])
                preset = p

        for p in LADSPAPresetLoader().presets():
            if p["preset_name"] == value:
                parameters = "sink_name=" + urllib.parse.quote(p["preset_name"])
                preset = p
        parameters =  parameters + " master=" + master + " "
        parameters =  parameters + " plugin=" + preset["plugin"]
        parameters =  parameters + " label=" + preset["label"]
        parameters =  parameters + " control=" + preset["control"]
        self.pa_sink_proxy().set_ladspa_sink(parameters)
