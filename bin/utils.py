"""Collection of helper functions"""


import sys, os, errno, fnmatch, subprocess, time, copy
import errno, stat, shutil
import json
from gitignore_parser import parse_gitignore
#import platform, tarfile
#from collections import deque

from my_globals import ADOPTED_PKGS_DIR
from my_globals import DEPS_FILE


# Module globals
_dirstack = []
quite_mode   = False
verbose_mode = False


#-----------------------------------------------------------------------------
def standardize_dir_sep( pathinfo ):
    return pathinfo.replace( '/', os.sep ).replace( '\\', os.sep )
    
def force_unix_dir_sep( pathinfo ):
    return pathinfo.replace( '\\', '/')

def push_dir( newDir ):
    global _dirstack
    
    if ( not os.path.exists(newDir) ):
        exit( "ERROR: Invalid path: "+ newDir )
    
    _dirstack.append( os.getcwd() )
    os.chdir( newDir )
    
    
def pop_dir():
    global _dirstack
    os.chdir( _dirstack.pop() )

#-----------------------------------------------------------------------------
def print_warning( msg ):
    if ( not quite_mode ):
        print( "Warn:  " + msg )

def set_quite_mode( newstate ):
    global quite_mode
    quite_mode = newstate
       

def print_verbose( msg, no_new_line=False, bare=False ):
    if ( verbose_mode ):
        if ( not no_new_line ):
            if ( bare ):
                print( msg )
            else:
                print( "Info:  " + msg )
        else:
            if ( bare ):
                print( msg, end='' )
            else:
                print( "Info:  " + msg, end='' )
        
def set_verbose_mode( newstate ):
    global verbose_mode
    verbose_mode = newstate
       
       
def display_scm_message( cmd, msg, scm ):
    cmd = f"evie.py --scm {scm} {cmd} {msg}"
    t = run_shell( cmd, False )
    if ( not is_error(t) and t[1] != None and t[1] != '' ):
        print( t[1] )

  
#-----------------------------------------------------------------------------
def mkdirs( dirpath ):
    
    # Attempt to create the workspace directory    
    try:
        os.makedirs(dirpath, exist_ok=True)
    except OSError as exc: 
        sys.exit( f"Unable to create directory path: {dirpath} ({exc})" )

    
def cat_file( fobj, strip_comments=True, strip_blank_lines=True ):
    # process all entries in the file        
    for line in fobj:
       
        # drop comments and blank lines
        line = line.strip()
        if ( strip_comments and line.startswith('#') ):
            continue
        if ( strip_blank_lines and line == '' ):
            continue

        if ( type(line) is bytes ):
            line = line.decode()

        print( line )
        
def remove_tree( root, err_msg=None, warn_msg=None ):
    try:
        shutil.rmtree( root, _handleRemoveReadonly )
    except Exception as exc:
        if ( err_msg != None ):
            sys.exit( f'{err_msg} ({exc})' )
        elif ( warn_msg != None ):
            print_warning( f'{warn_msg} ({exc})' )


# This function handles issue with Windows when deleting files marked as readonly
def _handleRemoveReadonly(func, path, exc):
  excvalue = exc[1]
  if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
      os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
      func(path)
  else:
      raise   
  
# This function returns true the root the primary repository
def find_root( primary_scm_tool, verobse ):
    # Note: Running the SCM command creates a nested run_shell scenario - it only works if 'verbose' is turned off (not sure why!!!)
    cmd = f'evie.py --scm {primary_scm_tool} findroot'
    t   = run_shell( cmd, False )
    check_results( t, "ERROR: Failed find the root of the primary/local Repository" )
    return t[1].strip()
        
# Sets/clears the 'readonly' bit/flag for the entire specified directory tree
def set_tree_readonly( root, set_as_read_only = True ):
    mode = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH if set_as_read_only else stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
    for root,dirs,files in os.walk(root):
        for f in files:
            filename = os.path.join(root, f)
            os.chmod(filename, mode)
    
#-----------------------------------------------------------------------------
# return None if not able to load the file
def load_deps_file():
    f = os.path.join(  ADOPTED_PKGS_DIR(), DEPS_FILE() )

    try:
        with open(f) as f:
            return json.load( f )
    except:
        return None

