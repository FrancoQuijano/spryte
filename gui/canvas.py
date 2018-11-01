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
        # FIXME: Fijarse si x, y pertenecen a este pixelmap

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



class CanvasConfig:

    DEFAULT_LAYOUT_SIZE = (16, 16)
    DEFAULT_TOOL = ToolType.PEN
    DEFAULT_TOOL_SIZE = 1
    DEFAULT_PRIMARY_COLOR = Color.BLACK
    DEFAULT_SECONDARY_COLOR = Color.WHITE
    DEFAULT_ZOOM = 100
    DEFAULT_PIXEL_SIZE = 20
    DEFAULT_RESIZABLE = True
    DEFAULT_EDITABLE = True

    def __init__(self, layout_size=DEFAULT_LAYOUT_SIZE, tool=DEFAULT_TOOL,
                 tool_size=DEFAULT_TOOL_SIZE,
                 primary_color=DEFAULT_PRIMARY_COLOR,
                 secondary_color=DEFAULT_SECONDARY_COLOR,
                 zoom=DEFAULT_ZOOM, pixel_size=DEFAULT_PIXEL_SIZE,
                 resizable=DEFAULT_RESIZABLE, editable=DEFAULT_EDITABLE):

        self._layout_size = layout_size
        self._tool = tool
        self._tool_size = tool_size
        self._primary_color = primary_color
        self._secondary_color = secondary_color
        self._zoom = zoom
        self._pixel_size = pixel_size
        self._resizable = resizable
        self._editable = editable

        self._callbacks = {}

    def connect(self, property_name, callback):
        property_name = property_name.replace("-", "_")
        if not property_name in self._callbacks.keys():
            self._callbacks[property_name] = []

        self._callbacks[property_name].append(callback)

    def emit(self, property_name):
        property_name = property_name.replace("-", "_")
        if property_name not in self._callbacks.keys():
            return

        value = None
        if "_" + property_name in self.__dict__.keys():
            value = self.__dict__["_" + property_name]

        for callback in self._callbacks[property_name]:
            callback(value)

    @property
    def layout_size(self):
        return self._layout_size

    @layout_size.setter
    def layout_size(self, value):
        self._layout_size = value
        self.emit("layout-size")

    @property
    def tool(self):
        return self._tool

    @tool.setter
    def tool(self, value):
        self._tool = value
        self.emit("tool")

    @property
    def tool_size(self):
        return self._tool_size

    @tool_size.setter
    def tool_size(self, value):
        self._tool_size = value
        self.emit("tool-size")

    @property
    def primary_color(self):
        return self._primary_color

    @primary_color.setter
    def primary_color(self, value):
        self._primary_color = value
        self.emit("primary-color")

    @property
    def secondary_color(self):
        return self._secondary_color

    @secondary_color.setter
    def secondary_color(self, value):
        self._secondary_color = value
        self.emit("secondary-color")

    @property
    def zoom(self):
        return self._zoom

    @zoom.setter
    def zoom(self, value):
        self._zoom = value
        self.emit("zoom")

    @property
    def pixel_size(self):
        return self._pixel_size

    @pixel_size.setter
    def pixel_size(self, value):
        self._pixel_size = value
        self.emit("pixel-size")

    @property
    def resizable(self):
        return self._resizable

    @resizable.setter
    def resizable(self, value):
        self._resizable = value
        self.emit("resizable")

    @property
    def editable(self):
        return self._editable

    @editable.setter
    def editable(self, value):
        self._editable = value
        self.emit("editable")


