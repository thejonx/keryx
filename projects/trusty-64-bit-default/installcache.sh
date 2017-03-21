#!/bin/sh -
#
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

exit 0