def write_deps_file( json_dictionary ):
    # make sure the pkgs.adopted directory exists
    if ( not os.path.isdir( ADOPTED_PKGS_DIR() ) ):
        mkdirs( ADOPTED_PKGS_DIR() )

    f = os.path.join(  ADOPTED_PKGS_DIR(),DEPS_FILE() )
    data = json.dumps( json_dictionary, indent=2 )
    with open( f, "w+" ) as file:
        file.write( data )


def json_get_package( dep_list, package_to_find ):
    if ( len(dep_list) > 0 ):
        try:
            idx = 0
            for p in dep_list:
                if ( p['pkgname'] == package_to_find ):
                    return p, idx
                idx = idx + 1

            return None, None
        except Exception as e:
            sys.exit( f"ERROR: Dependency file is corrupt {e}" )
    return None, None

def json_create_dep_entry( pkgname, pkgtype, parentdir, date_adopted, ver_sem, ver_branch, ver_id, repo_name, repo_type, repo_origin ):
    ver_dict  = { "semanticVersion" : ver_sem, "branch" : ver_branch, "tag" : ver_id }
    repo_dict = { "name" : repo_name, "type": repo_type, "origin" : repo_origin }
    dep_dict  = { "pkgname" : pkgname, "pkgtype" : pkgtype, "adoptedDate": date_adopted, "parentDir" : parentdir, "version" : ver_dict, "repo": repo_dict }
    return dep_dict

def json_update_deps_file_with_new_entry( current_deps, new_dep_entry, is_weak_dep=False ):
    if ( is_weak_dep ):
        current_deps['weakDeps'].append( new_dep_entry )
    else:
        current_deps['immediateDeps'].append( new_dep_entry )
    write_deps_file( current_deps )

def json_find_dependency( deps, pkgname ):
    deptype    = 'immediateDeps'
    pkgobj,idx = json_get_package( deps[deptype], pkgname )
    if ( pkgobj == None ):
        deptype    = 'weakDeps'
        pkgobj,idx = json_get_package( deps[deptype], pkgname )
        if ( pkgobj == None ):
            return None, None, None
    return pkgobj, deptype, idx


def json_get_parentdir( pkgdict ):
    return '<none>' if pkgdict['parentDir'] == None else pkgdict['parentDir']

def json_get_semver( pkgdict ):
    return '<none>' if pkgdict['version']['semanticVersion'] == None else pkgdict['version']['semanticVersion']

def json_get_branch( pkgdict ):
    return '<none>' if pkgdict['version']['branch'] == None else pkgdict['version']['branch']

def json_get_tag( pkgdict ):
    return '<none>' if pkgdict['version']['tag'] == None else pkgdict['version']['tag']

def json_get_repo_name( pkgdict ):
    return '<none>' if pkgdict['repo']['name'] == None else pkgdict['repo']['name']

def json_get_repo_type( pkgdict ):
    return '<none>' if pkgdict['repo']['type'] == None else pkgdict['repo']['type']

def json_get_repo_origin( pkgdict ):
    return '<none>' if pkgdict['repo']['origin'] == None else pkgdict['repo']['origin']

#-----------------------------------------------------------------------------
# Filters the directory list by the 'ignore file', dirs with no files
def walk_dir_ignored( root, ignore_file ):
    push_dir( root )
    ignored = parse_gitignore( ignore_file )
    pop_dir()

    list = []
    for root, dirs, files in os.walk(root):
        if ( len(files) > 0 ):
            if ( ignored( root ) == False ):
                list.append( root )
            
    return list        

#-----------------------------------------------------------------------------
def parse_pattern( string ):
    # default result values
    parent_dir = ''
    pattern    = string
    rflag      = False
    
    # Search for supported wildcards 
    idx = string.find('...')
    if ( idx != -1 ):
        rflag = True
    else:
        idx = string.find('?')
        if ( idx == -1 ):
            idx = string.find('[')
            if ( idx == -1 ):
                idx = string.find('*')
                
                
    # Seperate parent directory from pattern/filename
    if ( idx != -1 ):
        end_idx    = string.rindex(os.sep,0,idx)
        parent_dir = string[:end_idx]
        if ( rflag ):
            pattern = string[end_idx+1+3:] 
        else:    
            pattern = string[end_idx+1:]
        
    return (idx!=-1, rflag, parent_dir, pattern )


