#!/usr/bin/env python3

import argparse
import json
from pathlib import Path, PurePath
import string
import sys
import xml.etree.ElementTree as ET
import os


def getEnvironment(environment):
    environmentString = "unknown"

    if(environment=="test"):
        environmentString = "TestName"
    if(environment=="prod"):
        environmentString = "FileName"
    
    return environmentString

def getExtension(device, subtype):
    extension = "unknown"

    if(device=="d7500"):
        if(subtype=="nef"):
            extension = "nef"

    if(device=="iphone-x"):
        if(subtype=="jpeg"):
            extension = "jpeg"
        if(subtype=="mov"):
            extension = "mov"

    return extension

def getOperation(device, subtype):
    operation = "unknown"

    if(device=="d7500"):
        if(subtype=="nef"):
            operation = "-_ENV_<Pe_${DateTimeOriginal}_TaO__SESSION__$filename"
    if(device=="iphone-x"):
        if(subtype=="jpeg"):
            operation = "-_ENV_<Pe_${FileModifyDate}_TaO__SESSION__$filename"
        if(subtype=="mov"):
            operation = "-_ENV_<Pe_${CreationDate}_TaO__SESSION__$filename"
    
    return operation

parser = argparse.ArgumentParser(description='Change name of files based on device, filetype and EXIF data.')
parser.add_argument("-p", help="Change name of files", action='store_true', dest='prod')
parser.add_argument("-t", help="Display name of files", action='store_false', dest='prod')
parser.add_argument("--doit", help="Perform name change", action='store_true', dest='doit')
parser.add_argument("--nodebug", help="Hide debug messages", action='store_false', dest='debug')
parser.add_argument("device", help="d7500, iphone-x")
parser.add_argument("subtype", help="d7500(nef), iphone-x(jpeg.mov)")
parser.add_argument("session", help="Session")
parser.add_argument("path", help="Path")
args = parser.parse_args()
prod = args.prod
device = args.device
subtype = args.subtype
session = args.session
path = args.path
doit = args.doit
debug= args.debug
if(debug):
    print("prod:{}, device:{}, subtype:{}, doit:{}, debug:{}".format(prod, device, subtype, doit, debug))
extension = getExtension(device, subtype)
if(extension=="unknown"):
    exit("Device {} and subtype {} has no extension defined.".format(device, subtype))
operation = getOperation(device, subtype)
if(operation=="unknown"):
    exit("Device {} and subtype {} has no operation defined.".format(device, subtype))
if(debug):
    print("extension={}, operation={}".format(extension, operation))
op = operation.replace("_SESSION_", session)
if(prod):
    op = op.replace("_ENV_", "FileName")
else:
    op = op.replace("_ENV_", "TestName")
if(debug):
    print("op={}".format(op))

cmd = "exiftool -d %y%m%d '{}' -ext {} {}".format(op, extension, path)
if(debug):
    print("cmd={}".format(cmd))

if(doit):
    os.system(cmd)

