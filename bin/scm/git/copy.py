
"""
Creates a non-tracked/local copy of the specified repository/branch/reference
===============================================================================
usage: evie [common-opts] copy [options] <dst> <repo> <origin> <id>

Arguments:
    <dst>            Parent directory for where the copy is placed. The
                     directory is specified as a relative path to the root
                     of primary repository.
    <repo>           Name of the repository to copy.
    <origin>         Path/URL to the repository.
    <id>             Label/Tag/Hash/Version of code to be copied.
    
Options:
    -p PKGNAME       Specifies the Package name if different from the <repo> 
                     name
    -b BRANCH        Specifies the source branch in <repo>.  The use/need
                     of this option in dependent on the <repo> SCM type.
                       
Options:
    -h, --help       Display help for this command.

    
Notes:
    o The command MUST be run in the root of the primary respostiory.
    
"""
import os, sys
import utils
from docopt.docopt import docopt


#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'copy', "Creates a non-tracked/local copy of a SCM Repository" ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    # -b option is not supported/needed
    if ( args['-b'] != None ):
        sys.exit( "The '-b' option is not supported/needed.  Use a 'remote-ref' as the <id> argument" )

    # Default Package name
    pkg = args['<repo>']
    if ( args['-p'] ):
        pkg = args['-p']

    # Make sure the destination directory exists
    dst = os.path.join( os.getcwd(), args['<dst>'] )
    utils.print_verbose( f"Destination for the copy: {dst}" )
    utils.mkdirs( dst )

    # Create a clone of the repo
    # NOTE: I hate cloning the entire repo - but I have not found a way to get JUST a snapshot by a remote-ref
    cmd = f'git clone -n {args["<origin>"]}/{args["<repo>"]}.git {pkg}'
    utils.push_dir( dst )
    t = utils.run_shell( cmd, common_args['-v'] )
    utils.pop_dir()    
    if ( utils.is_error(t) ):   # Clean-up dst dir if there was failure
        utils.remove_tree( dst ) 
    utils.check_results( t, "ERROR: Failed the retreive/clone the specified package/repository." )

    # Checkout the desire tag/branch/remote-ref
    cmd = f'git checkout {args["<id>"]}'
    utils.push_dir( os.path.join( dst, pkg ) )
    t = utils.run_shell( cmd, common_args['-v'] )
    utils.pop_dir()    

    # Remove the .git directoy since this is a non-tracked copy
    gitdir = os.path.join( dst, pkg, ".git" )
    utils.remove_tree( gitdir, warn_msg="Not able to remove the .git directory for local copy" )
