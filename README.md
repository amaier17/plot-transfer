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
