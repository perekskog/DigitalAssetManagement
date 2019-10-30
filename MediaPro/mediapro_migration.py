#!/usr/bin/env python3

import argparse
import json
from pathlib import Path, PurePath
import string
import sys
import xml.etree.ElementTree as ET

default_headline = '(no headline)'
default_datecreated = '1900-01-01'
default_sender = 'Unmapped sender'


ns = {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
      'role': 'http://characters.example.com',
      'photoshop': 'http://ns.adobe.com/photoshop/1.0/',
      'dc': 'http://purl.org/dc/elements/1.1/',
      'mediapro': 'http://ns.iview-multimedia.com/mediapro/1.0/'}

def get_props(sender_map, xmlfile):
    tree = ET.parse(xmlfile)

    root = tree.getroot()

    # Headline
    nheadline = len(root.findall('./rdf:RDF/rdf:Description/photoshop:Headline',ns))
    headline = ''
    if(nheadline==0):
        sys.stderr.write('{}: ERROR: Missing headline, replaced with {}\n'.format(xmlfile, default_headline))
        if(error_is_fatal):
            sys.exit(-1)
        headline = default_headline
    elif(nheadline>1):
        sys.stderr.write('{}: ERROR: More than 1 headline, replaced with {}\n'.format(xmlfile, default_headline))
        if(error_is_fatal):
            sys.exit(-1)
        headline = default_headline
    else:
        headline = root.find('./rdf:RDF/rdf:Description/photoshop:Headline',ns).text

    # Date created
    ndatecreated = len(root.findall('./rdf:RDF/rdf:Description/photoshop:DateCreated',ns))
    datecreated = ''
    if(ndatecreated==0):
        sys.stderr.write('{}: ERROR: Missing datecreated, replaced with {}\n'.format(xmlfile, default_datecreated))
        if(error_is_fatal):
            sys.exit(-1)
        datecreated = default_datecreated
    elif(ndatecreated>1):
        sys.stderr.write('{}: ERROR: More than 1 datecreated, replaced with {}\n'.format(xmlfile, default_datecreated))
        if(error_is_fatal):
            sys.exit(-1)
        datecreated = default_datecreated
    else:
        datecreated = root.find('./rdf:RDF/rdf:Description/photoshop:DateCreated',ns).text

    # Sender
    # Require either 1 (sender) or two, where first is top level sender (to disregard).
    # No support for several senders.
    sender_text = []
    sender_text_short = []

    senders = root.findall('./rdf:RDF/rdf:Description/dc:subject/rdf:Bag/rdf:li',ns)
    nsenders = len(senders)
    if(nsenders==0):
        sys.stderr.write('{}: ERROR: Missing sender, replaced with {}\n'.format(xmlfile, default_sender))
        if(error_is_fatal):
            sys.exit(-1)
    if(nsenders==1):
        sender_text = senders[0].text
    if(nsenders==2):
        # Prefix (Peer, ...) is in index 0
        sender_text = senders[0].text
    if(nsenders>2):
        sys.stderr.write('{}: ERROR: Too many senders: {}, replaced with {}\n'.format(xmlfile, senders, default_sender))
        if(error_is_fatal):
            sys.exit(-1)
        sender_text = default_sender

    if(sender_text in sender_map):
        sender_text_short = sender_map[sender_text]
    else:
        sys.stderr.write('{}: ERROR: Unmapped sender: {}, replaced with {}\n'.format(xmlfile, sender_text, default_sender))
        if(error_is_fatal):
            sys.exit(-1)
        sender_text_short = default_sender

    categories = root.findall('./rdf:RDF/rdf:Description/mediapro:CatalogSets/rdf:Bag/rdf:li',ns)
    #print(categories)

    categories_text = []
    for category in categories:
        categories_text.append(category.text)

    return (headline, datecreated, sender_text, sender_text_short, categories_text)

def get_new_filename(basedir, file, headline, datecreated, sender_text_short, categories_text):
    categories = ""
    for cat in categories_text:
        categories += "({})".format(cat.lower())

    date_formatted = datecreated.replace('-','')[2:]

    p = Path('{}/{}'.format(basedir, sender_text_short))
    p.mkdir(exist_ok=True)
    newfilename = "{}/{}/{}_{}_{} {}{}".format(basedir, sender_text_short, sender_text_short, date_formatted, headline, categories, file.suffix)
    return newfilename

parser = argparse.ArgumentParser(description='Extract metadata from XMP files \n Extracts headline, datecreated, senders and categories. \n Errors (missing headline, missing datecreated, unmapped sender) re printed on sys.stderr')
parser.add_argument("-r", "--rename-files", help="Rename files", action='store_const', const='rename_files')
parser.add_argument("--display-metadata", help="Display metadata", action='store_const', const='display_metadata')
parser.add_argument("--display-filename", help="Display new filename", action='store_const', const='display_metadata')
parser.add_argument("--error-is-fatal", help="Exit with no action at error", action='store_const', const='error_is_fatal')
parser.add_argument("sender_map", help="JSON mapping between sender and filname prefix")
parser.add_argument("directory", help="Directory with XMP files")
args = parser.parse_args()
rename_files = args.rename_files
display_metadata = args.display_metadata
display_filename = args.display_filename
error_is_fatal = args.error_is_fatal

senders = json.load(open(args.sender_map, 'r'), encoding="utf-8")
files = Path(args.directory).glob('*.XMP')

for file in files:
    props = get_props(senders, file)
    if(display_metadata):
        print('metadata: {}:{}'.format(file, props))
    (headline, datecreated, senders_text, senders_text_short, categories_text) = props
    file_base = PurePath(file).stem
    mediafile_all = Path(args.directory).glob('{}.*'.format(file_base))
    mediafile_notxmp = [f for f in mediafile_all if not f.suffix == '.XMP']
    if len(mediafile_notxmp) > 0:
        mediafile = mediafile_notxmp[0]
        new_filename = get_new_filename(args.directory, mediafile, headline, datecreated, senders_text_short, categories_text)
        if(display_filename):
            print("-> rename {} -> {}".format(mediafile, new_filename))
        if(rename_files):
            mediafile.rename(new_filename)

