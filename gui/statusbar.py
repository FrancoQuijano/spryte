#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gi.repository import Gtk


class Statusbar(Gtk.Box):

    def __init__(self):
        super().__init__()

        adjsutment = Gtk.Adjustment(100, 5, 2000, 5, 20, 1)
        self.zoombar = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjsutment)
        self.zoombar.set_draw_value(False)
        self.zoombar.set_size_request(150, 0)
        self.zoombar.set_show_fill_level(False)
        self.pack_end(self.zoombar, False, False, 0)

        marks = [50, 100, 200, 500, 1000, 2000]
        for mark in marks:
            self.zoombar.add_mark(mark, Gtk.PositionType.TOP, "{}%".format(mark))
