"""Collection of helper functions"""


import sys, os, errno, fnmatch, subprocess, time, calendar, copy
import errno, stat, shutil
import json
import collections
from gitignore_parser import parse_gitignore
from collections import deque
#import platform, tarfile
#from collections import deque

from my_globals import PACKAGE_INFO_DIR
from my_globals import PACKAGE_FILE
from my_globals import PKG_DIRS_FILE
from my_globals import IGNORE_DIRS_FILE
from my_globals import PACKAGE_FILE
from my_globals import OVERLAY_PKGS_DIR
from my_globals import PACKAGE_ROOT


# Module globals
_dirstack = []
quite_mode   = False
verbose_mode = False

TEMP_IGNORE_FILE_NAME = '__temp_' + IGNORE_DIRS_FILE() + "._delete_me__"
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
def deque_delete_nth(d, n):
    d.rotate(-n)
    d.popleft()
    d.rotate(n)

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
        shutil.rmtree( root, ignore_errors=False, onerror=_handleRemoveReadonly )
    except Exception as exc:
        if ( err_msg != None ):
            sys.exit( f'{err_msg} ({exc})' )
        elif ( warn_msg != None ):
            print_warning( f'{warn_msg} ({exc})' )


# This function handles issue with Windows when deleting files marked as readonly
def _handleRemoveReadonly(func, path, exc):
  excvalue = exc[1]
  if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == errno.EACCES:
      # ensure parent directory is writeable too
      pardir = os.path.abspath(os.path.join(path, os.path.pardir))
      if not os.access(pardir, os.W_OK):
        os.chmod(pardir, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO)

      os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
      func(path)
  else:
      raise   
  
# This function returns true the root the primary repository
def find_root( primary_scm_tool, verbose ):
    # Note: Running the SCM command creates a nested run_shell scenario - it only works if 'verbose' is turned off (because the 'verbose' output gets mixed in when the git command's output)
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
    

# Copies only the files in the src-dir to the dst-dir
def copy_files( srcdir, dstdir ):
    src_files = os.listdir(srcdir)
    for file_name in src_files:
        full_file_name = os.path.join(srcdir, file_name)
        if os.path.isfile(full_file_name):
            mkdirs( dstdir )
            shutil.copy(full_file_name, dstdir)

# Deletes all of the files in a directory AND deletes the directory if it is empty after deleting the files
def delete_directory_files( dir_to_delete ):
    src_files = os.listdir( standardize_dir_sep( dir_to_delete) )
    for file_name in src_files:
        full_file_name = os.path.join(dir_to_delete, file_name)
        if os.path.isfile(full_file_name):
            os.remove( full_file_name )

    # Delete the dir if it is now empty
    try:
        os.rmdir( dir_to_delete )
    except:
        pass

#-----------------------------------------------------------------------------
# return None if not able to load the file
def load_package_file( path=PACKAGE_INFO_DIR(), file=PACKAGE_FILE(), does_file_exist=None):
    f = os.path.join(  path, file )

    try:
        with open(f) as f:
            result = check_package_file( json.load( f ) )
            does_file_exist = True
            return result

    except Exception as e:
        does_file_exist = True
        return check_package_file( {} )

def load_dependent_package_file( pkgobj, file=PACKAGE_FILE() ):
    # OVERLAY package
    if ( pkgobj['pkgtype'] == 'overlay' ):
        return load_package_file( os.path.join( OVERLAY_PKGS_DIR(), pkgobj['pkgname'], PACKAGE_INFO_DIR() ) )

    # Readonly/Foreign Packages
    else:
        if ( pkgobj['parentDir'] == None ):
            sys.exit( f"ERROR: the {PACKAGE_FILE()} file is corrupt. There is no parent directory for the package: {pkgobj['pkgname']}" )
        return load_package_file( os.path.join(  pkgobj['parentDir'], pkgobj['pkgname'], PACKAGE_INFO_DIR() ) )

