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




def get_data(args):
    logger.info("called get_data")
    
    if args.list:
        payload = {'token':bdillahuToken}
        logger.debug(f"POST: {Dynalist_list_url} {payload}")
        r = requests.post(Dynalist_list_url, json = payload)
        logger.debug("RESPONSE: " + r.text)
        print(r.text)
    if args.file:
        for file_id in args.file:
            payload = {'token':bdillahuToken, 'file_id':file_id}
            logger.debug(f"POST: {Dynalist_read_url} {payload}")
            r = requests.post(Dynalist_read_url, json = payload)
            logger.debug("RESPONSE: " + r.text)
            print(r.text)




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
