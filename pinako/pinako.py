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
from os import geteuid, system, path

from display import *
from fileUtilities import *
from networking import *

#Exit if root
if geteuid() == 0:
    print("This program cannot be ran as root")
    exit(0)

#Set up the argument parser, add the needed options
parser = argparse.ArgumentParser(description='Control the central repository of Winry Linux.')
parser.add_argument('-i', "--init", type=str, metavar="PATH", help="Initialize the cache at the given absolute path")
parser.add_argument('-p', "--print", action="store_true", help="Show the currently staged changes")
parser.add_argument('-u', "--upload", action="store_true", help="Upload current repository changes")
parser.add_argument('-d', "--download", action="store_true", help="Download changes from repository")
parser.add_argument('-m', "--merge", action="store_true", help="Merge one branch into another")
parser.add_argument('-c', "--compare", action="store_true", help="Compare one branch to another")

#Output help if no argument is passed, exit
if len(argv) == 1:
    parser.print_help()
    exit(1)

#Display the banner
asciiArt.banner()

#Parse args
args=parser.parse_args()

#Load the configuration file
configurationData = configuration.loadConfiguration()

#Evaluate command line options and run the program
if args.init:
    #Make sure the cache path is absolute
    if not path.isabs(args.init):
        print("=> Error! Please use an absolute path for the cache")
        exit(1)

    #Set up the cache
    print("=> Creating cache directories")
    cacheOperations.createCache(args.init)

    #Configure the configuration file
    configuration.writeConfiguration(args.init, configurationData)

    #Establish an SSH connection
    sshClient = sshOperations.connect(configurationData["Username"], configurationData["ServerAddress"], configurationData["SSHKey"])

    #Load all the directories in the cache
    print("=> Populating the cache with dummy files")
    for branch in configurationData["Branches"]:
        cacheOperations.updateCache(sshClient, branch, args.init)

    exit(0)