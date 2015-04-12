"""Collection of helper functions related to package dependencies"""

import ConfigParser, os, tarfile
import utils

#------------------------------------------------------------------------------
def validate_dependencies( pkginfo, list_deps, list_weak, list_trans, common_args, nocheck_flag, file_name, cache=None ):

    # check for duplicate names in a package file
    if ( not nocheck_flag ):
        _valid_no_duplicate_pkgs( list_deps, list_weak, list_trans, file_name ) 
    
    # Housekeeping
    t     = (pkginfo['name'], pkginfo['branch'], pkginfo['version'])
    trail = []
    all   = []
    root  = utils.Node( t )
    all.extend( list_deps )
    all.extend( list_weak )
    if ( cache == None ):
        cache = {}
        
    # calculate all of the possible transitive dependencies
    trail.append( (file_name, t[0], t[1], t[2]) )
    build_node( root, all, common_args['--uverse'], trail, cache, list_weak )

    # Skip most of the test(s) when --nocheck
    root_actual = utils.Node( t )
    if ( not nocheck_flag ):
        # Housekeeping for: verify listed transitive dependencies are valid
        allall = list(all)
        allall.extend( list_trans )
        
        # check against "do-not-use" packages
        check_against_blacklist( common_args['--uverse'], allall, common_args, warn_on_do_not_use="Initial check shows a dependency on a 'Do-Not-Use' Package: {}-{}-{}." )

        # Run algorithm
        _build_actual( root_actual, all, allall, common_args['--uverse'], trail, cache, list_weak )

        # Check for stale transitive dependencies
        stale = find_unused_dependencies( root_actual, list_trans )
        if ( len(stale) > 0 ):
            print( "ERROR: Stale dependencies in the [transitive_deps] section:" )
            for d in stale:
                print( "ERROR:   " + d )
            exit(1)
                
        # Clean-up tree for print/display purposes
        trail  = [t]
        remove_duplicate_children( root_actual, trail )
    
        # Find weak ONLY dependencies
        trail = [t]
        root_noweak = utils.Node(t)
        build_node( root_noweak, list_deps, common_args['--uverse'], trail, cache, None )
        root_actual_noweak = utils.Node(t)
        _build_actual( root_actual_noweak, list_deps, allall, common_args['--uverse'], trail, cache, list_weak )
            
        # update returned trees with weak-ONLY info
        _mark_weak_only_nodes( root, root_noweak )
        _mark_weak_only_nodes( root_actual, root_actual_noweak )
        
        # Do another check against blacklist packages now that stale transitive dependencies have been removed
        check_against_blacklist( common_args['--uverse'], allall, common_args )
        
    # Return final trees                 
    return root, root_actual



def check_against_blacklist( uverse, list_all_deps, common_args, warn_on_do_not_use=None ):
    # check my dependencies against the "black list"
    for d in list_all_deps:

        # Read the dependency's publish histroy
        pkgname = d[0]
        fname   = os.path.join( uverse, pkgname ) + ".journal"
        journal = utils.read_journal_file( fname )
    
        # Check for hard errors
        l = utils.extract_pbv_from_journal( journal, 'do_not_use', pkgname )
        if ( d in l ):
            if ( warn_on_do_not_use != None ):
                utils.print_warning( warn_on_do_not_use.format( d[0], d[1], d[2] ) ) 
            else:
                exit( "ERROR: Dependent package - {}-{}-{} - has been marked as DO NOT USE.  You MUST update your dependencies to proceed.".format( d[0], d[1], d[2] ) )
        
        # Check for warning
        l = utils.extract_pbv_from_journal( journal, 'deprecate', pkgname )
        if ( d in l and warn_on_do_not_use == None):
            utils.print_warning( "Dependent package - {}-{}-{} - has been deprecated.  Recommend you upgrade the package.".format( d[0], d[1], d[2] ) )
        

            
