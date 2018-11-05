#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .canvases_notebook import CanvasesNotebook

from gi.repository import Gtk


class FileNotebookTab(Gtk.Box):

    def __init__(self, associated_notebook):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)

        self.associated_notebook = associated_notebook

        self.label = Gtk.Label()
        self.label.set_text("Untitled")
        self.pack_start(self.label, False, False, 0)

        self._close_button = Gtk.Button.new_from_icon_name(
            "window-close-symbolic", Gtk.IconSize.MENU)
        self.pack_end(self._close_button, False, False, 0)

    def set_label(self, text):
        # TODO: Fijar un tamaño maximo a mostrar?
        self.label.set_text(text)


class FilesNotebook(Gtk.Notebook):

    def __init__(self):
        Gtk.Notebook.__init__(self)

        self.notebooks = {}

        self.set_tab_pos(Gtk.PositionType.BOTTOM)

        new_tab_button = Gtk.Button.new_from_icon_name(
            "list-add-symbolic", Gtk.IconSize.MENU)
        new_tab_button.connect("clicked", lambda btn: self.append_page())
        self.set_action_widget(new_tab_button, Gtk.PackType.END)
        new_tab_button.show_all()

    def append_page(self):
        notebook = CanvasesNotebook()
        notebook.append_page()
        notebook.append_page()

        tab = FileNotebookTab(notebook)
        self.notebooks[notebook] = tab

        super().insert_page(notebook, tab, self.get_n_pages())
        self.set_tab_reorderable(notebook, True)

        notebook.show_all()
        tab.show_all()

        self.set_current_page(-1)

    def get_current_notebook(self):
        return self.get_children()[self.get_current_page()]

    def set_filename(self, file, index=None):
        if index is None:
            index = self.get_current_page()

        self.notebooks[self.get_children()[index]].set_label(file)
