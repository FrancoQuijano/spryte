#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gi.repository import Gtk
from gi.repository import GObject


class DiscreteScale(Gtk.Scale):
    """
    https://stackoverflow.com/a/39036673
    """

    def __init__(self, values, *args, **kwargs):
        super().__init__(*args, **kwargs)

        values.sort()
        self.values = values
        self.__last_value = self.values[1]

        adjustment = self.get_adjustment()
        adjustment.set_lower(values[0])
        adjustment.set_upper(values[-1])
        adjustment.set_value(self.__last_value)

        self.__changed_value_id = self.connect("change-value", self.__change_value)

    def __change_value(self, scale, scroll_type, value):
        value = self.__closest_value(value)
        if value == self.__last_value:
            return True

        self.handler_block(self.__changed_value_id)
        self.emit("change-value", scroll_type, value)
        self.handler_unblock(self.__changed_value_id)

        self.__last_value = value

        return True

    def __closest_value(self, value):
        return min(self.values, key=lambda v:abs(value-v))


class Statusbar(Gtk.Box):

    __gsignals__ = {
        "zoom-changed": (GObject.SIGNAL_RUN_LAST, None, [int]),
    }

    def __init__(self):
        super().__init__()

        marks = [50, 100, 200, 500, 1000, 1500, 2000]
        self.zoombar = DiscreteScale(marks)
        self.zoombar.set_draw_value(False)
        self.zoombar.set_size_request(150, 0)
        self.zoombar.connect("value-changed", self._zoom_changed_cb)
        self.pack_end(self.zoombar, False, False, 0)

    def _zoom_changed_cb(self, scale):
        self.emit("zoom-changed", int(self.zoombar.get_value()))
