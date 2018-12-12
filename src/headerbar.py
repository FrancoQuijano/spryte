#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .canvas import CanvasConfig
from .utils import gtk_version_newer_than

from gi.repository import Gtk
from gi.repository import GObject


class HeaderBar(Gtk.HeaderBar):

    __gsignals__ = {
        "tool-size-changed": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_INT]),
        "layout-size-changed": (GObject.SIGNAL_RUN_LAST, None, [GObject.TYPE_PYOBJECT]),
    }

    def __init__(self):
        super(HeaderBar, self).__init__()

        self._layout_size = list(CanvasConfig.DEFAULT_LAYOUT_SIZE)

        self.set_show_close_button(True)
        self._create_tool_size_buttons()

        self.options_button = Gtk.ToggleButton()
        self.options_button.connect("toggled", self._options_button_toggled_cb)
        self.pack_end(self.options_button)

        image = Gtk.Image.new_from_icon_name("open-menu-symbolic",
                                             Gtk.IconSize.BUTTON)
        self.options_button.set_image(image)

        self._create_options_popover()

    def _options_button_toggled_cb(self, button):
        if self.options_button.get_active():
            self.options_popover.show_all()

            if gtk_version_newer_than(3, 22):
                self.options_popover.popup()

            else:
                self.options_popover.show_now()

    def _options_popover_closed_cb(self, popover):
        self.options_button.set_active(False)

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

    def _create_options_popover(self):
        self.options_popover = Gtk.Popover()
        self.options_popover.set_position(Gtk.PositionType.BOTTOM)
        self.options_popover.set_relative_to(self.options_button)
        self.options_popover.connect("closed", self._options_popover_closed_cb)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.set_size_request(250, 1)
        vbox.set_margin_top(4)
        vbox.set_margin_bottom(4)
        vbox.set_margin_start(4)
        vbox.set_margin_end(4)
        self.options_popover.add(vbox)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(row, False, False, 0)

        label = Gtk.Label.new("Ancho:")
        row.pack_start(label, False, False, 0)

        default_width, default_height = self._layout_size

        width_spinner = Gtk.SpinButton.new_with_range(1, 1024, 1)
        width_spinner.set_value(default_width)
        row.pack_end(width_spinner, False, False, 0)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(row, False, False, 0)

        label = Gtk.Label.new("Alto:")
        row.pack_start(label, False, False, 0)

        height_spinner = Gtk.SpinButton.new_with_range(1, 1024, 1)
        height_spinner.set_value(default_height)
        row.pack_end(height_spinner, False, False, 0)

        width_spinner.connect("value-changed", self._layout_size_changed, 0)
        height_spinner.connect("value-changed", self._layout_size_changed, 1)

    def _tool_size_changed(self, button, size):
        self.emit("tool-size-changed", size)

    def _layout_size_changed(self, widget, index):
        """
        Esta función se modificó porque en versiones antiguas de Gtk al
        parecer había un bug en el cual no se podía usar un objeto
        heredado de Gtk.Widget como parámetro. En este caso, width_spinner
        y height_spinner llegaban de la forma (notar el nil en la dirección
        de memoria):
        <Gtk.SpinButton object at 0x7fd2ed97bca8 (uninitialized at 0x(nil))>

        Cuando deberían llegar de la forma:
        <Gtk.SpinButton object at 0x7fd2ec39d750 (GtkSpinButton at 0x1b2a540)>

        Por lo que al intentar llamar la función get_value en cualquiera
        de estos dos parámtros se recibía:
        (spryte.py:6715): Gtk-CRITICAL **: gtk_spin_button_get_value: assertion
        'GTK_IS_SPIN_BUTTON (spin_button)' failed
        """

        self._layout_size[index] = int(widget.get_value())
        self.emit("layout-size-changed", tuple(self._layout_size))
