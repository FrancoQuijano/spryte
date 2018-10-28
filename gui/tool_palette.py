#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .utils import Color, ToolType

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject


class Tool(object):

    def __init__(self, name="", icon=None, position=(0, 0),
                 tool_type=ToolType.PEN):

        self.name = name
        self.icon = icon
        self.position = position
        self.type = tool_type
        self.button = None


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
            Tool("Pen", icon="document-edit-symbolic", position=(0, 0), tool_type=ToolType.PEN),
            Tool("Bucket",              position=(0, 1), tool_type=ToolType.BUCKET),
            Tool("Eraser",              position=(0, 2), tool_type=ToolType.ERASER),
            Tool("Rectangle",           position=(0, 3), tool_type=ToolType.RECTANGLE),
            Tool("Move",                position=(0, 4), tool_type=ToolType.MOVE),
            Tool("Rectangle selection", position=(0, 5), tool_type=ToolType.RECTANGLE),
            Tool("Lighten",             position=(0, 6), tool_type=ToolType.LIGHTEN),
            Tool("Color Picker",        position=(0, 7), tool_type=ToolType.COLOR_PICKER),

            Tool("Vertical mirror pen", position=(1, 0), tool_type=ToolType.VERTICAL_MIRROR_PEN),
            Tool("SPECIAL_BUCKET",      position=(1, 1), tool_type=ToolType.SPECIAL_BUCKET),
            Tool("Stroke",              position=(1, 2), tool_type=ToolType.STROKE),
            Tool("Circle",              position=(1, 3), tool_type=ToolType.CIRCLE),
            Tool("Shape selection",     position=(1, 4), tool_type=ToolType.SHAPE_SELECTION),
            Tool("Lasso selection",     position=(1, 5), tool_type=ToolType.LASSO_SELECTION),
            Tool("Dithering",           position=(1, 6), tool_type=ToolType.DITHERING),
        ]

        self._create_tools_buttons()
        self._create_color_buttons()

    def _create_tools_buttons(self):
        _button = None

        for tool in self.tools:
            if tool.icon is None:
                button = Gtk.RadioButton.new_with_label_from_widget(
                    _button, "")  # tool.name)

            else:
                button = Gtk.RadioButton()
                image = Gtk.Image.new_from_icon_name("document-edit-symbolic",
                                                     Gtk.IconSize.BUTTON)
                button.set_image(image)
                button.set_group(_button)

            button.set_tooltip_text(tool.name)
            button.set_mode(False)
            button.connect("toggled", self._tool_changed, tool.type)
            self.attach(button, tool.position[0], tool.position[1], 1, 1)

            tool.button = button
            _button = button

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
