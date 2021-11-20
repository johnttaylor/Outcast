"""
 
Checks and manages a package dependencies
===============================================================================
usage: orc [common-opts] deps [options] check
       orc [common-opts] deps [options] show <adoptedpkg>
       orc [common-opts] deps [options] mv <pkg> 

Arguments:
    check               Checks for any missing dependencies
    show                Displays the transitive dependencies incurred via
                        the specified adopted package
    mv                  Moves an existing package dependency from immeidate
                        to weak and vice-versus
    <adoptedpkg>        Name of a adopted package
    <pkg>               Name of package to move

Options:
    --noweak            Skip checking weak dependencies
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
    print("{:<13}{}".format( 'deps', 'Checks and manages a package dependencies' ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    print("deps: work-in-progress")
    