def convert_tree_to_list( tree ):
    s      = encode_dep( tree.get_data(), False, False )
    result = [s]
    for cnode in tree.get_children():
        cdata = cnode.get_data()
        result.extend( convert_tree_to_list( cnode ) )
        
    return result
    
    
#------------------------------------------------------------------------------
def _mark_weak_only_nodes( full_tree, noweak_tree ):
    noweak_list = convert_tree_to_list( noweak_tree ) 
    _mark_tree( full_tree, noweak_list )
    

def _mark_tree( node, noweak_list ):
    for child in node.get_children():
        data  = child.get_data()
        entry = encode_dep( data, False, False )
        if ( not entry in noweak_list ):
            newval = ('*'+data[0], data[1], data[2] )
            child.set_data( newval )
        _mark_tree( child, noweak_list )


def _check_results( t, err_msg ):
    if ( t[0] != 0 ):
        if ( t[1] != None and t[1] != 'None None' ):
            print t[1]
        exit( err_msg )

#------------------------------------------------------------------------------
def find_unused_dependencies( tree, list_of_deps, encode=True ):

    # Convert the actual tree to a SET
    trans = set()
    edges = flatten_to_edges( tree )
    for x in edges:
        l,r = x.split(" : ")
        l   = _strip_and_expand( l )
        r   = _strip_and_expand( r )
        trans.add(l)
        trans.add(r)

    unused = []    
    for y in list_of_deps:
        i = encode_dep( y, False, False )
        if ( not i in trans ):
            if ( encode ):
                unused.append( i )
            else:
                unused.append( y )
            
    return unused
    
#------------------------------------------------------------------------------
def remove_duplicate_children( node, seen ):
    for cnode in node.get_children():
        cdata = cnode.get_data()
        if ( cdata in seen ):
            cnode.remove_all_children_nodes()
            continue
        
        seen.append( cdata )    
        remove_duplicate_children( cnode, seen )
            
#------------------------------------------------------------------------------
def read_package_spec( filename, top_fname='', fh=None ):

    cfg = ConfigParser.RawConfigParser(allow_no_value=True)
    cfg.optionxform = str
    fname           = filename
    
    if ( top_fname == '' ):
        if ( os.path.isfile(filename) ):
            utils.print_verbose( "Reading file: " + filename )
            cfg.read( filename )
        else:
            exit( "ERROR: File - {} - does not exist or is not a valid file name.".format( filename ) )
                
    else:
        utils.print_verbose( "Reading file: "  + top_fname  )
        fname = top_fname
        cfg.readfp( fh )
        fh.close()
    
    list_deps  = []
    list_weak  = []
    list_trans = []
    
    # load dependencys sections
    if ( cfg.has_section('immediate_deps') ):
        list_deps = _load_section( 'immediate_deps', cfg, fname )
        
    if ( cfg.has_section('weak_deps') ):
        list_weak = _load_section( 'weak_deps', cfg, fname )

    if ( cfg.has_section('transitive_deps') ):
        list_trans = _load_section( 'transitive_deps', cfg, fname )

    # load package info
    pkginfo = read_info(cfg, filename, top_fname)
  
    return pkginfo, list_deps, list_weak, list_trans, cfg 
    


def read_spec_from_tar_file( f ):
    # Open the child top file
    try:
        tar = tarfile.open( f )
        fh  = tar.extractfile( 'top/pkg.specification' )
    
    except Exception as ex:
        exit("ERROR: Trying to locate/read Package Top File: {}".format(f) )
    
    # Get pkg.specification info from the top file
    pkginfo  = read_package_spec( 'pkg.specification', f, fh )
    tar.close()
    return pkginfo


