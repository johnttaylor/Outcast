"""
 
Moves existing readonly or foreign adopted packages.
===============================================================================
usage: orc [common-opts] mv <pkg> <dst>

Arguments:
    <pkg>       Existing adopted package to move.  ONLY readonly and foreign 
                packages can be moved with this command.
    <dst>       Parent directory of where the adopted package will be moved to. 
                The directory is specified as a relative path to the root of 
                primary repository.    

Options:
    -h, --help       Display help for this command

Common Options:
    See 'orc --help'
    
    
Notes:
    
"""
import os, sys
import utils, shutil
from docopt.docopt import docopt

#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'ls', "Moves existing readonly or foreign adopted packages." ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    # Get the list of adopted packages
    deps = utils.load_deps_file()
    if ( deps == None ):
        sys.exit( 'ERROR: No packages have been adopted' )

    # Make sure the package is adopted and the it is 'moveable'
    pkg = args["<pkg>"]
    deps = utils.load_deps_file()
    if ( deps == None ):
        sys.exit( 'ERROR: No packages have been adopted' )
    pkgobj, deptype, pkgidx = utils.json_find_dependency( deps, pkg )
    if ( pkgobj == None ):
        sys.exit( f"ERROR: Package ({args['<pkg>']}) not adopted." )
    if ( pkgobj['pkgtype'] == 'overlay' ):
        sys.exit( "ERROR: The mv command cannot move an overlay package" )

    # Make sure that '<dst>' does NOT already exist
    if ( not os.path.isdir( args['<dst>'] ) ):
        sys.exit( f"ERROR: The parent directory ({args['<dst>']}) does NOT exist" )

    # Make sure that '<pkg>' does NOT already exist under '<dst>'
    dst = os.path.join( args['<dst>'], args["<pkg>"] )
    if ( os.path.exists( dst ) ):
        sys.exit( f"ERROR: {args['<dst>']} already exists under {args['<dst>']}" )


    # Physically move the package
    src = os.path.join( pkgobj["parentDir"], args["<pkg>"]  ) 
    try:
        shutil.move( src, dst )
    except Exception as e:
        sys.exit( f"ERROR: Unable to move the package ({e})" )

    # Update the package in the deps list
    pkgobj['parentDir'] = args['<dst>']
    deps[deptype].pop(pkgidx)
    utils.json_update_deps_file_with_new_entry( deps, pkgobj, is_weak_dep = True if deptype=='weakDeps' else False )
    utils.write_deps_file( deps )
    print( f"Package {src} moved to {dst}" )

