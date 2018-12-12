#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .canvases_notebook import CanvasesNotebook

from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import GObject


class FileNotebookTab(Gtk.Box):

    __gsignals__ = {
        "close": (GObject.SIGNAL_RUN_LAST, None, []),
    }

    def __init__(self, associated_notebook):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)

        self._associated_notebook = associated_notebook
        self._canvas_config = self._associated_notebook._canvas_config
        self._canvas_config.connect("modified", self._modified_changed_cb)

        self._text = "Untitled"

        self.set_size_request(150, 1)

        self.label = Gtk.Label()
        self.label.set_text(self._text)
        self.label.set_ellipsize(Pango.EllipsizeMode.END)
        self.pack_start(self.label, False, False, 0)

        self._close_button = Gtk.Button.new_from_icon_name(
            "window-close-symbolic", Gtk.IconSize.MENU)
        self._close_button.set_relief(Gtk.ReliefStyle.NONE)
        self._close_button.connect("clicked", self._close_button_clicked_cb)
        self.pack_end(self._close_button, False, False, 0)

    def set_label(self, text, bold=False):
        self._text = text
        if bold:
            text = "<b>%s</b>" % self._text

        self.label.set_markup(text)

    def _modified_changed_cb(self, modified):
        self.set_label(self._text, modified)

    def _close_button_clicked_cb(self, button):
        self.emit("close")


class FilesNotebook(Gtk.Notebook):

    __gsignals__ = {
        "save-before-closing": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT]),
        "primary-color-picked": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT]),
        "secondary-color-picked": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT]),
    }

    def __init__(self):
        Gtk.Notebook.__init__(self)

        self.notebooks = {}

        self.set_tab_pos(Gtk.PositionType.BOTTOM)

        new_tab_button = Gtk.Button.new_from_icon_name(
            "list-add-symbolic", Gtk.IconSize.MENU)
        new_tab_button.connect("clicked", lambda btn: self.append_page())
        self.set_action_widget(new_tab_button, Gtk.PackType.END)
        new_tab_button.show_all()

    def _primary_color_picked_cb(self, canvas, color):
        self.emit("primary-color-picked", color)

    def _secondary_color_picked_cb(self, canvas, color):
        self.emit("secondary-color-picked", color)

    def _close_tab_cb(self, tab):
        self.remove_page(tab._associated_notebook)

    def append_page(self):
        notebook = CanvasesNotebook()
        notebook.append_page()
        notebook.append_page()
        notebook.connect("primary-color-picked", self._primary_color_picked_cb)
        notebook.connect("secondary-color-picked", self._secondary_color_picked_cb)

        tab = FileNotebookTab(notebook)
        tab.connect("close", self._close_tab_cb)
        self.notebooks[notebook] = tab

        super().insert_page(notebook, tab, self.get_n_pages())
        self.set_tab_reorderable(notebook, True)

        notebook.show_all()
        tab.show_all()

        self.set_current_page(-1)

    def show_remove_page_warning(self, notebook):
        idx = self.get_children().index(notebook)
        self.set_current_page(idx)

        file = notebook._canvas_config.file
        filename = os.path.basename(file) if file is not None else "New file"

        dialog = Gtk.Dialog(
            "",
            self.get_toplevel(),
            0
        )

        close_button = Gtk.Button.new_from_icon_name("window-close-symbolic",
            Gtk.IconSize.BUTTON)
        close_button.set_label("Close without saving")
        dialog.add_action_widget(close_button, Gtk.ResponseType.CLOSE)

        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.YES)
        dialog.set_default_response(Gtk.ResponseType.YES)

        box = dialog.get_content_area()
        label = Gtk.Label("Save changes to %s before closing?" % filename)
        box.add(label)
        box.show_all()

        response = dialog.run()
        dialog.destroy()  # No quiero que el diálogo se quede en el fondo
                          # en caso de que el usuario elija guardar

        if response == Gtk.ResponseType.YES:
            self.emit("save-before-closing", notebook)

        elif response == Gtk.ResponseType.CLOSE:
            self.remove_page(notebook, force=True)

    def remove_page(self, notebook, force=False):
        if notebook._canvas_config.modified and not force:
            self.show_remove_page_warning(notebook)

        else:
            idx = self.get_children().index(notebook)
            super().remove_page(idx)

        if self.get_n_pages() == 0:
            self.append_page()

    def get_current_notebook(self):
        return self.get_children()[self.get_current_page()]

    def set_filename(self, file, index=None):
        if index is None:
            index = self.get_current_page()

        self.notebooks[self.get_children()[index]].set_label(file)
