#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import os
import numpy

from PIL import Image
from PIL import ImageSequence

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
    def pixelmap_to_svg(self, pixelmap):
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
        return output

    @classmethod
    def _save_as_svg(self, pixelmap, file):
        output = FileManagement.pixelmap_to_svg(pixelmap)
        with open(file, "w") as pfile:
            pfile.write(output)

    @classmethod
    def pixelmap_to_png(self, pixelmap):
        width, height = pixelmap.width, pixelmap.height
        pixels = []

        for y in range(0, height):
            pixels.append([])

        for x in range(0, width):
            for y in range(0, height):
                color = Color.cairo_to_rgba(pixelmap.get_pixel_color(x + 1, y + 1))
                pixels[y].append(color)

        array = numpy.array(pixels, dtype=numpy.uint8)
        return Image.fromarray(array)

    @classmethod
    def _save_as_png(self, pixelmap, file):
        image = FileManagement.pixelmap_to_png(pixelmap)
        image.save(file)

    @classmethod
    def pixelmaps_to_pngs(self, pixelmaps):
        return [FileManagement.pixelmap_to_png(pixelmap) for pixelmap in pixelmaps]

    @classmethod
    def _save_as_gif(self, pixelmaps, file):
        frames = FileManagement.pixelmaps_to_pngs(pixelmaps)
        primera = frames[0]
        del frames[0]

        loop = 0  # TODO
        duration = 250  # TODO

        primera.save(file, save_all=True, append_images=frames,
                     duration=duration, loop=loop,
                     transparency=0)

    @classmethod
    def save(self, pixelmaps, file):
        # TODO: Agregar la opción de guardar (en los formatos individuales:
        # png, svg, etc..) en una sola imagen, un frame al lado del otro

        if file.endswith(".svg"):
            i = 1
            file = file[:-len(".svg")]
            for pixelmap in pixelmaps:
                _file = file + " %d.svg" % i
                FileManagement._save_as_svg(pixelmap, _file)

                i += 1

        elif file.endswith(".png"):
            i = 1
            file = file[:-len(".svg")]
            for pixelmap in pixelmaps:
                _file = file + " %d.png" % i
                FileManagement._save_as_png(pixelmap, _file)

                i += 1

        elif file.endswith(".gif"):
            FileManagement._save_as_gif(pixelmaps, file)

        else:
            print("Actualmente el formato %s no está soportado, guardando como png..." % file.split(".")[-1])
            FileManagement.save(pixelmaps, file + ".png")


class PaintAlgorithms:

    @classmethod
    def flood_fill(self, pixelmap, x, y, current_color, new_color):
        if current_color == new_color:
            return

        if x > 1 and pixelmap.get_pixel_color(x - 1, y) == current_color and pixelmap.get_temp_pixel_color(x - 1, y) == Color.TRANSPARENT:
            pixelmap.set_temp_pixel_color(x - 1, y, new_color)
            self.flood_fill(pixelmap, x - 1, y, current_color, new_color)

        if x < pixelmap.width and pixelmap.get_pixel_color(x + 1, y) == current_color and pixelmap.get_temp_pixel_color(x + 1, y) == Color.TRANSPARENT:
            pixelmap.set_temp_pixel_color(x + 1, y, new_color)
            self.flood_fill(pixelmap, x + 1, y, current_color, new_color)

        if y > 1 and pixelmap.get_pixel_color(x, y - 1) == current_color and pixelmap.get_temp_pixel_color(x, y - 1) == Color.TRANSPARENT:
            pixelmap.set_temp_pixel_color(x, y - 1, new_color)
            self.flood_fill(pixelmap, x, y - 1, current_color, new_color)

        if y < pixelmap.height and  pixelmap.get_pixel_color(x, y + 1) == current_color and pixelmap.get_temp_pixel_color(x, y + 1) == Color.TRANSPARENT:
            pixelmap.set_temp_pixel_color(x, y + 1, new_color)
            self.flood_fill(pixelmap, x, y + 1, current_color, new_color)

    @classmethod
    def replace(self, pixelmap, current_color, new_color):
        if current_color == new_color:
            return

        for pixel in pixelmap.pixels:
            if pixelmap.get_pixel_color(pixel.x, pixel.y) == current_color:
                pixelmap.set_temp_pixel_color(pixel.x, pixel.y, new_color)

    @classmethod
    def line(self, pixelmap, x0, y0, x1, y1, color):
        """
        Algorítmo basado en el pseudocódigo de:
        https://es.wikipedia.org/wiki/Algoritmo_de_Bresenham#Descripci%C3%B3n
        """

        if x0 != x1:
            delta_y = (y1 - y0)
            delta_x = (x1 - x0)

            if delta_y >= 0:
                inclinacion_y_i = 1

            else:
                delta_y = - delta_y
                inclinacion_y_i = -1

            if delta_x >= 0:
                inclinacion_x_i = 1

            else:
                delta_x = -delta_x
                inclinacion_x_i = -1

            if delta_x >= delta_y:
                avance_y_recto = 0
                avance_x_recto = inclinacion_x_i

            else:
                avance_x_recto = 0
                avance_y_recto = inclinacion_y_i

                k = delta_x
                delta_x = delta_y
                delta_y = k

            x = x0
            y = y0

            avR = (2 * delta_y)
            av = (avR - delta_x)
            avI = (av - delta_x)

            while x != x1:
                pixelmap.set_temp_pixel_color(x, y, color)

                if av >= 0:
                    x += inclinacion_x_i
                    y += inclinacion_y_i
                    av += avI

                else:
                    x += avance_x_recto
                    y += avance_y_recto
                    av += avR

            if y != y1:
                # En algunas situaciones no se pintan los píxeles en la
                # columna del pixel final
                for _y in range(min(y, y1), max(y, y1) + 1):
                    pixelmap.set_temp_pixel_color(x, _y, color)

            # El último pixel siempre se pinta
            pixelmap.set_temp_pixel_color(x1, y1, color)

        else:
            for y in range(min(y0, y1), max(y0, y1) + 1):
                pixelmap.set_temp_pixel_color(x0, y, color)

def gtk_version_newer_than(major=3, minor=0, micro=0):
    _major = Gtk.get_major_version()
    _minor = Gtk.get_minor_version()
    _micro = Gtk.get_micro_version()

    return (_major > major) or \
           (_major == major and _minor > minor) or \
           (_major == major and _minor == minor and _micro >= micro)