def write_package_file( json_dictionary ):
    # make sure the pkgs.info directory exists
    if ( not os.path.isdir( PACKAGE_INFO_DIR() ) ):
        mkdirs( PACKAGE_INFO_DIR() )

    od = collections.OrderedDict(sorted(json_dictionary.items()))
    f  = os.path.join(  PACKAGE_INFO_DIR(),PACKAGE_FILE() )
    data = json.dumps( od, indent=2 )
    with open( f, "w+" ) as file:
        file.write( data )

def cat_package_file( indent=2, path=PACKAGE_INFO_DIR(), file=PACKAGE_FILE() ):
    f = os.path.join(  path, file )

    try:
        with open(f) as f:
            json_dict =  json.load( f )
            od = collections.OrderedDict(sorted(json_dict.items()))
            print( json.dumps( od, indent=indent ) )
            return json_dict
    except Exception as e:
        sys.exit( f"ERROR: Corrupt package file - {f} ({e})" )


def json_get_dep_package( dep_list, package_to_find ):
    if ( len(dep_list) > 0 ):
        try:
            idx = 0
            for p in dep_list:
                if ( p['pkgname'] == package_to_find ):
                    return p, idx
                idx = idx + 1

            return None, None
        except Exception as e:
            sys.exit( f"ERROR: Package file (dependencies) is corrupt {e}" )
    return None, None

def json_create_dep_entry( pkgname, pkgtype, parentdir, date_adopted, ver_sem, ver_branch, ver_id, repo_name, repo_type, repo_origin ):
    ver_dict  = { "semanticVersion" : ver_sem, "branch" : ver_branch, "tag" : ver_id }
    repo_dict = { "name" : repo_name, "type": repo_type, "origin" : repo_origin }
    dep_dict  = { "pkgname" : pkgname, "pkgtype" : pkgtype, "adoptedDate": date_adopted, "parentDir" : parentdir, "version" : ver_dict, "repo": repo_dict }
    return dep_dict

def json_update_package_file_with_new_dep_entry( json_dict, new_dep_entry, is_weak_dep=False ):
    if ( is_weak_dep ):
        json_dict['dependencies']['weak'].append( new_dep_entry )
    else:
        json_dict['dependencies']['strong'].append( new_dep_entry )
    write_package_file( json_dict )

def json_find_dependency( json_dictionary, pkgname ):
    deptype    = 'strong'
    pkgobj,idx = json_get_dep_package( json_dictionary['dependencies'][deptype], pkgname )
    if ( pkgobj == None ):
        deptype    = 'weak'
        pkgobj,idx = json_get_dep_package( json_dictionary['dependencies'][deptype], pkgname )
        if ( pkgobj == None ):
            return None, None, None
    return pkgobj, deptype, idx

# Returns list of dictionary 'dep' entries (a 'depType' key pair set to S|W is added to the dep dictionary instances)
def get_dependency_list( json_dict, include_immediate=True, include_weak=True ):
   # Get immeidate deps
    pkgs = []
    if ( include_immediate ):
        for p in json_dict['dependencies']['strong']:
            p['depType'] = 'S'
            pkgs.append( p )

    # Get weak deps
    if ( include_weak ):
        for p in json_dict['dependencies']['weak']:
            p['depType'] = 'W'
            pkgs.append( p )

    return pkgs

# Returns an empty list if no overlaid dirs
def json_get_list_adopted_overlay_deps( json_dictionary):
    olist = []
    try:
        deps = json_dictionary['dependencies']['strong']
        for d in deps:
            if ( d['pkgtype'] == 'overlay' ):
                olist.append( d )
        deps = json_dictionary['dependencies']['weak']
        for d in deps:
            if ( d['pkgtype'] == 'overlay' ):
                olist.append( d )
    except:
        pass

    return olist

def json_get_dep_parentdir( depdict ):
    return '<none>' if depdict['parentDir'] == None else depdict['parentDir']

