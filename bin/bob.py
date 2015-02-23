#! /usr/bin/env python
"""
 
Bob is an Outcast wrapper for invoking a package's build engine
===============================================================================
usage: bob [options] build [<args>...]
       bob [--qry]
       bob [--help]

Options:
    <args>               Command line args that a specific to the underlying
    -b ENGINE            Explicitly sets the build engine type [default: nqbp]. 
    --qry                Lists the supported build engines
    -h, --help           Displays this information

Notes:
    o Type 'bob build -h' for help on option specific to the selected build
      engine.
      
"""

import sys
import os
from subprocess import call

from docopt.docopt import docopt
import utils

from my_globals import BOB_VERSION
from my_globals import OUTCAST_PKGS_UVERSE
from my_globals import OUTCAST_UVERSE_TYPE



#------------------------------------------------------------------------------
def load_command( btype ):
    try:
        command_module = __import__("build_engines.{}.build".format(btype), fromlist=['build'])
    except ImportError:
        exit("'{}' is not a supported Build Engine. Use 'bob --qry' for list of supported build engines.".format( btype) )

    return command_module
        
        
#------------------------------------------------------------------------------
def display_build_engine_list():
    print( ' ' )
    print( "Type 'bob build --help' for build details. Type 'bob --help' for base usage." )
    print( "-------------------------------------------------------------------------------" )
    bpath = os.path.join( os.path.dirname(__file__), 'build_engines' )
    if ( os.path.exists( bpath ) ):
        files = os.listdir(bpath)
        for f in files:
            if ( os.path.isdir(os.path.join(bpath,f)) ):
                print f
      
    print( ' ' )

#------------------------------------------------------------------------------
# Parse command line
args = docopt(__doc__, version=BOB_VERSION(), options_first=True )

# Display list of build engines supported
if ( args['--qry'] ):
    display_build_engine_list()
        

# Trap no command specified        
elif ( not args['build'] ):
        docopt(__doc__,argv=['--help'])
    

# Invoke build engine
else:
    load_command( args['-b'] ).run( args, args['<args>'] )


    