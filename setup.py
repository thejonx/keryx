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

from __future__ import with_statement
from distutils.core import setup
from lib import consts
from contextlib import closing
from zipfile import ZipFile, ZIP_DEFLATED
import os, os.path, platform, sys, shutil, tarfile

def zipdir(basedir, archivename):
    assert os.path.isdir(basedir)
    with closing(ZipFile(archivename, "w", ZIP_DEFLATED)) as z:
        for root, dirs, files in os.walk(basedir):
            #NOTE: ignore empty directories
            for fn in files:
                absfn = os.path.join(root, fn)
                zfn = absfn[len(basedir)+len(os.sep):] #XXX: relative path
                z.write(absfn, zfn)



if platform.system() != 'Windows':
    sys.exit(1)

sys.argv.append('py2exe')

try:    
    import py2exe
except:
    print 'You need py2exe installed to build Keryx.'
    sys.exit(1)

binDir = 'bin'
distDir = 'dist'
buildDir = 'build'
ver = '%s_%s' % (consts.appNameShort, consts.appVersion)
winDir = 'win32'
linDir = 'linux'

manifest = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
    <assemblyIdentity version="0.64.1.0" processorArchitecture="x86" 
    name="Controls" type="win32"/>
    <description>%s</description>
    <dependency>
        <dependentAssembly>
            <assemblyIdentity type="win32" 
            name="Microsoft.Windows.Common-Controls" version="6.0.0.0" 
            processorArchitecture="X86" publicKeyToken="6595b64144ccf1df"
            language="*"/>
        </dependentAssembly>
    </dependency>
</assembly>
"""%consts.appName

setupOptions = { 
    'name': consts.appName,
    'author': consts.authors,
    'author_email': consts.email,
    'description': consts.description,
    'version': consts.appVersion,
    'url': consts.urlHomepage,
    'license': consts.license,
    'packages': ['lib', 'lib.wxkeryx'] + 
        [subpackage for subpackage in ('lib', 'lib.wxkeryx')],
    'scripts': ['keryx.py'],
    'zipfile': None,
    }


if __name__ == '__main__':
    #Clean up all .py* files that exist
    print "Cleaning directories"
    for root, dirs, files in os.walk(os.getcwd()):
        for name in files:
            if name.endswith('.pyc') or name.endswith('.pyo'):
                os.remove(os.path.join(root, name))

    if 'clean' in sys.argv: sys.exit()

    setupOptions.update({
        'windows' : [{ 'script' : 'keryx.py', 
            'other_resources' : [(24, 1, manifest)],
            'icon_resources': [(1, 'pixmaps/keryx.ico')]}],
        'options' : {'py2exe' : {
            'bundle_files': 1,
            'compressed' : 1, 
            'optimize' : 2, 
            # We need to explicitly include these packages because they 
            # are imported implicitly:
            'packages' : ['commands', 'gzip', 'win32file'], }}})

    # Begin setup
    setup(**setupOptions)

    # Remove mess py2exe makes
    if sys.argv[1] == 'py2exe':
        shutil.rmtree(os.path.join(os.getcwd(), buildDir))
        #shutil.rmtree(consts.dirLog)
        #shutil.rmtree(consts.dirProjects)
        if os.path.exists(binDir): shutil.rmtree(binDir)

        # Rename and move dist directory
        os.rename(distDir, winDir)
        shutil.move(winDir, os.path.join(os.path.join(binDir, ver),winDir))
       
        # Copy doc dir to bin
        shutil.copytree('doc', os.path.join(os.path.join(binDir, ver), 'doc'))
        shutil.copy('dlls\msvcp71.dll', os.path.join(os.path.join(binDir, ver), winDir))
        shutil.copy('dlls\gdiplus.dll', os.path.join(os.path.join(binDir, ver), winDir))

        # Copy .locale dir
        shutil.copytree('.locale', os.path.join(os.path.join(binDir, ver), '.locale'))

        # Create linux directory
        linDir = os.path.join(os.path.join(binDir, ver), linDir)
        os.mkdir(linDir)
        shutil.copy('keryx.py', linDir)
        shutil.copytree(os.path.join(os.getcwd(), 'lib'), os.path.join(linDir, 'lib'))

        # Copy to release
        shutil.copytree(consts.dirPixmaps, os.path.join(os.path.join(binDir, ver), 'pixmaps'))
        shutil.copytree(consts.dirPlugins, os.path.join(os.path.join(binDir, ver), 'plugins'))
        shutil.copytree('projects', os.path.join(os.path.join(binDir, ver), 'projects'))
        
        # Copy conf
        shutil.copy(os.path.join('doc', 'keryx.conf'), linDir)
        shutil.copy(os.path.join('doc', 'keryx.conf'), os.path.join(os.path.join(binDir, ver), winDir))

        # Build release zip
        zipdir(binDir, '%s.zip' % ver)
        shutil.move('%s.zip' % ver, binDir)
        
        # Build source tarball from linDir
        # Copy pixmaps and plugins to linux dir
        shutil.copytree(consts.dirPixmaps, os.path.join(linDir, 'pixmaps'))
        shutil.copytree(consts.dirPlugins, os.path.join(linDir, 'plugins'))
        shutil.copytree('projects', os.path.join(linDir, 'projects'))
        for x in ['app.fil', 'messages.pot', 'mki18n.py', 'setup.py']:
            shutil.copy(x, linDir)
        for x in ['doc', 'dlls']:
            shutil.copytree(x, os.path.join(linDir, x))
        
        t = tarfile.open(os.path.join(binDir,'%s_src.tar.bz2' % ver), mode='w:bz2')
        t.add(linDir, '%s_src' % ver)
        t.close()

        # We did it! Another fine release!
        print """
#################################################################

Successfully compiled %s %s
Release zip and tarball is located at:
%s

We did it! Another fine release!

PS: If you want to create a Linux binary, use pyinstaller. When 
you have it, replace everything in the linux directory (minus 
keryx.conf) with the binary. Good luck!

#################################################################"""  % \
(consts.appName, consts.appVersion, os.path.abspath(binDir))
