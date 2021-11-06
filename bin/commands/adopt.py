"""
 
Adopts the specified Repo/Package package
===============================================================================
usage: orc [common-opts] adopt [options] readonly <dst> <repo> <origin> <id>
       orc [common-opts] adopt [options] foreign  <dst> <repo> <origin> <id>               
       orc [common-opts] adopt [options] overlay  <repo> <origin> <id>

Arguments:
    <dst>            Parent directory for where the adopted package is placed. 
                     The directory is specified as a relative path to the root
                     of primary repository.    
    <repo>           Name of the repository to adopt
    <origin>         Path/URL to the repository
    <id>             Label/Tag/Hash/Version of code to be adopted
    
Options:
    --weak           Adopt the package as 'weak' dependencies.  The default is
                     to adopt as an 'immediate' dependency. A 'weak' dependency 
                     is not progated when determining transitive dependencies.
    --semver VER     Specifies the semantic version info for the package
                     being adopted. This information is not required, but
                     recommended if it is available.
    -p PKGNAME       Specifies the Package name if different from the <repo> 
                     name
    -b BRANCH        Specifies the source branch in <repo>.  The use/need
                     of this option in dependent on the <repo> SCM type.
    -h, --help       Display help for this command

Common Options:
    See 'orc --help'
    
    
Notes:

"""
import os, sys
import utils
import uuid
from docopt.docopt import docopt
from datetime import datetime, date, time, timezone
from my_globals import OVERLAY_PKGS_DIR
from my_globals import PACKAGE_INFO_DIR
from my_globals import TEMP_DIR_NAME

#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'adopt', "Adopts an external package" ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    # Default Package name
    pkg = args['<repo>']
    if ( args['-p'] ):
        pkg = args['-p']

    # default branch option
    branch_opt = ""
    if ( args['-b'] ):
        branch_opt = '-b ' + args['-b']

    # Get the current time
    dt_string = datetime.now().strftime("%Y %b %d %H:%M:%S")

    # check for already adopted
    deps = utils.load_package_file()
    if ( deps != None ):
        pkgobj, deptype, pkgidx = utils.json_find_dependency( deps, pkg )
        if ( pkgobj != None ):
            sys.exit( f'Package {pkg} already has been adopted as {deptype} dependency' );
    else:
        deps = { "immediateDeps":[], "weakDeps": []}
        
    # double check if the package has already been adopted (i.e. there was manual edits to the deps.json file)
    if ( not args['overlay'] ):
        dstpkg = os.path.join( args['<dst>'], pkg)
        if ( os.path.exists( dstpkg ) ):
            sys.exit( f"ERROR: The destination - {dstpkg} - already exists" )

    #
    # Adopt: Foreign
    # 
    if ( args['foreign'] ):
        # Copy the FO package
        cmd = f"evie.py --scm {common_args['--scm']} copy -p {pkg} {branch_opt} {args['<dst>']} {args['<repo>']} {args['<origin>']} {args['<id>']}"
        t   = utils.run_shell( cmd, common_args['-v'] )
        utils.check_results( t, f"ERROR: Failed to make a copy of the repo: {args['<repo>']}", 'copy', 'get-error-msg', common_args['--scm']  )

        # update the deps.json file
        d = utils.json_create_dep_entry( pkg, "foreign", args['<dst>'], dt_string, args['--semver'], args['-b'], args['<id>'], args['<repo>'], common_args['--scm'], args['<origin>'] )
        utils.json_update_package_file_with_new_dep_entry( deps, d, args['--weak'] )

        # Display parting message (if there is one)
        utils.display_scm_message( 'copy', 'get-success-msg', common_args['--scm'] )

    #
    # Adopt: ReadOnly 
    # 
    elif ( args['readonly'] ):
        # Mount the RO package
        cmd = f"evie.py --scm {common_args['--scm']} mount -p {pkg} {branch_opt} {args['<dst>']} {args['<repo>']} {args['<origin>']} {args['<id>']}"
        t   = utils.run_shell( cmd, common_args['-v'] )
        utils.check_results( t, f"ERROR: Failed to mount the repo: {args['<repo>']}", 'mount', 'get-error-msg', common_args['--scm'] )

        # update the deps.json file
        d = utils.json_create_dep_entry( pkg, "readonly", args['<dst>'], dt_string, args['--semver'], args['-b'], args['<id>'], args['<repo>'], common_args['--scm'], args['<origin>'] )
        utils.json_update_package_file_with_new_dep_entry( deps, d, args['--weak'] )

        # Mark files as readonly
        utils.set_tree_readonly( dstpkg )

        # Display parting message (if there is one)
        utils.display_scm_message( 'mount', 'get-success-msg', common_args['--scm'] )
        
    #
    # Adopt: overlay
    # 
    else:
        # Get a temporary copy of the OV package
        tmpdst = os.path.join( PACKAGE_INFO_DIR(), TEMP_DIR_NAME() )
        cmd = f"evie.py --scm {common_args['--scm']} copy --force -p {pkg} {branch_opt} {tmpdst} {args['<repo>']} {args['<origin>']} {args['<id>']}"
        t   = utils.run_shell( cmd, common_args['-v'] )
        utils.check_results( t, f"ERROR: Failed to make a copy of the repo: {args['<repo>']}", 'copy', 'get-error-msg', common_args['--scm']  )

        # Copy the adoptee's package info directory
        utils.copy_pkg_info_dir( os.path.join( OVERLAY_PKGS_DIR(), pkg, PACKAGE_INFO_DIR() ), os.path.join( tmpdst, pkg, PACKAGE_INFO_DIR() ) )

        # Get list of directories to copy/overlay
        d = utils.get_owned_dirs( os.path.join( tmpdst, pkg, PACKAGE_INFO_DIR()), os.path.join( tmpdst, pkg, OVERLAY_PKGS_DIR()), os.path.join( tmpdst, pkg ) )
        # do copy
        # update the adoptee's pkg-dirs.lst file 
        print(d)

        # update the deps.json file
        #d = utils.json_create_dep_entry( pkg, "overlay", args['<dst>'], dt_string, args['--semver'], args['-b'], args['<id>'], args['<repo>'], common_args['--scm'], args['<origin>'] )
        #utils.json_update_package_file_with_new_dep_entry( deps, d, args['--weak'] )