#------------------------------------------------------------------------------
def parse_entry( line, pkgpath ):
    file_include = False
    if ( line.startswith('!') ):
        line         = line[1:]
        file_include = True
        
    has_pattern, rflag, parent_dir, pattern = parse_pattern( line )
    path  = pkgpath + os.sep + parent_dir
    files = []

    # Process a 'normal' entry 
    if ( not file_include ):
        if ( not has_pattern ):
            files.append( pkgpath + os.sep + pattern )
        elif ( not rflag ):
            files.extend( get_file_list( pattern, path ) )
        else:
            files.extend( walk_file_list( pattern, path ) )

    # Process a 'include' entry (reference to another export header file)
    else:
        if ( not has_pattern ):
            read_export_header_file( pkgpath + os.sep + pattern, pkgpath, files )
        elif ( not rflag ):
            export_files = get_file_list( pattern, path )
            for f in export_files:
                read_export_header_file( f, pkgpath, files )
        else:
            export_files = walk_file_list( pattern, path )
            for f in export_files:
                read_export_header_file( f, pkgpath, files )
        
    return files
        
        
#-----------------------------------------------------------------------------
def get_file_list( pattern, parentdir ):
    list  = []
    if ( os.path.exists( parentdir ) ):
        files = os.listdir(parentdir)
        for f in fnmatch.filter(files,pattern):
            list.append( os.path.join(parentdir,f) )
      
    return list
    
        
#-----------------------------------------------------------------------------
def walk_file_list( pattern, pkgpath ):
    list = []
    for root, dirs, files in os.walk(pkgpath):
        for f in fnmatch.filter(files,pattern):
            list.append( os.path.join(root,f) )
            
    return list        


#-----------------------------------------------------------------------------
def concatenate_commands( cmd1, cmd2 ):
    if ( platform.system() == 'Windows' ):
        return cmd1 + " & " + cmd2
    else:
        return cmd1 + " , " + cmd2


#-----------------------------------------------------------------------------
def read_export_header_file( hfile, pkgpath, headers ):         
    try:
        inf = open( hfile, 'r' )

        # process all entries in the file        
        for line in inf:
           
            # drop comments and blank lines
            line = line.strip()
            if ( line.startswith('#') ):
                continue
            if ( line == '' ):
                continue
       
            # 'normalize' the file entries
            line = standardize_dir_sep( line.strip() )
        
            # Process 'add' entries
            if ( not line.startswith('-') ):
                headers.extend( parse_entry(line,pkgpath) )
            
                # make sure there are not duplicates in the list
                headers = list(set(headers))
     
            # Process 'exclude' entries
            else:    
                xlist = parse_entry(line[1:],pkgpath)
                for e in xlist:
                    try:
                        headers.remove(e)
                    except:
                        pass
    
        inf.close()
    except:
        print_warning( "Unable to open export header file: {}".format(hfile) )
        
    return headers
    
#-----------------------------------------------------------------------------
def walk_linksrc( linksrc, parentpath, common_args ):
    list = []
    for root, dirs, files in os.walk(parentpath):
        for f in files:
            info    = get_pkg_source( os.path.join(root,f), common_args['-p'], common_args['-w'], OUTCAST_LOCAL_PKG_SUFFIX() )
            display = info
            if ( OUTCAST_LOCAL_PKG_SUFFIX() in info ):
                parts   = info.split(os.sep)
                path    = os.path.join( *parts[1:-1] )
                info    = os.path.join( common_args['-w'], path )
                display = os.path.join( OUTCAST_LOCAL_PKG_SUFFIX(), path )
                
            if ( info.startswith(linksrc) ):
                list.append( (os.path.join(root,f), display) ) 
            
    return list
    
#-----------------------------------------------------------------------------
def walk_clean_empty_dirs( path ):
    for dirpath, _, _ in os.walk(path, topdown=False):
        if dirpath == path:
            break
                
        try:
            os.rmdir(dirpath)
        except OSError as ex:
            if ( ex.errno == errno.ENOTEMPTY ):
                pass

