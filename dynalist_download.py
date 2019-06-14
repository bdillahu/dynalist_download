#!env python3


# for debugging, run 'pudb3' with command line you want

import logging
import urllib.request
import json
import argparse
import requests
from datetime import datetime
import re
import os
import shutil

# TODO - implement a "with Archive" and "without Archive" flag - don't do the Archive tree if "without Archive"
#        Then you can do the Archive once a day and the rest more often
# TODO - implement a markdown output format - similar to orgmode with repeated '#' for headlines and YAML style metadata blocks


bdillahuToken = "xxxxxxxx"


Dynalist_list_url = "https://dynalist.io/api/v1/file/list"
Dynalist_edit_url = "https://dynalist.io/api/v1/file/edit"
Dynalist_read_url = "https://dynalist.io/api/v1/doc/read"
Dynalist_add_url  = "https://dynalist.io/api/v1/inbox/add"

# Constants
body = {'token': bdillahuToken}
root_path = "/mnt/filer/Filing/Programming/2019-06-11_DynalistDownload/dynalist_archive"
text_extension = ".txt"
org_extension  = ".org"
json_raw_filename = "+json_raw"
json_pretty_filename = "+json_pretty"
json_extension = ".json"
list_filename  = "+dynalist_list"

def output_json(args, raw_json):
    logger.debug("called output_json")

    if not isinstance(raw_json, dict):
        raw_json = json.loads(raw_json)
    if 'json' in args.format:
        if args.output_path:
            path = os.path.join(args.output_path, f"{json_pretty_filename}{json_extension}")
            if os.path.exists(path):
                os.remove(path)
            f=open(path, "a+")
            f.write(json.dumps(raw_json, indent=4))
            f.close()
        else:    
            print(json.dumps(raw_json, indent=4))        
    if 'json-raw' in args.format:
        if args.output_path:
            path = os.path.join(args.output_path, f"{json_raw_filename}{json_extension}")
            if os.path.exists(path):
                os.remove(path)
            f=open(path, "a+")
            json.dump(raw_json, f)
