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

import commands
import gzip
import os
import platform
import shutil
import struct

import lib
from lib import plugins, consts, log

PLUGIN_NAME = 'Debian'
PLUGIN_TYPE = 'OS'
PLUGIN_VERSION = '0.92.4'
PLUGIN_AUTHOR = 'Chris Oliver <excid3@gmail.com>'

FILE = 'debian.conf'

class Debian(plugins.pluginBase):
    def IsOS(self): 
        """Returns bool if current OS uses APT"""
        if os.path.exists('/etc/apt/'):     
            return True
        else:
            return False

    def createProject(self, name): 
        """Creates project files"""
        dirNew = os.path.join(consts.dirProjects, name)

        #try:
        if 1:
            # Set information
            info = self.__setInfo()
            self.__grabFiles(name, dirNew)

            outfile = open(os.path.join(dirNew, FILE), 'wb')
            outfile.write('%s: %s\n' % (_('Computer Name'), info[0]) + \
                            '%s: %s\n' % (_('OS Name'), info[1]) + \
                            '%s: %s\n' % (_('OS Version'), info[2]) + \
                            '%s: %s\n' % (_('Architecture'), info[3]) + \
                            '%s: %s\n' % (_('Kernel'), info[4]))
            outfile.close()

            return True
        # except:
        #    log.error(_('Problem writing to project settings file'))
        return False

    def loadProject(self, directory):
        infile = open(os.path.join(directory, FILE), 'rb')
        data = infile.read()
        infile.close()
        data = data.split()

        return [data[2], data[5], data[8], data[10], data[12]]

    def loadLocalPackageList(self, dir, arch):
        listDir = os.path.join(dir, 'lists')
        debs = self.__parseSources(dir)
        filenames = self.__filesFromDebs(debs, arch)
        installed = self.__getInstalled(dir)

        # Initialize vars
        packages = {}

        for item in filenames:
            try:
                data = open(os.path.join(listDir, item), 'rb')
                url = 'http://%s' % item.split('_dists')[0].replace('_','/')
                # Append all packages to list
                packages = self.__readPackages(data, installed, packages, url)  
            except Exception, exc:
                log.error(_('Unable to open file: ') + str(exc))
                
        return packages

    def loadInternetPackageList(self, dir, arch):
        listDir = os.path.join(dir, "lists")
        debs = self.__parseSources(dir)
        #TODO: extract hashes for list files from Release files
        # and 'return zip(urls, tempnames, checksums)' instead
        tempnames = self.__tempFilesFromDebs(debs, arch, listDir)
        urls = self.__urlsFromDebs(debs, arch)

        return zip(urls, tempnames)  # Returns urls, gzip file locations

    def getDependencies(self, dir, allPackages, packageName):
        """Takes package name and returns package information for each 
        dependency (recursive)
        """
        urls = []
        if not allPackages.has_key(packageName): 
            return {}
        values = allPackages.get(packageName)
        dependencies = values[5].split(", ")
        dependencies += values[8].split(", ")  # Apt-get treats recommends as dependencies
        dependencies += values[9].split(", ")  # pre-depends are important too
        filename = values[6].split("/")  # Get the parts for the package filename
        urls.append((values[6], os.path.join(dir, filename[len(filename)-1]), values[10]))
        values[2] = values[3]
        allPackages[packageName] = values

        for item in dependencies:
            data = item.split()
            if not data == []:
                # Get dependencies for this package too if it isnt already installed
                if allPackages.has_key(data[0]) and not allPackages.get(data[0])[2]:
                    urls += self.getDependencies(dir, allPackages, data[0])

        return urls

    def getSources(self, dir):
        """Returns filename of main sources file"""
        return os.path.join(os.path.join(dir, 'sources'), 'sources.list')

    def installCache(self, projdir, scriptname, move=False):
        """Transfers index files to the APT cache. 
        Uses sh script called as 'root'
        """
        packsdir = os.path.join(projdir, 'packages')
        # Make sure there are packages to install
        if not os.path.exists(packsdir):
            log.error(_("%s does not exist: no packages to be installed") % \
                        (packsdir))
            return False
        # If we're missing the partial dir, APT will throw a fit.
        partialdir = os.path.join(packsdir, 'partial')
        if not os.path.exists(partialdir):
            os.mkdir(partialdir)

        scriptpath = os.path.join(projdir, '%s.sh' % scriptname)
        bin = '#!/bin/sh -'
        spacks = [x for x in os.listdir(packsdir) if os.path.isfile(os.path.join(packsdir, x)) and (os.path.splitext(x)[1] == '.deb')]
        packnames = ' '.join([x[:x.find('_')] for x in spacks])
        content = bin+"""\n#
# Keryx 0.92.4 install script
#
# Used to transfer the necessary files back to a computer
# from a project so that the downloaded packages can
# be installed.
#
# Usage installcache.sh [<project directory>] ['-move']
#
# written by jacseen, class=amateur :)
# http://keryxproject.org   mailto:keryx@lists.launchpad.net

if [ -n "$1" ] && [ -e "$1" ]
then
    proj="$1"
    shift
else
    proj="$(pwd)"
fi
cd "$proj"

if [ -n "$1" ] && [ "$1" = "-move" ]
then
    transfer="mov"
else
    transfer="copy"
fi

slists=lists
tlists=/var/lib/apt/lists
ssources=sources
tsources=/etc/apt

#Find all index files, skipping the 'status' files and copy them
cd ./"$slists"/
if [ ! $? = 0 ] #if cannot cd into lists, not project dir
then
    echo "Not project dir: $(pwd)"
    exit 65
fi
filelist=`find -maxdepth 1 -iname '*_dists_*'`

#TODO:attain lock on folder $tlists to be package-manager-friendly
# will be attained directly with python in later versions

for fn in $filelist
do
    cp -t "$tlists" "$fn"
    if [ ! $? = 0 ]
    then
        echo "Failure when copying list: $fn"
        exit 66
    fi
done

#TODO:release lock on folder $tlists

### Debs will no longer be moved to the cache. The downloads directory will ###
### Be made Temporary cache. ###

# Find all downloaded packages and move to cache
# cd ../"$spacks"/
# filelist=`find -maxdepth 1 -name '*.deb'`

# TODO:attain lock on folder $tpacks to be package-manager-friendly
# will be attained directly with python in later versions

#TODO:release lock on folder $tpacks

#Update the main sources.list file in case it was changed in keryx

cd ../"$ssources"/
cp -t "$tsources" "sources.list"
if [ ! $? = 0 ]
then
    echo "Failure when copying sources.list"
    exit 68
fi

# Update the APT caches with the latest lists
apt-cache gencaches

exit 0"""
        try:
            script = open(scriptpath, 'wb')
            script.write(content)
            script.close()
        except:
            log.error(_('installCache: Could not write the script %s') % scriptpath)
            return False

        if move:
            transfer='-move'
        else:
            transfer=''

        log.info(_('installCache: launching script as root'))
        run = self.__runRoot('sh', '%s %s %s' % (scriptpath,  projdir, transfer))
        if run[0] != 0:
            log.error('exit code:%i\n%s' % (run[0], run[1]))
            log.info(_('installCache: failed'))
            return False
        log.info(_('installCache: transfer success'))
        return True

    def installPacks(self, projdir, packnames):
        packsdir = os.path.join(projdir, 'packages')
        run = self.__runRoot('apt-get', '-y -o dir::cache::archives=\"%s\" ' \
                    'install %s; echo \"Press [ENTER] to exit.\"; ' \
                    'read x' % (packsdir, packnames))
        if run[0] != 0:
            log.error(_('exit code:%i\n%s' % (run[0], run[1])))
            log.info(_('Failed run package installation as root'))
            return False
        log.info(_('installCache: success'))
        return True

    def installRepo(self):
        """Transfers all downloaded packages into a Repository and updates the 
        OS about it, then tells it to install them. Uses script called as 'root'
        """
        return True

    def updateStatus(self, outdir, infile="/var/lib/dpkg/status"):
        """Update the project's status file (list of installed packages)"""
        lists_dir = os.path.join(outdir, 'lists')
        outfile = os.path.join(lists_dir, "status")
        outfilebak = os.path.join(lists_dir, "status.bak")
        # Back up the current status file.
        run = self.__runRoot('cp', '%s %s' % (outfile, outfilebak))
        # Copy in the new status file.
        run = self.__runRoot('cp', '%s %s' % (infile, outfile))
        #TODO: check for error from 'cp', return False
        return True  # Everything went well.

    def __readPackages(self, infile, installed, packages, mainUrl=''):
        # up-to-date, name, installed ver, latest ver, descrip, depends, 
        # filename, size(int)
        current = ['','','','','','','','','','',{}]

        for line in infile:
            if line.startswith("Package:"):     current[1] = line[9:-1]
            if line.startswith("Version:"):     current[3] = line[9:-1]
            if line.startswith("Description:"): current[4] = lib.utf(line[13:-1])
            if line.startswith("Depends:"):     current[5] = line[9:-1]
            if line.startswith("Filename:"):    current[6] = lib.joinUrl(mainUrl, line[10:-1])
            if line.startswith("Size:"):        current[7] = int(line[6:-1])
            if line.startswith("Recommends:"):  current[8] = line[12:-1]
            if line.startswith("Pre-Depends:"): current[9] = line[13:-1]
            if line.startswith("MD5sum:"):      current[10].update({'MD5sum':line[8:-1]})
            if line.startswith("SHA1:"):        current[10].update({'SHA1':line[6:-1]})
            if line.startswith("SHA256:"):      current[10].update({'SHA256':line[8:-1]})

            if line.startswith("\n") and current[1] != '': # Finished reading this package, append it
                self.__updatePackage(current, installed, packages) # Set the packages installed version
                current = ['','','','','','','','','','',{}]

        return packages

    def __updatePackage(self, package, installed, packages):
        """Sets package information"""
        version = version_compare() # Initialize version comparison class

        if packages.has_key(package[1]):  # Package already exists so update values if need be
            if version.compare(packages[package[1]][3], package[3]) == 2: 
                return  # If it's an older one, skip it

        # Update installed version
        for item in installed:
            if package[1] == item[0]:
                #Compare version numbers, set icon accordingly
                # 0 # up-to-date
                # 1 # update
                # 2 # error
                package[0] = version.compare(item[1], package[3])
                package[2] = item[1]  # Set the installed version

        packages[package[1]] = package  # Set package info

    def __setInfo(self): 
        """Sets the Debian project info"""
        uname = platform.uname()
        comp_name = uname[1]

        # platform.architecture works when run from source, but when compiled
        # it always returns 32-bit.
        #os_arch = platform.architecture()[0]

        apt_version = commands.getoutput('apt-get -v')
        first_line = apt_version.split('\n')[0]
        if 'i386' in first_line:
            os_arch = '32bit'
        elif 'amd64' in first_line:
            os_arch = '64bit'
        else:
            log.error(_('unable to detect architecture. Defaulting to 32-bit. ' \
                        'If this is incorrect, edit your project\'s debian.conf.'))
            os_arch = '32bit'

        os_kern = uname[2]
        try:
            status = commands.getstatusoutput('cat /etc/issue.net')
            if status[0] != 0: log.error(_('Problem retrieving Debian version'))
            temp = status[1].split()
            os_name = temp[0]
            os_ver = temp[1]
        except:
            os_name = os_ver = _('Unknown')
        return [comp_name, os_name, os_ver, os_arch, os_kern]

    def __grabFiles(self, name, folder): 
        """Grabs files necessary for a Debian project"""
        dirLists = os.path.join(folder, 'lists')
        dirSources = os.path.join(folder, 'sources')

        try:    
            shutil.copytree('/etc/apt/', dirSources)
        except: 
            pass # Will always raise errors because some files are only readable by root
        try:    
            shutil.copytree('/var/lib/apt/lists/', dirLists)
        except: 
            try: os.mkdir(dirLists)
            except OSError: pass  # The directory probably already exists
        shutil.copyfile('/var/lib/dpkg/status', os.path.join(dirLists,'status'))
        shutil.copyfile('/var/lib/dpkg/status', os.path.join(dirLists,'status.bak'))

    def __parseSources(self, dir): 
        """Returns list of all deb entries for project"""
        sources = []
        sourcesDir = os.path.join(dir, 'sources')

        # Parse main source file
        main_source = os.path.join(sourcesDir, 'sources.list')
        if os.path.exists(main_source):
            sources += self.__parseFile(main_source)

        # Parse extra source files
        sourcesdDir = os.path.join(sourcesDir, 'sources.list.d')
        if os.path.exists(sourcesdDir):
            sourcesd = os.listdir(sourcesdDir)
            for item in sourcesd:
                if item.endswith('.list'): sources += self.__parseFile(os.path.join(sourcesdDir, item))
    
        return sources

    def __parseFile(self, location): 
        """Returns a sepcific file's deb entries"""
        found = []
        infile = open(location)
        for line in infile:
            if line.startswith('deb http://'):  #TODO: Add support for more protocols
                if line.endswith('\n'): found.append(line[:-1])
                else:                   found.append(line)
        return found

    def __filesFromDebs(self, deblist, arch, dir=''):
        """Generates a list of files from deb entries"""
        local = []
        for item in deblist:
            data = item.split()
            try:
                dtype = data[0]
                url = data[1]
                dist = data[2]
                if len(data) == 3: 
                    pass  #FIXME: Special case, append only the sections to the end
                for section in data[3:]:
                    if section.find('#') != -1: break # If a comment is encountered skip the line
                    main = lib.joinUrl(lib.joinUrl(lib.joinUrl(url, 'dists'), dist), section)
                    main = self.__appendArch(arch, main)
                    main = main[7:-3].replace('/','_')
                    local.append(os.path.join(dir, main)) # Strips unnecessary characters and appends to list
            except: 
                pass # Unable to parse deb entry
        return local

    def __tempFilesFromDebs(self, deblist, arch, dir=''):
        """Generates a list of files from deb entries"""
        local = []
        for item in deblist:
            data = item.split()
            try:
                dtype = data[0]
                url = data[1]
                dist = data[2]
                if len(data) == 3: pass #FIXME: Special case, append only the sections to the end
                for section in data[3:]:
                    if section.find('#') != -1: break # If a comment is encountered skip the line
                    main = lib.joinUrl(lib.joinUrl(lib.joinUrl(url, 'dists'), dist), section)
                    main = self.__appendArch(arch, main)
                    main = main[7:].replace('/','_')
                    local.append(os.path.join(dir, main)) # Strips unnecessary characters and appends to list
            except: pass # Unable to parse deb entry
        return local

    def __urlsFromDebs(self, deblist, arch):
        urls = []
        for item in deblist:
            data = item.split()
            try:
                dtype = data[0]
                url = data[1]
                dist = data[2]
                if len(data) == 3: pass
                for section in data[3:]:
                    if section.find('#') != -1: break
                    main = lib.joinUrl(lib.joinUrl(lib.joinUrl(url, 'dists'), dist), section)
                    main = self.__appendArch(arch, main)
                    urls.append(main)
            except: pass
        return urls


    def __appendArch(self, arch, location): 
        """Appends an architecture to a location"""
        if arch == '32bit': return lib.joinUrl(location, 'binary-i386/Packages.gz')
        elif arch == '64bit': return lib.joinUrl(location, 'binary-amd64/Packages.gz')
        return location

    def __getInstalled(self, dir):
        """Gets a list of installed packages"""
        status = open(os.path.join(os.path.join(dir, 'lists'),'status'), 'rb')

        installed = []
        current = ['', '', ''] # name, version, status
        for line in status:
            if line.startswith('Package:'): current[0] = line[9:-1]
            if line.startswith('Version:'): current[1] = line[9:-1]
            if line.startswith('Status:'):  current[2] = line[8:-1]
            if line.startswith('\n') and current[2] == 'install ok installed':
                installed.append(current)
                current = ['', '', '']

        status.close()
        return installed

    def __runRoot(self, program, args):
        root = ''
        for a in ('pkexec', 'kdesu', 'kdesudo'):
            if commands.getstatusoutput('which '+a)[0] == 0:
                root = a
                break
        if root == '': return (64, 'Could not find superuser access')
        try:
            exit = commands.getstatusoutput('%s %s %s' % \
                                            (root, program, args))
        except:
            exit = (64, 'Error spawning shell command')
        return exit