#-----------------------------------------------------------------------------
class Node(object):
    def __init__(self, data ):
        self.data     = data
        self.nodenum  = 0
        self.parent   = None
        self.children = []

    def __repr__(self, level=0):
        ret = "{} {}\n".format( "  "*level, repr(self.data) )
        for child in self.children:
            ret += child.__repr__(level+1)
        return ret
    
       
    def add_child_node( self, obj ):
        self.children.append( obj )
        obj.parent = self
        
    def remove_child_node( self, obj ):
        self.children.remove(obj)
        obj.parent = None
            
    def remove_all_children_nodes( self ):
        for c in self.children:
            c.parent = None
        self.children = []
        
    def add_child_data( self, data ):
        c = Node(data)
        self.add_child_node( c )
        
    def add_children_nodes( self, list ):
        for o in list:
            self.add_child_node( o )
            
    def add_children_data( self, list ):
        for d in list:
            self.add_child_data( d )
            
    def get_children( self ):
        return self.children    
        
    def get_data( self ):
        return self.data
            
    def set_data( self, newdata ):
        self.data = newdata
        
    def set_nodenum( self, num ):
        self.nodenum = num
        
    def get_nodenum( self ):
        return self.nodenum
        

    def set_node_number_by_height( self, num ):
        queue = deque()
        queue.append( self )
        while( len(queue) > 0 ):
            node         = queue.popleft()
            node.nodenum = num
            num         += 1
            for c in node.children:
                queue.append(c)
    
    def clone_sub_tree_from( self, src ):
        self.data     = copy.deepcopy(src.data)
        self.nodenum  = 0
        self.children = []
        self._clone_children_from( src )
        
            
    def _clone_children_from( self, src ):
        for x in src.children:
            newnode = Node(None)
            self.add_child_node( newnode )
            newnode.clone_sub_tree_from( x )
        
def flatten_tree_to_list( root_node, list_to_append_to ):
    for cnode in root_node.get_children():
        list_to_append_to.append(cnode.get_data())
        flatten_tree_to_list( cnode, list_to_append_to )    
                               
# Format is <pkg>\<branch>\<ver>
def convert_to_long_format( entry, stripLeadingChar='*', sep=os.sep ):
    p,b,v = entry
    if ( p[0] == stripLeadingChar ):
        p = p[1:]

    c = f'{p}{sep}{b}'
    if ( v != '' ):
        c = f'{c}{sep}{v}'
    
    return c
        

#-----------------------------------------------------------------------------
def find_duplicates_in_list(l, filter_blank_comment_lines=False):
    """ Returns a list of duplicate entries.  If no duplicates, then an empty list is returned"""
    if ( filter_blank_comment_lines ):
        filtered = []
        for x in l:
            if ( x.startswith('#') or x.strip() == '' ):
                continue
            filtered.append( x )
        l = filtered

    return list(set([x for x in l if l.count(x) > 1]))


def remove_duplicates( l ):
    return list(set(l))
        
def remove_from_list( item, l ):
    if ( item in l ):
        l.remove(item)
        
#-----------------------------------------------------------------------------
def run_shell( cmd, verbose_flag=False, on_err_msg=None ):
    if ( verbose_flag ):
        print_verbose(cmd)
        p = subprocess.Popen( cmd, shell=True )
    else:
        p = subprocess.Popen( cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )

    r  = p.communicate()
    r0 = '' if r[0] == None else r[0].decode()
    r1 = '' if r[1] == None else r[1].decode()
    if ( p.returncode != 0 and on_err_msg != None ):
        exit(on_err_msg)
    return (p.returncode, f"{r0} {r1}" )

def is_error( t ):
    if ( t[0] != 0 ):
        return True;

    return False

def check_results( t, err_msg, scm_cmd=None, scm_msg=None, scm=None ):
    if ( t[0] != 0 ):
        if ( t[1] != None and t[1] != 'None None' ):
            print(t[1])
        if ( scm_cmd == None ):
            sys.exit( err_msg )
        else:
            print( err_msg )
            display_scm_message( scm_cmd, scm_msg, scm )
            sys.exit(1)



