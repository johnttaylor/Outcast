"""
 
Checks and manages a package dependencies
===============================================================================
usage: orc [common-opts] deps [options] check
       orc [common-opts] deps [options] show <adoptedpkg>
       orc [common-opts] deps [options] mv <pkg> 

Arguments:
    check               Checks for any missing or cyclical dependencies
    show                Displays the transitive dependencies incurred via
                        the specified adopted package
    mv                  Moves an existing package dependency from immeidate
                        to weak and vice-versus
    <adoptedpkg>        Name of a adopted package
    <pkg>               Name of package to move

Options:
    --noweak            Skip checking weak dependencies
    -h, --help          Display help for this command

Common Options:
    See 'orc --help'
    
    
Notes:
    
"""
import os, json, sys
import utils
from docopt.docopt import docopt

#---------------------------------------------------------------------------------------------------------
def display_summary():
    print("{:<13}{}".format( 'deps', 'Checks and manages a package dependencies' ))
    

#------------------------------------------------------------------------------
def run( common_args, cmd_argv ):
    args = docopt(__doc__, argv=cmd_argv)
    exit_code = 0;

    # Load my package info
    json_dict = utils.load_package_file()

    # CHECK dependencies
    if ( args['check'] ):
        print( f"Checking dependencies for package: {utils.json_get_package_name(json_dict)}" )

        # Build dependency tree. 
        tree = utils.Node( json_dict )
        build_tree( tree, json_dict )
        print( tree )

        # Compatible check: for weak and strong
        # for each child
        #   is found in granchildren (iterate over all grandchildren)
        #       is child compatible with grandchild?
        #           -->error -->show dep tree to grandchild

        # missing check: for weak and strong
        # for each grandchild:
        #   is not found in children
        #       -->error -->show dep tree to granchild

        #childern = utils.get_dependency_list( json_dict )
        #for c in childern:
        #    dep_dict = utils.load_dependent_package_file( c )
        #    root.add_child_data( dep_dict ) 
        #for cnode in node.get_children():
        #    dep_dict = utils.load_dependent_package_file( c )

        #    cdict = cnode.get_data()

        #grand_childern              = []
        #missing_weak_list           = []
        #missing_strong_list         = []
        #not_compatible_weak_list    = []
        #not_compatibleg_strong_list = []
        
        ## Get transitive dependencies
        #for dd in childern:
        #    dep_dict = utils.load_dependent_package_file( dd )
        #    dep_list = utils.get_dependency_list( dep_dict )
        #    grand_childern.extend( dep_list )
            
        #    # Check for cyclical deps
        #    for d in dep_list:
        #        if ( d['pkgname'] == json_dict['info']['pkgname'] ):
        #            if ( d['depType'] == 'S' ):
        #                print( f"ERROR: Cyclical weak dependency. Transitive Package - {dd['pkgname']} - depends on: {json_dict['info']['pkgname']}" )
        #                if ( common_args['-v'] ):
        #                    cat_child_pacakge( dd['pkgname'] )
        #                exit_code = 1
        #            if ( d['depType'] == 'W' ):
        #                print( f"Warning: Cyclical strong dependency. Transitive Package - {dd['pkgname']} - depends on: {json_dict['info']['pkgname']}" )
        #                if ( common_args['-v'] ):
        #                    cat_child_pacakge( dd['pkgname'] )

        #        # Is the granchild account for in the childern list?
        #        gc, c = is_in_list( d, childern )
        #        if ( gc != None ):
        #            # Now check for compatiblity
        #            gc_ver = utils.json_get_dep_semver( gc )
        #            c_ver  = utils.json_get_dep_semver( c )
        #            if ( not utils.is_semver_compatible( gc_ver, c_ver ) ):
        #                if ( c['depType'] == 'W' ):
        #                    not_compatible_weak_list.append( (gc, c, gc_ver, c_ver) )
        #                else:
        #                    if (  gc['depType'] == 'W' ):
        #                        not_compatible_weak_list.append( (gc, c, gc_ver, c_ver) )
        #                    else:
        #                        not_compatibleg_strong_list.append( (gc, c, gc_ver, c_ver) )
        #                        exit_code = 1

        #        # MISGING dependency
        #        else:
        #            if ( dd['depType'] == 'W' ):
        #                missing_weak_list.append( (dd,d) )
        #            else:
        #                if (  d['depType'] == 'W' ):
        #                    missing_weak_list.append( (dd,d) )
        #                else:
        #                    missing_strong_list.append( (dd,d) )
        #                    exit_code = 1

                    
        ## Display missing lists
        #if ( len(missing_weak_list) > 0 ):
        #    for dd,d in missing_weak_list:
        #        print(f"Warning: Missing weak dependency. Transitive Package - {dd['pkgname']} - depends on: {d['pkgname']}")
        #        if ( common_args['-v'] ):
        #            cat_child_pacakge( dd['pkgname'] )
        #            print()
        #if ( len(missing_strong_list) > 0 ):
        #    for dd,d in missing_strong_list:
        #        print(f"ERROR: Missing strong dependency. Transitive Package - {dd['pkgname']} - depends on: {d['pkgname']}")
        #        if ( common_args['-v'] ):
        #            cat_child_pacakge( dd['pkgname'] )
        #            print()

        ## Display incompatible lists
        #if ( len(not_compatible_weak_list) > 0 ):
        #    for (gc,c,gc_ver,c_ver) in not_compatible_weak_list:
        #        print(f"Warning: Non-compatible weak dependency. Transitive Package - {c['pkgname']} - depends on: {gc['pkgname']}, version: {gc_ver}. HAVE version: {c_ver}") 
        #        if ( common_args['-v'] ):
        #            print( "NEED:" )
        #            cat_child_pacakge( gc['pkgname'] )
        #            print()
        #            print( "HAVE:" )
        #            cat_child_pacakge( c['pkgname'] )
        #            print()
        #if ( len(not_compatibleg_strong_list) > 0 ):
        #    for (gc,c,gc_ver,c_ver) in not_compatibleg_strong_list:
        #        print(f"ERROR: Non-compatible strong dependency. Transitive Package - {c['pkgname']} - depends on: {gc['pkgname']}, version: {gc_ver}. HAVE version: {c_ver}") 
        #        if ( common_args['-v'] ):
        #            print( "NEED:" )
        #            cat_child_pacakge( gc['pkgname'] )
        #            print()
        #            print( "HAVE:" )
        #            cat_child_pacakge( c['pkgname'] )
        #            print()

        #if ( exit_code != 0 ):
        #    sys.exit( exit_code )

        #print("All dependencies checks completed.")
        #sys.exit( 0 )



def is_in_list( needle, haystack ):
    for s in haystack:
        if ( s['pkgname'] == needle['pkgname'] ):
            return (needle, s )
    return ( None, None )

    
def cat_child_pacakge( pkgname ):
    cmd = f"orc.py cat {pkgname}"
    t   = utils.run_shell( cmd  )
    utils.check_results( t, "" )
    if ( not utils.is_error( t ) ):
        print(t[1])


def build_tree( node, json_dict ):
    children = utils.get_dependency_list( json_dict )
    if ( len(children) > 0 ):
        for c in children:
            dep_dict = utils.load_dependent_package_file( c )
            if ( utils.json_get_package_name(dep_dict) != None ):
                node.add_child_data( dep_dict ) 

    for cnode in node.get_children():
        grand_children = utils.get_dependency_list( cnode.get_data() )
        if ( len(grand_children) > 0 ):
            for gc in grand_children:
                dep_dict = utils.load_dependent_package_file( gc )
                if ( utils.json_get_package_name(dep_dict) != None ):
                    cnode.add_child_data( dep_dict ) 