def json_get_dep_semver( depdict ):
    return '<none>' if depdict['version']['semanticVersion'] == None else depdict['version']['semanticVersion']

def json_get_dep_branch( depdict ):
    return '<none>' if depdict['version']['branch'] == None else depdict['version']['branch']

def json_get_dep_tag( depdict ):
    return '<none>' if depdict['version']['tag'] == None else depdict['version']['tag']

def json_get_dep_repo_name( depdict ):
    return '<none>' if depdict['repo']['name'] == None else depdict['repo']['name']

def json_get_dep_repo_type( depdict ):
    return '<none>' if depdict['repo']['type'] == None else depdict['repo']['type']

def json_get_dep_repo_origin( depdict ):
    return '<none>' if depdict['repo']['origin'] == None else depdict['repo']['origin']


def json_get_package_primary_dirs( json_dictionary ):
    if ( json_dictionary != None ):
        return json_dictionary['directories']['primary']

def json_get_package_extra_dirs( json_dictionary ):
    l = []
    try:
        for d in json_dictionary['directories']['adoptedExtras']:
            l.append( standardize_dir_sep(d) )
    except:
        pass
    return l
   
    return json_dictionary['directories']['adoptedExtras']


def json_update_package_file_with_new_primary_dirs( json_dictionary, list_of_dirs ):
    json_dictionary['directories']['primary'] = list_of_dirs
    write_package_file( json_dictionary )

def json_update_package_file_with_new_extra_dirs( json_dictionary, list_of_dirs ):
    stdlist = []
    for d in list_of_dirs:
        stdlist.append( force_unix_dir_sep( d ) )
    json_dictionary['directories']['adoptedExtras'] = stdlist
    write_package_file( json_dictionary )


def json_update_package_file_info( json_dictionary, pkgname = None, desc =None, owner=None, email=None, url=None, rname=None, rtype=None, rorigin=None ):
    if ( pkgname != None ):
        json_dictionary['info']['pkgname']        = pkgname
    if ( desc != None ):
        json_dictionary['info']['desc']           = desc
    if ( owner != None ):
        json_dictionary['info']['owner']          = owner
    if ( email != None ):
        json_dictionary['info']['email']          = email
    if ( url != None ):
        json_dictionary['info']['url']            = url
    if ( rname != None ):
        json_dictionary['info']['repo']['name']   = rname
    if ( rtype != None ):
        json_dictionary['info']['repo']['type']   = rtype
    if ( rorigin != None ):
        json_dictionary['info']['repo']['origin'] = rorigin

def json_copy_info( json_dict_in ):
    dict_out = { 'info':{} }
    dict_out['info']['pkgname']        = json_dict_in['info']['pkgname']
    dict_out['info']['desc']           = json_dict_in['info']['desc']
    dict_out['info']['owner']          = json_dict_in['info']['owner']
    dict_out['info']['email']          = json_dict_in['info']['email']
    dict_out['info']['url']            = json_dict_in['info']['url']
    dict_out['info']['repo']           = {}
    dict_out['info']['repo']['name']   = json_dict_in['info']['repo']['name']
    dict_out['info']['repo']['type']   = json_dict_in['info']['repo']['type']
    dict_out['info']['repo']['origin'] = json_dict_in['info']['repo']['origin']

    return dict_out

# create version entry.  If NO date is provided than the current time is used
def json_create_version_entry( comment, semver, date=None ):
    now = int(time.time())
    t   = time.gmtime(now)
    if ( date != None ):
        t   = time.strptime( date )
        now = calendar.timegm( t )
    entry  = { "comment" : comment, "version" : semver, "date" : time.asctime(t), "timestamp": now }
    return entry

# update the 'current' published version
def json_update_current_version( json_dict, ver_entry, save_pkg=True ):
    json_dict['publish']['current'] = ver_entry
    if ( save_pkg ):
        write_package_file( json_dict )


