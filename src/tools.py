#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .utils import ToolType, Color


class Tool(object):

    def __init__(self, name, tool_type):

        self.name = name
        self.type = tool_type
        self.button = None
        self.icon = self._get_icon_path()

    def _get_icon_path(self):
        return ToolType.ICONS.get(self.type, None)

    def _get_color(self, primary, secondary, color):
        if color == Color.PRIMARY:
            return primary

        else:
            return secondary

    def apply(self, canvas, coords, color=Color.PRIMARY, primary=None, secondary=None):
        pass

    def get_selected_pixels(self, canvas, x, y):
        pixels = [(x, y)]

        if not ToolType.is_resizable(self.type):
            return pixels

        if canvas.config.tool_size >= 2:
            # La X es donde está el mouse
            # ---------
            # | X | 1 |
            # |---|---|
            # | 3 | 2 |
            # ---------
            pixels.extend([(x + 1, y),      # 1
                           (x + 1, y + 1),  # 2
                           (x, y + 1)])     # 3

        if canvas.config.tool_size >= 3:
            # La X es donde está el mouse
            # -------------
            # | 4 | 5 | 6 |
            # |---|---|---|
            # | 7 | X | 1 |
            # |---|---|---|
            # | 8 | 2 | 3 |
            # .............
            pixels.extend([(x - 1, y - 1),   # 4
                           (x, y - 1),       # 5
                           (x + 1, y - 1),   # 6
                           (x - 1, y),       # 7
                           (x - 1, y + 1)])  # 8

        if canvas.config.tool_size == 4:
            # La X es donde está el mouse
            # -----------------
            # | 4 | 5 | 6 | 9 |
            # |---|---|---|---|
            # | 7 | X | 1 | 10|
            # |---|---|---|---|
            # | 8 | 2 | 3 | 11|
            # |---|---|---|---|
            # | 12| 13| 14| 15|
            # -----------------
            pixels.extend([(x + 2, y - 1),   # 9
                           (x + 2, y),       # 10
                           (x + 2, y + 1),   # 11
                           (x - 1, y + 2),   # 12
                           (x, y + 2),       # 13
                           (x + 1, y + 2),   # 14
                           (x + 2, y + 2)])  # 15

        return pixels


class Pencil(Tool):

    def __init__(self):
        Tool.__init__(self, "Pencil", ToolType.PENCIL)

    def apply(self, canvas, coords, color=Color.PRIMARY, primary=None, secondary=None):
        new_color = self._get_color(primary, secondary, color)
        for x, y in coords:
            canvas.pixelmap.set_temp_pixel_color(x, y, new_color)

        return True


class VerticalMirrorPencil(Tool):

    def __init__(self):
        Tool.__init__(self, "Vertical mirror pencil", ToolType.VERTICAL_MIRROR_PENCIL)

    def apply(self, canvas, coords, color=Color.PRIMARY, primary=None, secondary=None):
        return Pencil.apply(self, canvas, coords, color, primary, secondary)

    def get_selected_pixels(self, canvas, x, y):
        pixels = super().get_selected_pixels(canvas, x, y)

        for x, y in pixels:
            mx = canvas.config.layout_size[0] - x + 1
            if (mx, y) not in pixels:
                pixels.append((mx, y))

        return pixels