#-----------------------------------------------------------------------------
def parse_vernum( string ):
    pre = None
    t   = string.split('.')
    if ( len(t) < 3 or len(t) > 3 ):
        exit( "ERROR: Malformed version number: [{}].".format( string ) )
        
    # Parse pre-release (if it exists)
    t2 = t[2].split('-')
    if ( len(t2) == 2 ):
        pre  = t2[1]
        t[2] = t2[0]
    elif ( len(t2) > 2 ):
        exit( "ERROR: Malformed version number (prerelease id): [{}]".format( string ) )
    
    
    return (t[0], t[1], t[2], pre)
    
def parse_package_name( string ):
    # Returns a tuple: (pkg, branch, (maj.min.pat[-pre]), original_string )
    pkg, branch, ver = string.split('-',2) 
    return (pkg, branch, ver, string )

def build_vernum( m, n, p, pre=None ):
    ver = "{}.{}.{}".format(m,n,p)
    if ( pre != None and pre != ''):
        ver = "{}-{}".format(ver,pre)
       
    return ver

def numerically_compare_versions( ver1, ver2 ): # Returns -1, 0, 1 when ver1<ver2, ver1==ver2, ver1>ver2 respectively
    ver1_major, ver1_minor, ver1_patch, ver1_pre = parse_vernum( ver1 )
    ver2_major, ver2_minor, ver2_patch, ver2_pre = parse_vernum( ver2 )
    
    # Compare major indexes
    if ( ver1_major < ver2_major ):
        return -1
    if ( ver1_major > ver2_major ):
        return 1
    
    # Compare minor indexes (If I get here the major indexes are equal)
    if ( ver1_minor < ver2_minor ):
        return -1
    if ( ver1_minor > ver2_minor ):
        return 1
            
    # Compare patch indexes (If I get here the minor indexes are equal)
    if ( ver1_patch < ver2_patch ):
        return -1
    if ( ver1_patch > ver2_patch ):
        return 1
            
    # Compare prerel indexes (If I get here the patch indexes are equal)
    if ( ver1_pre < ver2_pre ):
        return -1
    if ( ver1_pre > ver2_pre ):
        return 1
            
    # If I get there - both versions are numerically equal
    return 0
    
            
def is_ver1_backwards_compatible_with_ver2( newer, older, newer_bhist=None ):
    pkg_older, branch_older, ver_older = older
    pkg_newer, branch_newer, ver_newer = newer
    
    
    # Same branch...
    if ( branch_older == branch_newer ):
        return _test_compatible( ver_older, ver_newer )
    
    # Different branches, but NO branch history provided
    elif ( newer_bhist == None ):
        # Withouth branch history, there is no way to determine compatibility
        return False   

    # Reverse traversal of branch history looking for compatibility
    else:
        # Walk the tree 'backwards'
        nodes, first, last = bhist
        return _inspect_parents( branch_newer, ver_newer, branch_older, ver_older, last )

        
def increment_version( base_ver, inc_patch=False, inc_minor=False, inc_major=False, new_prelease=None ):
    m,n,p,pre = parse_vernum( base_ver )
    if ( inc_major ):
        m   = int(m) + 1
        n   = 0
        p   = 0
        pre = ''
    elif ( inc_minor ):
        n   = int(n) + 1
        p   = 0
        pre = ''
    elif ( inc_patch ):
        p   = int(p) + 1
        pre = ''

    if ( new_prelease != None ):
        pre = new_prelease
        
    return build_vernum( m, n, p, pre )            

