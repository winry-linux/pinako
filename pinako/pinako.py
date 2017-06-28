#!/usr/bin/env python

#   This file is part of Pinako - <http://github.com/joshuastrot/pinako>
#
#   Copyright 2017, Joshua Strot <joshuastrot@gmail.com>
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

import argparse

from sys import argv
from os import geteuid, symlink

from display import *
from configure import *
from ssh import *
from cache import *

#Exit if root
if geteuid() == 0:
    print("This program cannot be ran as root")
    exit(0)

#Set up the argument parser, add the needed options
parser = argparse.ArgumentParser(description='Control the central repository of Winry Linux.')
parserGroup = parser.add_mutually_exclusive_group()
parserGroup.add_argument('-i', "--init", type=str, metavar="PATH", help="Initialize the cache at the given absolute path")
parserGroup.add_argument('-d', "--download", action="store_true", help="Download changes from repository")
parserGroup.add_argument('-s', "--show", action="store_true", help="Show the currently staged changes")
parserGroup.add_argument('-v', "--verify", action="store_true", help="Verify the repository is safe to upload")
parserGroup.add_argument('-u', "--upload", action="store_true", help="Upload current repository changes")
parserGroup.add_argument('-m', "--merge", action="store_true", help="Merge one branch into another")
parserGroup.add_argument('-c', "--compare", action="store_true", help="Compare one branch to another")

#Output help if no argument is passed, exit
if len(argv) == 1:
    parser.print_help()
    exit(1)

#Display the banner
asciiArt.banner()

#Parse args
args=parser.parse_args()

#Load the configuration file
configurationData = configurationFile.loadConfiguration()

#Begin running the main program
if args.init:
    targetDirectory = args.init

    #Instantiate the SSHClient object
    sshClient = sshClient.sshClient(configurationData["Username"], configurationData["ServerAddress"], configurationData["SSHKey"])

    #Load all the files for the cache
    initialize.loadFiles(sshClient, targetDirectory, configurationData["Branches"], configurationData["Architectures"])

    #Write the new cache location
    configurationFile.writeConfiguration(targetDirectory, configurationData)

elif args.download:
    targetDirectory = configurationData["Cache"]

    #Instantiate the SSHClient object
    sshClient = sshClient.sshClient(configurationData["Username"], configurationData["ServerAddress"], configurationData["SSHKey"])

    #Load all the files for the Cache
    initialize.loadFiles(sshClient, targetDirectory, configurationData["Branches"], configurationData["Architectures"])

elif args.show:
    targetDirectory = configurationData["Cache"]

    #Search the cache for new files
    search.regular(targetDirectory, configurationData["Branches"], configurationData["Architectures"])

elif args.verify:
    targetDirectory = configurationData["Cache"]

    #Verify the repository
    safe = search.verifyRepository(targetDirectory, configurationData["Branches"], configurationData["Architectures"])

    if not safe:
        print("=> Repository is not safe!")
    else:
        print("=> Repository appears safe. Use your best judgement though.")

elif args.upload:
    targetDirectory = configurationData["Cache"]

    #Make sure the cache is safe
    safe = search.verifyRepository(targetDirectory, configurationData["Branches"], configurationData["Architectures"])

    if not safe:
        print("=> Repository is not safe!")
        exit(1)
    else:
        print("=> Repository appears safe. Use your best judgement though.")

    #Find list of new packages
    newFiles = search.regular(targetDirectory, configurationData["Branches"], configurationData["Architectures"])

    if not newFiles:
        print("=> Nothing to do!")
        #exit(1)

    #Move new files to pool and make new symlinks
    prepare.prepareCache(targetDirectory, newFiles, configurationData["Branches"], configurationData["Architectures"])

    #Regenerate the DB's
    prepare.generateDB(targetDirectory, configurationData["Branches"], configurationData["Architectures"])

    #Update the state file
    prepare.modifyState(targetDirectory, configurationData["PackagerName"], configurationData["PackagerEmail"])

    #Compress to tar
    prepare.compress(targetDirectory)

    #Instantiate the SSHClient object
    sshClient = sshClient.sshClient(configurationData["Username"], configurationData["ServerAddress"], configurationData["SSHKey"])

    #Update the server 
    updateServer.updateServer(sshClient, configurationData["Branches"], configurationData["PackagerName"], configurationData["PackagerEmail"])