#------------------------------------------------------------------------------
def build_node( parent_node, children_data, path_to_uverse, trail, cache, weak_deps, no_warn_on_weakcycle=False, trans=None ):
    parent_node.add_children_data( children_data )
    for cnode in parent_node.get_children():
        p,b,v = _get_node_data_and_substitute( cnode, trans )
        fname = build_top_fname(p,b,v)
        cpath = os.path.join( path_to_uverse, fname )

        # trap weak-cyclic dependencies
        n = (fname, p, b, v)
        if ( _test_for_weak_cyclic(n,trail,weak_deps) ):
            if ( not no_warn_on_weakcycle ):
                utils.print_warning( "Weak Cyclic dependency." )
                utils.print_warning( "   " + _convert_trail_to_string(trail,n) )
            continue
            
        # trap cyclic dependencies
        if ( _test_for_cyclic(n,trail) ):
            print "ERROR: Cyclic dependency."
            _display_trail(trail,n)
            exit(1)

        # Keep a trail for diagnostic/error messages purposes
        trail.append(n)

        # Read the child's top file (but ONLY once)
        info = read_top_file( cpath, fname, trail, cache )
        
        # Process the child top file
        i,d,w,t,bhist = info
        if ( len(d) > 0 ):
            newresult = build_node( cnode, d, path_to_uverse, trail, cache, weak_deps, no_warn_on_weakcycle, trans )
            result    = False if not result else newresult
        trail.remove(n)
    
            
def _get_node_data_and_substitute( node, trans=None ):
    # default behavior
    if ( trans == None ):
        return node.get_data()
    
    # substitute different version for a transitive dependency
    p,b,v = node.get_data()
    for x in trans:
        if ( p == x[0] ):
            node.set_data( x )
            return x
    
    # If I get here than no substitution is needed/required        
    return (p,b,v)
   
        
def build_top_fname( p, b, v ):
    return p + '-' + b + '-' + v + '.top'
       
         
def _test_for_cyclic( t, trail ):
    for x in trail:
        if ( t[1] == x[1] ):
            return True
    
    return False


def _test_for_weak_cyclic( t, trail, weak_deps ):
    if ( weak_deps != None and len(trail) > 1 ):
        root           = trail[0]
        imm_child      = trail[1]
        weak_pkg_names = _extract_pkgnames( weak_deps )
        
        if ( imm_child[1] in weak_pkg_names ):
            if ( t[1] == root[1] ):
                return True

    return False;


def _display_trail(trail, n=None):
    print "ERROR:   ",
    print _convert_trail_to_string(trail,n)

        
def _convert_trail_to_string( trail, n=None):
    result = []
    for i in trail:
        result.append( encode_dep(i[1:],use_quotes=False) )
        result.append( " -> " )
    if ( n != None ):
        result.append( encode_dep(i[1:],use_quotes=False) )
        
    return "".join(result)
    

#------------------------------------------------------------------------------
def _load_section( section, cfg, fname ):
    children = []
    options  = cfg.options(section)
    
    for entry in options:
        entry = entry.replace('*','',1)
        try:
            pkg, branch, ver = utils.standardize_dir_sep(entry).split(os.sep)
        except:
            exit( "ERROR: Malformed dependency entry [{}.{}] in file: {}".format(section,entry,fname) )
            
        if ( branch == '' ):
            branch = 'main'
        children.append( (pkg, branch, ver) )

    return children       
    
#------------------------------------------------------------------------------
def _valid_no_duplicate_pkgs( list_deps, list_weak, list_trans, fname ):
    
    # check by section
    _valid_no_duplicate_pkgs_in_section( list_deps,  fname, "Duplicate Package name(s) within section: [immediate_deps]" )
    _valid_no_duplicate_pkgs_in_section( list_weak,  fname, "Duplicate Package name(s) within section: [weak_deps]" )
    _valid_no_duplicate_pkgs_in_section( list_trans, fname, "Duplicate Package name(s) within section: [transitive_deps]" )

    # check for dups across sections
    l = []
    l.extend( list_deps )
    l.extend( list_weak )
    _valid_no_duplicate_pkgs_in_section( l, fname, "Duplicate Package name(s) occurred in section: [weak_deps]" )
    l.extend( list_trans )
    _valid_no_duplicate_pkgs_in_section( l, fname, "Duplicate Package name(s) occurred in section: [transitive_deps]" )

        
