""
import os, sys
import utils
from docopt.docopt import docopt
import scm.copy 
import scm.git.mount

#---------------------------------------------------------------------------------------------------------
def display_summary():
    scm.copy.display_summary()

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(scm.copy.USAGE, argv=cmd_argv)

    # Use the mount command so as to have consistent pre/post GIT behavior with adopting non-integrated packages
    cmd_argv[0] = 'mount'
    cmd_argv.insert(1, '--noro')
    scm.git.mount.run( common_args, cmd_argv )
