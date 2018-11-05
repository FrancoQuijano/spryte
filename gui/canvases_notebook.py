#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .utils import Color
from .canvas import Canvas
from .canvas import CanvasConfig
from .canvas import CanvasContainer

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject


TAB_CANVAS_CONFIG = None


class CanvasNotebookTab(Gtk.Box):

    __gsignals__ = {
        "delete": (GObject.SIGNAL_RUN_LAST, None, []),
    }

    def __init__(self, associated_canvas):
        Gtk.Box.__init__(self)

        self.set_border_width(5)
        self.set_orientation(Gtk.Orientation.VERTICAL)

        self._associated = associated_canvas
        self._timeout_leave = None

        self.overlay = Gtk.Overlay()
        self.overlay.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK |
                                Gdk.EventMask.LEAVE_NOTIFY_MASK |
                                Gdk.EventMask.BUTTON_PRESS_MASK |
                                Gdk.EventMask.BUTTON_RELEASE_MASK |
                                Gdk.EventMask.BUTTON_MOTION_MASK)

        self.overlay.connect("enter-notify-event", self._enter_cb)
        self.overlay.connect("leave-notify-event", self._leave_cb)
        self.pack_start(self.overlay, True, True, 0)

        # FIXME: El tamaño del canvas de los tabs debería ser fijo, siempre
        # Si cierro el programa y lo abro con algún proyecto a medias,
        # probablemente el tamaño de las pestañas cambie, el siguiente código
        # solo previene que un tab nuevo tenga un tamaño diferente (al haber
        # cambiado el tamaño del canvas antes de que se cree este tab.
        global TAB_CANVAS_CONFIG
        if TAB_CANVAS_CONFIG is None:
            TAB_CANVAS_CONFIG = CanvasConfig(
                zoom=500,
                layout_size=self._associated.canvas.config.layout_size,
                resizable=False,
                editable=False)

        self.canvas = Canvas(config=TAB_CANVAS_CONFIG)
        self.canvas.set_size_request(100, 100)
        # self.canvas.set_resizable(False)
        self.overlay.add(self.canvas)

        overlay_box = Gtk.Box()

        overlay_box.set_orientation(Gtk.Orientation.VERTICAL)
        self.overlay.add_overlay(overlay_box)

        hbox = Gtk.Box()
        hbox.set_orientation(Gtk.Orientation.HORIZONTAL)
        overlay_box.pack_start(hbox, True, True, 0)

        self.index_label = Gtk.Label()
        self.index_label.set_valign(Gtk.Align.START)
        self.index_label.set_margin_bottom(4)
        self.index_label.set_margin_start(4)
        self.index_label.set_margin_end(4)
        self.index_label.set_margin_top(4)
        hbox.pack_start(self.index_label, False, False, 0)

        self.top_revealer = Gtk.Revealer()
        self.top_revealer.set_halign(Gtk.Align.END)
        self.top_revealer.set_valign(Gtk.Align.START)
        self.top_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        hbox.pack_start(self.top_revealer, True, True, 0)

        delete_button = Gtk.Button.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU)
        delete_button.connect("enter-notify-event", self._enter_cb)
        delete_button.connect("clicked", lambda b: self.emit("delete"))
        self.top_revealer.add(delete_button)
        self.top_revealer.set_reveal_child(False)

        self.show_all()

    def _enter_cb(self, canvas, event):
        if self._timeout_leave is None:
            self.top_revealer.set_reveal_child(True)
            self.top_revealer.show_all()

        else:
            GLib.source_remove(self._timeout_leave)
            self._timeout_leave = None

    def _leave_cb(self, canvas, event):
        def hide_revealers(*args):
            self.top_revealer.set_reveal_child(False)
            self._timeout_leave = None

            return GLib.SOURCE_REMOVE

        if self._timeout_leave is not None:
            GLib.source_remove(self._timeout_leave)

        self._timeout_leave = GLib.timeout_add(200, hide_revealers, None)

    def get_canvas(self):
        return self.canvas

    def set_index(self, index):
        self.index_label.set_label(str(index))


