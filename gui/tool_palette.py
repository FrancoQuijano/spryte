#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gi.repository import Gtk


class Tool(object):

    def __init__(self, name="", icon=None, position=(0, 0)):
        self.name = name
        self.icon = icon
        self.position = position
        self.button = None


class ToolPalette(Gtk.Grid):

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
