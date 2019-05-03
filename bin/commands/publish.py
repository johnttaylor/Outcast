"""
 
Publishes a Package to the Native Outcast Universe
===============================================================================
usage: orc [common-opts] publish [options] --major <pkgname> <summary>
       orc [common-opts] publish [options] --minor <pkgname> <summary>
       orc [common-opts] publish [options] --patch <pkgname> <summary>
       orc [common-opts] publish [options] --version VER <pkgname> <summary>
       orc [common-opts] publish [options] --revert <pkgname> 


Arguments:
    <pkgname>           Name of package to publish
    --patch             Publish as a patch, i.e. increment the existing patch 
                        index.
    --minor             Publish as an additive content change, i.e. increment 
                        the existing minor index.
    --major             Publish as break in compatiblity change, i.e. increment 
                        the existing major index.
    --version VER       Sets the version number explicitly.  Note: Can include
                        a prelease identifier.                    
    <summary>           Summary/short comments (enclose in quotes)
    --revert            This option is used to clean-up after a failed publish
                        attempt.  It does no harm to call the publish command
                        with the --revert option even if there is nothing to
                        clean-up.
    
Options:
    --prerelease VAL    Publishes the package with a prelease value of 'VAL'.
                        This option is ONLY valid when using 'major', 'minor',
                        'patch' publish options.
    --comments FILE     Includes additional comments from FILE
    --pkgroot PATH      Explicit path to the package's root directory.  If not
                        specified, the package root is assume to be the Workspace 
                        directory.
    --label PREFIX      Prefix to use when generating the SCM label. 
                        [Default: OUTCAST_]
    --format FMT        Sets the compressor format to FMT [Default: gztar]
    --vault VFILE       The contents of VFILE specify which Package Vault to 
                        publish the package to.  The default is used to your
                        site's default Package Vault.
    -o, --override      If the package already exists in the Native Package
                        Universe or Package Vault - overwrite current contents.
    --retry             USE THIS COMMAND WITH CAUTION.  This option essential
                        runs the '--revert' command first and the performs the
                        attempts the publish with the '--overrride' option
                        turned on.
    --dry-run           Peforms all of the publish steps EXCEPT no changes and
                        or updates are made to the package specification, 
                        Package Vault or Package Universe.
    --nopending         Skips enforcing that no pending changes to the SCM 
                        repository before publishing
    --nodeps            Skips checking/verifying the package's dependencies
    --nogetdeps         Skips pulling and mounting dependent packages.
    --noclean           Does not executes the package's top/tools/clean script
    --notests           Does not executes the package's top/tools/tests script
    --nobuild           Does not executes the package's top/tools/build script
    --nons              Does not update the packages's pkg.namespaces AND does
                        not check for namespace collisions.
    --nonewer           Does not enforce the requirement that the publish 
                        version be newer than the last publish of the package
                        on the branch.
    --keeptars          When this option is set AND the --dry-run option is 
                        set, then the generated tar files are NOT deleted when
                        the script ends.  The typical use of this option is for
                        use with build machines.
    --ci script         This is used when performing Continious Integration 
                        builds to provide additional actions just after the
                        get dependencies step and just prior to executings the
                        packagees 'clean' script.  In addition, this option 
                        enables the '--dry-run' switch.

                  
    -h, --help          Display help for this command

Common Options:
    See 'orc --help'
    
    
Notes:
    o It is STRONGLY recommended to NOT USE the any of the '--noxxx' options!
    o If a '.' is used for <pkgname> then <pkgname> is derived from the
      the current working directory where the command was invoked from.  
     
    
    
"""
import os
import shutil
import time
import configparser
import symlinks
import utils
import deps
from docopt.docopt import docopt

from my_globals import OUTCAST_XPKGS_DIRNAME
from my_globals import OUTCAST_XINC_DIRNAME
from my_globals import OUTCAST_LOCAL_PKG_SUFFIX
from my_globals import OUTCAST_TOP_DIR

toptar = ''
pkgtar = ''
scmlabel = ''