def _inspect_parents( now_bname, now_ver, older_bname, older_ver, curnode, level=0 ):
    
    # Verbose info
    if ( level == 0 ):
        print_verbose("BEGIN branch compatibility traversal for target/older node: {} {}".format(older_bname, older_ver) )
    print_verbose( "{:>2} : curnode={}, now={} {}".format(level, curnode, now_bname, now_ver ) )
    level += 1
    
    # NOTE: There are two scenarios for what my "parent" link means:
    #       1) Direct lineage, i.e. same branch just older publish point.  At this
    #          point I need to check if there was compatibility break between the
    #          two publish points.  And since we are still on the same branch, the
    #          semantic versioning is still valid
    #       2) Start of a new branch.  This is potentially problematic because I
    #          now need to test compatibility across branches which breaks 
    #          semantic versioning.  HOWEVER, the branching/version rules for when
    #          starting a new branch is that the 1st publish point on the new 
    #          branch is based/derived from the origin line.  What this means is
    #          in this very specific use case it is OKAY to compare version across
    #          branches.
   
    # Trap the case of a 'new branch'
    if ( now_bname != curnode.name ):
        if ( curnode.name == older_bname ):
            return _test_compatible( older_ver, now_ver )

    # Check if I am compatible with latest branch node on my direct lineage
    if ( not _test_compatible( curnode.version, now_ver ) ):
        return False
    
    # Stepparent -->i.e. go back via merge path
    if ( curnode.stepparent != None ):
        if ( _get_merge_wgt( curnode.stepparent, curnode ) == 'major' ):
            return False
        
        # if the step-parent branch IS the 'right branch' -->do compatibility check immediately
        if ( curnode.stepparent.name == older_bname ):
            return _test_compatible( older_ver, curnode.stepparent.version )
        
        # keep searching    
        if ( _inspect_parents( curnode.stepparent.name, curnode.stepparent.version, older_bname, older_ver, curnode.stepparent, level ) ):
            return True
                
    # Go back in direct lineage
    if ( curnode.parent != None ):
        return _inspect_parents( curnode.name, curnode.version, older_bname, older_ver, curnode.parent, level )
    else:
        return False
        

def _test_compatible( older, newer ):

    older_major, older_minor, older_patch, older_pre = parse_vernum( older )
    newer_major, newer_minor, newer_patch, newer_pre = parse_vernum( newer )
    
    # Compare: Major
    if ( older_major != newer_major ):
        return False
    
    # Compare: Minor
    if ( older_minor > newer_minor ):
        return False
    
    # Compare: Patch
    if ( (older_minor == newer_minor) and (older_patch > newer_patch) ):
        return False

    # Compare: Pre-release fields
    if ( (older_minor == newer_minor) and (older_patch == newer_patch) ):
        
        # Pre-release ALWAYS has less precendence than a 'normal' release
        if ( newer_pre != None ):
            if ( older_pre == None ):
                return false
 
            # TODO: Currently only support simple 'string compare' for the prerelease field
            if ( older_pre > newer_pre ):
                return False
      
    # If I get here - the versions are compatible
    return True


#-----------------------------------------------------------------------------
def append_to_file( fd, filename ):
    try:
        f   = open( filename, "r" )
        buf = f.read(1024)
        while( buf != '' ):
            fd.write(buf)
            buf = f.read(1024)
        f.close()
        
    except Exception as ex:
        exit( "ERROR: {}".format(ex) )        

#-----------------------------------------------------------------------------
def print_tar_list( tar_file_name, verbose=False ):
    try:
        print( tar_file_name )
        t = tarfile.open( tar_file_name )
        t.list( verbose )
        t.close()
    except Exception as ex:
        exit( "ERROR: Can't read archive file: {}. Error={}.".format( tar_file_name, ex ) )
        


#------------------------------------------------------------------------------
now   = 0
local = None

def mark_time( current_time = False ):
    global now, local
    if ( not current_time ):
        current_time = time.time()
        
    now       = int( current_time ) 
    local     = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(now))
    return now, local

def get_marked_time():
    global now, local
    return now, local
    
        
#-----------------------------------------------------------------------------
def render_dot_file_as_pic( pictype, oname ):
    if ( pictype ):
        cmd   = "dot -T{} -x -O {}".format(pictype,oname)
        fname = "{}.{}".format( oname, pictype )
        if ( os.path.isfile(fname) ):
            print_warning("Removing existing rendered {} file: {}".format(pictype,fname) )
            try:
                os.remove(fname)
            except Exception as ex:
                exit( "ERROR: {}".format(ex) )
        
        p  = subprocess.Popen( cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        r  = p.communicate()
        r0 = '' if r[0] == None else r[0].decode()
        r1 = '' if r[1] == None else r[1].decode()
        if ( p.returncode ):
            print( r0 + ' ' + r1 )
            exit( "ERROR: Failed rendering the .DOT file (ensure that the GraphVis 'bin/' directory is in your path)" )
        