class version_compare(object):
    def __init__(self):
        pass

    def compare(self, str1, str2):
        version1 = version(str1)
        version2 = version(str2)

        ver_type = ["epoch", "upstream", "debian"]
        test_type = [0, 2, 1]

        parse1 = []
        parse2 = []

        version_list1 = [version1.epoch(), version1.upstream(), version1.debian_version()]
        version_list2 = [version2.epoch(), version2.upstream(), version2.debian_version()]

        for index in range(3):
#            value = test_type[index] # The number scheme had to change because debian changes have priority over non-debian
            equal = self.__compare_info(version_list1[index], version_list2[index], ver_type[index])
            if equal != 0:
                break

        return equal

    def __compare_info(self, string1, string2, ver_type):
        equal = 0
#        print string1,
#        print "   ",
#        print string2,
#        print "    ",
#        print ver_type
        if string1 and string2: # Both strings contain a value
            data = version_parse(string1)
            parse1 = data.parse()
            data = version_parse(string2)
            parse2 = data.parse()

            max = len(parse1)
            if len(parse1) > len(parse2):
                max = len(parse2)
            for count in range(max):  # Go through the parsed list of the version number broken down by type
                compare1 = parse1[count][1]
                type1 = parse1[count][0]
                compare2 = parse2[count][1]
                type2 = parse2[count][0]
