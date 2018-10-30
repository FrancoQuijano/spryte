#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import os
import numpy

from PIL import Image

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
    def cairo_to_rgba(self, color, scale=255):
        return (int(color[0] * scale),
                int(color[1] * scale),
                int(color[2] * scale),
                int(color[3] * scale))

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

    @classmethod
    def save(self, window, directory=None):
        if directory is None:
            directory = os.path.expanduser("~")

        dialog = Gtk.FileChooserDialog("Please choose a file", window,
                                       Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        dialog.set_do_overwrite_confirmation(True)

        response = dialog.run()
        file = None

        if response == Gtk.ResponseType.OK:
            file = dialog.get_filename()

        dialog.destroy()
        return file


class FileManagement:

    @classmethod
    def _save_as_svg(self, canvas, file):
        print("FileManagement.save_as_svg")

    @classmethod
    def _save_as_png(self, canvas, file):
        width, height = canvas.get_sprite_size()
        pixelmap = canvas.get_pixelmap()

        pixels = []

        for y in range(0, height):
            pixels.append([])

        for x in range(0, width):
            for y in range(0, height):
                color = Color.cairo_to_rgba(pixelmap.get_pixel_color(x + 1, y + 1))
                pixels[y].append(color)

        array = numpy.array(pixels, dtype=numpy.uint8)
        img = Image.fromarray(array)
        img.save(file)

    @classmethod
    def save(self, canvas, file):
        if file.endswith(".svg"):
            FileManagement._save_as_svg(canvas, file)

        else:
            FileManagement._save_as_png(canvas, file)


def flood_fill(pixelmap, x, y, current_color, new_color):
    if current_color == new_color:
        return

    if x > 0 and pixelmap.get_pixel_color(x - 1, y) == current_color:
        pixelmap.set_pixel_color(x - 1, y, new_color)
        flood_fill(pixelmap, x - 1, y, current_color, new_color)

    if x < pixelmap.height and pixelmap.get_pixel_color(x + 1, y) == current_color:
        pixelmap.set_pixel_color(x + 1, y, new_color)
        flood_fill(pixelmap, x + 1, y, current_color, new_color)

    if y > 0 and pixelmap.get_pixel_color(x, y - 1) == current_color:
            pixelmap.set_pixel_color(x, y - 1, new_color)
            flood_fill(pixelmap, x, y - 1, current_color, new_color)

    if y < pixelmap.height and  pixelmap.get_pixel_color(x, y + 1) == current_color:
            pixelmap.set_pixel_color(x, y + 1, new_color)
            flood_fill(pixelmap, x, y + 1, current_color, new_color)
