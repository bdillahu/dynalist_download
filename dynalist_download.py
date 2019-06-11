#!env python3

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


def parse_doc_list(raw_doc_list):
    logger.info("called parse_doc_list")

    doc_list = json.loads(raw_doc_list)
    logger.info(f"Parsed doc_list: {doc_list}")
    return doc_list


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
        
    if args.list:
        raw_doc_list = list_docs()
        doc_list = json.loads(raw_doc_list.text)
        print(json.dumps(doc_list, indent=4))
    if args.file:
        for file_id in args.file:
            raw_file_contents = file_content(file_id)
            file_contents = json.loads(raw_file_contents.text)
            print(json.dumps(file_contents, indent=4))
    if args.dump_all:
        doc_list = list_docs()
        # somehow parse that
        for file_id in doc_list_parsed:
            file_contents = file_content(file_id)
            print(file_contents.text)




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
    parser.set_defaults(func=get_data)
    subparsers = parser.add_subparsers(help="sub-command help")

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
