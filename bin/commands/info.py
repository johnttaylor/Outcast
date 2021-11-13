"""
 
Sets/Updates the Package description and basic information fields
===============================================================================
usage: orc [common-opts] info <desc> <owner> <email> <url>
       orc [common-opts] info <desc> <owner> <email> <url> <rname> <rtype> <rorigin>
       orc [common-opts] info [options]

Arguments:
    <desc>              Brief description of the package. 
    <owner>             Name of principle contact/owner of the package
    <email>             Email address for the <owner>
    <url>               URL of home page for the package
    <rname>             Repository name
    <rtype>             Repository type (e.g. 'git')
    <rorigin>           Reposiotyr origina (e.g. https://github.com/johnttaylor)
    
Options:
    --desc    DESC      Update the description field
    --owner   NAME      Update the owner field
    --email   ADDR      Update the owner email field
    --url     PATH      Update the package's URL field
    --rname   NAME      Update the repository name ield
    --rtype   TYPE      Update the repository type field
    --rorigin ORG       Update the repository origin field
    -h, --help          Display help for this command

Common Options:
    See 'orc --help'
    
Notes:
    o For fields that contain spaces - use qouble quotes.

Examples:
    orc info "My Package" "John Doe" johndoe@fakeemail.com www.mypackage.com
    orc info --owner "john smith" --email johnsmith@fakeemail.com
    
"""
import os, sys, json
import utils
from docopt.docopt import docopt
from my_globals import PACKAGE_INFO_DIR
from my_globals import OVERLAY_PKGS_DIR
from my_globals import PACKAGE_FILE


#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'info', 'Sets/updates the package description and information' ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)

    # Load the package file
    json_dict = utils.load_package_file()
    if ( json_dict == None ):
        json_dict = {}

    # Setting all fields
    if ( args['<rorigin>'] ):
        utils.json_update_package_file_info( json_dict, args['<desc>'], args['<owner>'], args['<email>'], args['<url>'], args['<rname>'], args['<rtype>'], args['<rorigin>'] )

    # Setting basic fields
    elif ( args['<desc>'] ):
        utils.json_update_package_file_info( json_dict, args['<desc>'], args['<owner>'], args['<email>'], args['<url>'] )

    # Update the description
    if ( args['--desc'] ):
        utils.json_update_package_file_info( json_dict, desc= args['--desc']  )
        pass

    # Update the owner
    if ( args['--owner'] ):
        utils.json_update_package_file_info( json_dict, owner=args['--owner'] )
        pass

    # Update the email
    if ( args['--email'] ):
        utils.json_update_package_file_info( json_dict, email=args['--email'] )
        pass

    # Update the url
    if ( args['--url'] ):
        utils.json_update_package_file_info( json_dict, url=args['--url']  )
        pass

    # Update the url
    if ( args['--url'] ):
        utils.json_update_package_file_info( json_dict, url=args['--url']  )
        pass

    # Update the repo name
    if ( args['--url'] ):
        utils.json_update_package_file_info( json_dict, rname=args['--rname']  )
        pass

    # Update the repo type
    if ( args['--url'] ):
        utils.json_update_package_file_info( json_dict, rtype=args['--rtype']  )
        pass

    # Update the repo origin
    if ( args['--url'] ):
        utils.json_update_package_file_info( json_dict, rorigin=args['--rorigin']  )
        pass

    # save updates
    utils.write_package_file( json_dict )
    info_dict = utils.json_copy_info( json_dict )
    print( json.dumps( info_dict, indent=2 ) )


        

