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

    BLACK = (0, 0, 0, 1)
    WHITE = (1, 1, 1, 1)
    TRANSPARENT = (0, 0, 0, 0)

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
    def cairo_to_rgb(self, color, scale=255):
        # Warning: se pierde la información de la transparencia
        color = self.cairo_to_rgba(color, scale)
        return (color[0], color[1], color[2])

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
    def _save_as_svg(self, pixelmap, file):
        pixel_size = 20  # FIXME: Hay que respetar el tamaño del layout

        indent = "  "
        output = '<svg width="%d" height="%d">\n' % (pixelmap.width * pixel_size, pixelmap.height * pixel_size)

        for pixel in pixelmap.pixels:
            color = Color.cairo_to_rgb(pixel.color)
            x = (pixel.x - 1) * pixel_size
            y = (pixel.y - 1) * pixel_size
            output += '%s<rect x="%d" y="%d" width="%d" height="%d" ' \
                      'style="fill:rgb(%d,%d,%d)" fill-opacity="%f" />\n' % (
                        indent, x, y, pixel_size, pixel_size,
                        *color, pixel.color[3])

        output += "</svg>"

        with open(file, "w") as pfile:
            pfile.write(output)

    @classmethod
    def _save_as_png(self, pixelmap, file):
        width, height = pixelmap.width, pixelmap.height
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
    def save(self, pixelmap, file):
        if file.endswith(".svg"):
            FileManagement._save_as_svg(pixelmap, file)

        else:
            FileManagement._save_as_png(pixelmap, file)


class PaintAlgorithms:

    @classmethod
    def flood_fill(self, pixelmap, x, y, current_color, new_color):
        if current_color == new_color:
            return

        if x > 1 and pixelmap.get_pixel_color(x - 1, y) == current_color:
            pixelmap.set_pixel_color(x - 1, y, new_color)
            self.flood_fill(pixelmap, x - 1, y, current_color, new_color)

        if x < pixelmap.width and pixelmap.get_pixel_color(x + 1, y) == current_color:
            pixelmap.set_pixel_color(x + 1, y, new_color)
            self.flood_fill(pixelmap, x + 1, y, current_color, new_color)

        if y > 1 and pixelmap.get_pixel_color(x, y - 1) == current_color:
            pixelmap.set_pixel_color(x, y - 1, new_color)
            self.flood_fill(pixelmap, x, y - 1, current_color, new_color)

        if y < pixelmap.height and  pixelmap.get_pixel_color(x, y + 1) == current_color:
            pixelmap.set_pixel_color(x, y + 1, new_color)
            self.flood_fill(pixelmap, x, y + 1, current_color, new_color)

    @classmethod
    def replace(self, pixelmap, current_color, new_color):
        if current_color == new_color:
            return

        for x in range(1, pixelmap.width + 1):
            for y in range(1, pixelmap.height + 1):
                if pixelmap.get_pixel_color(x, y) == current_color:
                    pixelmap.set_pixel_color(x, y, new_color)
