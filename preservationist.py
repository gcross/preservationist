#!/usr/bin/python3

################################################################################
################################ CONFIGURATION #################################
################################################################################


################################################################################
################################### IMPORTS ####################################
################################################################################

from collections import abc, namedtuple
from datetime import datetime, timedelta
import shutil
import time
import os
import os.path
import subprocess
import sys

################################################################################
############################# CONFIGURATION CLASSES ############################
################################################################################

class _infinite:
    pass
infinite = _infinite()


class exponential:
    def __init__(self,base=2):
        self.base = base

################################################################################
################################## CONSTANTS ###################################
################################################################################

HOURLY_DELTA = timedelta(hours=-1)
DAILY_DELTA = 24 * HOURLY_DELTA
WEEKLY_DELTA = 7 * DAILY_DELTA
MONTHLY_DELTA = 4 * WEEKLY_DELTA
QUARTERLY_DELTA = 3 * MONTHLY_DELTA
YEARLY_DELTA = 4 * QUARTERLY_DELTA

TIME_FORMAT = '%Y-%m-%d @ %H:%M'

################################################################################
################################## FUNCTIONS ###################################
################################################################################

def binSnapshots(bin_boundary_generator, snapshots):
    '''Given a generator of the bin boundaries (going backwards in time), and a
       list of snapshots, returns a list with the snapshots in each bin and a
       list with the snapshots that were too far in the past to fit into any
       bin.
       
       NOTE: both bin_boundary_generator and snapshots must be sorted from the
            future to the past
    '''
    now = datetime.now()
    i = 0
    
    # First, we skip past all of the snapshots that say that they were taken in
    # the future as there is no good way to handle them since they shouldn't
    # even exist.
    while i < len(snapshots) and snapshots[i] < now:
        print('Snapshot {} is in the future'.format(datetime.strftime(TIME_FORMAT,snapshots[i])))
        i += 1 
    
    # Now we sort the snapshots into bins.
    bins = []
    while i < len(snapshots):
        try:
            right_boundary = next(bin_boundary_generator)
        except StopIteration:
            break
        bin = []
        while snapshots[i] < right_boundary:
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
    if isinstance(number_to_keep,abc.Container):
        yield from generateBinBoundaries(createBoundaryGenerator(n, delta) for n in number_to_keep)
    elif number_to_keep is infinite:
        # There is no maximum integer so we just pick a value larger than any
        # user is going to want.
        maximum = 1000000 
    elif isinstance(number_to_keep,exponential):
        i = -1
        while True:
            print("exp yield",i*delta)
            yield i * delta
            i *= number_to_keep.base
    else:
        maximum = number_to_keep
    for i in range(-1,maximum,-1):
        yield i * delta

def generateBinBoundaries(boundary_generators):
    '''Returns a boundary generator made by merging all of the input
       boundary generators. You can model how this function works in
       your head by imagining that all of the input generators are
       turned into sets, unioned together, and then the resulting
       set is iterated over (where the ordering here is from the
       future to the past.
    '''
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
        minimum_boundary = min(boundaries)
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
        snapshot_path = datetime.strftime(snapshot, TIME_FORMAT) 
        print('Pruning snapshot {}...'.format(snapshot_path))
        if not dry_run:
            shutil.rmtree(snapshot_path,True)

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
    # First, check to see if another protectionist process is already active.
    i_am_active = os.path.join(snapshot_path,'i_am_active')
    if os.path.exists(i_am_active):
        print('Another preservationist process is already running, so I will abort.')
        print('(If this is not true, then delete i_am_active in the snapshots directory.)')
        return

    try:
        # Create a file that signifies that we are active in the snapshots
        # directory.
        open(i_am_active,'a').close()

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
        # interpret every directory whose date follows the time format as being
        # a snapshot and ignore everything else.
        snapshots = []
        for potential_snapshot in os.listdir(snapshot_path):
            try:
                snapshots.append(time.strptime(potential_snapshot, TIME_FORMAT))
            except ValueError:
                pass
        
        # Sort the snapshots from future to past (i.e., going backwards in
        # time).
        snapshots.sort()
        snapshots.reverse()
        
        # Now we sort the snapshots into bins
        bins, far_past_snapshots = binSnapshots(bin_boundary_generator, snapshots)
        
        # In each bin, we prune all but the oldest snapshot.
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
            [os.path.join(source_path,''),os.path.join(current_directory,'')]
        )
        print('Running {}...'.format(' '.join(run_rsync)))
        if not dry_run:
            process = subprocess.Popen(run_rsync,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            for line in process.stdout:
                print(line.decode('utf-8'),end='')
            return_code = process.wait()
            if return_code != 0:
                print("Failed to run rsync: return code {}".format(return_code))
                return

        # Rename the new snapshot
        snapshot = datetime.strftime(datetime.now(),TIME_FORMAT)
        print('Renaming {} to {}...'.format(current_directory,os.path.join(snapshot_path,snapshot)))
        if not dry_run:
            os.rename(current_directory,snapshot)
    finally:
        if os.path.exists(i_am_active):
            os.remove(i_am_active)