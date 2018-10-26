#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib


class Pixel(object):

    def __init__(self, x=0, y=0, color=(1, 1, 1)):
        self.x = x
        self.y = y
        self.color = color


class PixelMap(object):

    def __init__(self, width=48, height=48):
        self.width = width
        self.height = height

        self.__index = 0
        self.pixels = []

    def __iter__(self):
        return self

    def __next__(self):
        if self.__index >= len(self.pixels):
            self.__index = 0
            raise StopIteration

        self.__index += 1
        return self.pixels[self.__index - 1]

    def __contains__(self, obj):
        for pixel in self:
            if pixel.x == obj[0] and pixel.y == obj[1]:
                return True

        return False

    def get_pixel_at(self, x, y):
        for pixel in self:
            if pixel.x == x and pixel.y == y:
                return pixel

        return None

    def set_pixel_color(self, x, y, color):
        pixel = self.get_pixel_at(x, y)
        if pixel is None:
            pixel = Pixel(x, y, color)
            self.pixels.append(pixel)

        else:
            pixel.color = color


class Canvas(Gtk.DrawingArea):

    def __init__(self, pixel_size=5, zoom=100, sprite_width=48,
                 sprite_height=48):
        super(Canvas, self).__init__()

        self.editable = True
        self.pixel_size = pixel_size
        self.zoom = zoom
        self.sprite_width = sprite_width
        self.sprite_height = sprite_height

        self.pixelmap = PixelMap(sprite_width, sprite_height)
        self.pixelmap.set_pixel_color(1, 1, (1, 0, 0))
        self.pixelmap.set_pixel_color(2, 2, (0, 1, 0))
        self.pixelmap.set_pixel_color(3, 3, (0, 0, 1))
        self.pixelmap.set_pixel_color(4, 4, (0, 0, 0))
        self.pixelmap.set_pixel_color(5, 5, (1, 0, 0))
        self.pixelmap.set_pixel_color(6, 1, (0, 0, 0))
        self.pixelmap.set_pixel_color(7, 2, (1, 0, 0))
        self.pixelmap.set_pixel_color(8, 3, (0, 1, 0))
        self.pixelmap.set_pixel_color(9, 4, (0, 0, 1))
        self.pixelmap.set_pixel_color(10, 5, (0, 0, 0))

        self.resize()

        self.add_events(Gdk.EventMask.SCROLL_MASK)

        self.connect("draw", self._draw_cb)
        self.connect("scroll-event", self._scroll_cb)

    def resize(self):
        factor = self.zoom / 100
        width = (self.pixel_size * (self.sprite_width + 1)) * factor
        height = (self.pixel_size * (self.sprite_height + 1)) * factor
        self.set_size_request(width, height)

    def _scroll_cb(self, canvas, event):
        if event.state in [Gdk.ModifierType.SHIFT_MASK,
                           Gdk.ModifierType.CONTROL_MASK]:
            if event.state == Gdk.ModifierType.CONTROL_MASK:
                # Elimino el modificador para que piense que el usuario
                # hizo un scroll normal
                event.state = 0

            return False

        if event.direction == Gdk.ScrollDirection.UP:
            self.zoom += 2

        else:
            self.zoom -= 2

        self.resize()
        #self.redraw()

        # Me aseguro de que no se haga scroll ya que se está haciendo zoom
        return True

    def _draw_cb(self, canvas, ctx):
        alloc = self.get_allocation()
        factor = self.zoom / 100

        self._draw_bg(ctx)

        for pixel in self.pixelmap:
            x = (alloc.width / self.sprite_width * (pixel.x - 1))
            y = (alloc.height / self.sprite_height * (pixel.y - 1))

            ctx.set_source_rgb(*pixel.color)
            ctx.rectangle(x, y, self.pixel_size * factor, self.pixel_size * factor)
            ctx.fill()

    def _draw_bg(self, ctx):
        size = 13
        c1 = (0.5, 0.5, 0.5)
        c2 = (0.8, 0.8, 0.8)

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

    def redraw(self):
        GLib.idle_add(self.queue_draw)


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
