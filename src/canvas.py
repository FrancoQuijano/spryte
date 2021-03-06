#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function

from PIL import Image

from .utils import Color, ToolType, PaintAlgorithms, FileManagement
from .tools import TOOLS

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

        self.pixels = []
        self.temp_pixels = []

    def __iter__(self):
        return self

    def __contains__(self, obj):
        for pixel in self.pixels:
            if pixel.x == obj[0] and pixel.y == obj[1]:
                return True

        return False

    @classmethod
    def new_from_image(self, image):
        pixelmap = PixelMap()
        pixelmap.width, pixelmap.height = image.width, image.height
        pixelmap.load_data_from_image(image)

        return pixelmap

    def get_pixel_at(self, x, y):
        for pixel in self.pixels:
            if pixel.x == x and pixel.y == y:
                return pixel

        return None

    def get_temp_pixel_at(self, x, y):
        for pixel in self.temp_pixels:
            if pixel.x == x and pixel.y == y:
                return pixel

        return None

    def get_pixel_color(self, x, y):
        pixel = self.get_pixel_at(x, y)
        if pixel is not None:
            return pixel.color

        else:
            return Color.TRANSPARENT

    def set_pixel_color(self, x, y, color):
        if x <= 0 or x > self.width or y <= 0 or y > self.height:
            return

        pixel = self.get_pixel_at(x, y)
        if pixel is None and color[Color.ALPHA] != 0:
            pixel = Pixel(x, y, color)
            self.pixels.append(pixel)

        elif color[Color.ALPHA] != 0:
            pixel.color = color

        elif color[Color.ALPHA] == 0:
            self.delete_pixel_at(x, y)

    def get_temp_pixel_color(self, x, y):
        pixel = self.get_temp_pixel_at(x, y)
        if pixel is not None:
            return pixel.color

        else:
            return Color.TRANSPARENT

    def set_temp_pixel_color(self, x, y, color):
        if x <= 0 or x > self.width or y <= 0 or y > self.height:
            return

        pixel = self.get_temp_pixel_at(x, y)
        if pixel is None:
            if self.get_pixel_at(x, y) is None and color[Color.ALPHA] == 0:
                return

            pixel = Pixel(x, y, color)
            self.temp_pixels.append(pixel)

        elif color[Color.ALPHA] != 0:
            pixel.color = color

    def delete_pixel_at(self, x, y):
        for pixel in self.pixels:
            if pixel.x == x and pixel.y == y:
                del self.pixels[self.pixels.index(pixel)]
                break

    def delete_temp_pixel(self, pixel):
        del self.temp_pixels[self.temp_pixels.index(pixel)]

    def delete_temp_pixel_at(self, x, y):
        for pixel in self.temp_pixels:
            if pixel.x == x and pixel.y == y:
                self.delete_temp_pixel(pixel)
                break

    def delete_temp_pixels(self):
        while len(self.temp_pixels) > 0:
            self.delete_temp_pixel(self.temp_pixels[0])

    def untemp_pixels(self):
        for pixel in self.temp_pixels:
            self.set_pixel_color(pixel.x, pixel.y, pixel.color)

        self.delete_temp_pixels()

    def load_data_from_image(self, image):
        self.pixels = []

        image = image.convert("RGBA")

        for x in range(0, image.size[0]):
            for y in range(0, image.size[1]):
                r, g, b, a = image.getpixel((x, y))

                if a == 0:
                    continue

                color = Color.rgba_to_cairo((r, g, b, a))
                self.pixels.append(Pixel(x + 1, y + 1, color))

    def copy(self):
        pixelmap = PixelMap(self.width, self.height)
        pixelmap.pixels = self.pixels.copy()
        pixelmap.temp_pixels = self.temp_pixels.copy()

        return pixelmap

    def is_empty(self):
        return len(self.pixels) == 0


