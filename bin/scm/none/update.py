"""
 
Updates a previously mounted repository
===============================================================================
usage: evie [common-opts] update [options] <dst> <repo> <origin> <id>

Arguments:
    <dst>            PARENT directory for where the copy-to-be-updated is
                     located.  The directory is specified as a relative path to
                     the root of primary repository.<pkg>            
    <repo>           Name of the repository to update
    <origin>         Path/URL to the repository
    <id>             Label/Tag/Hash/Version of code to be updated
    
Options:
    -b BRANCH        Specifies the source branch in <repo>.  The use/need
                     of this option in dependent on the <repo> SCM type.
                        
Options:
    -h, --help          Display help for this command

    
Notes:
    o The command MUST be run in the root of the primary respostiory.

"""
import os
import utils
from docopt.docopt import docopt


#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'mount', "Updates a previously mounted SCM Repository" ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)


    # Return 'error' since this is just a stub
    exit(1)
