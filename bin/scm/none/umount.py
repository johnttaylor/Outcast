"""
 
Removes a previously 'mounted' repository
===============================================================================
usage: evie [common-opts] mount [options] <dst> <repo> <origin> <id>

Arguments:
    <dst>            PARENT directory for where the package was mounted.  The
                     directory is specified as a relative path to the root
                     of primary repository.
    <repo>           Name of the repository to unmount
    <origin>         Path/URL to the repository
    <id>             Label/Tag/Hash/Version of code to be unmounted
    
Options:
    -p PKGNAME       Specifies the Package name if different from the <repo> 
                     name
    -b BRANCH        Specifies the source branch in <repo>.  The use/need
                     of this option in dependent on the <repo> SCM type.
                        
Options:
    -h, --help          Display help for this command

    
Notes:
    o The command MUST be run in the root of the primary respostiory.
    o This command only applied to repositories previously mounted using
      the 'mount' command.

"""
import os
import utils
from docopt.docopt import docopt


#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'umount', "Removes a previously 'mounted' SCM Repository" ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)


    # Return 'error' since this is just a stub
    exit(1)
