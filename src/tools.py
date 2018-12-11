#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils import ToolType


class Tool(object):

    def __init__(self, name, tool_type):

        self.name = name
        self.type = tool_type
        self.button = None
        self.icon = self._get_icon_path()

    def _get_icon_path(self):
        return ToolType.ICONS.get(self.type, None)

    def apply(self, canvas, primary=None, secondary=None):
        pass


class Pencil(Tool):

    def __init__(self):
        Tool.__init__(self, "Pencil", ToolType.PENCIL)

    def apply(self, canvas, primary=None, secondary=None):
        pass
