#!/usr/bin/env python3

import argparse
import glob
import json
import sys
from subprocess import run, PIPE, check_output, check_call, DEVNULL
from pathlib import Path
import time

_THRESHOLD = 107000000000
_TIME_THRESHOLD = 600

class AllFullException(Exception):
    pass

def parse_args():
    parser = argparse.ArgumentParser(description="This script will check the plots directories and attempt to transfer them via rsync when completed")
    parser.add_argument("-c", "--config", help="Path to the config file for this transfer program (default: /opt/chia/transfer.json)",
                        default="/opt/chia/transfer.json", type=argparse.FileType("r"))

    try:
        args = parser.parse_args()
    except Exception as e:
        parser.print_help()
        raise e

    return args

def will_fit(user, ip, file, dest):
    if ip is None:
        output = check_output(["df", str(dest)])
    else:
        output = check_output(["ssh", f"{user}@{ip}", "-C", "df", str(dest)])

    avail = int(output.splitlines()[1].split()[3]) * 1024
    if Path(file).stat().st_size < avail:
        return True
    else:
        return False

def transfer_plot(file, config):
    print(f"Found plot {file} ready to transfer...")
    for dest in config["dest"]:
        for folder in dest["folders"]:
            ip = dest.get("dest-ip", None)
            if not will_fit(dest["user"], ip, file, folder):
                print(f"{folder} is full...skipping")
                continue
            if ip is None:
                print(f"Attempting local transfer to {folder}...", flush=True, end="")
            else:
                print(f"Attempting transfer to {dest['dest-ip']}:{folder}...", flush=True, end="")
            try:
                arg_list = ["rsync", f'--bwlimit={config["bw-limit"]}', "--remove-source-files", "-E", str(file)]
                if ip is None:
                    arg_list += [f'{folder}']
                else:
                    arg_list += [f'{dest["user"]}@{dest["dest-ip"]}:{folder}']

                check_call(arg_list)
                print(f"Transfer succeeded", flush=True)
                return
            except:
                print(f"Transfer failed", flush=True)
                continue

    raise AllFullException(f"Could not fit {file} anywhere. Please check your json config.")

if __name__ == "__main__":
    args = parse_args()
    config = json.load(args.config)

    # First we walk the source(s) directory to see if there are any finished plots
    for source in config["source"]:
        for name in glob.glob(source + "*.plot"):
            init_size = Path(name).stat().st_size
            delta_time = time.time() - Path(name).stat().st_mtime

            if init_size >= _THRESHOLD:
                if delta_time >= _TIME_THRESHOLD:
                    transfer_plot(name, config)

    print("No files transferred")
