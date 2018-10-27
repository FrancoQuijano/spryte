#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .utils import Color

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject


class Tool(object):

    def __init__(self, name="", icon=None, position=(0, 0)):
        self.name = name
        self.icon = icon
        self.position = position
        self.button = None


class ToolPalette(Gtk.Grid):

    __gsignals__ = {
        "primary-color-changed": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT]),
        "secondary-color-changed": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT])
    }

    def __init__(self):
        super(ToolPalette, self).__init__()

        self.set_column_homogeneous(True)

        self.tools = [
            Tool("Pen", icon="document-edit-symbolic", position=(0, 0)),
            Tool("Bucket",              position=(0, 1)),
            Tool("Eraser",              position=(0, 2)),
            Tool("Rectangle",           position=(0, 3)),
            Tool("Move",                position=(0, 4)),
            Tool("Rectangle selection", position=(0, 5)),
            Tool("Lighten",             position=(0, 6)),
            Tool("Color Picker",        position=(0, 7)),

            Tool("Vertical mirror pen", position=(1, 0)),
            Tool("Layer",               position=(1, 1)),
            Tool("Stroke",              position=(1, 2)),
            Tool("Circle",              position=(1, 3)),
            Tool("Shape selection",     position=(1, 4)),
            Tool("Lasso selection",     position=(1, 5)),
            Tool("Dithering",           position=(1, 6)),
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

            button.set_mode(False)
            self.attach(button, tool.position[0], tool.position[1], 1, 1)

            tool.button = button
            _button = button

    def _create_color_buttons(self):
        btn1 = Gtk.ColorButton()
        btn1.set_use_alpha(True)
        btn1.connect("color-set", self._primary_color_changed)
        self.attach(btn1, 0, 8, 1, 1)

        color = Gdk.RGBA()
        color.red = 0
        color.green = 0
        color.blue = 0
        color.alpha = 1
        btn1.set_rgba(color)

        btn2 = Gtk.ColorButton()
        btn2.set_use_alpha(True)
        btn2.connect("color-set", self._secondary_color_changed)
        self.attach(btn2, 1, 8, 1, 1)

        color = Gdk.RGBA()
        color.red = 1
        color.green = 1
        color.blue = 1
        color.alpha = 1.0
        btn2.set_rgba(color)

    def _primary_color_changed(self, btn):
        color = Color.gdk_to_cairo(btn.get_color(), btn.get_alpha())
        self.emit("primary-color-changed", color)

    def _secondary_color_changed(self, btn):
        color = Color.gdk_to_cairo(btn.get_color(), btn.get_alpha())
        self.emit("secondary-color-changed", color)
