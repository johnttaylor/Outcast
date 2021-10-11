"""
 
Removes an adopted package
===============================================================================
usage: orc [common-opts] rm [options] <adoptedpkg>

Arguments:
    <adoptedpkg>        Name of an adopted package to be removed
    
Options:
    -h, --help          Display help for this command

Common Options:
    See 'orc --help'x`
    
    
Notes:
    o If  <adoptedpkg> is not speficied, then the repository's primary 
      package information is displayed.
    
"""
import os
import utils
from docopt.docopt import docopt


#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'rm', 'Removes an adopted package' ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    print("rm: work-in-progress")
        