class CanvasesNotebook(Gtk.Notebook):

    def __init__(self):
        Gtk.Notebook.__init__(self)

        self.canvases = {}

        self._realized = False
        self._canvas_config = None

        self.set_tab_pos(Gtk.PositionType.LEFT)
        self.set_scrollable(True)
        self.connect("realize", self._realize_cb)
        self.connect("switch-page", self._switch_page_cb)
        self.connect("page-reordered", self._page_reordered_cb)

    def _realize_cb(self, notebook):
        self._realized = True

    def _switch_page_cb(self, notebook, canvas, num):
        if num == self.get_n_pages() - 1 and self._realized:
            self.append_page()
            self.set_current_page(self.get_n_pages() - 2)

    def _canvas_changed_cb(self, canvas):
        tab_canvas = self.canvases[canvas].get_canvas()
        tab_canvas.set_pixelmap(canvas.get_pixelmap())

    def _canvas_size_changed_cb(self, canvas):
        tab_canvas = self.canvases[canvas].get_canvas()

        tab_canvas.config._layout_size = canvas.config.layout_size
        tab_canvas.resize()

    def _delete_tab_cb(self, tab):
        idx = self.get_children().index(tab._associated)

        if idx < self.get_n_pages() - 1:
            if idx == self.get_n_pages() - 2:
                self.set_current_page(self.get_n_pages() - 3)

            self.remove_page(idx)
            del self.canvases[tab._associated]

            tab._associated.destroy()
            tab.destroy()

        self.reset_indices()

    def _page_reordered_cb(self, notebook, child, page_num):
        if page_num == len(self.get_children()) - 1:
            self.append_page()

        self.reset_indices()

    def reset_indices(self):
        idx = 1
        for child in self.get_children():
            tab = self.get_tab_label(child)
            tab.set_index(idx)

            idx += 1

    def append_page(self):
        canvas = CanvasContainer(config=self._canvas_config)
        canvas.connect("changed", self._canvas_changed_cb)
        canvas.connect("size-changed", self._canvas_size_changed_cb)

        if self._canvas_config is None:
            self._canvas_config = canvas.canvas.config

        tab = CanvasNotebookTab(canvas)
        tab.set_index(self.get_n_pages() + 1)
        tab.connect("delete", self._delete_tab_cb)

        self.canvases[canvas] = tab

        super().insert_page(canvas, tab, self.get_n_pages())
        self.set_tab_reorderable(canvas, True)

        canvas.show_all()
        tab.show_all()

    def set_tool(self, tool):
        self._canvas_config.tool = tool

    def set_tool_size(self, size):
        self._canvas_config.tool_size = size

    def set_layout_size(self, size):
        self._canvas_config.layout_size = size

    def set_primary_color(self, color):
        self._canvas_config.primary_color = color

    def set_secondary_color(self, color):
        self._canvas_config.secondary_color = color

    def set_zoom(self, zoom):
        self._canvas_config.zoom = zoom

    def get_current_canvas(self):
        return self.get_children()[self.get_current_page()]

    def open_file(self, file):
        current_canvas = self.get_current_canvas()

        if current_canvas.modified:
            self.append_page()

        current_canvas.set_file(file)

    def get_file(self):
        return self._canvas_config.file

    def set_file(self, file, refresh=True):
        if refresh:
            self._canvas_config.file = file

        else:
            self._canvas_config._file = file

    def get_pixelmaps(self):
        pixelmaps = []

        for canvas in self.get_children()[:-1]:
            pixelmaps.append(canvas.get_pixelmap())

        return pixelmaps

    def undo(self):
        self.get_current_canvas().undo()

    def redo(self):
        self.get_current_canvas().redo()
