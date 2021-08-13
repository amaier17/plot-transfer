#!/usr/bin/env python3

import argparse
import glob
import json
import logging
import logging.handlers
import os
import sys
from subprocess import run, PIPE, check_output, check_call, DEVNULL
from pathlib import Path
import time

_THRESHOLD = 107000000000
_TIME_THRESHOLD = 100

class AllFullException(Exception):
    pass


class SyslogBOMFormatter(logging.Formatter):
    def format(self, record):
        result = super().format(record)
        return f"plot-transfer:{result}"


handler = logging.handlers.SysLogHandler('/dev/log')
formatter = SyslogBOMFormatter(logging.BASIC_FORMAT)
handler.setFormatter(formatter)
root = logging.getLogger()
root.setLevel(os.environ.get("LOGLEVEL", "INFO"))
root.addHandler(handler)


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

def check_legacy(user, ip, folder, legacy_folder):
    try:
        print("didn't fit but checking legacy")
        plot = check_output(["ssh", f"{user}@{ip}", "-C", "ls", str(folder) + "/" + legacy_folder]).split()[0].decode()
        logging.warning(f"Deleting legacy plot {plot}...")
        print(f"Deleting legacy plot {plot}...")
        check_call(["ssh", f"{user}@{ip}", "-C", "rm", str(folder) + "/" + legacy_folder + "/" + plot])
    except Exception:
        pass


def transfer_plot(file, config):
    logging.info(f"Found plot {file} ready to transfer...")
    print(f"Found plot {file} ready to transfer...")
    for dest in config["dest"]:
        for folder in dest["folders"]:
            can_fit = True
            ip = dest.get("dest-ip", None)
            user = dest.get("user", None)
            if not will_fit(user, ip, file, folder):
                can_fit = False
                if "legacy" in dest:
                    check_legacy(user, ip, folder, dest["legacy"])
                    if will_fit(user, ip, file, folder):
                        can_fit = True
            if not can_fit:
                logging.warning(f"{folder} is full...skipping")
                print(f"{folder} is full...skipping")
                continue
            if ip is None:
                logging.info(f"Attempting local transfer to {folder}...")
                print(f"Attempting local transfer to {folder}...", flush=True, end="")
            else:
                logging.info(f"Attempting transfer to {ip}:{folder}...")
                print(f"Attempting transfer to {ip}:{folder}...", flush=True, end="")
            try:
                arg_list = ["rsync", f'--bwlimit={config["bw-limit"]}', "--preallocate", "--remove-source-files", "-E", str(file)]
                if ip is None:
                    arg_list += [f'{folder}']
                else:
                    arg_list += [f'{user}@{ip}:{folder}']

                check_call(arg_list)
                logging.info(f"Transfer succeeded")
                print(f"Transfer succeeded", flush=True)
                return
            except Exception as e:
                logging.error(f"Transfer failed for {e}")
                print(f"Transfer failed for {e}", flush=True)
                continue

    raise AllFullException(f"Could not fit {file} anywhere. Please check your json config.")


if __name__ == "__main__":
    args = parse_args()
    config = json.load(args.config)
    file_transferred = False

    # First we walk the source(s) directory to see if there are any finished plots
    for source in config["source"]:
        for name in glob.glob(source + "*.plot"):
            init_size = Path(name).stat().st_size
            delta_time = time.time() - Path(name).stat().st_mtime

            if init_size >= _THRESHOLD:
                if delta_time >= _TIME_THRESHOLD:
                    transfer_plot(name, config)
                    file_transferred = True

    if not file_transferred:
        logging.warning("No files transferred!")
        print("No files transferred")

try:
    exit(main())
except Exception:
    logging.exception("Exception in main()")
    exit(1)