class Bucket(Tool):

    def __init__(self):
        Tool.__init__(self, "Bucket", ToolType.BUCKET)

    def _flood_fill(self, pixelmap, x, y, current_color, new_color):
        if current_color == new_color:
            return

        if x > 1 and pixelmap.get_pixel_color(x - 1, y) == current_color and pixelmap.get_temp_pixel_color(x - 1, y) == Color.TRANSPARENT:
            pixelmap.set_temp_pixel_color(x - 1, y, new_color)
            self._flood_fill(pixelmap, x - 1, y, current_color, new_color)

        if x < pixelmap.width and pixelmap.get_pixel_color(x + 1, y) == current_color and pixelmap.get_temp_pixel_color(x + 1, y) == Color.TRANSPARENT:
            pixelmap.set_temp_pixel_color(x + 1, y, new_color)
            self._flood_fill(pixelmap, x + 1, y, current_color, new_color)

        if y > 1 and pixelmap.get_pixel_color(x, y - 1) == current_color and pixelmap.get_temp_pixel_color(x, y - 1) == Color.TRANSPARENT:
            pixelmap.set_temp_pixel_color(x, y - 1, new_color)
            self._flood_fill(pixelmap, x, y - 1, current_color, new_color)

        if y < pixelmap.height and  pixelmap.get_pixel_color(x, y + 1) == current_color and pixelmap.get_temp_pixel_color(x, y + 1) == Color.TRANSPARENT:
            pixelmap.set_temp_pixel_color(x, y + 1, new_color)
            self._flood_fill(pixelmap, x, y + 1, current_color, new_color)

    def apply(self, canvas, coords, color=Color.PRIMARY, primary=None, secondary=None):
        x, y = 0, 1

        _color = self._get_color(primary, secondary, color)

        for coord in coords:
            current_pixel = canvas._selected_pixels[0]
            current_color = canvas.pixelmap.get_pixel_color(*current_pixel)
            canvas.pixelmap.set_temp_pixel_color(coord[x], coord[y], _color)
            self._flood_fill(canvas.pixelmap, coord[x], coord[y], current_color, _color)

        return True


class SpecialBucket(Tool):

    def __init__(self):
        Tool.__init__(self, "Special bucket", ToolType.SPECIAL_BUCKET)

    def apply(self, canvas, coords, color=Color.PRIMARY, primary=None, secondary=None):
        current_pixel = canvas._selected_pixels[0]
        current_color = canvas.pixelmap.get_pixel_color(*current_pixel)
        new_color = self._get_color(primary, secondary, color)

        if current_color == new_color:
            return

        if current_color != Color.TRANSPARENT:
            for pixel in canvas.pixelmap.pixels:
                if canvas.pixelmap.get_pixel_color(pixel.x, pixel.y) == current_color:
                    canvas.pixelmap.set_temp_pixel_color(pixel.x, pixel.y, new_color)

        else:
            for x in range(1, canvas.pixelmap.width + 1):
                for y in range(1, canvas.pixelmap.height + 1):
                    if canvas.pixelmap.get_pixel_color(x, y) == Color.TRANSPARENT:
                        canvas.pixelmap.set_temp_pixel_color(x, y, new_color)

        return True


class Eraser(Tool):

    def __init__(self):
        Tool.__init__(self, "Eraser", ToolType.ERASER)

    def apply(self, canvas, coords, color=Color.PRIMARY, primary=None, secondary=None):
        for x, y in coords:
            canvas.pixelmap.set_temp_pixel_color(x, y, Color.TRANSPARENT)

        return True


class Rectangle(Tool):

    def __init__(self):
        Tool.__init__(self, "Rectangle", ToolType.RECTANGLE)

    def apply(self, canvas, coords, color=Color.PRIMARY, primary=None, secondary=None):
        _color = self._get_color(primary, secondary, color)

        start = canvas.get_relative_coords(*canvas._click_mouse_position)
        end = canvas.get_relative_coords(*canvas._mouse_position)

        if start[0] >= end[0] and start[1] >= end[1]:
            resp = end
            end = start
            start = resp

        elif start[0] > end[0] and start[1] <= end[1]:
            resp1 = (end[0], start[1])
            resp2 = (start[0], end[1])

            start = resp1
            end = resp2

        elif start[0] < end[0] and start[1] >= end[1]:
            resp1 = (start[0], end[1])
            resp2 = (end[0], start[1])

            start = resp1
            end = resp2

        temp_pixels = []

        for x in range(start[0], end[0] + 1):
            for y in range(start[1], end[1] + 1):
                if x + 1 > start[0] + canvas.config.tool_size and \
                   x - 1 < end[0] - canvas.config.tool_size and \
                   y + 1 > start[1] + canvas.config.tool_size and \
                   y - 1 < end[1] - canvas.config.tool_size:

                   continue

                canvas.pixelmap.set_temp_pixel_color(x, y, _color)

        return True


