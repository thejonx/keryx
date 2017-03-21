# This script is based off of mac9416's QuickRepo.py script
# with some behavioral changes made by jacseen
#
# Designed for use with Keryx 0.92.x
#

import sys, os, os.path, shutil
from gzip import GzipFile
from optparse import OptionParser

parser = OptionParser(description='%prog uses a set of package lists to assemble a debian repository structure from a pile of packages. Designed for use with Keryx inside \'projects/<projectname>\'.')

parser.add_option('-l', '--lists', dest='listdir', default='./lists', metavar='DIR', help='Dir from which the lists are to be loaded. [default: %default]')
parser.add_option('-p', '--pkgs', dest='packdir', default='./packages', metavar='DIR', help='Dir of packages to process. [default: %default]')
parser.add_option('-r', '--repo', dest='repodir', default='./quick_repo', metavar='DIR', help='Dir for the repo. Will be added to if it exists, created if not. [default: %default]')
parser.add_option('-m', action='store_true', dest='move', default=False, help='Move the packages to the repo. Always deletes source deb, even if not \'-o\'. Default is to copy packages.')
parser.add_option('-o', action='store_true', dest='overwrite', default=False, help='If packages already exist in repo, they will overwritten. Default is to leave packages untouched.')

(options, args) = parser.parse_args()
options.listdir = os.path.abspath(options.listdir)
options.packdir = os.path.abspath(options.packdir)
options.repodir = os.path.abspath(options.repodir)

if not os.path.isdir(options.listdir): parser.error('There is somethin\' wrong with you, son! You don\'t even have a %s directory. Make sure that you are running this script from within an APT-type Keryx project.' % options.listdir)
if not os.path.isdir(options.packdir): parser.error('What\'s this?! I can\'t find the %s directory. Try running this script from within an APT-type Keryx project.' % options.packdir)

listfiles = os.listdir(options.listdir)
packfiles = os.listdir(options.packdir)

for i in listfiles[:]:
    if (not i.endswith('Packages')) or (i.startswith('_')): listfiles.remove(i)


def stripDotCom(text):
    append = False
    final = ''
    for item in text.split('_'):
        if item == 'dists': append = True
        if append:
            final = os.path.join(final, item)
    return final

def splitPacks(text):
    filename = ''
    packs = {}
    for block in text.split('\n\n'):
        for line in block.split('\n'):
            if line.startswith('Filename: '):
                filename = line[10:]
        if filename != '':
            packs.update({filename:block})
    return packs

def sendFile(src, dest, move):
    if not move:                                                            # If user wanted the package copied...
        print "Copying: " + os.path.split(pack[0])[-1] + "..."              # Then copy the deb into the repo.
        shutil.copy(src, dest)
    else:                                                                   # If user wanted package moved...
        print "Moving: " + os.path.split(pack[0])[-1] + "..."               # then move deb and delete src
        shutil.move(src, dest)
    return

count = 0
lists = {}
for filename in listfiles:
    try:
        listfile = open(os.path.join(options.listdir, filename), 'rb')
    except:
        print "Well, that list just wouldn't load: " + filename
        continue
    packs = splitPacks(listfile.read()) # splitPacks returns {packfilename:packtext, etc.}
    listfile.close()
    if lists.has_key(stripDotCom(filename)):       # If a list located in the same part of the repo has already been scanned...
        lists[stripDotCom(filename)].update(packs) # Simply add the current data to that file.
    else:                                          # Else...
        lists.update({stripDotCom(filename):packs})# Add the new list!
    countdup = len(lists[stripDotCom(filename)]) - len(packs)
    count += 1
    print "Loaded", count, "of", len(listfiles), "lists ->", str(len(packs)), "more packages,", str(countdup), "duplicates."

for packlist in lists.iteritems():
    packlisttext = ""
    dirlist = os.path.abspath(os.path.join(options.repodir, packlist[0]))
    for pack in packlist[1].iteritems():
        dirpack = os.path.abspath(os.path.join(options.repodir, pack[0]))
        packname = os.path.split(pack[0])[-1]
        if packname in packfiles:                                               # If the file from the index file is in the packages directory...
            if not os.path.exists(dirpack):                                     # If the package does not already exist in repo,
                packlisttext += (pack[1] + '\n\n')                              # add the files' info to the new index file,
                if not os.path.exists(os.path.dirname(dirpack)):                # and check if directory needs to be created.
                    try:
                        os.makedirs(os.path.dirname(dirpack))                   # If the destination dir doesn't exist, create it.
                        print "Creating dir: " + os.path.dirname(pack[0])
                    except:
                        print "Failed creating dir: " + os.path.dirname(pack[0])
                        pass
                sendFile(os.path.join(options.packdir, packname), dirpack, options.move)
            else:                                                               # Package already exists in repo
                if options.overwrite:
                    sendFile(os.path.join(options.packdir, packname), dirpack, options.move)
                else:
                    if options.move:
                        print 'File exists ' + packname + ', deleting...'
                        os.remove(os.path.join(options.packdir, packname))
            packfiles.remove(packname)
    if packlisttext != '':                                            # Only bother with the Packages.gz file if there is a reason
        if not os.path.exists(os.path.dirname(dirlist)): 
            try:
                os.makedirs(os.path.dirname(dirlist))
                print "Creating dir: " + os.path.dirname(packlist[0])
            except:
                print "Failed creating dir: " + os.path.dirname(packlist[0])
                pass
        print "Writing file: " + packlist[0] + '.gz'
        packlistfile = file(dirlist + '.gz', 'ab')           # If repo already has this Packages.gz file then add the new files to it.
        gzfile = GzipFile(dirlist, 'ab', 9, packlistfile)
        gzfile.write(packlisttext)
        gzfile.close()
        packlistfile.close()

