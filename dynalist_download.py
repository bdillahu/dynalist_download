#!env python3


# for debugging, run 'pudb3' with command line you want

import logging
import urllib.request
import json
import argparse
import requests

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


def output_doc(args, raw_json, level):
    # central output dispatcher
    logger.info("called output_doc")

    def output_plain(raw_json, level):
        logger.info("called output_json")

        if 'title' in raw_json:
            # I don't think this will ever happen
            print("    " * level, f"{raw_json['title']}")
        if 'content' in raw_json:
            print("    " * level, f"{raw_json['content']}")

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


def output_file(args, raw_json, level):
    # central output dispatcher
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

    def list_docs():
        logger.info("called list_docs")

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
        data = next(item for item in file_contents['nodes'] if item['id'] == id)
        #for node in file_contents['nodes']:
        if 'children' in data:
            output_doc(args, data, level)
            for child in data['children']:
                walk_doc_tree(args, file_contents, child, level + 1)
        else:
            output_doc(args, data, level)
            level -= 1

    def walk_file_tree(args, doc_list, id, level):
        # the entire list of documents (files and folders)
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
            # TODO - put call to get and print document contents here
            level -= 1

                    
    # If no format specified, use plain
    if not args.format:
        args.format = ['plain']
    
    # Get list of all documents
#    if args.list:
#        raw_doc_list = list_docs()
#        doc_list = json.loads(raw_doc_list.text)
#        #print(json.dumps(doc_list, indent=4))
#        output(args, doc_list, 0)

    # Get contents of file(s) based on file_id received from the all-docs list
    if args.file:
        for file_id in args.file:
            raw_file_contents = file_content(file_id)
            file_contents = json.loads(raw_file_contents.text)
            walk_doc_tree(args, file_contents, 'root', 0)
#            print(json.dumps(file_contents, indent=4))
            
    raw_doc_list = list_docs()
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
    parser.add_argument("--dump-all", 
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
    
    parser = get_parser()
    run_parser(parser)