class Stroke(Tool):

    def __init__(self):
        Tool.__init__(self, "Stroke", ToolType.STROKE)

    def _get_useful_pixels(self, canvas):
        """
        Devuelve la mínima cantidad de píxeles necesarios
        para aplicar la herramienta stroke (cuando canvas.config.tool_size
        es igual a 3 o 4, para un tool_size de 1 o 2 no es necesaria la
        optimización). Aún así, esta optimización parece no ser suficiente.
        """

        start = canvas.get_relative_coords(*canvas._click_mouse_position)
        end = canvas.get_relative_coords(*canvas._mouse_position)

        x1, y1 = start
        x2, y2 = end

        start_points = []
        end_points = []
        # -----------------
        # | 4 | 5 | 6 | 9 |
        # |---|---|---|---|
        # | 7 | X | 1 | 10|
        # |---|---|---|---|
        # | 8 | 2 | 3 | 11|
        # |---|---|---|---|
        # | 12| 13| 14| 15|
        # -----------------

        if canvas.config.tool_size <= 2:
            # Si es de 1x1 o 2x2 no hay gran pérdida de rendimiento
            start_points = canvas.get_selected_pixels(canvas._click_mouse_position)
            end_points = canvas.get_selected_pixels(canvas._mouse_position)

        elif canvas.config.tool_size == 3:
            if x1 > x2 and y1 > y2:
                start_points = [
                    (x1 + 1, y1 - 1),
                    (x1 + 1, y1),
                    (x1 + 1, y1 + 1),
                    (x1, y1 + 1),
                    (x1 - 1, y1 + 1),
                ]

                end_points = [
                    (x2 + 1, y2 - 1),
                    (x2, y2 - 1),
                    (x2 - 1, y2 - 1),
                    (x2 - 1, y2),
                    (x2 - 1, y2 + 1),
                ]

            elif x1 > x2 and y1 < y2:
                start_points = [
                    (x1 - 1, y1 - 1),
                    (x1, y1 - 1),
                    (x1 + 1, y1 -1),
                    (x1 + 1, y1),
                    (x1 + 1, y1 + 1),
                ]

                end_points = [
                    (x2 - 1, y2 - 1),
                    (x2 - 1, y2),
                    (x2 - 1, y2 + 1),
                    (x2, y2 + 1),
                    (x2 + 1, y2 + 1)
                ]

            elif x1 < x2 and y1 > y2:
                start_points = [
                    (x1 - 1, y1 - 1),
                    (x1 - 1, y1),
                    (x1 - 1, y1 + 1),
                    (x1, y1 + 1),
                    (x1 + 1, y1 + 1)
                ]

                end_points = [
                    (x2 - 1, y2 - 1),
                    (x2, y2 - 1),
                    (x2 + 1, y2 -1),
                    (x2 + 1, y2),
                    (x2 + 1, y2 + 1),
                ]

            elif x1 < x2 and y1 < y2:
                start_points = [
                    (x1 + 1, y1 - 1),
                    (x1, y1 - 1),
                    (x1 - 1, y1 - 1),
                    (x1 - 1, y1),
                    (x1 - 1, y1 + 1),
                ]

                end_points = [
                    (x2 + 1, y2 - 1),
                    (x2 + 1, y2),
                    (x2 + 1, y2 + 1),
                    (x2, y2 + 1),
                    (x2 - 1, y2 + 1),
                ]

            elif y1 == y2 and x1 >= x2:
                start_points = [(x1 + 1, y1 + i) for i in range(-1, 2)]
                end_points = [(x2 - 1, y2 + i) for i in range(-1, 2)]

            elif y1 == y2 and x1 < x2:
                start_points = [(x1 - 1, y1 + i) for i in range(-1, 2)]
                end_points = [(x2 + 1, y2 + i) for i in range(-1, 2)]

            elif x1 == x2 and y1 > y2:
                start_points = [(x1 + i, y1 + 1) for i in range(-1, 2)]
                end_points = [(x2 + i, y2 - 1) for i in range(-1, 2)]

            elif x1 == x2 and y1 < y2:
                start_points = [(x1 + i, y1 - 1) for i in range(-1, 2)]
                end_points = [(x2 + i, y2 + 1) for i in range(-1, 2)]

        else:
        #elif self.config.tool_size == 4:
            if x1 > x2 and y1 > y2:
                start_points = [
                    (x1 + 2, y1 - 1),
                    (x1 + 2, y1),
                    (x1 + 2, y1 + 1),
                    (x1 + 2, y1 + 2),
                    (x1 + 1, y1 + 2),
                    (x1, y1 + 2),
                    (x1 - 1, y1 + 2)
                ]

                end_points = [
                    (x2 + 2, y2 - 1),
                    (x2 + 1, y2 - 1),
                    (x2, y2 - 1),
                    (x2 - 1, y2 - 1),
                    (x2 - 1, y2),
                    (x2 - 1, y2 + 1),
                    (x2 - 1, y2 + 2)
                ]

            elif x1 > x2 and y1 < y2:
                start_points = [
                    (x1 - 1, y1 - 1),
                    (x1, y1 - 1),
                    (x1 + 1, y1 - 1),
                    (x1 + 2, y1 - 1),
                    (x1 + 2, y1),
                    (x1 + 2, y1 + 1),
                    (x1 + 2, y1 + 2),
                ]

                end_points = [
                    (x2 - 1, y2 - 1),
                    (x2 - 1, y2),
                    (x2 - 1, y2 + 1),
                    (x2 - 1, y2 + 2),
                    (x2, y2 + 2),
                    (x2 + 1, y2 + 2),
                    (x2 + 2, y2 + 2),
                ]

            elif x1 < x2 and y1 > y2:
                start_points = [
                    (x1 - 1, y1 - 1),
                    (x1 - 1, y1),
                    (x1 - 1, y1 + 1),
                    (x1 - 1, y1 + 2),
                    (x1, y1 + 2),
                    (x1 + 1, y1 + 2),
                    (x1 + 2, y1 + 2)
                ]

                end_points = [
                    (x2 - 1, y2 - 1),
                    (x2, y2 - 1),
                    (x2 + 1, y2 - 1),
                    (x2 + 2, y2 - 1),
                    (x2 + 2, y2),
                    (x2 + 2, y2 + 1),
                    (x2 + 2, y2 + 2)
                ]

            elif x1 < x2 and y1 < y2:
                start_points = [
                    (x1 + 2, y1 - 1),
                    (x1 + 1, y1 - 1),
                    (x1, y1 - 1),
                    (x1 - 1, y1 - 1),
                    (x1 - 1, y1),
                    (x1 - 1, y1 + 1),
                    (x1 - 1, y1 + 2),
                ]

                end_points = [
                    (x2 + 2, y2 - 1),
                    (x2 + 2, y2),
                    (x2 + 2, y2 + 1),
                    (x2 + 2, y2 + 2),
                    (x2 + 1, y2 + 2),
                    (x2, y2 + 2),
                    (x2 - 1, y2 + 2),
                ]

            elif y1 == y2 and x1 >= x2:
                start_points = [(x1 + 2, y1 + i) for i in range(-1, 3)]
                end_points = [(x2 - 1, y1 + i) for i in range(-1, 3)]

            elif y1 == y2 and x1 < x2:
                start_points = [(x1 - 1, y1 + i) for i in range(-1, 3)]
                end_points = [(x2 + 2, y1 + i) for i in range(-1, 3)]

            elif x1 == x2 and y1 > y2:
                start_points = [(x1 + i, y1 + 2) for i in range(-1, 3)]
                end_points = [(x2 + i, y2 - 1) for i in range(-1, 3)]

            elif x1 == x2 and y1 < y2:
                start_points = [(x1 + i, y1 - 1) for i in range(-1, 3)]
                end_points = [(x2 + i, y2 + 2) for i in range(-1, 3)]

        return start_points, end_points

    def _draw_line(self, pixelmap, x0, y0, x1, y1, color):
        """
        Algorítmo basado en el pseudocódigo de:
        https://es.wikipedia.org/wiki/Algoritmo_de_Bresenham#Descripci%C3%B3n
        """

        if x0 != x1:
            delta_y = (y1 - y0)
            delta_x = (x1 - x0)

            if delta_y >= 0:
                inclinacion_y_i = 1

            else:
                delta_y = - delta_y
                inclinacion_y_i = -1

            if delta_x >= 0:
                inclinacion_x_i = 1

            else:
                delta_x = -delta_x
                inclinacion_x_i = -1

            if delta_x >= delta_y:
                avance_y_recto = 0
                avance_x_recto = inclinacion_x_i

            else:
                avance_x_recto = 0
                avance_y_recto = inclinacion_y_i

                k = delta_x
                delta_x = delta_y
                delta_y = k

            x = x0
            y = y0

            avR = (2 * delta_y)
            av = (avR - delta_x)
            avI = (av - delta_x)

            while x != x1:
                pixelmap.set_temp_pixel_color(x, y, color)

                if av >= 0:
                    x += inclinacion_x_i
                    y += inclinacion_y_i
                    av += avI

                else:
                    x += avance_x_recto
                    y += avance_y_recto
                    av += avR

            if y != y1:
                # En algunas situaciones no se pintan los píxeles en la
                # columna del pixel final
                for _y in range(min(y, y1), max(y, y1) + 1):
                    pixelmap.set_temp_pixel_color(x, _y, color)

            # El último pixel siempre se pinta
            pixelmap.set_temp_pixel_color(x1, y1, color)

        else:
            for y in range(min(y0, y1), max(y0, y1) + 1):
                pixelmap.set_temp_pixel_color(x0, y, color)

    def apply(self, canvas, coords, color=Color.PRIMARY, primary=None, secondary=None):
        start_points, end_points = self._get_useful_pixels(canvas)
        _color = self._get_color(primary, secondary, color)

        for i in range(0, len(start_points)):
            x0, y0 = start_points[i]
            x1, y1 = end_points[i]

            self._draw_line(canvas.pixelmap, x0, y0, x1, y1, _color)

        return True