#            f.write(f"{raw_json}\n")
            f.close()
        else:    
            print(raw_json)


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
#        return (datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'))
        return (datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S %a'))

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

def convert_tags_to_org(string):
    logger.debug(f"called convert_tags_to_org - {string}")

    # Only implemented in headline
    # since tags my be inline with text in Dynalist, this may not make sense
    # and definitely doesn't in the note field in my opinion

    # - https://stackoverflow.com/questions/16440267/how-to-find-a-word-that-starts-with-a-specific-character
    # - https://stackoverflow.com/questions/20282452/regex-to-match-word-beginning-with
    # not the lower case \b is a word boundary and the Upper \B is non-word - I think

    # is it really a string, or a list of something
    if isinstance(string, str):
        search = r'(\[.*\])\((.*)\)'
        replace = r'[[\2]\1]'
        tags = re.findall(r'\B[#@]\w+', string)
        
        if tags:
            # pull the tags out of the string
            for tag in tags:
                string = string.replace(f" {tag}", '')

            # remove # and @ from tag list
            # this will actually remove both a leading and trailing @ or #
            # tags = ([s.strip('@#') for s in tags])
            # this version will only remove a leading character, but doesn't matter what it is
            tags = ([s[1:] for s in tags])

            # append the new org style tags
            tagstring = ':'.join(tags)
            string = f"{string}      :{tagstring}:"
                
        logger.debug(f"converted tag - {string}")
        return string
    else:
        # should never happen
        logger.error(f"called convert_tags_to_org on NON-STRING - {string}")
    
    
def add_folder(args, path):
    logger.debug(f"called write_out - {path}")

    if args.output_path:
        # TODO - add some error checking - try statement
        logger.debug(f"creating directory - {path}")
        if not os.path.exists(path):
            os.mkdir(path)
        else:
            if not os.path.isdir(path):
                logger.error(f"FILE IN THE WAY! - {path}")
        
               
def write_out(args, string, path, format):
    logger.debug(f"called write_out - {string}")
    # write to stdout unless an output directory is given

#    print(string)
#    if not path is None:
    if (args.output_path) and not (path is None):
        if (args.list) and (os.path.isdir(path)):
            if format == 'plain':
                path = f"{list_filename}{text_extension}"
            elif format == 'orgmode':
                path = f"{list_filename}{org_extension}"
        if (os.path.isdir(path)):
            path = os.path.join(path, f"Untitled - Root")
        f=open(os.path.join(args.output_path, path), "a+")
        f.write(f"{string}\n")
        f.close()
    else:    
        print(string)

            

def git_commit(args):
    logger.debug(f"called git_commit")

    
        
def output_doc(args, raw_json, level, path):
    # central output dispatcher for documents and their nodes
    logger.debug("called output_doc")

    def output_plain(raw_json, level, path):
        logger.debug("called output_json")

        path = f"{path}{text_extension}"

        if 'title' in raw_json:
            # I don't think this will ever happen
            write_out(args, "    " * level + f"{raw_json['title']}", path, 'plain')
        if 'content' in raw_json:
            write_out(args, "    " * level + f"{raw_json['content']}", path, 'plain')
            for key, value in raw_json.items():
                if (key == 'created') or (key == 'modified'):
                    value = convert_date(value)
                write_out(args, "    " * level + f"  - {key} = {value}", path, 'plain')
            write_out(args, " \n", path, 'plain')
#            print("    " * level, json.dumps(raw_json, indent = level * 4, separators=(',', ': ')))

    def output_orgmode(raw_json, level, path):
        logger.debug("called output_orgmode")

        path = f"{path}{org_extension}"
        
        if 'title' in raw_json:
            # I don't think this will ever happen
            write_out(args, "*" * level + f" {raw_json['title']}", path, 'orgmode')
        if 'content' in raw_json:
            content = raw_json['content']
            content = convert_links_to_org(content)
            content = convert_tags_to_org(content)
            write_out(args, "*" * level + f" {content}", path, 'orgmode')
            write_out(args, ":PROPERTIES:", path, 'orgmode')
            for key, value in raw_json.items():
                if (key == 'note') or (key == 'content'):
                    value = convert_links_to_org(value)
                if not (key == 'note'):
                    write_out(args, f":{key.upper()}: {value}", path, 'orgmode')
            write_out(args, ":END:", path, 'orgmode')

            # write the note at the end of the properties drawer
            write_out(args, raw_json['note'], path, 'orgmode')

    def output_archive(raw_json, level):
        # json + orgmode
        logger.debug("called output_archive")

        output_json(raw_json)
        output_orgmode(raw_json)

    for format in args.format:
#        if format == 'json':
#            output_json_pretty(args, raw_json)
#        elif format == 'json-raw':
#            output_json_raw(args, raw_json)
        if format == 'plain':
            output_plain(raw_json, level, path)
        elif format == 'orgmode':
            output_orgmode(raw_json, level, path)
        elif format == 'archive':
            output_archive(raw_json, level)


def output_file(args, raw_json, level, path):
    # central output dispatcher for file list
    logger.debug("called output_file")

    def output_plain(raw_json, level, path):
        logger.debug("called output_json")

        write_out(args, "    " * level + f"{raw_json['title']} - {raw_json['id']} - {raw_json['type']}", path, 'plain')

    def output_orgmode(raw_json, level, path):
        logger.debug("called output_orgmode")

        write_out(args, "*" * level + f" {raw_json['title']}", path, 'orgmode')
        write_out(args, ":PROPERTIES:", path, 'orgmode')
        write_out(args, f":ID: {raw_json['id']}", path, 'orgmode')
        write_out(args, f":TYPE: {raw_json['type']}", path, 'orgmode')
        write_out(args, ":END:", path, 'orgmode')

    def output_archive(raw_json, level):
        # json + orgmode
        logger.debug("called output_archive")

        output_json(raw_json)
        output_orgmode(raw_json)

    for format in args.format:
#        if format == 'json':
#            output_json_pretty(args, raw_json)
#        elif format == 'json-raw':
#            output_json_raw(args, raw_json)
        if format == 'plain':
            output_plain(raw_json, level, path)
        elif format == 'orgmode':
            output_orgmode(raw_json, level, path)
        elif format == 'archive':
            output_archive(raw_json, level)


def get_data(args):
    logger.debug("called get_data")

    # This is the main entry point of the program


    def list_files():
        # get list of all files from API call
        logger.debug("called list_files")

        payload = {'token':bdillahuToken}
        logger.debug(f"POST: {Dynalist_list_url} {payload}")
        r = requests.post(Dynalist_list_url, json = payload)
        logger.debug("RESPONSE: " + r.text)
        return r

    def file_content(file_id):
        logger.debug("called file_content")
        payload = {'token':bdillahuToken, 'file_id':file_id}
        logger.debug(f"POST: {Dynalist_read_url} {payload}")
        r = requests.post(Dynalist_read_url, json = payload)
        logger.debug("RESPONSE: " + r.text)
        return r


    def walk_doc_tree(args, file_contents, id, level, path):
        # an individual document (outline)
        logger.debug("called walk_doc_tree - recursive")

        logger.debug(f"tree root - {file_contents['title']} - {id}")
        if 'nodes' in file_contents:
            data = next(item for item in file_contents['nodes'] if item['id'] == id)
                
            #for node in file_contents['nodes']:
            if 'children' in data:
                output_doc(args, data, level, path)
                for child in data['children']:
                    walk_doc_tree(args, file_contents, child, level + 1, path)
            else:
                output_doc(args, data, level, path)
                level -= 1
        else:
            output_doc(args, file_contents, level, path)

            
    def walk_file_tree(args, doc_list, id, level, path):
        # process the entire list of documents (files and folders)
        logger.debug("called walk_file_tree - recursive")

        logger.debug(f"tree root - {id}")
        # - https://stackoverflow.com/questions/8653516/python-list-of-dictionaries-search
        data = next(item for item in doc_list['files'] if item['id'] == id)
        if data['type'] == 'folder':
            if args.output_path:
                if not (data['title'] == 'Untitled') and (args.dump_all or args.file):
                    if not 'json' in args.format:
                        path = os.path.join(path, data['title'])
                        add_folder(args, path)
            output_file(args, data, level, path)
            for child in data['children']:
                walk_file_tree(args, doc_list, child, level + 1, path)
        else:
            output_file(args, data, level, path)
            if args.dump_all:
                # call the API and get the details for this document
                raw_file_contents = file_content(id)
                file_contents = json.loads(raw_file_contents.text)
                if ('json' in args.format) or ('json-raw' in args.format):
                    output_json(args, raw_file_contents.text)

                if args.output_path:
                    path = os.path.join(path, file_contents['title'])
                walk_doc_tree(args, file_contents, 'root', level, path)
            level -= 1

    def cleanup_output_path(args):
        logger.debug(f"called cleanup_output_path")
        logger.debug(f"Removing all existing content - {args.output_path}/*")

        # Remove list output file
        if args.list:
            logger.debug(f"Removing list output files")

            # Remove the previous output file
            output_path = os.path.join(args.output_path, f"{list_filename}{text_extension}")
            if os.path.exists(output_path):
                os.remove(output_path)

        # Clean out output directory
        if args.dump_all:
            # I don't just blow away everything because I want .git to stay
            
            # Get list of all files and directories
            filelist = os.listdir(args.output_path)
        
            # Remove .git from list
            filelist.remove('.git')
        
            for file in filelist:
                filepath = os.path.join(args.output_path, file)
                if os.path.isdir(filepath):
                    shutil.rmtree(filepath)
                else:
                    os.remove(filepath)

    def cleanup_file(args, filename):
        logger.debug(f"called cleanup_file - {filename}")

        if 'plain' in args.format:
            path = os.path.join(args.output_path, f"{filename}{text_extension}")
            if os.path.exists(path):
                os.remove(path)
        if 'orgmode' in args.format:
            path = os.path.join(args.output_path, f"{filename}{org_extension}")
            if os.path.exists(path):
                os.remove(path)

                    
    # If no output format specified, use plain
    if not args.format:
        args.format = ['plain']

    if args.list and args.output_path:
        if ('json' in args.format) or ('json-raw' in args.format):
            print("ERROR: '--list' and '--format json' not available to write to external files")
            print("       use '--dump_all' and '--format json'")
            exit

    # If output to files, clean out existing directory
    if args.output_path:
        if 'dump_all' in args.format:
            cleanup_output_path(args)
        else:
            if 'json' in args.format:
                path = os.path.join(args.output_path, f"{json_pretty_filename}{json_extension}")
                if os.path.exists(path):
                    os.remove(path)
            if 'json-raw' in args.format:
                path = os.path.join(args.output_path, f"{json_pretty_filename}{json_extension}")
                if os.path.exists(path):
                    os.remove(path)
            if args.list:
                if 'plain' in args.format:
                    path = os.path.join(args.output_path, f"{list_filename}{text_extension}")
                    if os.path.exists(path):
                        os.remove(path)
                if 'orgmode' in args.format:
                    path = os.path.join(args.output_path, f"{list_filename}{org_extension}")
                    if os.path.exists(path):
                        os.remove(path)
        
    # Get list of all documents

    # Given a file_id (manually obtained or availalbe from the all-files list)
    # retrieve contents of that file, walking the node tree
    if args.file:
        for file_id in args.file:
            # call the API and get the details for this document
            raw_file_contents = file_content(file_id)
            file_contents = json.loads(raw_file_contents.text)
            if ('json' in args.format) or ('json-raw' in args.format):
                output_json(args, file_contents)
            if args.output_path:
                cleanup_file(args, file_contents['title'])
            walk_doc_tree(args, file_contents, 'root', 0, file_contents['title'])
    else:
        # anything else --list or --dump_all

        # get list of files
        raw_doc_list = list_files()
        doc_list = json.loads(raw_doc_list.text)
        logger.debug(f"Root File ID: {doc_list['root_file_id']}")

        #if any(item in args.format for item in ['json', 'json-raw']):
        if 'json' in args.format:
            output_json(args, doc_list)
        elif 'json-raw' in args.format:
            output_json(args, doc_list)
        if args.format:
            # there are still other formats being requested
            walk_file_tree(args, doc_list, doc_list['root_file_id'], 0, args.output_path)

            
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
    parser.add_argument("--output_path",
                        help="if directory given, output goes to that location instead of stdout - EXISTING CONTENTS WILL BE DELETED",
                        action="store")
    parser.add_argument("--dump_all", 
                        help="Dump contents of all documents",
                        action="store_true")
    parser.add_argument("--format",
                        help="output format - json, plain text, orgmode, archive (json + orgmode) - can appear multiple times",
                        choices=['json', 'json-raw', 'plain', 'orgmode', 'archive'],
                        action="append")
    group = parser.add_mutually_exclusive_group()
    
    
    parser.set_defaults(func=get_data)
#    subparsers = parser.add_subparsers(help="sub-command help")

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
        logger.debug("Debug level set")

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
