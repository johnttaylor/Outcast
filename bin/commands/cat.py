"""
 
Displays information about the specified package
===============================================================================
usage: orc [common-opts] cat [options] 
       orc [common-opts] cat [options] <adoptedpkg>

Arguments:
    <adoptedpkg>        Name of an adopted package to inspect
    
Options:
    -h, --help          Display help for this command

Common Options:
    See 'orc --help'
    
    
Notes:
    o If  <adoptedpkg> is not speficied, then the repository's primary 
      package information is displayed.
    
"""
import os
import utils
from docopt.docopt import docopt


#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'cat', 'Displays information for a package' ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    print("cat: work-in-progress")
        