class ColorPicker(Tool):

    def __init__(self):
        Tool.__init__(self, "Color picker", ToolType.COLOR_PICKER)

    def apply(self, canvas, coords, color=Color.PRIMARY, primary=None, secondary=None):
        x, y = coords[0]
        cairo_color = canvas.pixelmap.get_pixel_color(x, y)

        if color == Color.PRIMARY:
            canvas.emit("primary-color-picked", cairo_color)

        elif color == Color.SECONDARY:
            canvas.emit("secondary-color-picked", cairo_color)


class Dithering(Tool):

    def __init__(self):
        Tool.__init__(self, "Dithering", ToolType.DITHERING)

    def apply(self, canvas, coords, color=Color.PRIMARY, primary=None, secondary=None):
        for x, y in coords:
            if (x + y) % 2 == 0:
                canvas.pixelmap.set_temp_pixel_color(x, y,
                    canvas.config.primary_color if color == Color.PRIMARY else canvas.config.secondary_color)

            else:
                canvas.pixelmap.set_temp_pixel_color(x, y,
                    canvas.config.secondary_color if color == Color.PRIMARY else canvas.config.primary_color)

        return True


TOOLS = {
    ToolType.PENCIL: Pencil(),
    ToolType.VERTICAL_MIRROR_PENCIL: VerticalMirrorPencil(),
    ToolType.BUCKET: Bucket(),
    ToolType.SPECIAL_BUCKET: SpecialBucket(),
    ToolType.ERASER: Eraser(),
    ToolType.RECTANGLE: Rectangle(),
    ToolType.STROKE: Stroke(),
    # ToolType.MOVE: (),
    # ToolType.CIRCLE: (),
    # ToolType.RECTANGLE_SELECTION: (),
    # ToolType.SHAPE_SELECTION: (),
    # ToolType.LIGHTEN: (),
    # ToolType.LASSO_SELECTION: (),
    ToolType.COLOR_PICKER: ColorPicker(),
    ToolType.DITHERING: Dithering(),
}
