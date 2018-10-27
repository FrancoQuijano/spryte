#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division


class Color:

    PRIMARY = 1
    SECONDARY = 2

    @classmethod
    def gdk_to_cairo(self, color, alpha=65535):
        return (color.red / 65535,
                color.green / 65535,
                color.blue / 65535,
                alpha / 65535)