#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'publish', 'Publishes a Package to the Native Outcast Universe.' ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)
    
    # Trap the '.' notation for <pkgname> argument
    utils.check_use_current_package( args )

    # Force the dry-run option when the --ci option is set
    if ( args['--ci'] != None ):
        args['--dry-run'] = True

    # Capture publish time
    now, local = utils.mark_time(common_args['--now'])

    
    # House keeping
    override   = '--override' if args['--override'] else ""
    root       = args['--pkgroot'] if args['--pkgroot'] else common_args['-w']
    pkgroot    = os.path.join( root, args['<pkgname>'] )
    pathtop    = os.path.join( pkgroot, OUTCAST_TOP_DIR() )
    pathtools  = os.path.join( pathtop, "tools" )
    pkg_spec   = os.path.join( pathtop, "pkg.specification" )
    chg_log    = os.path.join( pathtop, "pkg.journal" )
    br_log     = os.path.join( pathtop, "pkg.branching" )
    namespaces = os.path.join( pathtop, "pkg.namespaces" )
    cwd        = os.getcwd()
    checkin_ns = ""
    
    
    # set vault file
    if ( not args['--vault'] ):
        args['--vault'] = os.path.join( common_args['--uverse'], "default.vault" )

    # REVERT
    if ( args['--revert'] or args['--retry'] ):
        print("= Reverting SCM checkouts...")
        cmd = 'evie.py -v -w {} revert {} {} {}'.format( root, args['<pkgname>'], pkg_spec, chg_log )
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed revert of SCM checkouts.", cleanall_flag=False )
        _clean_up(all=False)
        if ( not args['--retry'] ):
            exit(0)
        
        # If I get here than retry option has been set -->so force the override option to be on
        args['--override'] = True
        override           = '--override'        
        
    # PUBLISH
    utils.push_dir( pathtop )

    # Get info from the pkg.branching file
    bname  = None
    minver = None
    if ( os.path.isfile(br_log) ):
        try:
            fd = open( br_log, 'r' )
            bname, minver = utils.get_branch_and_min_ver_info( fd, br_log )
            fd.close()
    
        except Exception as ex:
            exit( "ERROR: Unable to open branch log file: {} ({})".format(br_log,ex) )


    # Read the current pkg.specification (also determines branch/version# for the publish operation) 
    global scmlabel
    ver, bname, cfg = _read_package_spec( args, pkg_spec, bname, minver )
    pkgname         = "{}-{}-{}".format( args['<pkgname>'], bname, ver )
    scmlabel        = args['--label'] + pkgname
    

    # Ensure the Native Package universe is current
    if ( not common_args['--norefresh'] ):
        print("= Refreshing the Native Package Universes...")
        cmd = 'ceres.py -v -w {} --user "{}" --passwd "{}" --now {} refresh'.format(root, common_args['--user'], common_args['--passwd'], now )
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed Refresh the Native Package Universe." )


    # New publish version# MUST be the latest on the branch (i.e. can't publish "back in time" or duplicate publish)
    if ( not args['--nonewer'] ):
        _enforce_newer( common_args['--uverse'], args['<pkgname>'], bname, ver )


    # Check for pending checkings
    if ( not args['--nopending'] ):
        print("= Checking for pending changes...")
        cmd = 'evie.py -v -w {} --user "{}" --passwd "{}" --now {} pending {}'.format( root, common_args['--user'], common_args['--passwd'], now, args['<pkgname>'] )
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed pending check." )
        
    # Check dependencies
    if ( not args['--nodeps'] ):
        print("= Checking dependencies...")
        cmd = 'orc.py -v -w {} --user "{}" --passwd "{}" --norefresh --now {} checkdeps'.format(root, common_args['--user'], common_args['--passwd'], now ) 
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed the dependency check." )
        
    # get needed dependencies
    if ( not args['--nogetdeps'] ):
        print("= Getting dependencies...")
        cmd = 'orc.py -v -w {} --user "{}" --passwd "{}" --norefresh --now {} getdeps {} --override'.format(root, common_args['--user'], common_args['--passwd'], now, args['<pkgname>'] ) 
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed getting (and mounting) dependencies." )

    # Run CI script (when provided)
    if ( args['--ci'] != None ):
        print("= Continiouse Integration (CI) script ...") 
        cmd = args['--ci']
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed CI script." )
            
    # Clean everthing before building
    if ( not args['--noclean'] ):
        print("= Pre-cleaning...") 
        p   = os.path.join( pathtools, "clean.py" )
        cmd = "{} {}".format(p, pkgroot )
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed Pre-clean." )
                   
    # Build...
    if ( not args['--nobuild'] ):
        print("= Building...")
        p   = os.path.join( pathtools, "build.py" )
        cmd = "{} {}".format(p, pkgroot )
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed Building." )
                   
    # Update namespaces (I do this after the build to handle the case of autogen'd source code)
    if ( not args['--nons'] ):
        print("= Updating pkg.namespaces...")
        checkin_ns = namespaces
        cmd = 'evie.py -v -w {} --user "{}" --passwd "{}" --now {} checkout {} {}'.format(root, common_args['--user'], common_args['--passwd'], now, args['<pkgname>'], namespaces )
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed SCM checkout of {}.".format(namespaces) )
        p   = os.path.join( pathtools, "namespaces.py" )
        cmd = "{} {}".format(p, pkgroot )
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed to update pkg.namespaces (error with tools/namespaces.py)." )

        # Check for namespace collisions
        print("= Check for namespace collisions...")
        cmd = 'orc.py -v -w {} --user "{}" --passwd "{}" --norefresh --now {} namespaces --check'.format(root, common_args['--user'], common_args['--passwd'], now ) 
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed the namespace collision check." )
          
    # Test...
    if ( not args['--notests'] ):
        print("= Run tests...")
        p   = os.path.join( pathtools, "test.py" )
        cmd = "{} {}".format(p, pkgroot )
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed tests." )

    # Clean everthing before archiving/publishing
    if ( not args['--noclean'] ):
        print("= Post-cleaning...") 
        p   = os.path.join( pathtools, "clean.py" )
        cmd = "{} {}".format(p, pkgroot )
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed Pre-clean." )
                   

    # edit pkg.specification 
    print("= Updating pkg.specification...")
    cmd = 'evie.py -v -w {} --user "{}" --passwd "{}" --now {} checkout {} {}'.format(root, common_args['--user'], common_args['--passwd'], now, args['<pkgname>'], pkg_spec )
    t   = utils.run_shell( cmd, common_args['-v'] )
    _check_results( t, "ERROR: Failed SCM checkout of {}.".format(pkg_spec) )
    _update_package_spec( pkg_spec, cfg )
    
    # update changelog
    if ( args['--dry-run'] ):
        print("= Updating pkg.journal... SKIPPING (dry-run)")
    else:
        print("= Updating pkg.journal...")
        cmd = 'evie.py -v -w {} --user "{}" --passwd "{}" --now {} checkout {} {}'.format(root, common_args['--user'], common_args['--passwd'], now, args['<pkgname>'], chg_log )
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed SCM checkout of {}.".format(chg_log) )
        utils.update_journal_publish( chg_log, common_args['--user'], args['<summary>'], args['--comments'], ver, bname, scmlabel )
        
    # Archive the package
    print("= Archiving the package...")
    global pkgtar
    pkgtar = os.path.join( cwd, pkgname + "." + args['--format'] )
    cmd = 'evie.py -v -w {} --user "{}" --passwd "{}" --now {} archive {} --format {} {} {}'.format(root, common_args['--user'], common_args['--passwd'], now, override, args['--format'], args['<pkgname>'], pkgtar )
    t   = utils.run_shell( cmd, common_args['-v'] )
    _check_results( t, "ERROR: Failed Archiving package." )

    # Archive the top directory
    print("= Archiving the package's top/ directory...")
    global toptar
    toptar = os.path.join( cwd, pkgname + "." + OUTCAST_TOP_DIR() )
    cmd = 'evie.py -v -w {} --user "{}" --passwd "{}" --now {} archive {} --format {} -d {} {} {} '.format(root, common_args['--user'], common_args['--passwd'], now, override, args['--format'], OUTCAST_TOP_DIR(), args['<pkgname>'], toptar )
    t   = utils.run_shell( cmd, common_args['-v'] )
    _check_results( t, "ERROR: Failed Archiving package top/ directory." )
    
    # Trap 'dry-run'
    if ( args['--dry-run'] ):
        print("= Pushing package archive to the Package Vault... SKIPPING (dry-run)") 
        print("= Distributing the Package Top file to the Native and Foreigh Package Universes... SKIPPING (dry-run)") 
        print("= Checkin files and labeling the package in the SCM repository... SKIPPING (dry-run)")
        print("Completed DRY-RUN of publish of: ", pkgname)
        cmd = 'evie.py -v -w {} revert {} {} {}'.format( root, args['<pkgname>'], pkg_spec, chg_log )
        utils.run_shell( cmd, common_args['-v'] )
        _clean_up(True, args)
        
    else:
        # push archive to the vault
        print("= Pushing package archive to the Package Vault...")
        cmd = 'orc.py -v -w {} --user "{}" --passwd "{}" --now {} pushv --vault {} {} {}'.format(root, common_args['--user'], common_args['--passwd'], now, args['--vault'], override, pkgtar )
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed pushing package archive to the Package Vault." )

        # copy the top file to the native package universe
        print("= Distributing the Package Top file to the Native and Foreigh Package Universes...")
        cmd = 'ceres.py -v -w {} --user "{}" --passwd "{}" --now {} distribute {} {} "{}"'.format(root, common_args['--user'], common_args['--passwd'], now, override, toptar, args['<summary>'] )
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed Updating the Native Package Universe." )
   
        
        # Checkin files
        print("= Checkin files and labeling the package in the SCM repository...")
        cmd = 'evie.py -v -w {} --user "{}" --passwd "{}" --now {} checkin {} {} {} "{}" {} {} {}'.format(root, common_args['--user'], common_args['--passwd'], now, override, args['<pkgname>'], scmlabel, args['<summary>'], pkg_spec, chg_log, checkin_ns )
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed Checking and Labeling in the SCM repository." )
    
        # All Done!
        print("Completed publish of:", pkgname)
        _clean_up(all=False)
    
    
