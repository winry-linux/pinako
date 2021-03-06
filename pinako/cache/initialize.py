#!/usr/bin/env python

#   This file is part of Pinako - <http://github.com/winry-linux/pinako>
#
#   Copyright 2017, Joshua Strot <joshua@winrylinux.org>
#
#   Pinako is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Pinako is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Pinako. If not, see <http://www.gnu.org/licenses/>.

from os import makedirs, path, symlink
from shutil import rmtree

def initializeCache(target, branches = ["winry-stable", "winry-testing"]):
    """Initialize a cache with the default files."""

    #Verify and remove cache
    if path.isdir(target):
        print("=> Cache already exists. Are you sure you'd like to remove it?")
        confirmation = input("=[Y/n]> ")

        if confirmation != "n" or confirmation != "N":
            rmtree(target)
        else:
            print("=> Exiting.")
            exit(1)

    #Make new cache
    makedirs("%(target)s" % locals(), exist_ok=True)
    makedirs("%(target)s/pool" % locals(), exist_ok=True)

    #Make branches
    for branch in branches:
            makedirs("%(target)s/%(branch)s" % locals(), exist_ok=True)

def loadFiles(sshClient, target, serverPath, branches = ["winry-stable", "winry-testing"]):
    """Initialize the cache with it's needed directories"""

    #Initialize an empty cache
    initializeCache(target, branches)

    #Grab list of pool files
    poolFiles = sshClient.runCommand("find %(serverPath)s/pool -mindepth 1" % locals())[1].readlines()
    poolFiles = [poolFiles.strip().split("/")[-1] for poolFiles in poolFiles]
    print(poolFiles)

    #Populate the pool
    for file in poolFiles:
        sshClient.down("%(target)s/pool/%(file)s" % locals(), "%(serverPath)s/pool/%(file)s" % locals())

    #Populate the branches
    for branch in branches:
        filesList = sshClient.runCommand("find %(serverPath)s/%(branch)s -mindepth 1 ! -type l" % locals())[1].readlines()
        linksList = sshClient.runCommand("find %(serverPath)s/%(branch)s -mindepth 1 -type l" % locals())[1].readlines()
        filesList = [files.strip() for files in filesList]
        linksList = [links.strip() for links in linksList]

        #Download the databases
        for file in filesList:
            fileName = file.split("/")[-1]
            linkName = fileName.replace(".tar.gz", "")
            sshClient.down("%(target)s/%(branch)s/%(fileName)s" % locals(), file)

            #Make symbolic links for the databases
            if fileName != ".htaccess":
                symlink("%(fileName)s" % locals(), "%(target)s/%(branch)s/%(linkName)s" % locals())

        for file in linksList:
            fileName = file.split("/")[-1]
            if file.endswith(".xz") or file.endswith(".sig"):
                symlink("../../pool/%(fileName)s" % locals(), "%(target)s/%(branch)s/%(fileName)s" % locals())
