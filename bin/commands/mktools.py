"""
 
Creates a template tools/ directory (for package specific publish support)
===============================================================================
usage: orc [common-opts] mktools [options]


Options:
    --path DIR          Path of parent directory for the tools/ directory. The
                        default operation is to create the tools/ directory in
                        the current working directory.
    -o,--override       Overwrites the individual tools scripts if they already
                        exist
    -h, --help          Display help for this command


Common Options:
    See 'orc --help'


Notes:
    o Part of the publish process requires that the package is built without
      errors and tested.  What 'built' and 'tested' means is package specific.
      The scripts that are create are stub scripts that define the interface
      that the Orc engine requires to invoking the package specific hooks.
      
"""
import os, shutil
import utils
from docopt.docopt import docopt


#---------------------------------------------------------------------------------------------------------
def display_summary():
    print "{:<13}{}".format( 'mktools', 'Creates a template tools/ directory.' )
    
#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    # set the file path and name
    path = os.getcwd()
    if ( args['--path'] ) :
        path = args['--path']
    d = os.path.join( path, 'tools' )
    
    # Create the tools/ directory if it does not exist
    utils.mkdirs( d )
    
    # Get path to template scripts
    toolspath = os.path.join( os.path.dirname(__file__), "..", "..", 'templates', 'top', 'tools' )
   
    # Copy template scripts 
    scripts = utils.get_file_list( '*.py', toolspath )
    for f in scripts:
    
        # Check if file already exists
        fname = os.path.join( d, os.path.basename(f) )
        if ( os.path.isfile( fname ) ):
            if ( not args['--override'] ):
                utils.print_warning( "Skipping File: {} (it already exists).".format( fname ) )
                continue
            else:
                utils.print_warning( "Overwriting file: {}.".format( fname ) )
        
        # copy file    
        shutil.copy( f, fname )
            
    
 