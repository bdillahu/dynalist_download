#!/bin/bash
echo "Running dynalist_archive"
cd "/mnt/filer/Filing/Dynalist_Archive/dynalist_archive"
#eval `ssh-agent -s`
HOME=/home/bdillahu LANG=en_US.UTF-8 /usr/bin/pipenv run /home/bdillahu/.local/share/virtualenvs/dynalist_download-7qtNjrkx/bin/python /mnt/filer/Filing/Programming/2019-06-11_DynalistDownload/dynalist_download/dynalist_download.py --list --dump_all --format plain --format orgmode --json pretty --json raw --output_path "/mnt/filer/Filing/Dynalist_Archive/dynalist_archive" --git 
echo "Completed dynalist_archive"
