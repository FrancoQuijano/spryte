#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gi.repository import Gtk
from gi.repository import GObject


class HeaderBar(Gtk.HeaderBar):

    __gsignals__ = {
        "tool-size-changed": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_INT]),
    }

    def __init__(self):
        super(HeaderBar, self).__init__()

        self.set_show_close_button(True)
        self._create_tool_size_buttons()

    def _create_tool_size_buttons(self):
        hbox = Gtk.Box()
        hbox.set_orientation(Gtk.Orientation.HORIZONTAL)
        hbox.get_style_context().add_class("linked")

        _button = None
        for x in range(1, 5):
            button = Gtk.RadioButton.new_with_mnemonic_from_widget(
                _button, "_%d" % x)

            button.set_mode(False)
            button.connect("toggled", self._tool_size_changed, x)
            hbox.pack_start(button, False, False, 0)

            _button = button

        self.pack_start(hbox)

    def _tool_size_changed(self, button, size):
        self.emit("tool-size-changed", size)
