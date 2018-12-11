#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Gio
from gi.repository import Gtk

import src
from src import ToolPalette
from src import HeaderBar
from src import CanvasContainer
from src import Statusbar
from src import FilesNotebook
from src.utils import FileChooserManager
from src.utils import FileManagement


class SpryteApp(Gtk.Application):

    def __init__(self, *args, **kargs):
        super().__init__(*args, application_id="org.zades.spryte", **kargs)

        self.windows = []

    def _create_actions(self):
        actions = [
            # File
            ("new_file",   "app.new_file",   ["<Primary>N"], self.new_file),
            ("open_file",  "app.open_file",  ["<Primary>O"], self.open),
            ("save",       "app.save",       ["<Primary>S"], self.save),
            ("save_as",    "app.save_as",    ["<Primary><Shift>S"], self.save_as),
            ("close_file", "app.close_file", ["<Primary>W"], self.close_file),

            # Edit
            ("undo", "app.undo", ["<Primary>Z"], self.undo),
            ("redo", "app.redo", ["<Primary><Shift>Z", "<Primary>Y"], self.redo),
        ]

        for name, detailed_name, accesls, callback in actions:
            action = Gio.SimpleAction.new(name, None);
            self.set_accels_for_action(detailed_name, accesls);
            self.add_action(action);

            if callback is not None:
                action.connect("activate", callback)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        # TODO: Crear menús

        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)

        self._create_actions()

    def do_activate(self):
        if len(self.windows) == 0:
            win = SpryteWindow(application=self, title="Spryte")
            self.windows.append(win)

        self.windows[0].present()

    def on_quit(self, action, param):
        self.quit()

    def get_current_window(self):
        # TODO: hacer save en la ventana actual, si es que voy a permitir
        # más de una ventana en simultáneo
        return self.windows[0]

    def new_file(self, action, param):
        self.get_current_window().new_file()

    def open(self, action, param):
        self.get_current_window().open()

    def save(self, action, param):
        self.get_current_window().save()

    def save_as(self, action, param):
        self.get_current_window().save_as()

    def close_file(self, action, param):
        self.get_current_window().close_file()

    def undo(self, action, param):
        self.get_current_window().undo()

    def redo(self, action, param):
        self.get_current_window().redo()


class SpryteWindow(Gtk.ApplicationWindow):

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

        self.set_default_size(620, 480)

        self.headerbar = HeaderBar()
        self.headerbar.connect("tool-size-changed", self._tool_size_changed_cb)
        self.headerbar.connect("layout-size-changed", self._layout_size_changed_cb)
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

        self.files_notebook = FilesNotebook()
        self.files_notebook.append_page()
        self.files_notebook.connect("save-before-closing", self._save_before_closing_cb)
        self.files_notebook.connect("primary-color-picked", self._primary_color_picked_cb)
        self.files_notebook.connect("secondary-color-picked", self._secondary_color_picked_cb)
        self.layout.pack_start(self.files_notebook, True, True, 0)

        self.statusbar = Statusbar()
        self.statusbar.connect("zoom-changed", self._zoom_changed_cb)
        self.box.pack_end(self.statusbar, False, False, 0)

        self.show_all()

    def get_current_cavases_notebook(self):
        return self.files_notebook.get_current_notebook()

    def _tool_size_changed_cb(self, headerbar, size):
        self.get_current_cavases_notebook().set_tool_size(size)

    def _layout_size_changed_cb(self, headerbar, size):
        self.get_current_cavases_notebook().set_layout_size(size)

    def _tool_changed_cb(self, palette, tool):
        self.get_current_cavases_notebook().set_tool(tool)

    def _primary_color_changed_cb(self, palette, color):
        self.get_current_cavases_notebook().set_primary_color(color)

    def _secondary_color_changed_cb(self, palette, color):
        self.get_current_cavases_notebook().set_secondary_color(color)

    def _zoom_changed_cb(self, statusbar, zoom):
        self.get_current_cavases_notebook().set_zoom(zoom)

    def _primary_color_picked_cb(self, canvas, color):
        self.tool_palette.set_primary_color(color)
        self.get_current_cavases_notebook().set_primary_color(color)

    def _secondary_color_picked_cb(self, canvas, color):
        self.tool_palette.set_secondary_color(color)
        self.get_current_cavases_notebook().set_secondary_color(color)

    def _save_before_closing_cb(self, files_notebook, frames_notebook):
        saved = self.save(frames_notebook._canvas_config.file)
        if saved:
            # En teoría, el force no es necesario
            self.files_notebook.remove_page(frames_notebook, force=True)

    def new_file(self):
        self.files_notebook.append_page()

    def open(self):
        files = FileChooserManager.open(self)

        for file in files:
            if not os.access(file, os.R_OK):
                print("WARNING: no se tienen permisos de lectura para %s" % file)
                break  # TODO: Cambiar por continue cuando agregue soporte para múltiples archivos

            self.get_current_cavases_notebook().open_file(file)
            break  # TODO: Agregar soporte para más de un archivo, luego borrar esto

    def save(self, file=None):
        if file is None:
            file = self.get_current_cavases_notebook().get_file()

            if file is None:
                return self.save_as()

        pixelmaps = self.get_current_cavases_notebook().get_pixelmaps()
        FileManagement.save(pixelmaps, file)

        self.get_current_cavases_notebook().set_file(file, refresh=False)
        self.files_notebook.set_filename(os.path.basename(file))

        return True

    def save_as(self):
        file = FileChooserManager.save(self)
        if file is not None:  # El usuario canceló la acción de guardar
            self.save(file)
            return True

        return False

    def close_file(self):
        notebook = self.files_notebook.get_current_notebook()
        self.files_notebook.remove_page(notebook)

    def undo(self):
        self.get_current_cavases_notebook().undo()

    def redo(self):
        self.get_current_cavases_notebook().redo()


if __name__ == "__main__":
    import signal

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = SpryteApp()
    exit_status = app.run(sys.argv)

    sys.exit(exit_status)
