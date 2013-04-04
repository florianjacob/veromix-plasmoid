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

from gi.repository import Gtk, GObject

from Channel import SinkChannel
from Channel import SinkInputChannel
from Channel import SourceChannel
from Channel import SourceOutputChannel
from Channel import LadspaChannel
from Channel import MediaPlayerChannel

class SortedChannelBox(Gtk.VBox):
    CHANNEL_PADDING = 2
    __gsignals__ = {
        'veromix-resize': (GObject.SIGNAL_RUN_FIRST, None, (),),
    }

    def __init__(self):
        Gtk.VBox.__init__(self)
        self.set_border_width(4)
        self.channels = {}

    def on_sink_remove(self, data, index):
        if int(index) in self.channels.keys():
            self.remove(self.channels[index])
            del self.channels[index]
        self.order_items()
        self.check_resize()

    def on_sink_info(self, widget, data):
        channel = None
        if data.get_index() not in self.channels.keys():
            if "device.ladspa.module" in data.properties().keys():
                channel = LadspaChannel()
            else:
                channel = SinkChannel()
        self._add_channel_widget(channel,data)

    def on_sink_input_info(self, widget, data):
        channel = None
        if data.get_index() not in self.channels.keys():
            channel = SinkInputChannel()
        self._add_channel_widget(channel, data)

    def on_source_info(self, widget, data):
        channel = None
        if data.get_index() not in self.channels.keys():
            channel = SourceChannel()
        self._add_channel_widget(channel,data)

    def on_source_output_info(self, widget, data):
        channel = None
        if data.get_index() not in self.channels.keys():
            channel = SourceOutputChannel()
        self._add_channel_widget(channel,data)

    def on_module_info(self, widget, data):
        for widget in self.channels.values():
            if widget.pa_sink_proxy():
                module = widget.pa_sink_proxy().get_owner_module()
                if module:
                    if module == str(data.get_index()):
                        widget.on_pa_module_data_updated(data)
        self.emit('veromix-resize')

    def on_volume_meter_sink(self, widget, index, value):
        for sink in self.get_sinks():
            if sink.pa_sink_proxy().get_index() == index:
                sink.slider.on_volume_meter_data(value)

    def on_volume_meter_sink_input(self, widget, index, value):
        for sink in self.get_sink_inputs():
            if sink.pa_sink_proxy().get_index() == index:
                sink.slider.on_volume_meter_data(value)

    def on_volume_meter_source(self, widget, index, value):
        # FIXME
        for sink in self.channels.values():
            if sink.pa_sink_proxy().get_index() == index:
                sink.slider.on_volume_meter_data(value)

    def on_media_player_added(self, widget, string, obj):
        channel = MediaPlayerChannel(string,obj)
        self._add_channel_widget(channel,obj)

    def on_media_player_removed(self, widget, string, obj):
        if string in self.channels.keys():
            self.remove(self.channels[string])
            del self.channels[string]
        self.order_items()
        self.check_resize()

    def _add_channel_widget(self, channel, data):
        if data.get_index() not in self.channels.keys():
            self.channels[data.get_index()] = channel
            self.pack_start(channel, True, True, self.CHANNEL_PADDING)
            self.show_all()
        self.channels[data.get_index()].on_pa_data_updated(data)
        self.order_items()

##
    def order_items(self):
        while(self.needs_ordering()):
            self._order_items()
        self.emit('veromix-resize')

    def needs_ordering(self):
        sorting = self._sort()
        if len(sorting) != len(self.get_children()):
            return False
        for i in range(0,len(sorting)):
            if self.get_children()[i] != sorting[i]:
                return True
        return False

    def get_sources(self):
        return list(filter(lambda channel: channel.pa_sink_proxy().is_source(), self.channels.values()))

    def get_sinks(self):
        return list(filter(lambda channel: channel.pa_sink_proxy().is_sink(), self.channels.values()))

    def get_default_sink(self):
        if len(self.channels.values()) == 0:
            return None
        collection = list(filter(lambda channel: channel.pa_sink_proxy().is_default(), self.channels.values()))
        if len(collection) == 0:
            return list(self.channels.values())[0]
        return collection[0]

    def get_sink_inputs(self):
        return list(filter(lambda channel: channel.pa_sink_proxy().is_sinkinput(), self.channels.values()))

    def get_media_players(self):
        return list(filter(lambda channel: channel.pa_sink_proxy().is_media_player(), self.channels.values()))

    def _order_items(self):
        sorting = self._sort()

        for i in range(0,len(sorting)):

            if self.get_children()[i]  != sorting[i]:
                self.reorder_child(self.get_children()[i], sorting.index(self.get_children()[i]))
                return


    def _sort(self):
        sources = []       #self._sort_by_attribute(self._get_source_widgets(objects), '_name')
        sourceoutputs = [] # self._sort_by_attribute(self._get_sinkoutput_widgets(objects), '_name')

        sinks = self._sort_by_attribute(self.get_sinks())
        sink_inputs = self._sort_by_attribute(self.get_sink_inputs())

        mediaplayers = self._sort_by_attribute(self.get_media_players()) # self._sort_by_attribute(self._get_mediaplayer_widgets(objects), '_name')
        sorting = []
        for s in sinks:
            if s.pa_sink_proxy().is_default_sink():
                sinks.remove(s)
                sinks.insert(0,s)
        for s in sourceoutputs:
            sorting.append(s)
            for so in sources:
                if int(s.index) == int(so.get_assotiated_source()):
                    sorting.append(so)

        #sinks.reverse()
        for s in sinks:
            sorting.append(s)
            for i in sink_inputs:
                if s.pa_sink_proxy().get_index() == i.pa_sink_proxy().get_output_index():
                    sorting.append(i)
                    # FIXME
                    for m in mediaplayers:
                        assoc = m.pa_sink_proxy().get_assotiated_sink_input(sink_inputs)
                        if assoc != None and int(i.pa_sink_proxy().get_index()) == assoc.pa_sink_proxy().get_index():
                            sorting.append(m)
        # FIXME
        #for i in set(objects).difference(set(sorting)):
            #sorting.append(i)
        return sorting

    def _sort_by_attribute(self, objects):
        return sorted(objects, key = lambda x: x.pa_sink_proxy()._nice_title)
