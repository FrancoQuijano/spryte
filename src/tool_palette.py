#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GdkPixbuf

from .utils import Color, ToolType, SPRYTE_DIR


class Tool(object):

    def __init__(self, name, position, tool_type):

        self.name = name
        self.position = position
        self.type = tool_type
        self.button = None
        self.icon = self._get_icon_path()

    def _get_icon_path(self):
        return ToolType.ICONS.get(self.type, None)


class ToolPalette(Gtk.Grid):

    __gsignals__ = {
        "tool-changed": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_INT]),
        "primary-color-changed": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT]),
        "secondary-color-changed": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT])
    }

    def __init__(self):
        super(ToolPalette, self).__init__()

        self.set_column_homogeneous(True)

        self.tools = [
            Tool("Pencil",              (0, 0), ToolType.PENCIL),
            Tool("Bucket",              (0, 1), ToolType.BUCKET),
            Tool("Eraser",              (0, 2), ToolType.ERASER),
            Tool("Rectangle",           (0, 3), ToolType.RECTANGLE),
            Tool("Move",                (0, 4), ToolType.MOVE),
            Tool("Rectangle selection", (0, 5), ToolType.RECTANGLE_SELECTION),
            Tool("Lighten",             (0, 6), ToolType.LIGHTEN),
            Tool("Color Picker",        (0, 7), ToolType.COLOR_PICKER),

            Tool("Vertical mirror pen", (1, 0), ToolType.VERTICAL_MIRROR_PENCIL),
            Tool("Replace color",       (1, 1), ToolType.SPECIAL_BUCKET),
            Tool("Stroke",              (1, 2), ToolType.STROKE),
            Tool("Circle",              (1, 3), ToolType.CIRCLE),
            Tool("Shape selection",     (1, 4), ToolType.SHAPE_SELECTION),
            Tool("Lasso selection",     (1, 5), ToolType.LASSO_SELECTION),
            Tool("Dithering",           (1, 6), ToolType.DITHERING),
        ]

        self._create_tools_buttons()
        self._create_color_buttons()

    def _create_tools_buttons(self):
        _button = None

        for tool in self.tools:
            button = Gtk.RadioButton.new_from_widget(_button)

            if _button is None:
                _button = button

            if tool.icon is None:
                # TODO: Sacar este if una vez estén todos los íconos
                pixbuf = None
                button.set_size_request(24, 24)

            else:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(tool.icon)
                pixbuf = pixbuf.scale_simple(24, 24, GdkPixbuf.InterpType.NEAREST)

            image = Gtk.Image.new_from_pixbuf(pixbuf)
            button.set_image(image)
            button.set_tooltip_text(tool.name)
            button.set_mode(False)
            button.connect("toggled", self._tool_changed, tool.type)
            self.attach(button, tool.position[0], tool.position[1], 1, 1)

            tool.button = button

    def _create_color_buttons(self):
        self.primary_color_button = Gtk.ColorButton()
        self.primary_color_button.set_use_alpha(True)
        self.primary_color_button.connect("color-set", self._primary_color_changed)
        self.attach(self.primary_color_button, 0, 8, 1, 1)

        self.set_primary_color((0, 0, 0, 1))

        self.secondary_color_button = Gtk.ColorButton()
        self.secondary_color_button.set_use_alpha(True)
        self.secondary_color_button.connect("color-set", self._secondary_color_changed)
        self.attach(self.secondary_color_button, 1, 8, 1, 1)

        self.set_secondary_color((1, 1, 1, 1))

    def _tool_changed(self, button, tool):
        self.emit("tool-changed", tool)

    def _primary_color_changed(self, btn):
        color = Color.gdk_to_cairo(btn.get_color(), btn.get_alpha())
        self.emit("primary-color-changed", color)

    def _secondary_color_changed(self, btn):
        color = Color.gdk_to_cairo(btn.get_color(), btn.get_alpha())
        self.emit("secondary-color-changed", color)

    def set_primary_color(self, color):
        self.primary_color_button.set_color(Color.cairo_to_gdk(color))
        self.primary_color_button.set_alpha(color[3] * 65535)

    def set_secondary_color(self, color):
        self.secondary_color_button.set_color(Color.cairo_to_gdk(color))
        self.secondary_color_button.set_alpha(color[3] * 65535)
