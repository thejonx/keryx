# -*- coding: utf-8 -*-
#
# Author: Chris Oliver (excid3@gmail.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import wx, os
from lib import plugins, consts

PLUGIN_NAME = 'ColorMap'
PLUGIN_TYPE = 'Interface'
PLUGIN_VERSION = '1.0'
PLUGIN_AUTHOR = 'Chris Oliver <excid3@gmail.com>'

class ColorMap(plugins.pluginBase):
    def start(self):
        self.pane = wx.Panel(self.app.notebook, -1, style=wx.TAB_TRAVERSAL) # Create a new pane
        index = self.app.notebook.GetImageList().Add(wx.Bitmap(consts.icon_update)) # Add an icon for the tab

        label_1 = wx.StaticText(self.pane, -1, " - Completely Updated")
        bitmap_1 = wx.StaticBitmap(self.pane, -1, wx.Bitmap(consts.icon_uptodate))
        label_2 = wx.StaticText(self.pane, -1, " - Has Updates")
        bitmap_2 = wx.StaticBitmap(self.pane, -1, wx.Bitmap(consts.icon_update))  
        label_3 = wx.StaticText(self.pane, -1, " - Downloaded")
        bitmap_3 = wx.StaticBitmap(self.pane, -1, wx.Bitmap(consts.icon_downloaded))
        label_4 = wx.StaticText(self.pane, -1, " - Newer Than Repository")
        bitmap_4 = wx.StaticBitmap(self.pane, -1, wx.Bitmap(consts.icon_error))

        # do layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)

        self.add(sizer_2, bitmap_1, label_1)        
        self.add(sizer_2, bitmap_2, label_2)        
        self.add(sizer_2, bitmap_3, label_3)        
        self.add(sizer_2, bitmap_4, label_4)        

        sizer_1.Add(sizer_2, 1, wx.ALIGN_CENTER_HORIZONTAL, 0)
        self.pane.SetSizer(sizer_1)

        # Add the pane
        self.app.notebook.AddPage(self.pane, _("Color Map"), False, index) 

    def add(self, sizer, bitmap, label):
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(bitmap, 0, 0, 0)
        sizer_1.Add(label, 0, 0, 0)
        sizer.Add(sizer_1, 0, 0, 0)

    def cleanup(self):
        for i in range(self.app.notebook.GetPageCount()): # Find the page and select it
            if self.app.notebook.GetPageText(i) == _("Color Map"):
                self.app.notebook.RemovePage(i)
                break
