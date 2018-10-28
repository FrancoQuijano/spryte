#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .utils import Color
from .canvas import Canvas
from .canvas import CanvasContainer

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject


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
                                Gdk.EventMask.BUTTON_RELEASE_MASK)

        self.overlay.connect("enter-notify-event", self._enter_cb)
        self.overlay.connect("leave-notify-event", self._leave_cb)
        self.pack_start(self.overlay, True, True, 0)

        self.canvas = Canvas(pixel_size=1, zoom=300,
                             sprite_width=self._associated.canvas.sprite_width,
                             sprite_height=self._associated.canvas.sprite_height,
                             editable=False)

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

        self.set_tab_pos(Gtk.PositionType.LEFT)
        self.set_scrollable(True)
        self.connect("realize", self._realize_cb)
        self.connect("switch-page", self._switch_page_cb)

    def _realize_cb(self, notebook):
        self._realized = True

    def _switch_page_cb(self, notebook, canvas, num):
        if num == self.get_n_pages() - 1 and self._realized:
            self.append_page()
            self.set_current_page(self.get_n_pages() - 2)

    def _canvas_changed_cb(self, canvas):
        tab_canvas = self.canvases[canvas].get_canvas()
        tab_canvas.set_pixelmap(canvas.get_pixelmap())

    def _delete_tab_cb(self, tab):
        idx = self.get_children().index(tab._associated)

        if idx < self.get_n_pages() - 1:
            self.remove_page(idx)
            del self.canvases[tab._associated]

            tab._associated.destroy()
            tab.destroy()

        idx = 1
        for child in self.get_children():
            tab = self.get_tab_label(child)
            tab.set_index(idx)

            idx += 1

    def append_page(self):
        canvas = CanvasContainer(sprite_width=32, sprite_height=32)
        canvas.connect("changed", self._canvas_changed_cb)

        tab = CanvasNotebookTab(canvas)
        tab.set_index(self.get_n_pages() + 1)
        tab.connect("delete", self._delete_tab_cb)

        self.canvases[canvas] = tab

        super().insert_page(canvas, tab, self.get_n_pages())
        canvas.show_all()
        tab.show_all()

    def set_tool_size(self, size):
        for canvas in self.canvases.keys():
            canvas.set_tool_size(size)

    def set_tool(self, tool):
        for canvas in self.canvases.keys():
            canvas.set_tool(tool)

    def set_primary_color(self, color):
        for canvas in self.canvases.keys():
            canvas.set_primary_color(color)

    def set_secondary_color(self, color):
        for canvas in self.canvases.keys():
            canvas.set_secondary_color(color)

    def set_zoom(self, zoom):
        for canvas in self.canvases.keys():
            canvas.set_zoom(zoom)