# Create a new 'current' and adds the old-current to the history array
def json_add_new_version( json_dict, ver_entry, save_pkg=True ):
    prev = json_dict['publish']['current']
    hist = json_dict['publish']['history']
    if ( prev != None ):
        hist.insert(0, prev)
    json_update_current_version( json_dict, ver_entry, save_pkg )

# edits an existing history entry
def json_update_history_version( json_dict, idx, comment, semver, save_pkg=True  ):
    # validate the index
    idx = int(idx)
    if ( idx >= len(json_dict['publish']['history']) or idx <  0 ):
        sys.exit(f"ERROR: Index value {idx} is out of range." )

    # Use the existing timestamp - but with new comments/ver
    e = json_dict['publish']['history'][idx]
    updated = json_create_version_entry( comment, semver, e['date'] )
    json_dict['publish']['history'][idx] = updated

    if ( save_pkg ):
        write_package_file( json_dict )

# Returns the Publish dictionary
def json_get_published( json_dict ):
    return( json_dict['publish'] )

# Returns the current published version
def json_get_current_version( json_dict ):
    return json_dict['publish']['current']

# Returns the current published version
def json_get_current_semver( json_dict ):
    return json_dict['publish']['current']['version']

# Returns the published history
def json_get_version_history( json_dict ):
    return json_dict['publish']['history']

# returns the package's name
def json_get_package_name( json_dict ):
    return json_dict['info']['pkgname']

# Performs a basic check of the file contents and/or ensure that a minimal number of key/value pairs exist
def check_package_file( json_dict_in ):
    if ( not 'publish' in json_dict_in ):
        json_dict_in['publish'] = {}
    if ( not 'current' in json_dict_in['publish'] ):
        json_dict_in['publish']['current'] = None
    if ( not 'history' in json_dict_in['publish'] ):
        json_dict_in['publish']['history'] = []

    if ( not 'dependencies' in json_dict_in ):
        json_dict_in['dependencies'] = {}
    if ( not 'strong' in json_dict_in['dependencies'] ):
        json_dict_in['dependencies']['strong'] = []
    if ( not 'weak' in json_dict_in['dependencies'] ):
        json_dict_in['dependencies']['weak'] = []

    if ( not 'directories' in json_dict_in ):
        json_dict_in['directories'] = {}
    if ( not 'primary' in json_dict_in['directories'] ):
        json_dict_in['directories']['primary'] = None
    if ( not 'adoptedExtras' in json_dict_in['directories'] ):
        json_dict_in['directories']['adoptedExtras'] = None

    if ( not 'info' in json_dict_in ):
        json_dict_in['info'] = {}
    if ( not 'pkgname' in json_dict_in['info'] ):
        json_dict_in['info']['pkgname'] = None
    if ( not 'desc' in json_dict_in['info'] ):
        json_dict_in['info']['desc'] = None
    if ( not 'owner' in json_dict_in['info'] ):
        json_dict_in['info']['owner'] = None
    if ( not 'email' in json_dict_in['info'] ):
        json_dict_in['info']['email'] = None
    if ( not 'url' in json_dict_in['info'] ):
        json_dict_in['info']['url'] = None
    if ( not 'repo' in json_dict_in['info'] ):
        json_dict_in['info']['repo'] = {}
    if ( not 'name' in json_dict_in['info']['repo'] ):
        json_dict_in['info']['repo']['name'] = None
    if ( not 'type' in json_dict_in['info']['repo'] ):
        json_dict_in['info']['repo']['type'] = None
    if ( not 'origin' in json_dict_in['info']['repo'] ):
        json_dict_in['info']['repo']['origin'] = None

    return json_dict_in

#-----------------------------------------------------------------------------
# return None if not able to load the file
def load_dirs_list_file( path=PACKAGE_INFO_DIR(), file=PKG_DIRS_FILE() ):
    f = os.path.join( path, file )
    try:
        with open(f) as f:
            lines = f.readlines()
            result = []
            for l in lines:
                result.append( standardize_dir_sep(l.strip()) )
            return result

    except Exception as e:
        print( e )
        return None

