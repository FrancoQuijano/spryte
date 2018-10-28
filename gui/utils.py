#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import os

from gi.repository import Gtk
from gi.repository import Gdk


class Color:

    PRIMARY = 1
    SECONDARY = 2

    RED = 0
    GREEN = 1
    BLUE = 2
    ALPHA = 3

    @classmethod
    def gdk_to_cairo(self, color, alpha=65535):
        return (color.red / 65535,
                color.green / 65535,
                color.blue / 65535,
                alpha / 65535)

    @classmethod
    def cairo_to_gdk(self, color):
        return Gdk.Color.from_floats(*(color[:3]))

    @classmethod
    def RGBA_from_values(self, color):
        rgba = Gdk.RGBA()
        rgba.red, rgba.blue, rgba.green, rgba.alpha = color

    @classmethod
    def rgba_to_cairo(self, color):
        return (
            color[0] / 255,
            color[1] / 255,
            color[2] / 255,
            color[3] / 255
        )


class ToolType:
    PEN = 0
    VERTICAL_MIRROR_PEN = 1
    BUCKET = 2
    SPECIAL_BUCKET = 3
    ERASER = 4
    RECTANGLE = 5
    STROKE = 6
    MOVE = 7
    CIRCLE = 8
    RECTANGLE_SELECTION = 9
    SHAPE_SELECTION = 10
    LIGHTEN = 11
    LASSO_SELECTION = 12
    COLOR_PICKER = 13
    DITHERING = 14

    @classmethod
    def is_resizable(self, tool):
        return tool not in [
            self.BUCKET,
            self.SPECIAL_BUCKET,
            self.RECTANGLE,
            self.MOVE,
            self.RECTANGLE_SELECTION,
            self.SHAPE_SELECTION,
            self.LASSO_SELECTION,
            self.COLOR_PICKER
        ]

    @classmethod
    def is_paint_tool(self, tool):
        return tool in [
            self.PEN,
            self.VERTICAL_MIRROR_PEN,
            self.BUCKET,
            self.SPECIAL_BUCKET,
            self.RECTANGLE,
            self.STROKE,
            self.CIRCLE,
            self.LIGHTEN,
            self.DITHERING
        ]


class FileChooserManager:

    @classmethod
    def open(self, window, path=None):
        if path is None:
            path = os.path.expanduser("~")

        dialog = Gtk.FileChooserDialog("Please choose a file", window,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        dialog.set_select_multiple(True)
        # self.add_filters(dialog)

        response = dialog.run()
        files = []
        if response == Gtk.ResponseType.OK:
            files = dialog.get_filenames()

        dialog.destroy()
        return files
