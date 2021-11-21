"""
 
Adopts the specified Repo/Package package
===============================================================================
usage: orc [common-opts] adopt [options] readonly <dst> <repo> <origin> <id>
       orc [common-opts] adopt [options] foreign  <dst> <repo> <origin> <id>               
       orc [common-opts] adopt [options] overlay  <repo> <origin> <id>
       orc [common-opts] adopt [options] clean 

Arguments:
    readonly         Adopts the specified package as a readonly package
    foreign          Adopts the specified package as a foreign package
    overlay          Adopts the specified package as a overlay package
    clean            Cleans up after a fail adoption of a OVERLAY package.
    <dst>            Parent directory for where the adopted package is placed. 
                     The directory is specified as a relative path to the root
                     of primary repository.    
    <repo>           Name of the repository to adopt
    <origin>         Path/URL to the repository
    <id>             Label/Tag/Hash/Version of code to be adopted
    
Options:
    --weak           Adopt the package as 'weak' dependencies.  The default is
                     to adopt as an 'strong' dependency. A 'weak' dependency 
                     is not progated when determining transitive dependencies.
    --semver VER     Specifies the semantic version info for the package
                     being adopted. This information is not required, but
                     recommended if it is available. NOTE: If the package being
                     adopted has an Outcast package.json file - then the adopt
                     command will attempt to use the adoptee's published
                     semantic vesion info.
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
from my_globals import PACKAGE_FILE
from my_globals import PKG_DIRS_FILE
from my_globals import IGNORE_DIRS_FILE
from my_globals import PACKAGE_ROOT


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

    # CLEAN-UP (for a failed overlay adoption)
    if ( args['clean'] ):
        tmpdst = os.path.join( PACKAGE_ROOT(), PACKAGE_INFO_DIR(), TEMP_DIR_NAME() )
        utils.remove_tree( tmpdst, "error", "warn" )
        sys.exit(0)

    # default branch option
    branch_opt = ""
    if ( args['-b'] ):
        branch_opt = '-b ' + args['-b']

    # Get the current time
    dt_string = datetime.now().strftime("%Y %b %d %H:%M:%S")

    # check for already adopted
    json_dict = utils.load_package_file()
    pkgobj, deptype, pkgidx = utils.json_find_dependency( json_dict, pkg )
    if ( pkgobj != None ):
        sys.exit( f'Package {pkg} already has been adopted as {deptype} dependency' );
        
    # double check if the package has already been adopted (i.e. there was manual edits to the package.json file)
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

        # update the package.json file
        dst_pkg_info    = os.path.join( args['<dst>'], pkg, PACKAGE_INFO_DIR() )
        incoming_semver = utils.get_adopted_semver( dst_pkg_info, args['--semver'] )
        d = utils.json_create_dep_entry( pkg, "foreign", args['<dst>'], dt_string, incoming_semver, args['-b'], args['<id>'], args['<repo>'], common_args['--scm'], args['<origin>'] )
        utils.json_update_package_file_with_new_dep_entry( json_dict, d, args['--weak'] )

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

        # update the package.json file
        dst_pkg_info    = os.path.join( args['<dst>'], pkg, PACKAGE_INFO_DIR() )
        incoming_semver = utils.get_adopted_semver( dst_pkg_info, args['--semver'] )
        d = utils.json_create_dep_entry( pkg, "readonly", args['<dst>'], dt_string, incoming_semver, args['-b'], args['<id>'], args['<repo>'], common_args['--scm'], args['<origin>'] )
        utils.json_update_package_file_with_new_dep_entry( json_dict, d, args['--weak'] )

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

        # Fail if missing outcast info
        src_pkg      = os.path.join( tmpdst, pkg )
        dst_pkg      = os.path.join( OVERLAY_PKGS_DIR(), pkg )
        dst_pkg_info = os.path.join( dst_pkg, PACKAGE_INFO_DIR() )
        src_pkg_info = os.path.join( src_pkg, PACKAGE_INFO_DIR() )
        if ( not os.path.isfile( os.path.join(src_pkg_info, PACKAGE_FILE() ) ) ):
            utils.remove_tree(tmpdst)
            sys.exit( f"ERROR: Package - {pkg} - does NOT have {PACKAGE_FILE()} file")
        if ( not os.path.isfile( os.path.join(src_pkg_info, PKG_DIRS_FILE() ) )):
            utils.remove_tree(tmpdst)
            sys.exit( f"ERROR: Package - {pkg} - does NOT have {PKG_DIRS_FILE()} file")
        if ( not os.path.isfile( os.path.join(src_pkg_info, IGNORE_DIRS_FILE() ) )):
            utils.remove_tree(tmpdst)
            sys.exit( f"ERROR: Package - {pkg} - does NOT have {IGNORE_DIRS_FILE()} file")

        # Copy the adoptee's package info directory
        utils.copy_pkg_info_dir( dst_pkg_info, src_pkg_info )

        # Copy the adoptee's extra info directories
        utils.copy_extra_dirs( dst_pkg, src_pkg )

        # Get list of directories to copy/overlay
        dirs = utils.get_owned_dirs( os.path.join( tmpdst, pkg ), os.path.join( tmpdst, pkg, PACKAGE_INFO_DIR()), os.path.join( tmpdst, pkg, OVERLAY_PKGS_DIR()) )
        utils.save_dirs_list_file( dirs, path=src_pkg_info )
        for d in dirs:
            src = os.path.join( src_pkg, d )
            dst = os.path.join( PACKAGE_ROOT(), d )
            utils.copy_files( src, dst )

        # Clean-up
        utils.remove_tree( tmpdst )

        # update the package.json file
        incoming_semver = utils.get_adopted_semver( dst_pkg_info, args['--semver'] )
        d = utils.json_create_dep_entry( pkg, "overlay", args['<dst>'], dt_string, incoming_semver, args['-b'], args['<id>'], args['<repo>'], common_args['--scm'], args['<origin>'] )
        utils.json_update_package_file_with_new_dep_entry( json_dict, d, args['--weak'] )
        print( f"Package - {pkg} - adopted as an OVERLAY package. Remember to add the new files to your SCM" )
