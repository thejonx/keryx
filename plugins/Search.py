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
from lib import consts, log, plugins, project

PLUGIN_NAME = 'Search'
PLUGIN_TYPE = 'Interface'
PLUGIN_VERSION = '1.0'
PLUGIN_AUTHOR = 'Chris Oliver <excid3@gmail.com>'

class Search(plugins.pluginBase):
    def start(self):
        #self.pane = wx.Panel(self.app.notebook, -1, style=wx.TAB_TRAVERSAL) # Create a new pane
        #index = self.app.notebook.GetImageList().Add(wx.Bitmap(consts.icon_find)) # Add an icon for the tab

        #TODO: Advanced search menu entry
        
        #menubar = self.app.GetMenuBar()
        #menuindex = menubar.FindMenu(_("&Edit"))
        #self.menu = menubar.GetMenu(menuindex)
        #self.editSearch = wx.MenuItem(self.menu, wx.NewId(), _("&Search\tCtrl-S"), _("Open search tab"), wx.ITEM_NORMAL)
        #self.editSearch.SetBitmap(wx.Bitmap(consts.icon_find))
        #self.menu.InsertItem(0, self.editSearch)
        #self.separator = self.menu.InsertSeparator(1)

        # Quick search in toolbar
        self.quick_search = wx.SearchCtrl(self.app.buttonPanel, style=wx.TE_PROCESS_ENTER)
        self.quick_search.ShowSearchButton(True)
        self.quick_search.ShowCancelButton(True)
        self.app.buttonPanel.GetSizer().Add(self.quick_search, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
        self.app.buttonPanel.Fit()
        self.app.Bind(wx.EVT_TEXT, self.OnQuickSearch, self.quick_search)
        self.app.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnQuickSearch, self.quick_search)
        self.app.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnQuickCancel, self.quick_search)
        
        # Search in notebook page
        #self.search = wx.SearchCtrl(self.pane, size=(200,-1), style=wx.TE_PROCESS_ENTER)
        #self.search.ShowSearchButton(True)
        #self.search.ShowCancelButton(True)

        #sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        #sizer_1 = wx.BoxSizer(wx.VERTICAL)
        #static = wx.StaticText(self.pane, label=_("Press Enter to start search"))
        #sizer_1.Add(static, 0, wx.ALL, 3)
        #sizer_1.Add(self.search, 0, wx.ALL, 3)
        #sizer.Add(sizer_1, 0, wx.ALIGN_CENTER, 0)

        # Create checkboxes
        #sb = wx.StaticBox(self.pane, -1, _("Included Results"))
        #box = wx.StaticBoxSizer(sb, wx.VERTICAL)
        #self.cbName = wx.CheckBox(self.pane, -1, _("Name"))
        #self.cbName.SetValue(True)
        #box.Add(self.cbName, 0, wx.ALL, 3)
        #self.cbDesc = wx.CheckBox(self.pane, -1, _("Description"))
        #self.cbDesc.SetValue(True)
        #box.Add(self.cbDesc, 0, wx.ALL, 3)
        #self.cbVer = wx.CheckBox(self.pane, -1, _("Version"))
        #box.Add(self.cbVer, 0, wx.ALL, 3)

        #sizer.Add(box, 0, wx.ALIGN_CENTER, 0)

        #self.pane.SetSizer(sizer)
        #self.app.notebook.AddPage(self.pane, _("Search"), False, index) # Add the pane

        # Set event bindings
        #self.app.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch, self.search)
        #self.app.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel, self.search)
        #self.app.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch, self.search)
        #self.app.notebook.GetTopLevelParent().Bind(wx.EVT_MENU, self.OnSearchMenu, self.editSearch)

#    def OnSearchMenu(self, evt):
#        for i in range(self.app.notebook.GetPageCount()): # Find the page and select it
#            if self.app.notebook.GetPageText(i) == _("Search"): self.app.notebook.SetSelection(i)

#    def OnSearch(self, evt):
#        self.OnDoSearch(None)
            
#    def OnCancel(self, evt):
#        self.search.SetValue("")
#        self.OnDoSearch(None)

    def OnQuickCancel(self, evt):
        self.quick_search.SetValue('')
        self.OnQuickSearch(None)

    def OnQuickSearch(self, evt):
        value = str(self.quick_search.GetValue())
        if value == "": self.app.list.SetMap(project.projects[len(project.projects) -1].packages) # Set full list
        else: # partial list
            dict = {}
            for i in project.projects[0].packages.iteritems():
                if (not i[0].find(value) == -1) or (not i[1][4].find(value) == -1) or (not i[1][2].find(value) == -1) or (not i[1][3].find(value) == -1): 
                    dict[i[0]] = i[1] # Keep entry
            self.app.list.SetMap(dict) # Show sorted list
        self.app.list.SortListItems(1, 1)

#    def OnDoSearch(self, evt):
#        value = str(self.search.GetValue())
#        if value == "": self.app.list.SetMap(project.projects[0].packages) # Set full list
#        else: # partial list
#            dict = {}
            
#            for i in project.projects[0].packages.iteritems():
#                if (self.cbName.IsChecked() == True and not i[0].find(value) == -1) or (self.cbDesc.IsChecked() == True and not i[1][4].find(value) == -1) or (self.cbVer.IsChecked() == True and (not i[1][2].find(value) == -1 or not i[1][3].find(value) == -1)): 
                # Found substring in key name
                # Found substring in description
                # Found substring in version
#                    dict[i[0]] = i[1] # Keep entry
                    
#            self.app.list.SetMap(dict) # Show sorted list
#        self.app.list.SortListItems(1, 1)
            
    def cleanup(self):
        #self.editSearch.Destroy()
        self.quick_search.Destroy()
        #self.menu.DeleteItem(self.editSearch)
        #self.menu.DeleteItem(self.separator)
        #for i in range(self.app.notebook.GetPageCount()): # Find the page and select it
        #    if self.app.notebook.GetPageText(i) == _("Search"):
        #        self.app.notebook.RemovePage(i)
        #        break


#########################################               
#            Gather with me             #
#     With the death of your sons       #
# Release your rage in this silent cage #
#             Born of fits              #
#         That engage outrage           #
#                       -John Gleissner #
#########################################
