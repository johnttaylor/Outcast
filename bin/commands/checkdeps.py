"""
 
Checks a pkg.specification file for valid dependencies
===============================================================================
usage: orc [common-opts] checkdeps [options] 
       orc [common-opts] checkdeps [options] <pkgname>

Options:
    <pkgname>           Package name in the current Workspace to check.  If no 
                        <pkgname> is specified, it is assumed that the CWD is
                        in the top/ directory of a locak package - and that
                        local package is the package run checkdeps on.
    --dot               Generate two '.dot' that can be rendered by GraphViz.
    --graph FORMAT      Converts the GraphViz '.dot' files to the specified
                        document FORMAT.  Example 'formats': "pdf", "svg"
                        Note: the '--graph' option does an implicit '--dot'
    --print             Display the package dependency trees on the console
    --nocheck           Skips most error checking and produces just the '.dot'
                        files.  Note: Some error checking can not be bypassed,
                        e.g. cyclic dependency check.
    -h, --help          Display help for this command

Common Options:
    See 'orc --help'


Notes:
    o Two '.dot' files are created: 'derived' and 'actual'.  The 'derived' tree 
      contains all dependencies as defined by the package's 1st level 
      dependencies and all of the subsequent dependencies as defined by the
      transitive packages' dependencies.  The 'actual' tree contains the 
      dependencies as enumerated solely by package's 'pkg.specification' file.
    o A prefix of '*' on a package name indicates that the package is a weak
      dependency or is transitive of only weak dependencies.
    o The version numbers show on the 'dervied' graph is the minimum required
      vesion.  The 'actual' graph shows what version where installed when the
      package was pushed.
    o For more details about GraphViz, see http://www.graphviz.org/
    
        
"""
from docopt.docopt import docopt
import subprocess, os
import utils, deps

#---------------------------------------------------------------------------------------------------------
def display_summary():
    print "{:<13}{}".format( 'checkdeps', 'Checks a pkg.specification file for valid dependencies.' )
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)
    
    # Local to the package's top/ directory
    file = 'pkg.specification'

    # Explicity local package name     
    if ( args['<pkgname>'] ):
        path = os.path.join( common_args['-w'], args['<pkgname>'], 'top' )
        if ( not os.path.isdir( path ) ):
            exit( "ERROR: Invalid <pkgname> ({})".format( path ) )
        utils.push_dir( path )
        
    # Ensure the Native Package universe is current
    if ( not common_args['--norefresh'] ):
        cmd = 'ceres.py -v -w {} --user "{}" --passwd "{}" refresh'.format(common_args['-w'], common_args['--user'], common_args['--passwd'] )
        t   = utils.run_shell( cmd, common_args['-v'] )
        _check_results( t, "ERROR: Failed Refresh the Native Package Universe." )


    p, d,w,t, cfg = deps.read_package_spec( file )
    dep_tree, act_tree = deps.validate_dependencies( p, d,w,t, common_args, args['--nocheck'], file )
    if ( not args['--nocheck'] ):
        print "All dependency checks PASSED."
    else:
        print "SKIPPED one or more dependency checks."
         
    # generate .DOT file
    if ( args['--dot'] or args['--graph'] ):
        _create_dot_file( file, "derived", dep_tree, args['--graph'] )
        _create_dot_file( file, "actual", act_tree, args['--graph'] )


    if ( args['--print'] ):
        print "Derived Transitive tree."
        print dep_tree
        if ( not args['--nocheck'] ):
            print "Actual Package tree."
            print act_tree

    
    
    
    
#------------------------------------------------------------------------------
def _create_dot_file( file, qualifier, tree, graph_opt ):
    # create .DOT file
    oname = file + "." + qualifier + ".dot"
    deps.create_dot_file( oname, tree )
    
    # generate the visual graph as a XXX file
    utils.render_dot_file_as_pic( graph_opt, oname )


#------------------------------------------------------------------------------
def _check_results( t, err_msg ):
    if ( t[0] != 0 ):
        if ( t[1] != None and t[1] != 'None None' ):
            print t[1]
        exit( err_msg )
