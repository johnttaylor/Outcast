#!/usr/bin/env python
"""
Null Script for building projects from Outcast
===============================================================================
usage: build [options] 

Options:
    -v                   Be verbose 
    -h, --help           Display help for common options/usage
    
Examples:
    
"""

import sys
import os
import subprocess

sys.path.append( os.path.dirname(__file__) + os.sep + ".." )
from docopt.docopt import docopt
import utils


#------------------------------------------------------------------------------
# Begin 
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv, options_first=True)
    
    print("NOP.  The 'None' build engine was selected")
