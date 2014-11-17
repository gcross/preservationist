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

# The directory where the backup snapshots should be stored.
snapshot_directory = '/backups/snapshots',

# The command to run rsync.
rsync_command = 'rsync',

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