class CanvasConfig:

    DEFAULT_LAYOUT_SIZE = (16, 16)
    DEFAULT_TOOL = ToolType.PENCIL
    DEFAULT_TOOL_SIZE = 1
    DEFAULT_PRIMARY_COLOR = Color.BLACK
    DEFAULT_SECONDARY_COLOR = Color.WHITE
    DEFAULT_ZOOM = 2000
    DEFAULT_SHOW_GRID = False
    DEFAULT_RESIZABLE = True
    DEFAULT_EDITABLE = True
    DEFAULT_FILE = None
    DEFAULT_MODIFIED = False

    def __init__(self, layout_size=DEFAULT_LAYOUT_SIZE, tool=DEFAULT_TOOL,
                 tool_size=DEFAULT_TOOL_SIZE,
                 primary_color=DEFAULT_PRIMARY_COLOR,
                 secondary_color=DEFAULT_SECONDARY_COLOR,
                 zoom=DEFAULT_ZOOM, show_grid=DEFAULT_SHOW_GRID,
                 resizable=DEFAULT_RESIZABLE, editable=DEFAULT_EDITABLE,
                 file=DEFAULT_FILE, modified=DEFAULT_MODIFIED):

        self._layout_size = layout_size
        self._tool = tool
        self._tool_size = tool_size
        self._primary_color = primary_color
        self._secondary_color = secondary_color
        self._zoom = zoom
        self._show_grid = show_grid
        self._resizable = resizable
        self._editable = editable
        self._file = file
        self._modified = modified

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
    def show_grid(self):
        return self._show_grid

    @show_grid.setter
    def show_grid(self, value):
        self._show_grid = value
        self.emit("show-grid")

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

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, value):
        self._file = value
        self.emit("file")

    @property
    def modified(self):
        return self._modified

    @modified.setter
    def modified(self, value):
        if value != self._modified:
            self._modified = value
            self.emit("modified")


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
        self.config.connect("file", self._file_changed_cb)

        self.pixelmap = PixelMap(*self.config.layout_size)

        self._pending_tool = None
        self._pressed_buttons = []
        self._mouse_position = (-1, -1)
        self._click_mouse_position = (None, None)
        self._hovered_pixels = []
        self._selected_pixels = []
        self._history = [self.pixelmap]
        self._last_saved_pixelmap = self.pixelmap
        self._current_layout_size = self.config.layout_size
        self._waiting_for_allocate = False

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
        self.connect("size-allocate", self._size_allocate_cb)

    def _scroll_cb(self, canvas, event):
        if event.state != Gdk.ModifierType.CONTROL_MASK:
            # Elimino el modificador para que piense que el usuario
            # hizo un scroll normal
            event.state = 0
            return False

        if event.direction == Gdk.ScrollDirection.UP:
            self.config.zoom = min(5000, self.config.zoom + 50)

        else:
            self.config.zoom = max(1, self.config.zoom - 50)

        self.resize()

        # Me aseguro de que no se haga scroll ya que se está haciendo zoom
        return True

    def _button_motion_cb(self, canvas, event):
        self._mouse_position = (event.x, event.y)

        hovered_pixels = self.get_hovered_pixels()
        if hovered_pixels == self._hovered_pixels:
            self.redraw()
            return

        if self.config.tool in [ToolType.STROKE, ToolType.RECTANGLE]:
            self.pixelmap.delete_temp_pixels()

        self._hovered_pixels = hovered_pixels

        if Gdk.BUTTON_PRIMARY in self._pressed_buttons:
            self.apply_tool_to_hovered_pixels(color=Color.PRIMARY)

        elif Gdk.BUTTON_SECONDARY in self._pressed_buttons:
            self.apply_tool_to_hovered_pixels(color=Color.SECONDARY)

        self.redraw()

    def _button_press_cb(self, canvas, event):
        button = event.get_button()[1]
        if button == Gdk.BUTTON_MIDDLE:
            return

        self._click_mouse_position = (event.x, event.y)

        # TODO: Si la tecla Ctrl está apretada, no deseleccionar pixeles
        # anteriormente seleccionados
        self.unselect_all_pixels()

        if button not in self._pressed_buttons:
            self._pressed_buttons.append(button)

        if button == Gdk.BUTTON_PRIMARY:
            self.apply_tool_to_hovered_pixels(color=Color.PRIMARY)

        elif button == Gdk.BUTTON_SECONDARY:
            self.apply_tool_to_hovered_pixels(color=Color.SECONDARY)

    def _button_release_cb(self, canvas, event):
        button = event.get_button()[1]
        if button == Gdk.BUTTON_MIDDLE:
            return

        if button in self._pressed_buttons:
            self._pressed_buttons.remove(button)

        if self._pending_tool is not None and self._pressed_buttons == []:
            self.config.tool = self._pending_tool
            self.redraw()

        self._click_mouse_position = (None, None)

        self._history = self._history[:self._history.index(self.pixelmap) + 1]
        prev = self.pixelmap
        self.pixelmap = PixelMap(self.pixelmap.width, self.pixelmap.height)

        for pixel in prev.pixels + prev.temp_pixels:
            self.pixelmap.set_pixel_color(pixel.x, pixel.y, pixel.color)

        self._history.append(self.pixelmap)

        prev.delete_temp_pixels()

        self.config.modified = True
        self.emit("changed")

    def _draw_cb(self, canvas, ctx):
        alloc = self.get_allocation()
        w = h = self.config.zoom / 100

        if self.config.show_grid and self.config.zoom >= 150 and self.config.editable:
            margin = 0.5

        else:
            margin = 0

        self._draw_bg(ctx)

        painted = []

        # Los pixeles temporales tienen preferencia
        for pixel in self.pixelmap.temp_pixels + self.pixelmap.pixels:
            coords = (pixel.x, pixel.y)
            if coords in painted:
                continue

            painted.append(coords)
            x, y = self.get_absolute_coords(*coords)

            ctx.set_source_rgba(*pixel.color)
            ctx.rectangle(x + margin, y + margin, w - 2 * margin, h - 2 * margin)
            ctx.fill()

        self._draw_hovered_pixels(ctx)
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

    def _draw_hovered_pixels(self, ctx):
        ctx.set_source_rgba(1, 1, 1, 0.2)

        for x, y in self._hovered_pixels:
            x, y = self.get_absolute_coords(x, y)
            w = h = self.config.zoom / 100
            margin = 1 if self.config.zoom >= 100 else 0
            ctx.rectangle(x + margin, y + margin, w - 2 * margin, h - 2 * margin)
            ctx.fill()

    def _draw_selected_pixels(self, ctx):
        ctx.set_source_rgba(*Color.SELECTED_PIXEL)

        for x, y in self._selected_pixels:
            x, y = self.get_absolute_coords(x, y)
            w = h = self.config.zoom / 100
            margin = 1 if self.config.zoom >= 100 else 0
            ctx.rectangle(x + margin, y + margin, w - 2 * margin, h - 2 * margin)
            ctx.fill()

    def _size_allocate_cb(self, canvas, alloc):
        if self._waiting_for_allocate:
            self._waiting_for_allocate = False
            self.resize()

    def redraw(self):
        GLib.idle_add(self.queue_draw)

    def resize(self):
        width, height = self.config.layout_size

        if not self.config.resizable:
            alloc = self.get_allocation()

            if not self._waiting_for_allocate:
                self._waiting_for_allocate = True
                return
 
            self.config._zoom = 100 * min(alloc.width / width, alloc.height / height)
            self.redraw()

            return

        width = width * self.config.zoom / 100
        height = height * self.config.zoom / 100
        self.set_size_request(width, height)

        # No es necesario llamar self.redraw() a menos que
        # no se cambie el tamaño

    def set_layout_size(self, size):
        new_width, new_height = size
        current_width, current_height = self._current_layout_size

        for x in range(new_width + 1, current_width + 1):
            for y in range(1, current_height + 1):
                self.pixelmap.delete_pixel_at(x, y)

        for x in range(1, new_width + 1):
            for y in range(new_height + 1, current_height + 1):
                self.pixelmap.delete_pixel_at(x, y)

        self.set_sprite_size((new_width, new_height))
        self.config.modified = True
        self.emit("size-changed")

    def set_sprite_size(self, size):
        self._current_layout_size = size
        self.pixelmap.width, self.pixelmap.height = self.config.layout_size
        self.resize()

    def _zoom_changed_cb(self, zoom):
        self.resize()

    def get_relative_coords(self, x, y):
        factor = 100 / self.config.zoom
        return int(x * factor) + 1, int(y * factor) + 1

    def get_absolute_coords(self, x, y):
        factor = self.config.zoom / 100
        return factor * (x - 1), factor * (y - 1)

    def apply_tool_to_hovered_pixels(self, color=Color.PRIMARY):
        tool = TOOLS.get(self.config.tool, None)

        if tool is not None:
            redraw = tool.apply(self, self._hovered_pixels, color, self.config.primary_color, self.config.secondary_color)
            if redraw:
                self.redraw()

    def get_hovered_pixels(self, start=None):
        if start is None:
            x, y = self.get_relative_coords(*self._mouse_position)

        else:
            x, y = self.get_relative_coords(*start)

        tool = TOOLS.get(self.config.tool, None)
        if tool is not None:
            return tool.get_hovered_pixels(self, x, y)

        return [(x, y)]

    def get_pixelmap(self):
        return self.pixelmap

    def set_pixelmap(self, pixelmap, refresh=True, reset=False):
        self.pixelmap = pixelmap
        if reset:
            self._history = [self.pixelmap]

        else:
            self._history.append(self.pixelmap)

        self.config.modified = False

        if refresh:
            self.redraw()

    def _file_changed_cb(self, filename):
        self.config.layout_size = FileManagement.get_image_dimensions(filename)
        self.resize()

        self.config.modified = False
        self.emit("changed")

    def set_file(self, file, refresh=True):
        if refresh:
            self.config.file = file

        else:
            self.config._file = file
            self.config.modified = False

    def get_sprite_size(self):
        return self.config.layout_size

    def undo(self):
        index = self._history.index(self.pixelmap)
        if index > 0:
            self.pixelmap = self._history[index - 1]
            self.redraw()

            self.config.modified = self.pixelmap != self._last_saved_pixelmap
            self.emit("changed")

    def redo(self):
        index = self._history.index(self.pixelmap)
        if index < len(self._history) - 1:
            self.pixelmap = self._history[index + 1]
            self.redraw()

            self.config.modified = self.pixelmap != self._last_saved_pixelmap
            self.emit("changed")

    def select_pixel(self, x, y):
        coord = (x, y)
        if not coord in self._selected_pixels:
            self._selected_pixels.append(coord)

    def unselect_pixel(self, x, y):
        coord = (x, y)
        if coord in self._selected_pixels:
            self._selected_pixels.remove(coord)

    def unselect_all_pixels(self):
        while len(self._selected_pixels) > 0:
            self.unselect_pixel(*self._selected_pixels[0])


class CanvasContainer(Gtk.Box):

    __gsignals__ = {
        "primary-color-picked": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT]),
        "secondary-color-picked": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT]),
        "changed": (GObject.SIGNAL_RUN_LAST, None, []),
        "size-changed": (GObject.SIGNAL_RUN_LAST, None, []),
    }

    def __init__(self, *args, **kargs):
        super(CanvasContainer, self).__init__()

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

        self.config = self.canvas.config
        self.pixelmap = self.canvas.pixelmap

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

    def set_pixelmap(self, pixelmap, *args, **kargs):
        self.canvas.set_pixelmap(pixelmap, *args, **kargs)

    def set_file(self, file, refresh=True):
        self.canvas.set_file(file, refresh=refresh)

    def get_file(self):
        return self.canvas.get_file()

    def get_config(self):
        return self.canvas.config

    def undo(self):
        self.canvas.undo()

    def redo(self):
        self.canvas.redo()
