"""
 
Returns the root directory of the current local repository
===============================================================================
usage: evie [common-opts] findroot

Options:
    -h, --help          Display help for this command

    
Notes:
    o The command MUST be run within the local repository.

"""
import os
import utils
from docopt.docopt import docopt


#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'findroot', "Returns the root directory of the current local repository" ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    # Return 'error' since this is just a stub
    exit(1)