class Canvas(Gtk.DrawingArea):

    __gsignals__ = {
        "primary-color-picked": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT]),
        "secondary-color-picked": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT]),
        "changed": (GObject.SIGNAL_RUN_LAST, None, []),
        "size-changed": (GObject.SIGNAL_RUN_LAST, None, []),
    }

    def __init__(self, config=None, *args, **kargs):
        super(Canvas, self).__init__()

        if config is None:
            self.config = CanvasConfig(*args, **kargs)

        else:
            self.config = config

        self.config.connect("layout-size", self.set_layout_size)
        self.config.connect("zoom", self._zoom_changed_cb)

        self.pixelmap = PixelMap(*self.config.layout_size)
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

        if self.config.editable:
            self.add_events(Gdk.EventMask.SCROLL_MASK |
                            Gdk.EventMask.POINTER_MOTION_MASK |
                            Gdk.EventMask.BUTTON_MOTION_MASK)

            self.connect("scroll-event", self._scroll_cb)
            self.connect("motion-notify-event", self._button_motion_cb)
            self.connect("button-press-event", self._button_press_cb)
            self.connect("button-release-event", self._button_release_cb)

        self.connect("draw", self._draw_cb)

    def resize(self):
        width, height = self.config.layout_size

        if not self.config.resizable:
            alloc = self.get_allocation()
            m = min(alloc.width, alloc.height)
            self.config.zoom = 100 * min(alloc.width / width, alloc.height / height)
            return

        factor = self.config.zoom / 100
        width = self.config.pixel_size * width * factor
        height = self.config.pixel_size * height * factor
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
            self.config.zoom = min(2000, self.config.zoom + 10)

        else:
            self.config.zoom = max(1, self.config.zoom - 10)

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
            self.config.tool = self._pending_tool
            self.redraw()

        self.emit("changed")

    def _draw_cb(self, canvas, ctx):
        alloc = self.get_allocation()
        factor = self.config.zoom / 100
        w = h = self.config.pixel_size * factor
        margin = 1 if self.config.zoom >= 100 and self.config.editable else 0

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
            factor = self.config.zoom / 100
            w = h = self.config.pixel_size * factor
            margin = 1 if self.config.zoom >= 100 else 0
            ctx.rectangle(x + margin, y + margin, w - 2 * margin, h - 2 * margin)
            ctx.fill()

    def redraw(self):
        GLib.idle_add(self.queue_draw)

    def set_tool_size(self, size):
        # self.config.tool_size = size
        # self.redraw()
        print("Implementar Canvas.set_tool_size")

    def set_layout_size(self, size):
        new_width, new_height = size
        current_width, current_height = self.config.layout_size

        for x in range(new_width + 1, current_width + 1):
            for y in range(1, current_height + 1):
                self.pixelmap.delete_pixel_at(x, y)

        for x in range(1, new_width + 1):
            for y in range(new_height + 1, current_height + 1):
                self.pixelmap.delete_pixel_at(x, y)

        self.set_sprite_size((new_width, new_height))

    def set_sprite_size(self, size):
        self.layout_size = size
        self.pixelmap.width, self.pixelmap.height = self.layout_size
        self.resize()

    def set_tool(self, tool):
        if Gdk.BUTTON_PRIMARY in self._pressed_buttons or  \
            Gdk.BUTTON_SECONDARY in self._pressed_buttons:

            self._pending_tool = tool

        else:
            self.config.tool = tool
            self.redraw()

    def _zoom_changed_cb(self, zoom):
        self.resize()

    def get_relative_coords(self, x, y):
        factor = 1 / (self.config.pixel_size * self.config.zoom / 100)
        return int(x * factor) + 1, int(y * factor) + 1

    def get_absolute_coords(self, x, y):
        factor = self.config.pixel_size * self.config.zoom / 100
        return factor * (x - 1), factor * (y - 1)

    def apply_tool(self, x, y, color=Color.PRIMARY):
        cairo_color = (0, 0, 0, 1)
        paint_selected_pixel = True

        if ToolType.is_paint_tool(self.config.tool):
            if color == Color.PRIMARY:
                cairo_color = self.config.primary_color

            elif color == Color.SECONDARY:
                cairo_color = self.config.secondary_color

            if self.config.tool == ToolType.BUCKET:
                paint_selected_pixel = False
                current_pixel = self.get_selected_pixels()[0]
                current_color = self.pixelmap.get_pixel_color(*current_pixel)
                PaintAlgorithms.flood_fill(self.pixelmap, x, y, current_color, cairo_color)

                self.pixelmap.set_pixel_color(x, y, cairo_color)
                self.redraw()

            elif self.config.tool == ToolType.SPECIAL_BUCKET:
                paint_selected_pixel = False
                selected_color = self.pixelmap.get_pixel_color(x, y)
                PaintAlgorithms.replace(self.pixelmap, selected_color, cairo_color)

                self.redraw()

        elif self.config.tool == ToolType.ERASER:
            cairo_color = (1, 1, 1, 0)

        elif self.config.tool == ToolType.COLOR_PICKER:
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
        print("Canvas.set_primary_color")

    def set_secondary_color(self, color):
        print("Canvas.set_secondary_color")

    def get_selected_pixels(self):
        x, y = self.get_relative_coords(*self._mouse_position)
        pixels = [(x, y)]

        if not ToolType.is_resizable(self.config.tool):
            return pixels

        if self.config.tool_size >= 2:
            # La X es donde está el mouse
            # ---------
            # | X | 1 |
            # |---|---|
            # | 3 | 2 |
            # ---------
            pixels.extend([(x + 1, y),      # 1
                           (x + 1, y + 1),  # 2
                           (x, y + 1)])     # 3

        if self.config.tool_size >= 3:
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

        if self.config.tool_size == 4:
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

        if self.config.tool == ToolType.VERTICAL_MIRROR_PEN:
            for x, y in pixels:
                mx = self.config.layout_size[0] - x + 1
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
            self.config.layout_size = image.size
            self.pixelmap.load_data_from_image(image)
            self.resize()

            self.emit("size-changed")
            self.emit("changed")

    def get_sprite_size(self):
        return self.config.layout_size

    def set_editable(self, editable):
        print("Implementar Canvas.set_editable")

    def get_editable(self):
        return self.config.editable

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

    def __init__(self, *args, **kargs):
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

        self.canvas = Canvas(*args, **kargs)
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

    def get_pixelmap(self):
        return self.canvas.get_pixelmap()

    def set_pixelmap(self, pixelmap, refresh=True):
        self.canvas.set_pixelmap(pixelmap, refresh=True)

    def set_file(self, filename, refresh=True):
        self.canvas.set_file(filename, refresh=refresh)

    def get_file(self):
        return self.canvas.get_file()

    def get_config(self):
        return self.canvas.config
