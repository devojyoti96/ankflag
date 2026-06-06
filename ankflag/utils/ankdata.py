import logging
import psutil
import argparse
import requests
import sys
import os
import getpass
import numpy as np
from datetime import datetime as dt
from parfive import Downloader

all_filenames = [
    "udocker-englib-1.2.11.tar.gz",
]

def get_cachedir():
    """
    Get cache directory
    """
    homedir = os.path.expanduser("~")
    cachedir = f"{homedir}/.ankflag"
    os.makedirs(cachedir, exist_ok=True)
    return cachedir
    
    
def create_datadir(datadir=""):
    """
    Create data directory

    Parameters
    ----------
    datadir : str, optional
        User provided custom data directory
    """
    cachedir = get_cachedir()
    if datadir == "":
        datadir = f"{cachedir}/ankflag_data"
    else:
        datadir = f"{datadir}/ankflag_data"
    os.makedirs(datadir, exist_ok=True)
    with open(f"{cachedir}/ankflag_data_dir.txt", "w") as f:
        f.write(str(datadir) + "\n")
    return


def get_datadir():
    """
    Get package data directory

    Returns
    -------
    str
        Data directory
    """
    cachedir = get_cachedir()
    if not os.path.exists(f"{cachedir}/ankflag_data_dir.txt"):
        return None
    with open(f"{cachedir}/ankflag_data_dir.txt", "r") as f:
        datadir = f.read().strip()
    os.makedirs(datadir, exist_ok=True)
    return datadir


def get_zenodo_file_urls(record_id):
    url = f"https://zenodo.org/api/records/{record_id}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return [(f["links"]["self"], f["key"]) for f in data.get("files", [])]


def download_with_parfive(record_id, update=False, output_dir="zenodo_download"):
    print("####################################")
    print("Downloading data files ...")
    print("####################################")
    urls = get_zenodo_file_urls(record_id)
    os.makedirs(output_dir, exist_ok=True)
    total_cpu = psutil.cpu_count()
    dl = Downloader(max_conn=min(total_cpu, len(all_filenames) + 1))
    for file_url, filename in urls:
        if filename in all_filenames:
            if not os.path.exists(f"{output_dir}/{filename}") or update:
                if os.path.exists(f"{output_dir}/{filename}"):
                    os.system(f"rm -rf {output_dir}/{filename}")
                dl.enqueue_file(file_url, path=output_dir, filename=filename)
    results = dl.download()
    for f in results:
        os.chmod(f, 0o755)


def init_ankflag_data(datadir="",update=False):
    """
    Initiate aNKflag data

    Parameters
    ----------
    update : bool, optional
        Update data, if already exists
    """
    create_datadir(datadir=datadir)
    datadir = get_datadir()
    unavailable_files = [
        f for f in all_filenames if not os.path.exists(f"{datadir}/{f}")
    ]
    if unavailable_files or update:
        record_id = "18327403"
        download_with_parfive(record_id, update=update, output_dir=datadir)
        timestr = dt.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        print(f"aNKflag data files are updated in: {datadir} at time: {timestr}")



