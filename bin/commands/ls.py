"""
 
Lists the adopted packages
===============================================================================
usage: orc [common-opts] ls [options] 

Arguments:
    
    
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
    print("{:<13}{}".format( 'ls', "Lists the adopted packages" ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    print("ls: work-in-progress")
        
        

