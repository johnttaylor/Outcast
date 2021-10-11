"""
 
Adopts the specified Repo/Package package
===============================================================================
usage: orc [common-opts] adopt [options] readonly <dst> <repo> <origin> <id>
       orc [common-opts] adopt [options] foreign <dst> <repo> <origin> <id>               
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
                     is not required to be progated when determining transitive 
                     dependencies.
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
import os
import utils
from docopt.docopt import docopt
from datetime import datetime, date, time, timezone

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

    # Get the current time
    dt_string = datetime.now().strftime("%Y %b %d %H:%M:%S")

    # check for already adopted
    deps = utils.load_deps_file()
    if ( deps != None ):
        if ( json_get_package( deps['immediateDeps'], pkg ) != None ):
            sys.exit( f'Package {pkg} already has been adopted as immediate dependency' );
        if ( json_get_package( deps['weakDeps'], pkg ) != None ):
            sys.exit( f'Package {pkg} already has been adopted as weak dependency' );

    #
    # Adopt: Foreign
    #
    if ( args['foreign'] ):
        # Copy the FO package
        # update the deps.json file
        d = utils.json_create_dep_entry( pkg, "foreign", args['<dst>'], dt_string, args['--semver'], args['-b'], args['<id>'], args['<repo>'], common_args['--scm'], args['<origin>'] )
        print(d)

        # clean-up if error

        

