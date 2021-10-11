""" Global variables """

    
#
def ORC_VERSION():
    return "v2.0.1-alpha"
    
def EVIE_VERSION():
    return ORC_VERSION()
    
# SCM for adopted packages
def OUTCAST_SCM_ADOPTED_TOOL():
    return 'OUTCAST_SCM_ADOPTED_TOOL'
   
# SCM for primary/local package
def OUTCAST_SCM_PRIMARY_TOOL():
    return 'OUTCAST_SCM_PRIMARY_TOOL'

def ADOPTED_PKGS_DIR():
    return 'pkgs.adopted'

def PRIMARY_PKG_DIR():
    return 'pkgs.info'

def DEPS_FILE():
    return 'deps.json'


#
#def NQBP_PRJ_DIR( newval=None ):
#    global _NQBP_PRJ_DIR
#    if ( newval != None ):
#        if ( newval.endswith(os.sep) ):
#            newval [:-1]
#        _NQBP_PRJ_DIR = newval
#    return _NQBP_PRJ_DIR

          
    
    
    
    
