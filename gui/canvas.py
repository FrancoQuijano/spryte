#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function

from PIL import Image

from .utils import Color, ToolType, PaintAlgorithms

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject


class Pixel(object):

    def __init__(self, x=0, y=0, color=(1, 1, 1, 1)):
        self.x = x
        self.y = y
        self.color = color


class PixelMap(object):

    def __init__(self, width=48, height=48):
        self.width = width
        self.height = height

        self.__index = 0
        self.__reset = False
        self.pixels = []

    def __iter__(self):
        return self

    def __contains__(self, obj):
        for pixel in self.pixels:
            if pixel.x == obj[0] and pixel.y == obj[1]:
                return True

        return False

    def get_pixel_at(self, x, y):
        for pixel in self.pixels:
            if pixel.x == x and pixel.y == y:
                return pixel

        return None

    def get_pixel_color(self, x, y):
        pixel = self.get_pixel_at(x, y)
        if pixel is not None:
            return pixel.color

        else:
            return (1, 1, 1, 0)

    def set_pixel_color(self, x, y, color):
        pixel = self.get_pixel_at(x, y)
        if pixel is None and color[Color.ALPHA] != 0:
            pixel = Pixel(x, y, color)
            self.pixels.append(pixel)

        elif color[Color.ALPHA] != 0:
            pixel.color = color

        elif color[Color.ALPHA] == 0:
            self.delete_pixel_at(x, y)

    def delete_pixel_at(self, x, y):
        i = 0
        for pixel in self.pixels:
            if pixel.x == x and pixel.y == y:
                del self.pixels[i]

            i += 1

    def load_data_from_image(self, image):
        self.pixels = []

        pixel_access = image.load()

        for x in range(0, image.size[0]):
            for y in range(0, image.size[1]):
                r, g, b, a = pixel_access[x, y]

                if a == 0:
                    continue

                color = Color.rgba_to_cairo((r, g, b, a))
                self.pixels.append(Pixel(x + 1, y + 1, color))


