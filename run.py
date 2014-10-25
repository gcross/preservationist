#!/usr/bin/python3

from preservationist import run

run(
#################################### Paths #####################################

source_path = '/',
snapshot_path = '/backups/internal/snapshots',
rsync_command = 'rsync',

############################## Intervals to keep ###############################

# If you use the value infinite, then there will be an infinite number of that
# interval kept; e.g. setting monthly to infinite means that a snapshot will be
# kept for every month as long as the hard drive doesn't fill up. Note that if
# you set a particular interval to infinite then the values of the intervals
# below it won't matter (as they are an integer multiple of it), so i.e. if you
# set monthly to infinite then there will also be infinitely many kept quarterly
# and yearly snapshots as well.

hourly = 24,
daily = 7,
weekly = 4,
monthly = 12,
quarterly = 'infinite',
yearly = 0,

#################################### Rsync #####################################

rsync_short_options = '-aAXv',
rsync_long_options = [
    '--delete',
    '--numeric-ids',
    '--relative',
    '--delete-excluded',
],

include = [],

exclude = [
    '/backups/',
    '/dev/*',
    '/proc/*',
    '/sys/*',
    '/tmp/*',
    '/run/*',
    '/mnt/*',
    '/media/*',
    '/lost+found/*',
    '/home/*/.local/share/Trash/*',
    '/fasthome/*/.local/share/Trash/*',
    '/home/gcross/JungleDisk',
],

################################ Miscellaneous #################################

dry_run = False,

################################################################################
)