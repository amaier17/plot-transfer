# Plot-Transfer
This repo contains a python script for auto transferring completed plots to
their destination drives for Chia.

## Requirements
- rsync
- python3
- installed ssh-keys with any remote machines

## Writing a json config file
An example config file is uploaded here as "transfer.json".
In the top level you can specify the bwlimit for the transfers,
the source directory(ies) of your plots, and the destination
dictionaries.

Inside of the 'dest' key, you can specify the list of possible
plot destinations. These can be either local to the machine or
remote on another machine.

The "legacy" key allows you to specify a folder from which to delete plots so
that your new plots will fit. The key should be a string of the folder name in
each of your destination folders (i.e. "legacy-folder"). For example, if your
/mnt/plots/disk0 is completely full and your layout is as follows:
/mnt/plots/disk0/legacy-folder -> The folder with old plots to replace
You can specify the "legacy": "legacy-folder" key and it will auto replace those
plots into the main /mnt/plots/disk0 directory with new ones.

### Local Desinations
To specifiy a local destination simply do not add the "dest-ip" or the "user"
keys to the dictionary.

### Remote Destinations
You will need to specify both the "dest-ip" and "user" keys here as well as
you'll likely want to ensure you have copied the appropriate ssh keys to the
remote machines.

### Folders
Finally you can then specify a list of folders for the destinations. This will
be accessed in order until they are full.