def _valid_no_duplicate_pkgs_in_section( list_deps, fname, msg ):
    pnames     = _extract_pkgnames( list_deps )
    duplicates = utils.find_duplicates_in_list( pnames )
    if ( len(duplicates) > 0 ):
        print "ERROR: In file - " + fname + ' - ' + msg 
        for n in duplicates:
            print "ERROR:   " + n
        exit(1)        
    
def _extract_pkgnames( list_of_deps ):
    list = []
    for p,b,v in list_of_deps:
        list.append(p.lower())
        
    return list     


#------------------------------------------------------------------------------
def create_dot_file( fname, root ):
    with open(fname, 'w' ) as f:
        f.write( "digraph { \n" )
        
        for item in flatten_to_edges( root ):
            item = item.replace(os.sep,"/")
            f.write( item.replace(" : "," -> ",1) + "\n" )
            
        f.write( "}\n" )

def _write_node( f, parent_node ):
    parent = encode_dep( parent_node.get_data() )
    
    for cnode in parent_node.get_children():
        child = encode_dep( cnode.get_data() )
        f.write( parent + " -> " + child + "\n")
        _write_node( f, cnode )

#------------------------------------------------------------------------------
def flatten_to_edges( root, compress_flag=True ):
    s = set()
    _flatten_node( s, root, compress_flag )
    return list(s)
    
def _flatten_node( flatset, parent_node, compress_flag ):
    parent = encode_dep( parent_node.get_data(), compress_flag )
    for cnode in parent_node.get_children():
        child = encode_dep( cnode.get_data(), compress_flag )
        edge  = parent + " : " + child
        flatset.add( edge )
        _flatten_node( flatset, cnode, compress_flag )
        
def encode_dep(t,compress_flag=True, use_quotes=True):
    p,b,v = t
    q     = '"'
    if ( use_quotes == False ):
        q = ''
        
    if ( compress_flag == True and b == 'main' ):
        b = ''
    return '{}{}{}{}{}{}{}'.format( q, p,os.sep, b,os.sep, v, q )
    
        
def _strip_and_expand( pkg ):
    pkg = pkg.strip('"')
    return pkg.replace(os.sep+os.sep, os.sep + "main" + os.sep, 1)


def tree_as_a_list( root ):
    l = []
    _walk_tree( root, l )
    return l
  
def _walk_tree( node, list ):
    list.append( node.get_data() )
    for cnode in node.get_children():
        list.append( cnode.get_data() )
        _walk_tree( cnode, list )
          
#------------------------------------------------------------------------------
def read_info( cfg, filename, top_fname ):
    
    if ( not cfg.has_section('info') ):
        exit( "ERROR: Missing [info] section in file:{} (in top file:{})".format(filename, top_fname) )

    pkginfo = {}    
    if ( not cfg.has_option('info','name') ):
        exit( "ERROR: Missing [info.name] option in file:{} (in top file:{})".format(filename, top_fname) )
    pkginfo['name'] = cfg.get('info','name')
    
    if ( not cfg.has_option('info','branch') ):
        exit( "ERROR: Missing [info.branch] option in file:{} (in top file:{})".format(filename, top_fname) )
    pkginfo['branch'] = cfg.get('info','branch')

    if ( not cfg.has_option('info','version') ):
        exit( "ERROR: Missing [info.version] option in file:{} (in top file:{})".format(filename, top_fname) )
    pkginfo['version'] = cfg.get('info','version')
    
    if ( not cfg.has_option('info','pubtime') ):
        exit( "ERROR: Missing [info.pubtime] option in file:{} (in top file:{})".format(filename, top_fname) )
    pkginfo['pubtime'] = int(float(cfg.get('info','pubtime')))
    
    if ( not cfg.has_option('info','pubtimelocal') ):
        exit( "ERROR: Missing [info.pubtimelocal] option in file:{} (in top file:{})".format(filename, top_fname) )
    pkginfo['pubtimelocal'] = cfg.get('info','pubtimelocal')
    
    if ( not cfg.has_option('info','desc') ):
        exit( "ERROR: Missing [info.desc] option in file:{} (in top file:{})".format(filename, top_fname) )
    pkginfo['desc'] = cfg.get('info','desc')
    
    if ( not cfg.has_option('info','owner') ):
        exit( "ERROR: Missing [info.desc] option in file:{} (in top file:{})".format(filename, top_fname) )
    pkginfo['owner'] = cfg.get('info','owner')
    
    if ( not cfg.has_option('info','email') ):
        exit( "ERROR: Missing [info.email] option in file:{} (in top file:{})".format(filename, top_fname) )
    pkginfo['email'] = cfg.get('info','email')
    
    pkginfo['url'] = ''
    if ( not cfg.has_option('info','url') ):
        pkginfo['url'] = cfg.get('info','url')

    return pkginfo
    
        
