#!/usr/bin/python3

################################################################################
################################ CONFIGURATION #################################
################################################################################


################################################################################
################################### IMPORTS ####################################
################################################################################

import atexit
from datetime import datetime, timedelta
import shutil
import os
import os.path
import subprocess
import sys

################################################################################
################################## CONSTANTS ###################################
################################################################################

HOURLY_DELTA = timedelta(hours=1)
DAILY_DELTA = 24 * HOURLY_DELTA
WEEKLY_DELTA = 7 * DAILY_DELTA
MONTHLY_DELTA = 4 * WEEKLY_DELTA
QUARTERLY_DELTA = 3 * MONTHLY_DELTA
YEARLY_DELTA = 4 * QUARTERLY_DELTA

DATETIME_FORMAT = '%Y-%m-%d @ %H:%M'

################################################################################
################################## FUNCTIONS ###################################
################################################################################

def binSnapshots(bin_boundary_generator, snapshots):
    '''Given a generator of the bin boundaries (going backwards in time), and a
       list of snapshots, returns a list with each element being a list that
       contains all of the snapshots that belong in the corresponding bin, and a
       list with the snapshots that were too far in the past to fit into any
       bin.
       
       NOTE: Both bin_boundary_generator and snapshots must already be sorted
             from the future to the past.
    '''
    now = datetime.now()
    i = 0
    
    # First, we skip past all of the snapshots that say that they were taken in
    # the future as there is no good way to handle them since they shouldn't
    # even exist.
    while i < len(snapshots) and snapshots[i] > now:
        log('Snapshot {} is in the future'.format(datetime.strftime(snapshots[i],DATETIME_FORMAT)))
        i += 1 
    
    # Now we sort the snapshots into bins.
    bins = []
    while i < len(snapshots):
        try:
            right_boundary = now + next(bin_boundary_generator)
        except StopIteration:
            break
        bin = []
        while i < len(snapshots) and snapshots[i] > right_boundary:
            bin.append(snapshots[i])
            i += 1
        bins.append(bin)

    # Return the binned snapshots, as well as any that taken past the last
    # bin boundary (i.e. those so far in the past that we don't want to keep
    # them anymore).
    return bins, snapshots[i:]
        

def createBoundaryGenerator(number_to_keep, delta):
    '''Given the number of bins to keep and their size, returns a generator
       that produces the boundaries of the bins ordered from the future to
       the past.
    '''
    if number_to_keep == 'infinite':
        # There is no maximum integer so we just pick a value larger than any
        # user is going to want.
        maximum = 1000000 
    else:
        maximum = number_to_keep
    for i in range(-1,-maximum,-1):
        yield i * delta

def generateBinBoundaries(boundary_generators):
    '''Returns a boundary generator made by merging all of the input boundary
       generators. You can model how this function works in your head by
       imagining that all of the input generators are turned into sets, unioned
       together, and then the resulting set is iterated over (where the ordering
       here is from the future to the past). The only reason why this function
       does not work in exactly that way is that generators are allowed to be
       infinite and so require special handling.
    '''
    boundary_generators = list(boundary_generators)
    boundaries = []
    empty_generator_indices = []
    for i, boundary_generator in enumerate(boundary_generators):
        try:
            boundaries.append(next(boundary_generator))
        except StopIteration:
            empty_generator_indices.append(i)
    for i in empty_generator_indices[::-1]:
        del boundary_generators[i]

    while boundaries:
        minimum_boundary = max(boundaries)
        yield minimum_boundary
        
        empty_generator_indices = []
        for i, boundary in enumerate(boundaries):
            if boundary == minimum_boundary:
                try:
                    boundaries[i] = next(boundary_generators[i])
                except StopIteration:
                    empty_generator_indices.append(i)
        for i in empty_generator_indices[::-1]:
            del boundaries[i]
            del boundary_generators[i]

def pruneSnapshots(snapshots,dry_run):
    '''Deletes all of the given snapshots.'''
    for snapshot in snapshots:
        snapshot_path = datetime.strftime(snapshot, DATETIME_FORMAT) 
        log('Pruning snapshot {}...'.format(snapshot_path))
        if not dry_run:
            shutil.rmtree(snapshot_path,True)

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

############################## Intervals to keep ###############################

hourly,
daily,
weekly,
monthly,
quarterly,
yearly,

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

    # Construct the bin boundary generator, which tells us how to place the
    # snapshots into the bins desired by the user.
    bin_boundary_generator = generateBinBoundaries(
        createBoundaryGenerator(number_to_keep, delta)
        for number_to_keep, delta in [
            (hourly, HOURLY_DELTA),
            (daily, DAILY_DELTA),
            (weekly, WEEKLY_DELTA),
            (monthly, MONTHLY_DELTA),
            (quarterly, QUARTERLY_DELTA),
            (yearly, YEARLY_DELTA),
        ]
    )

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

    # Now we assign the snapshots to bins.
    bins, far_past_snapshots = binSnapshots(bin_boundary_generator, snapshots)

    # In each bin, we prune all but the oldest snapshot. (Note that this means
    # that there will always be at least one snapshot kept.)
    for bin in bins:
        pruneSnapshots(bin[:-1],dry_run)

    # We also prune the snapshots that were too old to be placed in any bin.
    pruneSnapshots(far_past_snapshots,dry_run)

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
        [os.path.join(source_path,''),os.path.join(current_directory,''),
         '--link-dest={}'.format(os.path.join(snapshot_path,datetime.strftime(snapshots[0],DATETIME_FORMAT)))]
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