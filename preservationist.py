#!/usr/bin/python3

################################################################################
################################ CONFIGURATION #################################
################################################################################


################################################################################
################################### IMPORTS ####################################
################################################################################

import atexit
from datetime import date, datetime, timedelta
import shutil
import os
import os.path
import subprocess
import sys

################################################################################
################################## CONSTANTS ###################################
################################################################################

DATETIME_FORMAT = '%Y-%m-%d @ %H:%M'

################################################################################
################################## FUNCTIONS ###################################
################################################################################

def log(message,*args,**kwargs):
    print(datetime.strftime(datetime.now(),'[%Y-%m-%d @ %H:%M:%S] ') + message,*args,**kwargs)
    sys.stdout.flush()

################################################################################
##################################### RUN ######################################
################################################################################

def run(
        
#################################### Paths #####################################

source_path,
snapshot_path,
rsync_command,

#################################### Rsync #####################################

rsync_short_options,
rsync_long_options,
include,
exclude,

################################ Miscellaneous #################################

dry_run,

################################################################################
):
    if dry_run:
        log('This is just a dry run; no action will be taken.')
 
    # First, check to see if another protectionist process is already active.
    i_am_active = os.path.join(snapshot_path,'i_am_active')
    if not dry_run:
        if os.path.exists(i_am_active):
            log('Another preservationist process is already running, so I will abort.')
            log('(If this is not true, then delete i_am_active in the snapshots directory.)')
            log('(If you want to kill the running process, its id is in i_am_active.)')
            return

    # Create a sentinel file that signifies that we are active in the snapshots
    # directory.
    if not dry_run:
        with open(i_am_active,'w') as f:
            print(os.getpid(),file=f)

    # Ensure that the sentinel file is deleted when we quit.
    def delete_i_am_active():
        if os.path.exists(i_am_active):
            os.remove(i_am_active)
    atexit.register(delete_i_am_active)

    # Go through the snapshots directory and find all of the snapshots; we
    # interpret every directory whose date follows the time format as being a
    # snapshot and ignore everything else.
    snapshots = []
    for potential_snapshot in os.listdir(snapshot_path):
        try:
            snapshots.append(datetime.strptime(potential_snapshot, DATETIME_FORMAT))
        except ValueError:
            pass

    # Sort the snapshots from future to past (i.e., going backwards in time).
    snapshots.sort(reverse=True)

    # Delete old snapshots
    if snapshots:
        snapshots_to_prune = []

        # Keep the last 24 hours of snapshots
        one_day_ago = datetime.now() - timedelta(days=1)
        i = 0
        while i < len(snapshots) and snapshots[i] >= one_day_ago:
            i += 1
        j = i

        # Helper function for selecting all of the snapshots for a given day/month
        def selectToPrune(get_metric):
            nonlocal i, snapshots_to_prune
            this = get_metric(snapshots[i])
            j = i+1
            while j < len(snapshots) and get_metric(snapshots[j]) == this:
                j += 1
            snapshots_to_prune += snapshots[i:j-1]
            i = j

        # Keep daily snapshots for the last month
        last_daily_to_keep = datetime.now().date() - timedelta(days=30)
        while i < len(snapshots) and snapshots[i].date() >= last_daily_to_keep:
            selectToPrune(lambda x: x.date())

        # Keep monthly snapshots forever
        while i < len(snapshots):
            selectToPrune(lambda x: x.date().month)

        # Delete the snapshots to be pruned
        for snapshot in snapshots_to_prune:
            snapshot_path = datetime.strftime(snapshot, DATETIME_FORMAT)
            log('Pruning snapshot {}...'.format(snapshot_path))
            if not dry_run:
                shutil.rmtree(snapshot_path,True)

    # Create a directory for the snapshot that we will be taking
    current_directory = os.path.join(snapshot_path,'current')
    if not dry_run:
        os.makedirs(current_directory, exist_ok=True)

    # Run rsync
    run_rsync = (
        [rsync_command,rsync_short_options] +
        rsync_long_options +
        ['--include={}'.format(included_path) for included_path in include] +
        ['--exclude={}'.format(excluded_path) for excluded_path in exclude] +
        [os.path.join(source_path,''),os.path.join(current_directory,'')] +
        ([ '--link-dest={}'.format(os.path.join(snapshot_path,datetime.strftime(snapshots[0],DATETIME_FORMAT)))]
         if snapshots else [])
    )
    log('Running {}...'.format(' '.join(run_rsync)))
    if not dry_run:
        process = subprocess.Popen(run_rsync,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        # Annoyingly, the way that rsync buffers its output means that we can't
        # just use PIPE to do this for us, though maybe it is for the best as it
        # lets the rsync output lines be timestamped.
        for line in process.stdout:
            log(line.decode('utf-8'),end='')
        return_code = process.wait()
        # If rsync fails, then we assume that current is broken and so we don't
        # turn it into a snapshot.
        if return_code != 0:
            log("Failed to run rsync: return code {}".format(return_code))
            return

    # Rename the new snapshot
    snapshot_path = os.path.join(snapshot_path,datetime.strftime(datetime.now(),DATETIME_FORMAT))
    log('Renaming {} to {}...'.format(current_directory,snapshot_path))
    if not dry_run:
        os.rename(current_directory,snapshot_path)