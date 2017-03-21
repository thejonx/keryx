# original code from mac9416's script 'QuickRepo.py'
# modified and repurposed by jaseen

import os, os.path, hashlib
#from gzip import GzipFile


listdir   = os.path.join(os.getcwd(), 'lists')
packdir   = os.path.join(os.getcwd(), 'packages')
#hashtype = ('MD5sum: ', 'md5')
hashtype = ('SHA1: ', 'sha1')

if not os.path.exists(listdir):
    print "There is somethin' wrong with you, son! You don't even have a ./lists directory. Make sure that you are running this script from within an APT-type Keryx project.'"
if not os.path.exists(packdir):
    print "What's this?! I can't find a ./packages directory. Make sure that you are running this script from within an APT-type Keryx project."
listfiles = os.listdir(listdir)
packfiles = os.listdir(packdir)

def calcChecksum(filepath):
    try:                            # This code originally found in doubledetector.py from http://sebsauvage.net/python/
        file = open(filepath,'rb')  # some modifications made of course.
        if hashtype[1] == 'md5':
            digest = hashlib.md5()
        elif hashtype[1] == 'sha1':
            digest = hashlib.sha1()
        else:
            return '0'
        data = file.read(65536)
        while len(data) != 0:
            digest.update(data)
            data = file.read(65536)
        file.close()
    except:
        return '0'
    else:
        return digest.hexdigest()


def ParseLists(text):
    filename = ''
    hashsum = ''
    packs = {}
    for block in text.split('\n\n'):
        for line in block.split('\n'):
            if line.startswith('Filename: '):
                filename = os.path.split(line[10:])[-1]
            if line.startswith(hashtype[0]):
                hashsum = line[len(hashtype[0]):]
        if filename != '':
            if hashsum == '':
                print "A file without a '" + hashtype[0] + "', interesting: " + filename
            else:
                packs.update({filename:hashsum})
    return packs

count = 0
lists = {}
for filename in listfiles:
    try:
        listfile = open(os.path.join(listdir, filename), 'rb')
    except:
        print "Well, that list just wouldn't load: " + filename
        continue
    packs = ParseLists(listfile.read()) # ParseLists returns {packfilename:packmd5sum, etc.}
    listfile.close()
    lists.update(packs)         # Add the new list!
    count += 1
    print count, "read of", len(listfiles), "-", len(packs), "more names, ", len(lists), "unique"

packlistsums = 0
failed = 0
nocalc = 0
listsorted = sorted(lists.iterkeys())
for key in listsorted:
    if key in packfiles: # If the file from the index file is in the packages directory...
        sum = calcChecksum(os.path.join(packdir, key))
        packlistsums += 1
        if sum != lists[key] and sum != '0':
            os.remove(os.path.join(packdir, key))
            print "Failed " + str(key) + ": Removed."
            failed += 1
        elif sum == '0':
            print "Could not calc checksum", key
            nocalc += 1
print "Of", packlistsums, "debs processed,", failed, "failed,", nocalc, "could not be checked."
