#!/usr/bin/python3
################################# INSTRUCTIONS #################################
# To use this script, customize the settings, and then copy it to someplace    #
# where it can be run by cron or some other scheduler.                         #
################################################################################

################################################################################
#################################### WARNING ###################################
################################################################################
###   THIS SYSTEM DOES NOT HAVE ANY POLICIES FOR DELETING BACKUPS WHEN THE   ###
###    HARD DRIVE RUNS OUT OF SPACE!!! IF THIS HAPPENS, THEN BACKUPS WILL    ###
### CEASE. IT IS YOUR JOB TO MAKE SURE THAT THE BACKUP DRIVE IS NOT RUNNING  ###
###  OUT OF SPACE. IF IT DOES RUN OUT OF SPACE, THEN DELETE BACKUPS YOU NO   ###
### LONGER WANT MANUALLY, AND/OR LOWER THE NUMBER OF SNAPSHOTS THAT YOU KEEP.###
################################################################################
#################################### WARNING ###################################
################################################################################

from preservationist import run

run(
#################################### Paths #####################################

# The source path that you want to backup.
source_path = '/',

# The path where the backup snapshots should be stored.
snapshot_path = '/backups/snapshots',

# The command to run rsync.
rsync_command = 'rsync',

############################## Intervals to keep ###############################

# These values indicate which snapshots will be kept. For example, if hourly=10
# then there will be at most one snapshot kept per hour for the first 10 hours
# in the past.

# The lengths are all integer multiples of each other:
#   * a day is 24 hours
#   * a week is 7 days
#   * a month is 4 weeks
#   * a quarter is 3 months
#   * a year is 4 quarters
# This was done for two reasons.  First, because it is a lot simpler than
# invoking the calendar in all of the datetime calculations.  Second, because
# otherwise there would be gaps between intervals caused by one length not being
# a multiple of the others. So for example, if you let weekly=4 and monthly=1
# then there would in general be 2-3 days between the end of the last week and
# the end of the month if we didn't let a month be exactly 4 weeks.

# If the number of intervals is so few that they do not add up to the length of
# the next longer interval you are keeping --- for example, if hourly=10,
# daily=0 and weekly=1 --- then the leftover space between the end of the last
# interval you are keeping and the end of the first interval of the next longest
# interval you are keeping will form its own interval from which only one
# snapshot will be kept. So for example, if hourly=10, daily=0, and weekly=2,
# then at most one snapshot will be kept in each of the first ten hours in the
# past, the time from ten hours in the past to one week in the past, and the
# time from one week in the past to two weeks in the past. Note that this means
# that if hourly=24 and daily=1 then daily=1 is redundant (though it doesn't
# hurt).

# If the number of intervals is so many that they add up to more than some other
# length for which you are keeping intervals, then the smaller length intervals
# will subdivide the larger intervals. So for example if hourly=48 and daily=3
# then exactly one snapshot will be kept for each of the first 48 hours in the
# past and also for the time between the beginning and the end of the third day
# in the past.

# If you use the value 'infinite', then there will be an infinite number of that
# interval kept, so for example setting monthly='infinite' means that a snapshot
# will be kept for every month as long as the hard drive doesn't fill up. These
# intervals will subdivide all longer intervals (as described in the previous
# paragraph), making them redundant, so for example if monthly='infinite' then
# the quarterly and yearly intervals are redundant as they would just be
# subdivided into monthly intervals.

# If the number of intervals is zero, then no intervals of its length will be
# considered for keeping snapshots. There a couple of reasons why one might want
# to do this. First, when a non-zero number would be redundant because, for
# example, an infinite amount of one of the smaller intervals is being kept.
# Second, if one cares about keeping short-term backups to be able to recover
# from recent mistake and long-term backups to recover files far in the past,
# but not medium-term backups.

hourly = 24,
daily = 7,
weekly = 4,
monthly = 12,
quarterly = 'infinite',
yearly = 0,

#################################### Rsync #####################################

# Short and long options to be passed to rsync.
#
# If you want to check that rsync is doing the right thing when you have first
# set this system up, you can add 'v' to the short options to have rsync show
# all of the files it is copying.
rsync_short_options = '-aAX',
rsync_long_options = [
    '--delete',
    '--numeric-ids',
    '--relative',
    '--delete-excluded',
],

# Files to be included that are not accessible from the source path.
include = [],

# Files to be excluded from the backups.
exclude = [
    '/backups/*',
    '/dev/*',
    '/proc/*',
    '/sys/*',
    '/tmp/*',
    '/run/*',
    '/mnt/*',
    '/media/*',
    '/lost+found/*',
    '/home/*/.local/share/Trash/*',
],

################################ Miscellaneous #################################

# If this is true, then this script only prints out what it would do; it does
# not perform any I/O nor does it call rsync.
dry_run = True,

################################################################################
)