#                print max,
#                print "+_++_",
#                print count,
#                print ":> ",
#                print compare1,
#                print "----",
#                print compare2
#                print str(compare1).isalnum()
#                print str(compare2).isalnum()
                if type1 == "alpha"   and type2 == "alpha"     or \
                   type1 == "num"     and type2 == "num"       or \
                   type1 == "delimit" and type2 == "delimit":
                    if compare1 < compare2:
                        equal = 1
                        break
                    elif compare1 > compare2:
                        equal = 2
                        break
                elif type1 == "alpha"   and type2 == "num"     or \
                     type1 == "alpha"   and type2 == "delimit" or \
                     type1 == "alpha"   and type2 == "tilde"   or \
                     type1 == "num"     and type2 == "tilde"   or \
                     type1 == "delimit" and type2 == "num"     or \
                     type1 == "delimit" and type2 == "tilde":
                    equal = 2
                    break
                elif type1 == "num"     and type2 == "alpha"   or \
                     type1 == "num"     and type2 == "delimit" or \
                     type1 == "tilde"   and type2 == "alpha"   or \
                     type1 == "tilde"   and type2 == "num"     or \
                     type1 == "tilde"   and type2 == "delimit" or \
                     type1 == "delimit" and type2 == "alpha":
                    equal = 1
                    break
                elif type1 == "tilde"   and type2 == "tilde":
                    if len(str(compare1)) > len(str(compare2)):  # The more tilde characters, the less its value
                        equal = 1
                        break
                    elif len(str(compare1)) < len(str(compare2)):
                        equal = 2
                        break
            if equal == 0:
                if len(parse1) > max:
                    compare1 = parse1[max][1]
                    type1 = parse1[max][0]
