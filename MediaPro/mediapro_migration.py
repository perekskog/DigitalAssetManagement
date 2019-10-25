#!/usr/bin/env python3 


# TODO
#
# v Date formatting: 2019-10-12 -> 191012 (eller 20191012?)
# v Extension? Står inte i XMP-filen... Måste kolla extension på fil med samma basnamn...
# - Create (if not exist already) and move files into subdirectories.

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

    nheadline = len(root.findall('./rdf:RDF/rdf:Description/photoshop:Headline',ns))
    headline = ''
    if(nheadline==0):
        sys.stderr.write('{}: ERROR: Missing headline, replaced with {}\n'.format(xmlfile, default_headline))
        headline = default_headline
    else:
        headline = root.find('./rdf:RDF/rdf:Description/photoshop:Headline',ns).text

    ndatecreated = len(root.findall('./rdf:RDF/rdf:Description/photoshop:DateCreated',ns))
    datecreated = ''
    if(ndatecreated==0):
        sys.stderr.write('{}: ERROR: Missing datecreated, replaced with {}\n'.format(xmlfile, default_datecreated))
        datecreated = default_datecreated
    else:
        datecreated = root.find('./rdf:RDF/rdf:Description/photoshop:DateCreated',ns).text

    senders = root.findall('./rdf:RDF/rdf:Description/dc:subject/rdf:Bag/rdf:li',ns)
    #print(senders)
    senders_text = []
    senders_text_short = []
    for sender in senders:
        if(sender.text != 'Peer'):
            if(sender.text in sender_map):
                senders_text.append(sender.text)
                senders_text_short.append(sender_map[sender.text])
            else:
                sys.stderr.write('{}: ERROR: Unmapped sender: {}, replaced with {}'.format(xmlfile, sender.text, default_sender))
                senders_text.append(sender.text)
                senders_text_short.append(default_sender)

    categories = root.findall('./rdf:RDF/rdf:Description/mediapro:CatalogSets/rdf:Bag/rdf:li',ns)
    #print(categories)

    categories_text = []
    for category in categories:
        categories_text.append(category.text)

    return (headline, datecreated, senders_text, senders_text_short, categories_text)

def rename_file(basedir, file, headline, datecreated, senders_text_short, categories_text):
    categories = ""
    for cat in categories_text:
        categories += "({})".format(cat.lower())
    
    date_formatted = datecreated.replace('-','')[2:]

    sender = senders_text_short[0]
    #print('[{}]'.format(basedir))
    p = Path('{}/{}'.format(basedir, sender))
    p.mkdir(exist_ok=True)
    newfilename = "{}/{}/{}_{}_{} {}{}".format(basedir, sender, sender, date_formatted, headline, categories, file.suffix)

    print("    rename {} -> {}".format(file, newfilename))
    file.rename(newfilename)
    return

parser = argparse.ArgumentParser(description='Extract metadata from XMP files \n Extracts headline, datecreated, senders and categories. \n Errors (missing headline, missing datecreated, unmapped sender) re printed on sys.stderr')
parser.add_argument("-r", "--rename-files", help="Rename files", action='store_const', const='rename_files')
parser.add_argument("sender_map", help="JSON mapping between sender and filname prefix")
parser.add_argument("directory", help="Directory with XMP files")
args = parser.parse_args()

senders = json.load(open(args.sender_map, 'r'), encoding="utf-8")
files = Path(args.directory).glob('*.XMP')
rename_files = args.rename_files

for file in files:
    props = get_props(senders, file)
    print('{}:{}'.format(file, props))
    ()
    if(rename_files):
        (headline, datecreated, senders_text, senders_text_short, categories_text) = props
        file_base = PurePath(file).stem
        mediafile_all = Path(args.directory).glob('{}.*'.format(file_base))
        mediafile_notxmp = [f for f in mediafile_all if not f.suffix == '.XMP']
        rename_file(args.directory, mediafile_notxmp[0], headline, datecreated, senders_text_short, categories_text)
