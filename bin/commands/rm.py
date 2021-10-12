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


#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'rm', 'Removes an adopted package' ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    # Look up the details of the package to be removed
    pkg = args['<adoptedpkg>']
    deps = utils.load_deps_file()
    if ( deps == None ):
        sys.exit( 'ERROR: No packages have been adopted' )
    pkgobj = utils.json_get_package( deps['immediateDeps'], pkg )
    if ( pkgobj == None ):
        pkgobj = utils.json_get_package( deps['weakDeps'], pkg )
        if ( pkgobj == None ):
            sys.exit( f'Cannot find the package - {pkg} - in the list of adopted packages' );

    # default branch option
    branch_opt = ""
    if ( pkgobj['version']['branch'] != None ):
        branch_opt = '-b ' + args['-b']

    # READONLY Package
    if ( pkgobj['pkgtype'] == 'readonly' ):
        if ( pkgobj['parentDir'] == None ):
            sys.exit( "ERROR: the deps.json file is corrupt - there is no parent directory for the package" )

        cmd = f"evie.py --scm {pkgobj['repo']['type']} umount -p {pkgobj['pkgname']} {branch_opt} {pkgobj['parentDir']} {pkgobj['repo']['name']} {pkgobj['repo']['origin']} {pkgobj['version']['tag']}"
        t   = utils.run_shell( cmd, common_args['-v'] )
        utils.check_results( t, f"ERROR: Failed to umount the repo: {pkgobj['repo']['name']}" )
        
    # FOREIGN Package
    elif ( pkgobj['pkgtype'] == 'foreign' ):
        pass

    # OVERALY Package
    elif ( pkgobj['pkgtype'] == 'overlay' ):
        pass

    # Unsupported package type
    else:
        sys.exit( f"ERROR: Unsupport package type: {pkgobj['pkgtype']}. The deps.json file has been corrupted" )

