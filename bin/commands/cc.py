"""
 
Lists the supported compiler toolchain
===============================================================================
usage: orc [common-opts] cc [options] <pkgname>
       orc [common-opts] cc [options] <pkgname> <compiler>

Arguments:
    <pkgname>           Name of package to being queried
    <compiler>          When specified, outputs a string that can be executed
                        as shell command to set the environment to use the
                        specified compiler.
                                            
Options:
    -v          
    -h, --help          Display help for this command

Common Options:
    See 'orc --help'

Notes:
    o This command is intended to be executed using the Host Orc Wrapper (e.g.
      'orcw').
    o If a '.' is used for <pkgname> then <pkgname> is derived from the
      the current working directory where the command was invoked from.  

"""
from docopt.docopt import docopt
import subprocess, os, tarfile, sys
import utils, deps

#---------------------------------------------------------------------------------------------------------
def display_summary():
    print "{:<13}{}".format( 'cc', 'Lists the supported compilers.' )
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    # Trap the '.' notation for <pkgname> argument
    utils.check_use_current_package( args )
    
    compilers = os.path.join(common_args['-w'], args['<pkgname>'], 'top', 'compilers' )
    file_list = utils.get_file_list( "*.bat", compilers )
            
    
    # List support compilers
    if ( args['<compiler>'] == None ):
        _list_compilers(file_list)

    # Generate 'command' output
    else:
        cc =_find_in_list( args['<compiler>'], file_list )
        if ( cc == None ):
            print "Error: The specified compiler ({}) is not supported".format( cc )
            _list_compilers( file_list )
        else:
            print ".run: " + cc
    
    
#------------------------------------------------------------------------------
def _list_compilers(file_list):
    for f in file_list:
        temp = os.path.splitext(f)[0]
        print os.path.basename(temp)

def _find_in_list( compiler, file_list ):
    for f in file_list:
        temp = os.path.splitext(f)[0]
        name = os.path.basename(temp)
        if ( compiler == name ):
            return f

    return None
