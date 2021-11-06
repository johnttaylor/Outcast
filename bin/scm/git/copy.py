""
import os, sys
import utils
from docopt.docopt import docopt
import scm.copy 
import scm.git.mount

#---------------------------------------------------------------------------------------------------------
def display_summary():
    scm.copy.display_summary()

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(scm.copy.USAGE, argv=cmd_argv)

    # Use the mount command so as to have consistent pre/post GIT behavior with adopting non-integrated packages
    if ( not args['--force'] ):
        cmd_argv[0] = 'mount'
        cmd_argv.insert(1, '--noro')
        scm.git.mount.run( common_args, cmd_argv )

    # Do a brute force copy
    else:
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