def save_dirs_list_file( list_of_dirs, path=PACKAGE_INFO_DIR(), file=PKG_DIRS_FILE() ):
    f = os.path.join( path, file )
    try:
        with open(f, 'w') as f:
           files = "\n".join(list_of_dirs)
           f.write(force_unix_dir_sep( files) )
    except:
        sys.exit( f"WARNING: Failed to update the {f} with the directory list" )

# return None if not able to load the file
def load_overlaid_dirs_list_file( adopted_pkg_name, dir_list_file_root=OVERLAY_PKGS_DIR() ):
    if ( adopted_pkg_name == None ):
        return None
    p = os.path.join( dir_list_file_root, adopted_pkg_name, PACKAGE_INFO_DIR() )
    return load_dirs_list_file( path=p )

# returns None if there is no 'ignore file' in the pkg.info dir
def get_ignore_file( root ):
    f = os.path.join( root, PACKAGE_INFO_DIR(), IGNORE_DIRS_FILE() )
    if ( os.path.isfile( f ) ):
        return f

    return None

# Filters the directory list by the 'ignore file', dirs with no files
# If 'ignore_file' does NOT exist - than all dirs are returned
def walk_dir_filtered_by_ignored( tree_to_walk, ignore_file, pkgroot ):
    push_dir(pkgroot)

    ignored = None
    if ( ignore_file != None ):
        try:
            # Temporarly make a copy of the ignore file in the package root
            tmpname = os.path.join( pkgroot, TEMP_IGNORE_FILE_NAME )
            shutil.copy( ignore_file, tmpname )
            ignored = parse_gitignore( tmpname )
            os.remove( TEMP_IGNORE_FILE_NAME )
        except:
            ignored = None

    list = []
    for root, dirs, files in os.walk(tree_to_walk):
        if ( len(files) > 0 ):
            if ( ignored == None or ignored( root ) == False ):
                list.append( standardize_dir_sep(root) )
            
    pop_dir()
    return list        


# create list of dirs from adopted overlay dependencies
def get_adopted_overlaid_dirs_list( list_of_dep_pkgs, dir_list_file_root=OVERLAY_PKGS_DIR() ):
    result = []
    try:
        for p in list_of_dep_pkgs:
            d = load_overlaid_dirs_list_file( p['pkgname'], dir_list_file_root )
            if ( d != None ):
                result.extend( d )
    except Exception as e:
        pass

    return result

# gets a list of directories owned by a package being adopted
def get_adoptee_owned_dirs(  path_to_package_file=PACKAGE_INFO_DIR(), dir_list_file_root=OVERLAY_PKGS_DIR()  ):
    package_json = load_package_file( path_to_package_file);
    dirs         = load_overlaid_dirs_list_file( json_get_package_name(package_json), dir_list_file_root )
    return dirs

# Gets list of a packages owned directories
def get_owned_dirs( pkgroot, path_to_package_file=PACKAGE_INFO_DIR(), dir_list_file_root=OVERLAY_PKGS_DIR() ):
    package_json = load_package_file( path_to_package_file);
    overlay_deps = json_get_list_adopted_overlay_deps( package_json )
    odirs        = get_adopted_overlaid_dirs_list( overlay_deps, dir_list_file_root )
    dirsPrimary  = json_get_package_primary_dirs(package_json) 
    localdirs    = []
    ignorefile   = get_ignore_file(pkgroot)
    if ( dirsPrimary == None or len(dirsPrimary) == 0 ):
        sys.exit( "ERROR: NO 'primary' directories have been specified for the package" )

    for d in dirsPrimary:
        l = walk_dir_filtered_by_ignored( d, ignorefile, pkgroot ) 
        localdirs.extend( l )
    
    # Remove overlaid directories
    return [x for x in localdirs if x not in odirs]

