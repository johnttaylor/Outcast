"""
 
Creates a semi-tracked/local copy of the specified repository/branch/reference
===============================================================================
usage: evie [common-opts] mount [options] <dst> <repo> <origin> <id>

Arguments:
    <dst>            PARENT directory for where the copy is placed.  The
                     directory is specified as a relative path to the root
                     of primary repository.
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

    # -b option is not supported/needed
    if ( args['-b'] != None ):
        sys.exit( "The '-b' option is not supported/needed.  Use a 'remote-ref' as the <id> argument" )

    # Default Package name
    pkg = args['<repo>']
    if ( args['-p'] ):
        pkg = args['-p']

    # Make sure the Parent destination directory exists
    dst = args['<dst>'] 
    utils.mkdirs( dst )
    
    # Set directory for the subtree directory
    dst = os.path.join( dst, pkg )
    dst = utils.force_unix_dir_sep(dst)
    utils.print_verbose( f"Destination for the copy: {dst}" )

    # Create a 'subtree'
    cmd = f'git subtree add --prefix {dst} {args["<origin>"]}/{args["<repo>"]}.git {args["<id>"]} --squash'
    t = utils.run_shell( cmd, common_args['-v'] )
    if ( utils.is_error(t) ):   # Clean-up dst dir if there was failure
        utils.remove_tree( dst ) 
    utils.check_results( t, "ERROR: Failed the create a subtree for the specified package/repository." )