#------------------------------------------------------------------------------
def _clean_up(all=True, args=None):
    keeptars = False
    if ( args != None ):
        if ( args['--keeptars'] ):
            keeptars = True

    global pkgtar
    if ( os.path.isfile(pkgtar) and keeptars == False ):
        os.remove( pkgtar )
            
    global toptar
    if ( os.path.isfile(toptar) and keeptars == False ):
        os.remove( toptar )

    if ( all ):
        global scmlabel
        cmd = 'evie.py -v label delete {}'.format( scmlabel )
        utils.run_shell( cmd )
            

def _check_results( t, err_msg, cleanall_flag=True ):
    if ( t[0] != 0 ):
        if ( t[1] != None and t[1] != 'None None' ):
            print(t[1])
        _clean_up(cleanall_flag)
        exit( err_msg )

def _read_package_spec( args, pkg_spec, bname, minver ):
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.optionxform = str
    cfg.read( pkg_spec )
    
    pkginfo = deps.read_info( cfg, pkg_spec, "n/a" )
    
    # Make sure that the pkg.branching file and pkg.specification agree on the branch
    if ( bname != None ):
        if ( bname != pkginfo['branch'] ):
            exit( "ERROR: The latest branch ({}) in the branch history does not match branch info ({}) the pkg.specification file".format( bname, pkginfp['branch'] ))
            
    # explicity set the version
    if ( args['--version'] ):
        version = args['--version']
        
        # Warning if new version does not meet the minver requirement (as defined by the branch history)
        if ( minver != None and not utils.is_ver1_backwards_compatible_with_ver2( version, minver ) ):
            utils.print_warning( "Discrepancy between the branch history minver ({}) requirement and the version ({})being published.".format( minver, version ) )

    # incrementally bump the version number 
    else:
        version = utils.increment_version( pkginfo['version'], inc_major=args['--major'], inc_minor=args['--minor'], inc_patch=['--patch'], new_prelease=args['--prerelease'] )

        # Make sure it meet the minver requirement (as defined by the branch history)
        if ( minver != None and not utils.is_ver1_backwards_compatible_with_ver2( version, minver ) ):
            exit( "ERROR: Discrepancy between the branch history minver ({}) requirement and the version ({})being published.".format( minver, version ) )

    # Update (in RAM) the package spec file
    now, local = utils.get_marked_time()
    cfg.set( 'info', 'version', version )
    cfg.set( 'info', 'pubtime', now )
    cfg.set( 'info', 'pubtimelocal', local )
     
    # return the publish version
    return version, pkginfo['branch'], cfg


def _update_package_spec( pkg_spec, cfg ):
    # Update the pkg.specification file
    with open( pkg_spec, 'w' ) as cfgfile:
        cfg.write(cfgfile)
        cfgfile.close()

    
def _enforce_newer( uverse, pkgname, bname, ver ):

    # Get list of package for the specified package/branch
    files = utils.get_file_list( "{}-{}-*.top".format(pkgname,bname), uverse )
    pkgs  = []
    for f in files:
        p,e = os.path.splitext(os.path.basename(f))
        t   = utils.parse_package_name( p )
        pkgs.append(t[2])
  
    for x in pkgs:
        if ( utils.numerically_compare_versions(ver,x) < 1 ):
            exit( "Version to be publisehd ({}) is not newer than previously published version(s) ({}).".format(ver,x) )
            
    