#                    print compare1,
#                    print type1
                    if type1 == "num"   or \
                       type1 == "alpha" or \
                       type1 == "delimit":
                        equal = 2
                    elif type1 == "tilde":
                        equal = 1
                elif len(parse2) > max:
#                    print compare2,
#                    print type2
                    compare2 = parse2[max][1]
                    type2 = parse2[max][0]
                    if type2 == "num"   or \
                       type2 == "alpha" or \
                       type2 == "delimit":
                        equal = 1
                    elif type1 == "tilde":
                        equal = 2

        elif ver_type == "epoch"  and string1 and not string2 or \
             ver_type == "debian" and not string1 and string2:
            equal = 1
        elif ver_type == "debian" and string1 and not string2 or \
             ver_type == "epoch"  and not string1 and string2:
            equal = 2

        return equal

class version_parse(object):
    def __init__(self, string):
        self.string = string

    def parse(self):
        version_list = []

        build_type = "" # Tracks the current string type (num, alpha, delimit, tilde)
        string_val = ""

        for char in self.string:
            if self.__type_changed(build_type, char):
                if build_type: # The build type is not empty (there is a string ready to be appended
                    if string_val.isdigit():
                        version_list.append([build_type, int(string_val)]) # Convert string to integer
                        string_val = ""
                    else:
                        version_list.append([build_type, string_val])
                        string_val = ""
                build_type = self.__get_type(char)
            string_val += char

        if build_type:
            if string_val.isdigit():
                version_list.append([build_type, int(string_val)])
            else:
                version_list.append([build_type, string_val])

        return version_list # retuns a list of [build_type, string_val]

    def __type_changed(self, build_type, char):
        ret_val = False

        if (char.isdigit() and build_type != "num") or \
           (char.isalpha() and build_type != "alpha") or \
           (build_type == "num" and not char.isdigit()) or \
           (build_type == "alpha" and not char.isalpha()) or \
           (build_type == "tilde" and char != "~") or \
           (build_type == "delimit" and (char == "~" or char.isdigit() or char.isalpha())):
            ret_val = True

        return ret_val

    def __get_type(self, char):
        ret_type = ""
        if char.isalpha():
            ret_type = "alpha"
        elif char.isdigit():
            ret_type = "num"
        elif char == "~":
            ret_type = "tilde"
        else:
            ret_type = "delimit"

        return ret_type

class version(object):
    def __init__(self, ver_string):
        self.version = ver_string
        self.epoch_value = self.__get_epoch(self.version)
        upstream_deb = self.__get_upstrdeb(self.version)
        self.upstream_value = upstream_deb[0]
        self.debver_value = upstream_deb[1]

    def epoch(self):
        return self.epoch_value

    def upstream(self):
        return self.upstream_value

    def debian_version(self):
        return self.debver_value

    def __get_epoch(self, str1):
        ret_epoch = []
        epoch = str1.split(":")
        if len(epoch) > 1:
            ret_epoch = epoch[0]

        return ret_epoch

    def __get_upstrdeb(self, str1):
        ver_list = []
        version = str1.split("-")

        debver = ""
        upstream = ""

        if len(version) > 1:
            debver = version[len(version) - 1]
            for index in range(len(version) - 1):
                if index == 0:
                    upstream = version[index]
                else:
                    upstream += "-" + version[index]
        else:
            upstream = str1

        return [upstream, debver]
