"""
 
Displays/Derives the directory list for the Primary package's 'Owned' dirs
===============================================================================
usage: orc [common-opts] dirs [options] <dir>

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
    print("{:<13}{}".format( 'dirs', "Displays/derives my package's 'Owned' directories" ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    #print("dirs: work-in-progress")
    f = os.path.join( os.getcwd(), 'myignore.txt' )
    dirs =utils.walk_dir_ignored( args['<dir>'], f )
    for d in dirs:
        print(d)
        

