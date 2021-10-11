"""
 
Publishes the Primary Package
===============================================================================
usage: orc [common-opts] publish [options] <semver> <comments>

Arguments:
    <semver>        The Semantic version information for the Published version
    <comments>      Publish comments

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
    print("{:<13}{}".format( 'publish', 'Publishes the Primary package' ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    print("publish: work-in-progress")
        

