"""
 
Script that retrieves an SCM Repository as a local package
===============================================================================
usage: evie [common-opts] clone [options] <pkgname> <branch> <source>

Arguments:
    <pkgname>           Name of the package to retrieve
    <branch>            Specifies which branch to retrieve
    <source>            PATH is SCM specific information on the 'location' 
                        of the repository.

Options:
    --shallow           Clone a the repository with 'shallow history'. This
                        option reduces the amount of files and typically
                        only used when doing formal buildls
    --repo NAME         Name of the SCM repository if different from 
                        the <pkgname>
    -h, --help          Display help for this command

    
Notes:
    o The retrieved repository is located in the Workspace Root directory
    o Returns zero if the repository was succesfully retreived/cloned; else 
      non-zero is returned.  Note: if the pkgname already exists under the
      Workspace Root, the command will fail.
    
Examples (using GIT):
    evie clone colony.core dev-john https://github.com/johnttaylor

"""
import os
import utils
from docopt.docopt import docopt


#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( "clone", "Retrieves a SCM Repository to be used as local package" ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    # check if the pkg already exists in the workspace
    pkg = os.path.join( common_args['-w'], args['<pkgname>'] )
    if ( os.path.isfile(pkg) or os.path.isdir(pkg) ):
        exit( f'ERROR: The package ({pkg}) already exists in the Workspace.' )

    # Set repo name
    reponame = args['<pkgname>'] if ( args['--repo'] == None ) else args['--repo']

    # Set shallow option
    opts = '--depth 1' if ( args['--shallow'] ) else ''

    # Build GIT command
    cmd = f'git clone {opts} {args["<source>"]}/{reponame}.git {pkg}'
    t   = utils.run_shell( cmd, common_args['-v'] )
    _check_results( t, "ERROR: Failed the retreive/clone  the specified package/repository." )


def _check_results( t, err_msg ):
    if ( t[0] != 0 ):
        if ( t[1] != None and t[1] != 'None None' ):
            print(t[1])
        exit( err_msg )
