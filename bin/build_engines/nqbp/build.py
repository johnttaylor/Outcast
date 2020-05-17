#!/usr/bin/env python
"""
Script to build projects using NQBP
===============================================================================
usage: build [options] here [<opts>...]
       build [options] PATTERN [<opts>...]
       build [options] --file BLDLIST

Options:
    here                 Builds all NQBP projects starting from the current 
                         working directory.
    <opts>               Option(s) to be passed directly to NQBP
    PATTERN              If a subdir under PRJDIR matches PATTERN, then that
                         directory is built.  Standard Python wildcards can
                         be used in the PATTERN.
    --p2 FILTER          An second filter that is AND'd with PATTERN to
                         filter which sub-directories get built. Standard Python 
                         wildcards can be used in the FILTER.
    --p3 FILTER          An third filter that is AND'd with PATTERN to
                         filter which sub-directories get built. Standard Python 
                         wildcards can be used in the FILTER.
    --path PRJDIR        The full path to the project directory of the 
                         projects to build.  If no path is specified, the
                         current working directory is used for the project
                         path.
    --exclude DIR        Excludes the specified sub directory. Standard Python 
                         wildcards can be used in the DIR
    --e2 DIR             Excludes an additional sub directory. Standard Python 
                         wildcards can be used in the DIR
    --e3 DIR             Excludes an additional sub directory. Standard Python 
                         wildcards can be used in the DIR
    --file BLDLIST       A text file containing a list of projects to build.
                         The format of file is a list of 'build' commands. 
                         Blank lines and line starting with '#' are skipped.
    --xconfig SCRIPT     Name and full path to the compiler config script.  If 
                         no script is provided then it is assume no additional 
                         config/setup is required.
    --config SCRIPT      Same as the '--xconfig' option, but the name and path 
                         are relative to the package root directory
    -v                   Be verbose 
    -h, --help           Display help for common options/usage
    
Examples:
    ; Builds all NQBP projects (and all 'variants') under the projects/ 
    ; directory that contain 'mingw' in their path.  The '--bld-all' option 
    ; is NQBP option.
    build --path \mywrkspace\mypkg\projects mingw --bld-all
    
    ; Builds the projects listed in the file 'mybuild.lst'
    build --file mybuild.lst
    
"""

from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import subprocess
import fnmatch

sys.path.append( os.path.dirname(__file__) + os.sep + ".." )
from docopt.docopt import docopt
import utils

NQBP_PRJ_DIR_MARKER1 = 'projects'
NQBP_PRJ_DIR_MARKER2 = 'tests'
NQBP_PKG_TOP         = 'top'


#------------------------------------------------------------------------------
# Begin 
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv, options_first=True)
    
    # Set quite & verbose modes
    #utils.set_quite_mode( args['-q'] )
    utils.set_verbose_mode( args['-v'] )

    # Default the projects/ dir path to the current working directory
    ppath = os.getcwd()
    
    # Project dir path is explicit set
    if ( args['--path'] ):
        ppath = args['--path']

    
    # Get superset of projects to build
    utils.push_dir( ppath )
    pkgroot  = _find_pkgroot( ppath )    
    all_prjs = utils.walk_file_list( "nqbp???", ppath )

    # Get project list from a file
    if ( args['--file'] ):
        try:
            inf = open( args['--file'], 'r' )

            # process all entries in the file        
            for line in inf:
               
                # drop comments and blank lines
                line = line.strip()
                if ( line.startswith('#') ):
                    continue
                if ( line == '' ):
                    continue
           
                # 'normalize' the file entries
                line = utils.standardize_dir_sep( line.strip() )
        
                # Process 'add' entries
                cmd = "bob.py " + line
                utils.run_shell( cmd, args['-v'], "ERROR: Build from File failed." )
    
            inf.close()
        
        except Exception as ex:
            exit( "ERROR: Unable to open build list: {}".format(args['--file']) )
        
    

    # The project list is from the command line
    else:
        # Only build the projects that match the pattern
        pattern = args['PATTERN']
        if ( args['here'] ):
            pattern = '*'
    
        # Apply the include/exclude filters
        jobs = _filter_prj_list( all_prjs, pattern, pkgroot, args['--exclude'], args['--e2'], args['--e3'], args['--p2'], args['--p3'] )
       
        # Run the Jobs serially
        for p in jobs:
            _build_project(p, args['-v'], args['<opts>'], args['--config'], args['--xconfig'], pkgroot )

    # restore original cwd
    utils.pop_dir()
    
#------------------------------------------------------------------------------
def _filter_prj_list( all_prj, pattern, pkgroot, exclude=None, exclude2=None, exclude3=None, p2=None, p3=None ):
    list = []
    for p in all_prj:
        relpath = p.replace(pkgroot,'')
        dirs    = relpath.split(os.sep)
        if ( len(fnmatch.filter(dirs,pattern))> 0 ):
            keep1 = True if exclude == None or len(fnmatch.filter(dirs,exclude)) == 0 else False
            keep2 = True if exclude2 == None or len(fnmatch.filter(dirs,exclude2)) == 0 else False
            keep3 = True if exclude3 == None or len(fnmatch.filter(dirs,exclude3)) == 0 else False
            keep4 = True if p2 == None or len(fnmatch.filter(dirs,p2)) > 0 else False
            keep5 = True if p3 == None or len(fnmatch.filter(dirs,p3)) > 0 else False
            if ( keep1 and keep2 and keep3 and keep4 and keep5 ):
                list.append( p )
            

    return list
    
def _build_project( prjdir, verbose, bldopts, config, xconfig, pkgroot ):
    # reconcile config options
    cfg = None
    if ( config ):
        cfg = os.path.join( pkgroot, config )
    elif ( xconfig ):
        cfg = xconfig
    
    utils.push_dir( os.path.dirname(prjdir) )
    print("BUILDING: "+ prjdir)
    cmd = 'nqbp.py ' + " ".join(bldopts)
    if ( config ):
        cmd = utils.concatenate_commands( cfg, cmd )
    utils.run_shell( cmd, verbose, "ERROR: Build failure ({})".format(cmd) )
    utils.pop_dir()


#-----------------------------------------------------------------------------
def _find_pkgroot( from_fname ):
    root = _get_marker_dir( utils.standardize_dir_sep(from_fname), NQBP_PRJ_DIR_MARKER1 )
    if ( root != None ):
        pass
    
    else:
        root = _get_marker_dir( utils.standardize_dir_sep(from_fname), NQBP_PRJ_DIR_MARKER2 )
        if ( root != None ):
            pass
            
        else:
            print(( "ERROR: Cannot find the 'Package Root' from: " + from_fname ))
            exit(1)
                
    return root
    
   
def _get_marker_dir( from_fname, marker ):
    path   = from_fname.split(os.sep)
    result = ''  
    idx    = 0  
    path.reverse()
    
    try:
        idx = path.index(marker)
        idx = len(path) - idx -1
        path.reverse()
        for d in path[1:idx]:
            result += os.sep + d
        
    except:
        result = None
    
    if ( result == None ):
        result = _test_for_top( result, marker )    
    return result
    

def _test_for_top( dir, marker ):
    while( dir != None ):
        if ( os.path.isdir(dir + os.sep + NQBP_PKG_TOP) ) :
            break
        else:
            dir = _get_marker_dir( dir, marker )
    
    return dir
