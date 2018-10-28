#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .canvas import Canvas
from .canvas import CanvasContainer

from gi.repository import Gtk


class CanvasNotebookTab(Gtk.Box):

    def __init__(self, asociated_canvas):
        Gtk.Box.__init__(self)

        self.set_border_width(5)
        self.set_orientation(Gtk.Orientation.VERTICAL)

        self._asociated = asociated_canvas

        self.canvas = Canvas(pixel_size=1, zoom=300,
                             sprite_width=self._asociated.canvas.sprite_width,
                             sprite_height=self._asociated.canvas.sprite_height,
                             editable=False)

        self.pack_start(self.canvas, False, False, 0)

    def get_canvas(self):
        return self.canvas


class CanvasesNotebook(Gtk.Notebook):

    def __init__(self):
        Gtk.Notebook.__init__(self)

        self.canvases = {}

        self._realized = False

        self.set_tab_pos(Gtk.PositionType.LEFT)
        self.set_scrollable(True)
        self.connect("realize", self._realize_cb)
        self.connect("switch-page", self._switch_page_cb)

        #self._create_new_tab_button()

    def _realize_cb(self, notebook):
        self._realized = True

    def _switch_page_cb(self, notebook, canvas, num):
        if num == self.get_n_pages() - 1 and self._realized:
            self.append_page()
            self.set_current_page(self.get_n_pages() - 2)

    def _canvas_changed_cb(self, canvas):
        tab_canvas = self.canvases[canvas].get_canvas()
        tab_canvas.set_pixelmap(canvas.get_pixelmap())

    def append_page(self):
        canvas = CanvasContainer(sprite_width=32, sprite_height=32)
        canvas.connect("changed", self._canvas_changed_cb)
        tab = CanvasNotebookTab(canvas)

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
