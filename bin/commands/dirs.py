"""
 
Manages the package's 'Owned' dirs
===============================================================================
usage: orc [common-opts] dirs [-s|-o]
       orc [common-opts] dirs [options] ls
       orc [common-opts] dirs [options] set <primarydirs>...
       orc [common-opts] dirs [options] rm  <primarydirs>...

Arguments:
    ls                  Calculates the package's owned directories
    set                 Sets (in the package.json file) top-level 'primary' 
                        directories that will be overlaid when the package is 
                        adopted (as an overlay pacakge).
    rm                  Removes (from the package.json file) top-level 'primary'
                        dirtectories that will be 'overlaid' when the package
                        is adopted (as an overlay pacakge).
    <primarydirs>       One or more top-level 'primary' directories 
    
Options:
    -u                  Update the 'pkg-dirs.lst' file with the 'ls' results
    -s                  Displays the current 'pkg-dirs.lst' instead of
                        deriving the package's owned directories
    -o                  Displays the current list of 'overlay' directories
                        defined for the package.
    -h, --help          Display help for this command

Common Options:
    See 'orc --help'
    
    
Examples:
    dirs ls
    dirs set src tests
    dirs rm tests
    
"""
import os, sys
import utils
from docopt.docopt import docopt
from my_globals import PKG_DIRS_FILE

#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'dirs', "Manages my package's 'Owned' directories" ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    # Show existing dirs file
    if ( args['-s'] ):
        dirs = utils.load_dirs_list_file()
        if ( dirs != None ):
            for d in dirs:
                print(d)
        
        sys.exit(0)

    # Show the currently defined overlay directories
    if ( args['-o'] ):
        show_primary_dirs()
        sys.exit(0)

    # Set directories
    if ( args['set'] ):
        newdirs = args['<primarydirs>']
        check_valid_primary_dirs( newdirs )
        package_json = utils.load_package_file();
        pdirs = utils.json_get_package_primary_dirs(package_json) 
        if ( pdirs == None ):
            utils.json_update_package_file_with_new_primary_dirs( package_json, newdirs )
        else:
            # Filter out would-be-duplicates
            for d in newdirs:
                if ( not d in pdirs ):
                    pdirs.append( d )

            # Sort the list and update the file
            pdirs.sort()
            utils.json_update_package_file_with_new_primary_dirs( package_json, pdirs )

        # Show update list
        show_primary_dirs()
        sys.exit(0)

    # Remove directories
    if ( args['rm'] ):
        rmdirs = args['<primarydirs>']
        package_json = utils.load_package_file();
        pdirs = utils.json_get_package_primary_dirs(package_json) 
        if ( pdirs == None ):
            pass
        else:
            # Delete dirs
            newlist = []
            for d in pdirs:
                if ( not d in rmdirs ):
                    newlist.append( d )

            # Sort the list and update the file
            newlist.sort()
            utils.json_update_package_file_with_new_primary_dirs( package_json, newlist )

        # Show update list
        show_primary_dirs()
        sys.exit(0)

    # derive directories
    if ( args['ls'] ):
        owndirs = utils.get_owned_dirs()
        for d in owndirs:
            print(d)

        # Update the directory list file
        if ( args['-u'] ):
            utils.save_dirs_list_file( owndirs )

        sys.exit(0)

#
def show_primary_dirs():
    package_json = utils.load_package_file();
    pdirs = utils.json_get_package_primary_dirs(package_json) 
    if ( pdirs == None ):
        print( "No primary directories are currently set for the package" )
    else:
        for d in pdirs:
            print( d )

#
def check_valid_primary_dirs( dirlist ):
    for d in dirlist:
        path = os.path.join( os.getcwd(), d )
        if ( not os.path.isdir( d ) ):
            sys.exit( f"ERROR: Directory {d}{os.sep} does not exists or is not a top-level directory" )
