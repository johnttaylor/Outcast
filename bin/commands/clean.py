"""
 
Runs the specifcied Package's 'clean all' script
===============================================================================
usage: orc [common-opts] clean [options] <pkgname>

Arguments:
    <pkgname>           Package name in the current Workspace to operate on.
                        
Options:
    -h, --help          Display help for this command

Common Options:
    See 'orc --help'


Notes:
    o If a '.' is used for <pkgname> then <pkgname> is derived from the
      the current working directory where the command was invoked from.  
        
"""
from docopt.docopt import docopt
import subprocess, os, tarfile
import utils, deps

#---------------------------------------------------------------------------------------------------------
def display_summary():
    print "{:<13}{}".format( 'clean', "Runs the package's clean all script." )
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    # Trap the '.' notation for <pkgname> argument
    utils.check_use_current_package( args )

    # Executes the packages build script  
    pkgroot = os.path.join( common_args['-w'], args['<pkgname>'] )
    script  = os.path.join( pkgroot, 'top', 'tools', 'clean.py' )
    cmd = "{} {}".format(script, pkgroot )
    t   = utils.run_shell( cmd, common_args['-v'] )
    _check_results( t, "ERROR: Failed Cleaning." )
    
    
    
#------------------------------------------------------------------------------
def _check_results( t, err_msg ):
    if ( t[0] != 0 ):
        if ( t[1] != None and t[1] != 'None None' ):
            print t[1]
        exit( err_msg )
        
        