class Canvas(Gtk.DrawingArea):

    __gsignals__ = {
        "primary-color-picked": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT]),
        "secondary-color-picked": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT]),
        "changed": (GObject.SIGNAL_RUN_LAST, None, []),
        "size-changed": (GObject.SIGNAL_RUN_LAST, None, []),
    }

    def __init__(self, pixel_size=5, zoom=100, sprite_width=48,
                 sprite_height=48, editable=True):
        super(Canvas, self).__init__()

        self.editable = True
        self.resizable = True

        self.pixel_size = pixel_size
        self.tool_size = 1
        self.zoom = zoom
        self.sprite_width = sprite_width
        self.sprite_height = sprite_height
        self.editable = editable
        self.tool = ToolType.PEN
        self.primary_color = (0, 0, 0, 1)
        self.secondary_color = (1, 1, 1, 0)
        self.pixelmap = PixelMap(sprite_width, sprite_height)
        self.file = None
        self.modified = False

        self._pending_tool = None
        self._pressed_buttons = []
        self._mouse_position = (-1, -1)

        self.set_vexpand(False)
        self.set_hexpand(False)
        self.resize()

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK)

        if self.editable:
            self.add_events(Gdk.EventMask.SCROLL_MASK |
                            Gdk.EventMask.POINTER_MOTION_MASK |
                            Gdk.EventMask.BUTTON_MOTION_MASK)

            self.connect("scroll-event", self._scroll_cb)
            self.connect("motion-notify-event", self._button_motion_cb)
            self.connect("button-press-event", self._button_press_cb)
            self.connect("button-release-event", self._button_release_cb)

        self.connect("draw", self._draw_cb)

    def resize(self):
        if not self.resizable:
            alloc = self.get_allocation()
            m = min(alloc.width, alloc.height)
            self.zoom = 100 * min(alloc.width / self.sprite_width, alloc.height / self.sprite_height)
            return

        factor = self.zoom / 100
        width = self.pixel_size * self.sprite_width * factor
        height = self.pixel_size * self.sprite_height * factor
        self.set_size_request(width, height)

        # No es necesario llamar self.redraw() a menos que
        # no se cambie el tamaño

    def _scroll_cb(self, canvas, event):
        if event.state != Gdk.ModifierType.CONTROL_MASK:
            # Elimino el modificador para que piense que el usuario
            # hizo un scroll normal
            event.state = 0
            return False

        if event.direction == Gdk.ScrollDirection.UP:
            self.zoom = min(2000, self.zoom + 10)

        else:
            self.zoom = max(1, self.zoom - 10)

        self.resize()

        # Me aseguro de que no se haga scroll ya que se está haciendo zoom
        return True

    def _button_motion_cb(self, canvas, event):
        self._mouse_position = (event.x, event.y)

        if Gdk.BUTTON_PRIMARY in self._pressed_buttons:
            self.apply_tool_to_selected_pixels(color=Color.PRIMARY)

        elif Gdk.BUTTON_SECONDARY in self._pressed_buttons:
            self.apply_tool_to_selected_pixels(color=Color.SECONDARY)

        self.redraw()

    def _button_press_cb(self, canvas, event):
        button = event.get_button()[1]

        if button not in self._pressed_buttons:
            self._pressed_buttons.append(button)

        if button == Gdk.BUTTON_PRIMARY:
            self.apply_tool_to_selected_pixels(color=Color.PRIMARY)

        elif button == Gdk.BUTTON_SECONDARY:
            self.apply_tool_to_selected_pixels(color=Color.SECONDARY)

    def _button_release_cb(self, canvas, event):
        button = event.get_button()[1]

        if button in self._pressed_buttons:
            self._pressed_buttons.remove(button)

        if self._pending_tool is not None and self._pressed_buttons == []:
            self.tool = self._pending_tool
            self.redraw()

        self.emit("changed")

    def _draw_cb(self, canvas, ctx):
        alloc = self.get_allocation()
        factor = self.zoom / 100
        w = h = self.pixel_size * factor
        margin = 1 if self.zoom >= 100 and self.editable else 0

        self._draw_bg(ctx)

        for pixel in self.pixelmap.pixels:
            x, y = self.get_absolute_coords(pixel.x, pixel.y)

            ctx.set_source_rgba(*pixel.color)
            ctx.rectangle(x + margin, y + margin, w - 2 * margin, h - 2 * margin)
            ctx.fill()

        self._draw_selected_pixels(ctx)

    def _draw_bg(self, ctx):
        size = 13  # Esto es 100% arbitrario
        c1 = (0.4, 0.4, 0.4)
        c2 = (0.5, 0.5, 0.5)

        alloc = self.get_allocation()

        for i in range(0, alloc.width // size + 1):
            for j in range(0, alloc.height // size + 1):
                if (i + j) % 2 == 0:
                    ctx.set_source_rgb(*c1)

                else:
                    ctx.set_source_rgb(*c2)

                #print(i, j, c1 if (i + j) % 2 == 0 else c2)
                ctx.rectangle(i * size, j * size, size, size)
                ctx.fill()

    def _draw_selected_pixels(self, ctx):
        ctx.set_source_rgba(1, 1, 1, 0.2)

        for x, y in self.get_selected_pixels():
            x, y = self.get_absolute_coords(x, y)
            factor = self.zoom / 100
            w = h = self.pixel_size * factor
            margin = 1 if self.zoom >= 100 else 0
            ctx.rectangle(x + margin, y + margin, w - 2 * margin, h - 2 * margin)
            ctx.fill()

    def redraw(self):
        GLib.idle_add(self.queue_draw)

    def set_tool_size(self, size):
        self.tool_size = size
        self.redraw()

    def set_layout_size(self, size):
        width, height = size
        for x in range(width + 1, self.sprite_width + 1):
            for y in range(1, self.sprite_height + 1):
                self.pixelmap.delete_pixel_at(x, y)

        for x in range(1, width + 1):
            for y in range(height + 1, self.sprite_height + 1):
                self.pixelmap.delete_pixel_at(x, y)

        self.set_sprite_size(width, height)

    def set_tool(self, tool):
        if Gdk.BUTTON_PRIMARY in self._pressed_buttons or  \
            Gdk.BUTTON_SECONDARY in self._pressed_buttons:

            self._pending_tool = tool

        else:
            self.tool = tool
            self.redraw()

    def set_zoom(self, zoom):
        self.zoom = zoom
        self.resize()

    def get_relative_coords(self, x, y):
        factor = 1 / (self.pixel_size * self.zoom / 100)
        return int(x * factor) + 1, int(y * factor) + 1

    def get_absolute_coords(self, x, y):
        factor = self.pixel_size * self.zoom / 100
        return factor * (x - 1), factor * (y - 1)

    def apply_tool(self, x, y, color=Color.PRIMARY):
        cairo_color = (0, 0, 0, 1)
        paint_selected_pixel = True

        if ToolType.is_paint_tool(self.tool):
            if color == Color.PRIMARY:
                cairo_color = self.primary_color

            elif color == Color.SECONDARY:
                cairo_color = self.secondary_color

            if self.tool == ToolType.BUCKET:
                paint_selected_pixel = False
                current_pixel = self.get_selected_pixels()[0]
                current_color = self.pixelmap.get_pixel_color(*current_pixel)
                PaintAlgorithms.flood_fill(self.pixelmap, x, y, current_color, cairo_color)

                self.pixelmap.set_pixel_color(x, y, cairo_color)
                self.redraw()

            elif self.tool == ToolType.SPECIAL_BUCKET:
                paint_selected_pixel = False
                selected_color = self.pixelmap.get_pixel_color(x, y)
                PaintAlgorithms.replace(self.pixelmap, selected_color, cairo_color)

                self.redraw()

        elif self.tool == ToolType.ERASER:
            cairo_color = (1, 1, 1, 0)

        elif self.tool == ToolType.COLOR_PICKER:
            paint_selected_pixel = False
            cairo_color = self.pixelmap.get_pixel_color(x, y)

            if color == Color.PRIMARY:
                self.emit("primary-color-picked", cairo_color)

            elif color == Color.SECONDARY:
                self.emit("secondary-color-picked", cairo_color)

        if paint_selected_pixel:
            self.pixelmap.set_pixel_color(x, y, cairo_color)
            self.redraw()

    def apply_tool_to_absolute_coords(self, x, y, color=Color.PRIMARY):
        x, y = self.get_relative_coords(x, y)
        self.apply_tool(x, y, color)

    def apply_tool_to_selected_pixels(self, color=Color.PRIMARY):
        for x, y in self.get_selected_pixels():
            self.apply_tool(x, y, color)

    def set_primary_color(self, color):
        self.primary_color = color

    def set_secondary_color(self, color):
        self.secondary_color = color

    def get_selected_pixels(self):
        x, y = self.get_relative_coords(*self._mouse_position)
        pixels = [(x, y)]

        if not ToolType.is_resizable(self.tool):
            return pixels

        if self.tool_size >= 2:
            # La X es donde está el mouse
            # ---------
            # | X | 1 |
            # |---|---|
            # | 3 | 2 |
            # ---------
            pixels.extend([(x + 1, y),      # 1
                           (x + 1, y + 1),  # 2
                           (x, y + 1)])     # 3

        if self.tool_size >= 3:
            # La X es donde está el mouse
            # -------------
            # | 4 | 5 | 6 |
            # |---|---|---|
            # | 7 | X | 1 |
            # |---|---|---|
            # | 8 | 2 | 3 |
            # .............
            pixels.extend([(x - 1, y - 1),   # 4
                           (x, y - 1),       # 5
                           (x + 1, y - 1),   # 6
                           (x - 1, y),       # 7
                           (x - 1, y + 1)])  # 8

        if self.tool_size == 4:
            # La X es donde está el mouse
            # -----------------
            # | 4 | 5 | 6 | 9 |
            # |---|---|---|---|
            # | 7 | X | 1 | 10|
            # |---|---|---|---|
            # | 8 | 2 | 3 | 11|
            # |---|---|---|---|
            # | 12| 13| 14| 15|
            # -----------------
            pixels.extend([(x + 2, y - 1),   # 9
                           (x + 2, y),       # 10
                           (x + 2, y + 1),   # 11
                           (x - 1, y + 2),   # 12
                           (x, y + 2),       # 13
                           (x + 1, y + 2),   # 14
                           (x + 2, y + 2)])  # 15

        if self.tool == ToolType.VERTICAL_MIRROR_PEN:
            for x, y in pixels:
                mx = self.sprite_width - x + 1
                if (mx, y) not in pixels:
                    pixels.append((mx, y))

        return pixels

    def get_pixelmap(self):
        return self.pixelmap

    def set_pixelmap(self, pixelmap, refresh=True):
        self.pixelmap = pixelmap

        if refresh:
            self.redraw()

    def set_file(self, filename, refresh=True):
        self.file = filename

        if refresh:
            image = Image.open(filename)
            self.sprite_width, self.sprite_height = image.size
            self.pixelmap.load_data_from_image(image)
            self.resize()

            self.emit("size-changed")
            self.emit("changed")

    def set_sprite_size(self, width, height):
        self.sprite_width = width
        self.sprite_height = height
        self.pixelmap.width = width
        self.pixelmap.height = height
        self.resize()

    def get_sprite_size(self):
        return (self.sprite_width, self.sprite_height)

    def set_editable(self, editable):
        self.editable = editable

    def get_editable(self):
        return self.editable

    def set_resizable(self, resizable):
        self.resizable = resizable

    def get_resizable(self):
        return self.resizable

    def get_file(self):
        return self.file


class CanvasContainer(Gtk.Box):

    __gsignals__ = {
        "primary-color-picked": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT]),
        "secondary-color-picked": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT]),
        "changed": (GObject.SIGNAL_RUN_LAST, None, []),
        "size-changed": (GObject.SIGNAL_RUN_LAST, None, []),
    }

    def __init__(self, pixel_size=25, zoom=100, sprite_width=48,
                 sprite_height=48, editable=True):
        super(CanvasContainer, self).__init__()

        self.modified = False
        self.set_border_width(5)

        self.scroll = Gtk.ScrolledWindow()
        self.pack_start(self.scroll, True, True, 0)

        box1 = Gtk.Box()
        box1.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.scroll.add(box1)

        box2 = Gtk.Box()
        box2.set_orientation(Gtk.Orientation.VERTICAL)
        box1.pack_start(box2, True, False, 0)

        self.canvas = Canvas(pixel_size, zoom, sprite_width, sprite_height, editable)
        self.canvas.connect("changed", self._changed_cb)
        self.canvas.connect("size-changed", self._size_changed_cb)
        self.canvas.connect("primary-color-picked", self._primary_color_picked_cb)
        self.canvas.connect("secondary-color-picked", self._secondary_color_picked_cb)
        box2.pack_start(self.canvas, True, False, 0)

    def _changed_cb(self, canvas):
        self.emit("changed")

    def _size_changed_cb(self, canvas):
        self.emit("size-changed")

    def _primary_color_picked_cb(self, canvas, color):
        self.emit("primary-color-picked", color)

    def _secondary_color_picked_cb(self, canvas, color):
        self.emit("secondary-color-picked", color)

    def set_tool_size(self, size):
        self.canvas.set_tool_size(size)

    def set_layout_size(self, size):
        self.canvas.set_layout_size(size)

    def set_tool(self, tool):
        self.canvas.set_tool(tool)

    def set_zoom(self, zoom):
        self.canvas.set_zoom(zoom)

    def set_primary_color(self, color):
        self.canvas.set_primary_color(color)

    def set_secondary_color(self, color):
        self.canvas.set_secondary_color(color)

    def get_pixelmap(self):
        return self.canvas.get_pixelmap()

    def set_pixelmap(self, pixelmap, refresh=True):
        self.canvas.set_pixelmap(pixelmap, refresh=True)

    def set_file(self, filename, refresh=True):
        self.canvas.set_file(filename, refresh=refresh)

    def set_sprite_size(self, width, height):
        self.canvas.set_sprite_size(width, height)

    def get_sprite_size(self):
        return self.canvas.get_sprite_size()

    def set_editable(self, editable):
        self.canvas.set_editable(editable)

    def get_editable(self):
        return self.canvas.get_editable()

    def set_resizable(self, resizable):
        self.canvas.set_resizable(resizable)

    def get_resizable(self):
        return self.canvas.get_resizable()

    def get_file(self):
        return self.canvas.get_file()
