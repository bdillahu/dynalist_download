#!env python3


# for debugging, run 'pudb3' with command line you want

import logging
import urllib.request
import json
import argparse
import requests
from datetime import datetime
import re

# TODO - handle raw-json of documents better - instead of separate for each doc - but maybe that's right

bdillahuToken = "xxxxxxxx"


Dynalist_list_url = "https://dynalist.io/api/v1/file/list"
Dynalist_edit_url = "https://dynalist.io/api/v1/file/edit"
Dynalist_read_url = "https://dynalist.io/api/v1/doc/read"
Dynalist_add_url  = "https://dynalist.io/api/v1/inbox/add"


body = {'token': bdillahuToken}  


def output_json_raw(raw_json):
    logger.info("called output_json")

    print(raw_json)

def output_json_pretty(raw_json):
    logger.info("called output_json")
    print(json.dumps(raw_json, indent=4))        

def convert_date(timestamp):
    logger.debug(f"called convert_date - {timestamp}")

    # - https://stackoverflow.com/questions/3682748/converting-unix-timestamp-string-to-readable-date
    # if you encounter a "year is out of range" error the timestamp
    # may be in milliseconds, try `ts /= 1000` in that case
    if timestamp == 0:
        # empty or unknown
        return 'unknown'
    else:
        timestamp /= 1000
        return (datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'))

def convert_links_to_org(string):
    logger.debug(f"called convert_link_to_org - {string}")

    # is it really a string, or a list of something
    if isinstance(string, str):
        search = r'(\[.*\])\((.*)\)'
        replace = r'[[\2]\1]'
        string = re.sub(search, replace, string)
        logger.debug(f"converted link - {string}")
        return string
    else:
        # should never happen
        logger.error(f"called convert_link_to_org on NON-STRING - {string}")
        return f"NON-STRING - {string}"
    

def output_doc(args, raw_json, level):
    # central output dispatcher for documents and their nodes
    logger.info("called output_doc")

    def output_plain(raw_json, level):
        logger.info("called output_json")

        if 'title' in raw_json:
            # I don't think this will ever happen
            print("    " * level, f"{raw_json['title']}")
        if 'content' in raw_json:
            print("    " * level, f"{raw_json['content']}")
            for key, value in raw_json.items():
                if (key == 'created') or (key == 'modified'):
                    value = convert_date(value)
                print("    " * level, "- ", f"{key} = {value}")
#            print("    " * level, json.dumps(raw_json, indent = level * 4, separators=(',', ': ')))

    def output_orgmode(raw_json, level):
        logger.info("called output_orgmode")

        if 'title' in raw_json:
            # I don't think this will ever happen
            print("*" * level, f"{raw_json['title']}")
        if 'content' in raw_json:
            content = raw_json['content']
            content = convert_links_to_org(content)
            print("*" * level, f"{content}")
            print(":PROPERTIES:")
            for key, value in raw_json.items():
                if (key == 'note') or (key == 'content'):
                    value = convert_links_to_org(value)
                print(f":{key.upper()}: {value}")
            print(":END:")

    def output_archive(raw_json, level):
        # json + orgmode
        logger.info("called output_archive")

        output_json(raw_json)
        output_orgmode(raw_json)

    for format in args.format:
        if format == 'json':
            output_json_pretty(raw_json)
        elif format == 'json-raw':
            output_json_raw(raw_json)
        elif format == 'plain':
            output_plain(raw_json, level)
        elif format == 'orgmode':
            output_orgmode(raw_json, level)
        elif format == 'archive':
            output_archive(raw_json, level)


def output_file(args, raw_json, level):
    # central output dispatcher for file list
    logger.info("called output_file")

    def output_plain(raw_json, level):
        logger.info("called output_json")

        print("    " * level, f"{raw_json['title']} - {raw_json['id']} - {raw_json['type']}")

    def output_orgmode(raw_json, level):
        logger.info("called output_orgmode")

        print("*" * level, f"{raw_json['title']}")
        print(":PROPERTIES:")
        print(f":ID: {raw_json['id']}")
        print(f":TYPE: {raw_json['type']}")
        print(":END:")

    def output_archive(raw_json, level):
        # json + orgmode
        logger.info("called output_archive")

        output_json(raw_json)
        output_orgmode(raw_json)

    for format in args.format:
        if format == 'json':
            output_json_pretty(raw_json)
        elif format == 'json-raw':
            output_json_raw(raw_json)
        elif format == 'plain':
            output_plain(raw_json, level)
        elif format == 'orgmode':
            output_orgmode(raw_json, level)
        elif format == 'archive':
            output_archive(raw_json, level)


def get_data(args):
    logger.info("called get_data")

    # This is the main entry point of the program


    
    def list_files():
        # get list of all files from API call
        logger.info("called list_files")

        payload = {'token':bdillahuToken}
        logger.debug(f"POST: {Dynalist_list_url} {payload}")
        r = requests.post(Dynalist_list_url, json = payload)
        logger.debug("RESPONSE: " + r.text)
        return r

    def file_content(file_id):
        logger.info("called file_content")
        payload = {'token':bdillahuToken, 'file_id':file_id}
        logger.debug(f"POST: {Dynalist_read_url} {payload}")
        r = requests.post(Dynalist_read_url, json = payload)
        logger.debug("RESPONSE: " + r.text)
        return r

    def walk_doc_tree(args, file_contents, id, level):
        # an individual document (outline)
        logger.info("called walk_doc_tree - recursive")

        logger.info(f"tree root - {file_contents['title']} - {id}")
        # - https://stackoverflow.com/questions/8653516/python-list-of-dictionaries-search
        if 'nodes' in file_contents:
            data = next(item for item in file_contents['nodes'] if item['id'] == id)
            #for node in file_contents['nodes']:
            if 'children' in data:
                output_doc(args, data, level)
                for child in data['children']:
                    walk_doc_tree(args, file_contents, child, level + 1)
            else:
                output_doc(args, data, level)
                level -= 1
        else:
            output_doc(args, file_contents, level)

    def walk_file_tree(args, doc_list, id, level):
        # process the entire list of documents (files and folders)
        logger.info("called walk_file_tree - recursive")

        logger.info(f"tree root - {id}")
        # - https://stackoverflow.com/questions/8653516/python-list-of-dictionaries-search
        data = next(item for item in doc_list['files'] if item['id'] == id)
        if data['type'] == 'folder':
            output_file(args, data, level)
            for child in data['children']:
                walk_file_tree(args, doc_list, child, level + 1)
        else:
            output_file(args, data, level)
            if args.dump_all:
                # call the API and get the details for this document
                raw_file_contents = file_content(id)
                file_contents = json.loads(raw_file_contents.text)
                walk_doc_tree(args, file_contents, 'root', level)
            level -= 1

                    
    # If no output format specified, use plain
    if not args.format:
        args.format = ['plain']
    
    # Get list of all documents
#    if args.list:
#        raw_doc_list = list_files()
#        doc_list = json.loads(raw_doc_list.text)
#        #print(json.dumps(doc_list, indent=4))
#        output(args, doc_list, 0)

    # Given a file_id (manually obtained or availalbe from the all-files list)
    # retrieve contents of that file, walking the node tree
    if args.file:
        for file_id in args.file:
            raw_file_contents = file_content(file_id)
            file_contents = json.loads(raw_file_contents.text)
            walk_doc_tree(args, file_contents, 'root', 0)
    else:
        # anything else --list or --dump_all

        # get list of files
        raw_doc_list = list_files()
        doc_list = json.loads(raw_doc_list.text)
        logger.info(f"Root File ID: {doc_list['root_file_id']}")

        #if any(item in args.format for item in ['json', 'json-raw']):
        if 'json' in args.format:
            output_file(args, doc_list, 0)
            args.format.remove('json')
        elif 'json-raw' in args.format:
            output_file(args, doc_list, 0)
            args.format.remove('json-raw')
        if args.format:
            # there are still other formats being requested
            walk_file_tree(args, doc_list, doc_list['root_file_id'], 0)

            
#        for file in doc_list['files']:
#            if file['type'] == 'folder':
#                print(f"    Folder: {file['id']} - {file['title']} - {file['type']}")
#                for child in file['children']:
#                    # - https://stackoverflow.com/questions/8653516/python-list-of-dictionaries-search
#                    data = next(item for item in doc_list['files'] if item['id'] == child)
#                    print(f"        File: {data['id']} - {data['title']} - {data['type']}")


#        for file_id in doc_list.files:
#            file_contents = file_content(file_id)
#            print(file_contents.text)




def get_parser():
    parser = argparse.ArgumentParser(prog='Dynalist_Download')
    parser.add_argument("--debug", 
            help="enable debugging output",
            action="store_true")
    parser.add_argument("--gui",
            help="enable gui",
            action="store_true")
    parser.add_argument("--list", 
                        help="List all documents",
                        action="store_true")
    parser.add_argument("--file",
                        help="Download contents of file - can appear multiple times",
                        action="append")
    parser.add_argument("--dump_all", 
                        help="Dump contents of all documents",
                        action="store_true")
    parser.add_argument("--format",
                        help="output format - json, plain text, orgmode, archive (json + orgmode) - can appear multiple times",
                        choices=['json', 'json-raw', 'plain', 'orgmode', 'archive'],
                        action="append")
    parser.set_defaults(func=get_data)
    subparsers = parser.add_subparsers(help="sub-command help")

#    parser_new = subparsers.add_parser("format",
#                                       help="output format - json, plain text, orgmode, archive (json + orgmode) - can appear multiple times",
#                                       choices=['json', 'plain', 'orgmode', 'archive'],
#                                       default='plain',
#                                       const='plain',
#                                       nargs='?',
#                                       action="append")
#    parser_new.set_defaults(func=get_data)
    
    return parser



def run_parser(parser):
    args = parser.parse_args()

#    #try:
#    #    args = parser.parse_args()
#    #except:
#    #    parser.print_help()
#    #    sys.exit(0)

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.info("Debug level set")

    # Call the function
    args.func(args)


if __name__ == "__main__":
    logging.basicConfig(filename='dynalist_download.log', format='%(levelname)s:%(filename)s:%(module)s:%(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Create a parser for command line interface
    # Program flow will hit get_data() as the main entry point
    parser = get_parser()
    run_parser(parser)
