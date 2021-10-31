"""
 
Displays and Checks package dependencies
===============================================================================
usage: orc [common-opts] deps [options] 

Arguments:
    
    <change-type>
Options:
    -h, --help          Display help for this command

Common Options:
    See 'orc --help'
    
    
Notes:
    
"""
import os
import utils
from docopt.docopt import docopt

#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'deps', 'Displays and Checks package dependencies' ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    print("deps: work-in-progress")
    
