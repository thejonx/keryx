#!/usr/bin/env python
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

# Import commands here, even though we don't use it because debian.py uses it
# and our plugin system confuses pyinstaller. We need to manually specify this
# in keryx so that pyinstaller can grab it and bundle the code

# Import modules to satisfy plugin dependencies:
import commands

# Then import everything else.
import os
import sys

from lib import consts

#####################
# Set configuration #
#####################
if ('--config' in sys.argv): # If config is specified
    index = sys.argv.index('--config')
    try: filename = sys.argv[index + 1]
    except: 
        print 'ERROR: No config filename given'
        sys.exit(1)
        
    
    # Reinitialize consts if the a specific file has been passed
    import lib.config
    lib.config.fromFile(filename)

# Else if file_config exists, load it
elif os.path.exists(consts.file_config):
    import lib.config
    lib.config.fromFile(consts.file_config)
    
# Import log and project AFTER configuration has been set
from lib import log, project

################
# Translations #
################
try:
    import gettext
    import locale
    gettext.install(consts.appNameShort, consts.dirLocale, unicode=True)
    
    lang = locale.getdefaultlocale()[0]
    lang = gettext.translation(consts.appNameShort, consts.dirLocale, languages=[lang])
    lang.install()
except: pass

#TODO: Set wxWidgets translation information
 
###################
# Parse arguments #
###################
if ('--help' in sys.argv) or ('-h' in sys.argv):
    log.info(consts.parameters)
    sys.exit(0)

if ('--version' in sys.argv) or ('-v' in sys.argv):
    log.info('%s %s' % (consts.appName, consts.appVersion))
    sys.exit(0)

if ('--create' in sys.argv):
    import platform
    from lib import plugins, project
    try:
        index = sys.argv.index('--create')
        name = sys.argv[index + 1]
        plugin_name = 'debian'
    except:
        log.error(_('Unable to create project'))
        sys.exit(1)
    plugins.load(consts.dirPlugins, '', False) # Don't load interface plugins
    for item in range(0,len(plugins.OSPluginList)):
        if plugin_name == plugins.OSPluginList[item][0].lower():
            # Append new project
            project.projects.append(project.Project())
            proj = project.projects[len(project.projects) - 1]
    
            # Create project
            success, filename = proj.CreateKeryx(name, 
                                            plugins.OSPluginList[item][0],
                                            plugins.OSPluginList[item][1])

            if success: 
                log.info(_('Project created successfully.'))
                sys.exit(0)
    log.error(_('Unable to create project.'))
    log.info(_('Make sure a project by this name does not already exist and you have selected the right plugin for this project.'))
    sys.exit(1)


WXVER = "2.8"

if not hasattr(sys, "frozen"):  # If this isn't a compiled version of Keryx...
    import wxversion
    if wxversion.checkInstalled(WXVER):
        wxversion.select(WXVER)
    else:
        import wx
        app = wx.PySimpleApp()
        wx.MessageBox("Warning: The requested version of wxPython is not installed.\n"
                      "Please install version %s" % WXVER,
                      "wxPython Version Warning")
        app.MainLoop()

#############################
# Attempt to load interface #
#############################
#try:
if 1:
    import lib.wxkeryx
    lib.wxkeryx.Start()
#except Exception, e:
    #print e
#    log.error(_('Unable to load interface.'))
#    log.info(_('Make sure you have wxPython installed.'))
#    log.info(_('Read the README for details on installing wxPython'))
#    log.info(_('You can you \'python keryx.py --create\' to create a new project through the command-line if you do not have wxPython installed'))
#    log.info(_('Use \'python keryx.py --help\' to see all command-line parameters.'))
#    sys.exit(1)
