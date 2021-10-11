"""
 
Creates a semi-tracked/local copy of the specified repository/branch/reference
===============================================================================
usage: evie [common-opts] mount [options] <dst> <repo> <origin> <id>

Arguments:
    <dst>            Parent directory for where the copy is placed.
    <repo>           Name of the repository to mount
    <origin>         Path/URL to the repository
    <id>             Label/Tag/Hash/Version of code to be mounted
    
Options:
    -p PKGNAME       Specifies the Package name if different from the <repo> 
                     name
    -b BRANCH        Specifies the source branch in <repo>.  The use/need
                     of this option in dependent on the <repo> SCM type.
                        
Options:
    -h, --help          Display help for this command

    
Notes:
    o The command MUST be run in the root of the primary respostiory.
    o The 'mount' command is different from the 'copy' in that creates
      semi-tracked clone of the repository which can be updated directly from
      the source <repo> at a later date (think git subtrees)

"""
import os
import utils
from docopt.docopt import docopt


#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'mount', "Creates a semi-tracked/local copy of a SCM Repository" ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)


    # Return 'error' since this is just a stub
    exit(1)
