#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gtk

import gui
from gui import ToolPalette
from gui import HeaderBar
from gui import CanvasContainer
from gui import Statusbar


class SpryteApp(Gtk.Application):

    def __init__(self, *args, **kargs):
        super().__init__(*args, application_id="org.zades.spryte", **kargs)

        self.windows = []

    def do_startup(self):
        Gtk.Application.do_startup(self)
        # TODO: Crear menús

        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)

    def do_activate(self):
        if len(self.windows) == 0:
            win = SpryteWindow(application=self, title="Spryte")
            self.windows.append(win)

        self.windows[0].present()

    def on_quit(self, action, param):
        self.quit()


class SpryteWindow(Gtk.ApplicationWindow):

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

        self.set_default_size(620, 480)

        self.headerbar = HeaderBar()
        self.headerbar.connect("tool-size-changed", self._tool_size_changed_cb)
        self.set_titlebar(self.headerbar)

        self.box = Gtk.Box()
        self.box.set_orientation(Gtk.Orientation.VERTICAL)
        self.add(self.box)

        self.layout = Gtk.Box()
        self.layout.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.box.pack_start(self.layout, True, True, 0)

        self.tool_palette = ToolPalette()
        self.tool_palette.connect("tool-changed", self._tool_changed_cb)
        self.tool_palette.connect("primary-color-changed", self._primary_color_changed_cb)
        self.tool_palette.connect("secondary-color-changed", self._secondary_color_changed_cb)
        self.layout.pack_start(self.tool_palette, False, False, 0)

        self.canvas = CanvasContainer(pixel_size=20, sprite_width=32, sprite_height=32)
        self.layout.pack_start(self.canvas, True, True, 0)

        self.statusbar = Statusbar()
        self.statusbar.connect("zoom-changed", self._zoom_changed_cb)
        self.box.pack_end(self.statusbar, False, False, 0)

        self.show_all()

    def _tool_size_changed_cb(self, headerbar, size):
        self.canvas.set_tool_size(size)

    def _tool_changed_cb(self, palette, tool):
        self.canvas.set_tool(tool)

    def _primary_color_changed_cb(self, palette, color):
        self.canvas.set_primary_color(color)

    def _secondary_color_changed_cb(self, palette, color):
        self.canvas.set_secondary_color(color)

    def _zoom_changed_cb(self, statusbar, zoom):
        self.canvas.set_zoom(zoom)


if __name__ == "__main__":
    import signal

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = SpryteApp()
    exit_status = app.run(sys.argv)

    sys.exit(exit_status)