#-----------------------------------------------------------------------------
def copy_pkg_info_dir( dstdir, srcdir ):
    if ( not os.path.isdir( srcdir ) ):
        sys.exit( f"ERROR: Missing package info directory ({srcdir})" )
    mkdirs( dstdir )
    shutil.copytree( srcdir, dstdir, dirs_exist_ok=True )

def copy_extra_dirs( dstdir, src_package_root ):
    extra_dirs = get_extra_dirs( src_package_root )
    for d in extra_dirs:
        src = os.path.join( src_package_root, d )
        dst = os.path.join( dstdir, d )
        shutil.copytree( src, dst, dirs_exist_ok=True )

def get_extra_dirs( src_package_root ):
    package_path = os.path.join( src_package_root, PACKAGE_INFO_DIR())
    package_json = load_package_file( path=package_path )
    return json_get_package_extra_dirs( package_json )

#-----------------------------------------------------------------------------
def get_adopted_semver( src_pkg_info, default_return_value, pkgname, warn_nover ):
    package_json = load_package_file( path=src_pkg_info )
    current      = json_get_current_version( package_json )
    result       = default_return_value
    try:
        result = current['version']
    except Exception as e:
        pass

    if ( result == None and warn_nover ):
        print( f"Warning: No semantic version was specified/available for the adoptee package: {pkgname}" )
    
    return result

#-----------------------------------------------------------------------------
# Returns a tuple: (<strongList>, <weakList>), lists will be empty if no cyclical deps
def check_cyclical_deps( mypkg_name, pkgobj, suppress_warnings=False, file=PACKAGE_FILE() ):
    cyc_strong = []
    cyc_weak = []

    # Get Dependencies info
    dep_dict = load_dependent_package_file( pkgobj, file )
    if ( dep_dict == None and suppress_warnings == False ):
        print( f"Warning: Not able to check for Cyclical dependencs because the {pkgobj['pkgname']} does NOT have package.json file" )
        return (cyc_strong, cyc_weak)

    # Check for strong cyclical deps
    dep_deps = get_dependency_list( dep_dict, include_immediate=True, include_weak=False )
    for d in dep_deps:
        if ( d['pkgname'] == mypkg_name ):
            cyc_strong.append( d )

    # Check for weak cyclical deps
    dep_deps = get_dependency_list( dep_dict, include_immediate=False, include_weak=True )
    for d in dep_deps:
        if ( d['pkgname'] == mypkg_name ):
            cyc_weak.append( d )

    return(cyc_strong, cyc_weak)


#-----------------------------------------------------------------------------
def build_vernum( m, n, p, pre=None ):
    ver = "{}.{}.{}".format(m,n,p)
    if ( pre != None and pre != ''):
        ver = "{}-{}".format(ver,pre)
       
    return ver

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
    

def is_semver_compatible( older, newer ):

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
class Node(object):
    def __init__(self, data ):
        self.data     = data
        self.nodenum  = 0
        self.parent   = None
        self.children = []

    def __repr__(self, level=0):
        ret = "{}{}-{} ({})\n".format( "  "*level, self.get_pkgname(), self.get_semver(), self.get_dep_type() )
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
        return c
        
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
        
    def get_dep_type( self ):
        return self.data[1]

    def get_pkgname( self ):
        if ( self.parent == None ):
            if ( self.data[0] != None and self.data[0] != None ):
                return json_get_package_name( self.data[0] ) 
            else:
                return "<unknown>"

        return self.data[2]['pkgname']

    def get_semver( self ):
        if ( self.parent == None ):
            if ( self.data[0] != None and self.data[0]['publish']['current'] != None ):
                return json_get_current_semver( self.data[0] ) 
            else:
                return "<unknown>"

        return self.data[2]['version']['semanticVersion']
    
    def get_path_to_me( self ):
        path = deque()
        path.append( self )
        parent = self.parent 
        while( parent != None ):
            path.appendleft( parent )
            parent = parent.parent
        return path

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




