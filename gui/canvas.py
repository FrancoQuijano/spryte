#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function

from .utils import Color, ToolType

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib


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


class Canvas(Gtk.DrawingArea):

    def __init__(self, pixel_size=5, zoom=100, sprite_width=48,
                 sprite_height=48):
        super(Canvas, self).__init__()

        self.editable = True
        self.pixel_size = pixel_size
        self.tool_size = 1
        self.zoom = zoom
        self.sprite_width = sprite_width
        self.sprite_height = sprite_height
        self.tool = ToolType.PEN
        self._pending_tool = None
        self.primary_color = (0, 0, 0, 1)
        self.secondary_color = (1, 1, 1, 0)
        self.pixelmap = PixelMap(sprite_width, sprite_height)

        self._pressed_buttons = []
        self._mouse_position = (-1, -1)

        # Información para pruebas:
        pixels = [
            (1, 1, (1, 0, 0, 1)),
            (2, 2, (0, 1, 0, 1)),
            (3, 3, (0, 0, 1, 1)),
            (4, 4, (0, 0, 0, 1)),
            (5, 5, (1, 0, 0, 1)),
            (6, 1, (0, 0, 0, 1)),
            (7, 2, (1, 0, 0, 1)),
            (8, 3, (0, 1, 0, 1)),
            (9, 4, (0, 0, 1, 1)),
            (10, 5, (0, 0, 0, 1)),

            (1, 2, (0, 1, 1, 1)),
            (2, 3, (1, 0, 1, 1)),
            (3, 4, (1, 1, 0, 1)),

            (1, 3, (0.5, 0.75, 1, 1)),
            (2, 4, (0.75, 0.5, 1, 1)),
            (1, 4, (0, 0.75, 0.5, 1))
        ]

        for x, y, color in pixels:
            self.pixelmap.set_pixel_color(x, y, color)

        self.resize()

        self.add_events(Gdk.EventMask.SCROLL_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.BUTTON_MOTION_MASK)

        self.connect("draw", self._draw_cb)
        self.connect("scroll-event", self._scroll_cb)
        self.connect("motion-notify-event", self._button_motion_cb)
        self.connect("button-press-event", self._button_press_cb)
        self.connect("button-release-event", self._button_release_cb)

    def resize(self):
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
            self.zoom += 10

        else:
            self.zoom -= 10

        self.resize()
        #self.redraw()

        # Me aseguro de que no se haga scroll ya que se está haciendo zoom
        return True

    def _button_motion_cb(self, canvas, event):
        self._mouse_position = (event.x, event.y)

        if Gdk.BUTTON_PRIMARY in self._pressed_buttons:
            self.paint_selected_pixels(color=Color.PRIMARY)

        elif Gdk.BUTTON_SECONDARY in self._pressed_buttons:
            self.paint_selected_pixels(color=Color.SECONDARY)

        self.redraw()

    def _button_press_cb(self, canvas, event):
        button = event.get_button()[1]

        if button not in self._pressed_buttons:
            self._pressed_buttons.append(button)

        if button == Gdk.BUTTON_PRIMARY:
            self.paint_selected_pixels(color=Color.PRIMARY)

        elif button == Gdk.BUTTON_SECONDARY:
            self.paint_selected_pixels(color=Color.SECONDARY)

    def _button_release_cb(self, canvas, event):
        button = event.get_button()[1]

        if button in self._pressed_buttons:
            self._pressed_buttons.remove(button)

        if self._pending_tool is not None and self._pressed_buttons == []:
            self.tool = self._pending_tool
            self.redraw()

    def _draw_cb(self, canvas, ctx):
        alloc = self.get_allocation()
        factor = self.zoom / 100
        w = h = self.pixel_size * factor
        margin = 1 if self.zoom >= 100 else 0

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
        # Por ahora la única herramienta es el pincel de tamaño 1
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

    def paint_pixel(self, x, y, color=Color.PRIMARY):
        cairo_color = (0, 0, 0, 1)

        if self.tool == ToolType.ERASER:
            cairo_color = (1, 1, 1, 0)

        elif color == Color.PRIMARY:
            cairo_color = self.primary_color

        elif color == Color.SECONDARY:
            cairo_color = self.secondary_color

        self.pixelmap.set_pixel_color(x, y, cairo_color)
        self.redraw()

    def paint_absolute_coords(self, x, y, color=Color.PRIMARY):
        x, y = self.get_relative_coords(x, y)
        self.paint_pixel(x, y, color)

    def paint_selected_pixels(self, color=Color.PRIMARY):
        for x, y in self.get_selected_pixels():
            self.paint_pixel(x, y, color)

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


class CanvasContainer(Gtk.Box):

    def __init__(self, pixel_size=25, zoom=100, sprite_width=48,
                 sprite_height=48):
        super(CanvasContainer, self).__init__()

        self.set_border_width(5)

        box1 = Gtk.Box()
        box1.set_orientation(Gtk.Orientation.VERTICAL)
        self.canvas = Canvas(pixel_size, zoom, sprite_width, sprite_height)
        box1.pack_start(self.canvas, True, False, 0)

        box2 = Gtk.Box()
        box2.set_orientation(Gtk.Orientation.HORIZONTAL)
        box2.pack_start(box1, True, False, 0)

        self.scroll = Gtk.ScrolledWindow()
        self.pack_start(self.scroll, True, True, 0)

        self.scroll.add(box2)

    def set_tool_size(self, size):
        self.canvas.set_tool_size(size)

    def set_tool(self, tool):
        self.canvas.set_tool(tool)

    def set_zoom(self, zoom):
        self.canvas.set_zoom(zoom)

    def set_primary_color(self, color):
        self.canvas.set_primary_color(color)

    def set_secondary_color(self, color):
        self.canvas.set_secondary_color(color)
