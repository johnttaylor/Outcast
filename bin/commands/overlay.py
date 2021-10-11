"""
 
Adopts the specified Repo/Package package
===============================================================================
usage: orc [common-opts] adopt [options] readonly <repo> <origin> <id>
       orc [common-opts] adopt [options] forgeign <repo> <origin> <id>               
       orc [common-opts] adopt [options] overlay  <repo> <origin> <id>
Arguments:
    <repo>           Name of the repository to adopt
    <origin>         Path/URL to the repository
    <id>             Label/Tag/Hash/Version of code to be adopted
    
Options:
    -p PKGNAME       Specifies the Package name if different from the <repo> 
                     name
    -b BRANCH        Specifies the source branch in <repo>.  The use/need
                     of this option in dependent on the <repo> SCM type.
    -h, --help       Display help for this command

Common Options:
    See 'orc --help'
    
    
Notes:
    
"""
import os
import utils
from docopt.docopt import docopt

#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'adopt', "Adopts an external package" ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    print("adopt: work-in-progress")
        