#------------------------------------------------------------------------------
def _build_actual( node, children_data, all_entries, path_to_uverse, trail, cache, weak_deps ):
    node.add_children_data( children_data )
    for cnode in node.get_children():
        p,b,v = cdata = cnode.get_data()
        entry = _find_pkg_in_list( p, all_entries )
        
        # Trap missing transitive dependency (and properly handle the weak-cyclic condition)
        if ( entry == None ):
            if ( not _test_for_weak_cyclic( ("",p,b,v), trail, weak_deps ) ):
                print("ERROR: Missing a transitive dependency: {}".format(encode_dep(cdata,use_quotes=False)) )
                _display_trail(trail)
                exit(1)
            else:
                continue
            
        # Housekeeping
        pa,ba,va      = entry
        fname         = build_top_fname(pa,ba,va)
        cpath         = os.path.join( path_to_uverse, fname )
        a             = (fname, pa,ba,va)
        trail.append(a)

        # Access the child node's TOP file - including the branching history
        i,d,w,t,bhist = read_top_file( cpath, fname, trail, cache )
     
        # Check if actual transitive dependency is valid
        if ( not utils.is_ver1_backwards_compatible_with_ver2(entry,cdata,bhist) ):
            print("ERROR: Actual transitive dependency is NOT compatible. Required min ver={}".format(encode_dep(cdata,use_quotes=False)) )
            _display_trail(trail)
            exit(1)
       
        # modify child node to reflex actual transitive dependency
        cnode.set_data( entry )
        
        # process the child
        if ( len(d) > 0 ):
            _build_actual( cnode, d, all_entries, path_to_uverse, trail, cache, weak_deps )
        trail.remove(a)


    
    
def _find_pkg_in_list( pkg, pkglist ):
    for e in pkglist:
        p,b,v = e
        if ( pkg.lower() == p.lower() ):
            return e
    return None

def read_top_file( cpath, fname, trail, cache ):
    if ( not fname in cache ):
        # Open the child top file
        try:
            tar = tarfile.open( cpath )
            fh  = tar.extractfile( 'top/pkg.specification' )
        
        except Exception as ex:
            print("ERROR: Trying to locate/read Package Top File: {}".format(cpath) )
            _display_trail(trail)
            exit(1)
    
        # Get child dependency data from the top file
        info, d,w,t, cfg = read_package_spec( 'pkg.specification', fname, fh )
        bhist            = _get_branching_history( tar, trail )
        cache[fname]     = (info,d,w,t,bhist)
        tar.close()
        _valid_no_duplicate_pkgs( d, w, t, fname ) 

    return cache[fname]
    

    

def _get_branching_history( tar, trail ):

    # Open the branch history file
    try:
        fh  = tar.extractfile( 'top/pkg.branching' )
  
    # If no pkg.branching file is present -->then the assumption is that there is no branch history
    except KeyError:
        return None
    
    # Some other error -->hard stop    
    except Exception as ex:
        print("ERROR: Cannot open the 'pkg.branching' file in Package Top File: {}".format(cpath) )
        _display_trail(trail)
        exit(1)
    
    # Get the branch history
    n = utils.parse_branch_log( fh )
    fh.close()
    return n[0]
    
    
    