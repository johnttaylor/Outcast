"""
 
Removes an adopted package
===============================================================================
usage: orc [common-opts] rm [options] <adoptedpkg>

Arguments:
    <adoptedpkg>        Name of an adopted package to be removed
    
Options:
    -h, --help          Display help for this command

Common Options:
    See 'orc --help'
    
    
Notes:
    o If  <adoptedpkg> is not speficied, then the repository's primary 
      package information is displayed.
    
"""
import os, sys
import utils
from docopt.docopt import docopt
from my_globals import PACKAGE_FILE


#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'rm', 'Removes an adopted package' ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    # Look up the details of the package to be removed
    pkg = args['<adoptedpkg>']
    deps = utils.load_package_file()
    if ( deps == None ):
        sys.exit( 'ERROR: No packages have been adopted' )
    pkgobj, deptype, pkgidx = utils.json_find_dependency( deps, pkg )
    if ( pkgobj == None ):
        sys.exit( f'Cannot find the package - {pkg} - in the list of adopted packages' );

    # default branch option
    branch_opt = ""
    if ( pkgobj['version']['branch'] != None ):
        branch_opt = '-b ' + args['-b']

    # READONLY Package
    if ( pkgobj['pkgtype'] == 'readonly' ):
        if ( pkgobj['parentDir'] == None ):
            sys.exit( f"ERROR: the {PACKAGE_FILE()} file is corrupt - there is no parent directory for the package" )

        # Remove the package
        cmd = f"evie.py --scm {pkgobj['repo']['type']} umount -p {pkgobj['pkgname']} {branch_opt} {pkgobj['parentDir']} {pkgobj['repo']['name']} {pkgobj['repo']['origin']} {pkgobj['version']['tag']}"
        t   = utils.run_shell( cmd, common_args['-v'] )
        utils.check_results( t, f"ERROR: Failed to umount the repo: {pkgobj['repo']['name']}, 'umount', 'get-error-msg', common_args['--scm']" )
        
        # Remove the package from the deps list
        deps[deptype].pop(pkgidx)
        utils.write_package_file( deps )

        # Display parting message (if there is one)
        utils.display_scm_message( 'umount', 'get-success-msg', common_args['--scm'] )

    # FOREIGN Package
    elif ( pkgobj['pkgtype'] == 'foreign' ):
        if ( pkgobj['parentDir'] == None ):
            sys.exit( f"ERROR: the {PACKAGE_FILE()} file is corrupt - there is no parent directory for the package" )

        # Remove the package
        cmd = f"evie.py --scm {pkgobj['repo']['type']} rm -p {pkgobj['pkgname']} {branch_opt} {pkgobj['parentDir']} {pkgobj['repo']['name']} {pkgobj['repo']['origin']} {pkgobj['version']['tag']}"
        t   = utils.run_shell( cmd, common_args['-v'] )
        utils.check_results( t, f"ERROR: Failed to remove the package: {pkgobj['repo']['name']}, 'rm', 'get-error-msg', common_args['--scm']" )
        
        # Remove the package from the deps list
        deps[deptype].pop(pkgidx)
        utils.write_package_file( deps )

        # Display parting message (if there is one)
        utils.display_scm_message( 'rm', 'get-success-msg', common_args['--scm'] )

    # OVERALY Package
    elif ( pkgobj['pkgtype'] == 'overlay' ):
        pass

    # Unsupported package type
    else:
        sys.exit( f"ERROR: Unsupport package type: {pkgobj['pkgtype']}. The {PACKAGE_FILE()} file has been corrupted" )

