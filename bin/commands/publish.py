"""
 
Publishes the Primary Package
===============================================================================
usage: orc [common-opts] publish [options] <semver> <comments>
       orc [common-opts] publish [options] 

Arguments:
    <semver>        The Semantic version information for the Published version
    <comments>      Publish comments

Options:
    --edit          Updates the 'current' publish information in place, i.e.
                    does not create a new version.  The date/time fields are
                    NOT updated.
    --edithist N    Updates the 'N' entry in the History array.  N is zero
                    based index. The date/time fields are NOT updated.
    -w              Suppress warning about missing files
    -h, --help      Display help for this command

Common Options:
    See 'orc --help'
    
    
Notes:
    o Publishing simply associates a comment/date/semantic-version with
      package at a point in time (i.e. only the package.json file is updated).
    o The user is responsible for archiving/labeling/tagging the package
      in its native SCM environment.
    o Publishing is not require for package management. However, life is
      better with respect to managing dependencies if packages are published.

"""
import os, json
import utils
from docopt.docopt import docopt
from my_globals import PACKAGE_INFO_DIR
from my_globals import PKG_DIRS_FILE
from my_globals import IGNORE_DIRS_FILE



#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'publish', 'Publishes the Primary package' ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    # Get the package data
    json_dict = utils.load_package_file()

    # Edit in place
    if ( args['--edit'] ):
        prev = utils.json_get_current_version( json_dict )
        v = utils.json_create_version_entry( args['<comments>'], args['<semver>'], prev['date'] )
        utils.json_update_current_version( json_dict, v )

    # Edit a history entry
    elif ( args['--edithist'] ):
        utils.json_update_history_version( json_dict, args['--edithist'],  args['<comments>'], args['<semver>'] )

    # Create new entry
    elif ( args['<semver>'] ):
        v = utils.json_create_version_entry( args['<comments>'], args['<semver>'] )
        utils.json_add_new_version( json_dict, v )
        
    # display publish info
    p = utils.json_get_published( json_dict )
    print( json.dumps(p, indent=2) )

    # Display warnings
    if ( not args['-w'] ):
        f = os.path.join(PACKAGE_INFO_DIR(), PKG_DIRS_FILE() )
        if ( not os.path.isfile( f )):
            print( f"Warning: NO {f} file has been created for the package.  See the 'orc dirs' command")
        f = os.path.join(PACKAGE_INFO_DIR(), IGNORE_DIRS_FILE() )
        if ( not os.path.isfile( f )):
            print( f"Warning: NO {f} file has been created for the package. Create using a text editor.")
            print( f"         The file has same semantics as a .gitignore file.")

    
