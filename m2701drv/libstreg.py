#! /usr/bin/python3

"""
  streg python library
    |  Description: STARS registry control library.
    |  History:
    |     0.1     Beta     2022.3.3    Yasuko Nagatani

"""

# Define: program info
__author__ = 'Yasuko Nagatani'
__version__ = '0.1'
__date__ = '2022-03-03'
__license__ = 'KEK'

import sys
import os
import re
from collections import OrderedDict

class libstreg():
    """About Class libstreg

       Parameter filename is used as a registry filename. Use DEFAULT_FILENAME if omitted or given value is None.

       | See functions about
       |    loadcache and savecache: for registry file I/O.
       |    createcache and undefcache: to create or remove a cache key.
       |    getcache and setcache: to view or update a cache value.
       |    getlasterrortext: for getting error information text.

    """
    DEFAULT_FILENAME   = './reg.txt'

    def __init__(self, filename=None):
        """Initialize the streglib with the filename of the STARS registry.
               if the filename argument is omitted, DEFAULT_FILENAME is used.
        """
        if(filename is None):
            filename = self.DEFAULT_FILENAME
        self._filename = str(filename)
        self.debug      = False
        self.error      = 'Just initialized with the filename %s.' %(self._filename)
        self._CACHEORIGINAL = OrderedDict()
        self._CACHE         = OrderedDict()
        self._perlstregcompatible = False
    #--------------------------------------------------------------------------
    def setdebug(self, b):
        """setdebug

        Set true to the argument b, print debug info to stdout.

        """
        if(b == True):
            self.debug = b
        else:
            self.debug = False
        return(True)
    #--------------------------------------------------------------------------
    def printinfo(self):
        """printinfo

        Print the instance variables info, Just use for debug.

        """
        d=self.debug
        self.debug = True
        self._debugprint("debug=%s\n" %d)
        
        self._debugprint("New cache:\n")
        dict=self._CACHE
        if(len(dict)==0):
            self._debugprint("> No new cache:\n")
        for k,v in (dict.items()):
            msg = ''
            if(v == ''):
                msg=">%s##\n" %(k)
            else:
                msg=">%s#%s#\n" % (k, v)
            self._debugprint(msg)
        self._debugprint("Org cache:\n")
        dict2=self._CACHEORIGINAL
        if(len(dict2)==0):
            self._debugprint("> No original cache:\n")
        for k,v in (dict2.items()):
            msg = ''
            if(v == ''):
                msg=">%s##\n" %(k)
            else:
                msg=">%s#%s#\n" % (k, v)
            self._debugprint(msg)
        self.debug=d

    def _debugprint(self,msg):
        if(self.debug == True):
            sys.stdout.write(msg)

    def getlasterrortext(self):
        """getlasterrortext

        Return the last error string.

        """
        return(self.error)
    #--------------------------------------------------------------------------
    def getfilename(self):
        """getfilename

        Return the registry filename used in this instance.

        """
        return(self._filename)
    #--------------------------------------------------------------------------
    def loadcache(self):
        """loadcache

        Load all data from the regisry file to cache.

        Returns:
            (bool) True if cache loaded, False if not.

        """
        filename = self._filename
        self._debugprint("loadcache(%s):start.\n" %(filename))
        rt = self._loadcache(filename)
        self._debugprint("loadcache(%s):finish.\n" %(filename))
        return(rt)

    def _convdata2cache(self, lines):
        
        vdict = OrderedDict()
        for i in range(len(lines)):
            line = lines[i]
            line2 = line.rstrip();
            if(line2 == ''):
                # line empty: ignore
                continue
            if(line[-1] == '\n'):
                line = line[:-1]
                #self._debugprint("_convdata2cache(cut\\n:%s).\n" %(line))
            line = line.replace('\r','')
            if(line.startswith('#')):
                # line comment: load as comment
                k = '#' + str(i)
                vdict[k] = line
                self._debugprint("_convdata2cache(comment%s)(%s).\n" %(k ,line))
                continue
            # Check record format
            # Delimiter is '=' -> nodename and property expected not to include the delimiter.
            # Value-> '': allowable.
            m = re.search(r'^([^=]+)=(.*)', line)
            if(m):
                # load as record
                k = m.group(1)
                v = m.group(2)
                vdict[k] = v
                self._debugprint("_convdata2cache(%s)(%s).\n" %(k, v))
            else:
                # Invalid record format
                self.error      = 'Invalid data format %s.' %(line)
                # load as comment
                k = '#' + str(i)
                vdict[k] = line
                self._debugprint("_convdata2cache(invalid%s)(%s).\n" %(k,line))
            if('Vch2Rch' in k):
                gb_cnltmp = vdict[k]

        return(vdict)

    def _loadcache(self, filename, testonly=False):
        if(os.path.isdir(filename)==True):
            self.error      = "File '%s' exists as directory." %(filename)
            self._debugprint("_loadcache:%s\n" %(self.error))
            return(False)
        elif(os.path.isfile(filename)==False):
            self.error      = "File '%s' not found." %(filename)
            self._debugprint("_loadcache:%s\n" %(self.error))
            return(False)
        try:
            with open(filename, "r") as f:
                lines=f.readlines()
                vdict = self._convdata2cache(lines)
                if(testonly == True):
                    self.error      = 'Cache loadable not unchanged by testmode.'
                else:
                    # Refresh cache
                    self._CACHEORIGINAL = vdict
                    self._CACHE = OrderedDict()
                    self.error      = 'Cache loaded.'
                self._debugprint("_loadcache:%s\n" %(self.error))
                return(True)
            self.error      = "Failed to load cache."
            self._debugprint("_loadcache(%s):%s.\n" %(filename, self.error))
            return(False)
        except IOError:
            self.error="File I/O error detected at the file '%s'." %(filename)
        except Exception as e:
            self.error="Unexpected error. [%s]" %(sys.exc_info()[0])
        self._debugprint("_loadcache:%s\n" %(self.error))
        return(False)

#######################################################################################################################
# for  SelectConfigFile    20220526
#######################################################################################################################
    def loadCNL(self):
        """loadcache

        Load all data from the regisry file to cache.

        Returns:
            (bool) True if cache loaded, False if not.

        """
        filename = self._filename
        self._debugprint("loadcache(%s):start.\n" %(filename))
        rt = self._loadCNL(filename)
        self._debugprint("loadcache(%s):finish.\n" %(filename))
        return(rt)

    def _convdata2CNL(self, lines):
        
        vdict = OrderedDict()
        for i in range(len(lines)):
            line = lines[i]
            line2 = line.rstrip();
            if(line2 == ''):
                # line empty: ignore
                continue
            if(line[-1] == '\n'):
                line = line[:-1]
                #self._debugprint("_convdata2cache(cut\\n:%s).\n" %(line))
            line = line.replace('\r','')
            if(line.startswith('#')):
                # line comment: load as comment
                k = '#' + str(i)
                vdict[k] = line
                self._debugprint("_convdata2cache(comment%s)(%s).\n" %(k ,line))
                continue
            # Check record format
            # Delimiter is '=' -> nodename and property expected not to include the delimiter.
            # Value-> '': allowable.
            m = re.search(r'^([^=]+)=(.*)', line)
            if(m):
                # load as record
                k = m.group(1)
                v = m.group(2)
                vdict[k] = v
                self._debugprint("_convdata2cache(%s)(%s).\n" %(k, v))
            else:
                # Invalid record format
                self.error      = 'Invalid data format %s.' %(line)
                # load as comment
                k = '#' + str(i)
                vdict[k] = line
                self._debugprint("_convdata2cache(invalid%s)(%s).\n" %(k,line))
            # folloing items added for the command of SelectConfigFile
            if('Vch2Rch' in k):
                cnltmp = vdict[k]
#            else:
#                cnltmp = 'none'

        return(cnltmp)

    def _loadCNL(self, filename):
        try:
            with open(filename, "r") as f:
                lines=f.readlines()
                cnltmp = self._convdata2CNL(lines)
                return(cnltmp)
            self.error      = "Failed to load cache."
            self._debugprint("_loadcache(%s):%s.\n" %(filename, self.error))
            return(False)
        except IOError:
            self.error="File I/O error detected at the file '%s'." %(filename)
        except Exception as e:
            self.error="Unexpected error. [%s]" %(sys.exc_info()[0])
        self._debugprint("_loadcache:%s\n" %(self.error))
        return(False)

####################################################################################################################



    #--------------------------------------------------------------------------
    def savecache(self):
        """savecache

        Save all data in cache to the regisrty file.

        Returns:
            (bool) True if cache saved to file, False if not.

        """
        filename = self._filename
        self._debugprint("savecache(%s):start.\n" %(filename))
        rt = self._savecache(filename)
        self._debugprint("savecache(%s):finish.\n" %(filename))
        return(rt)

    def _generatesavedata(self):
        dict  = self._CACHEORIGINAL
        dict2 = self._CACHE
        lines = list()
        for k,v in (dict.items()):
            # Look original data first.
            data = k + '=' + v
            # Overwrite by cache.
            if(k in dict2):
                v = dict2[k]
                del(dict2[k])
                if(v is None):
                    # case undef cache: skip ignore
                    self._debugprint("_generatesavedata(undef)(%s).\n" %(k))
                    continue
                # overwrite by cache.
                data = k + '=' + v
                self._debugprint("_generatesavedata(cache)(%s).\n" %(data))
            # Overwrite by original comment.
            elif(k.startswith('#')):
                # load original as comment
                data = v
                self._debugprint("_generatesavedata(comment)(%s).\n" %(data))
            else:
                self._debugprint("_generatesavedata(original)(%s).\n" %(data))
            lines.append(data)
        for k,v in (dict2.items()):
            if(v is None):
                continue
            # case create cache:
            data = k + '=' + v
            self._debugprint("_generatesavedata(newcache)(%s)\n" %(data))
            lines.append(data)
        return(lines)

    def _savecache(self, filename, testonly=False):
        if(os.path.isdir(filename)==True):
            self.error      = "File '%s' exists as directory." %(filename)
            self._debugprint("_savecache:%s\n" %(self.error))
            return(False)
        lines = self._generatesavedata()
        try:
            with open(filename, "w") as wfh:
                for i in range(len(lines)):
                    line = lines[i]
                    wfh.write(line+'\n')
                vdict = self._convdata2cache(lines)
                if(filename == self._filename):
                    self.error      = 'Cache saved to file.'
                    if(testonly == True):
                        pass
                    else:
                        self.error      = 'Cache saved to file and refreshed.'
                        self._CACHEORIGINAL = vdict
                        self._CACHE = OrderedDict()
                else :
                    self.error = "Cache saved to file '%s'." %(filename)
            return(True)
        except IOError:
            self._debugprint("%s\n" %e)
            self.error="Failed to save cache to file '%s'" %(self._filename)
        except Exception as e:
            self._debugprint("%s\n" %e)
            self.error="Unexpected error. [%s]" %(sys.exc_info()[0])
        return(False)
    #--------------------------------------------------------------------------
    def getcache(self, nodename, property, notfoundret = None):
        """getcache

        Get a value of cache by given nodename and property.

        Args:
            nodename(string): stars nodename used for generating the name of key.
            property(string): property name used for generating the name of key.
            notfoundret(optional object): a value of return when the cache key not found. None is the default.

        Returns:
            (string) a value of key. 
            (object) The value of 'notfoundret' if not found.

        """
        k = self.makekey(nodename, property)
        if(k is None):
            return(notfoundret)
        dict1 = self._CACHE
        dict2 = self._CACHEORIGINAL
        if(k in dict1.keys()):
            v = dict1[k]
        elif(k in dict2.keys()):
            v = dict2[k]
        else:
            return(notfoundret)
        if(v is None):
            # Case removed. not in the property list.
            return(notfoundret)
        elif(v == ''):
            # Case empty.
            self.error = "Value empty."
        else:
            self.error = self.error.replace(' not found',' found')
        return(v)
     #--------------------------------------------------------------------------
    def getallkeys(self, valuefilter=None, nodefilter=None, notfoundret = None):
        """getallkeys

        Return list of registry keys.

        Optional parameters of valuefilter and nodefilter are used to filter the keys.
        No filtering if they are omitted or their value are None.

        Args:
            valuefilter(optinal,string):
                 Filter the keys which value equal with the valuefilter.
            nodefilter(optinal,string):
                 Filter the keys
                 of which nodenames start with nodefilter if the nodefilter endwiths '.' 
                 or of which nodenames equal with nodefilter[:-1] if nodefilter endwith ':'.  
                 or of both which nodenames start with nodefilter + '.' and which nodenames equals with nodefilter.
            notfoundret(optional object): a value of return when list of keys not found. None is the default.

        Returns:
            (list) List of registry keys.
            (object) The value of 'notfoundret' if no list.

        """

        sv = str(valuefilter)
        # Read all keys
        dict1 = self._CACHEORIGINAL
        dict2 = self._CACHE
        l_in  = [k for k,v in dict1.items() if ((k.startswith("#")==False))]
        l_in2 = [k for k,v in dict2.items() if ((k.startswith("#")==False))]
        l_in.extend(l_in2)
        sellist=sorted(set(l_in), key=l_in.index)
        # Filter by value
        retvals=list()
        for pkey in (sellist):
            m = re.search(r'^([^:]+):(.*)', pkey)
            if(m):
                n = m.group(1)
                if(nodefilter is not None):
                    if(nodefilter.endswith(':') and (n == nodefilter[:-1])):
                        pass
                    elif(nodefilter.endswith('.') and (n.startswith(nodefilter))):
                        pass
                    elif(n == nodefilter):
                        pass
                    elif(n.startswith(nodefilter+'.')):
                       pass
                    else:
                        continue
                p = m.group(2)
                v = self.getcache(n,p)
                if(v is not None):
                    if(valuefilter is None):
                        retvals.append(pkey)
                    elif(v == sv):
                        retvals.append(pkey)
        if(len(retvals)<=0):
            if(valuefilter is None):
                self.error = "List is void."
            else:
                self.error = "Key with value '%s' not found." %(sv)
            return(notfoundret)
        return(retvals)

    def getcacheregex(self, nodename, startproperty, notfoundret = None):
        """getcacheregex

        Return list of data.

        Parameters of nodename and startproperty are used to filter the data.

        Args:
            nodename(string): stars nodename used for filtering the name of key.
            startproperty(string): Filter keys which their properties start with the startproperty.
            notfoundret(optional object): a value of return when list of data not found. None is the default.

        Returns:
            (list) list of data format 'key=value'.
            (object) The value of 'notfoundret' if no list.
        """
        sk = self.makekey(nodename, startproperty)
        if(sk is None):
            return(notfoundret)
        dict1 = self._CACHE
        dict2 = self._CACHEORIGINAL
        l_in  = [k for k,v in dict1.items() if ((k.startswith(sk)==True))]
        l_in2 = [k for k,v in dict2.items() if ((k.startswith(sk)==True))]
        l_in.extend(l_in2)
        sellist=sorted(set(l_in), key=l_in.index)
        retvals=list()
        for pkey in (sellist):
            m = re.search(r'^([^:]+):(.*)', pkey)
            if(m):
                n = m.group(1)
                p = m.group(2)
                v = self.getcache(n,p)
                if(v is not None):
                    retvals.append(p+"="+v)
        if(len(retvals)<=0):
            self.error = "Property which starts with '%s' not found." %(sk)
            return(notfoundret)
        return(retvals)
    #--------------------------------------------------------------------------
    def createcache(self,nodename,property):
        """createcache

        Create a new cache key with value '' by given nodename and property.

        Args:
            nodename(string): stars nodename used for generating the name of key.
            property(string): property name used for generating the name of key.

        Returns:
            (bool) True if a new cache created, False if not.

        """
        return(self._createcache(nodename,property))

    def _createcache(self,nodename,property,value=''):
        k = self.makekey(nodename, property)
        if(k is None):
            return(False)
        orgv = self.getcache(nodename, property)
        if(orgv is not None):
            self.error = "'%s' is already exists in the property list." %(nodename)
            return(False)
        self.error = self.error.replace(' not found',' created')
        self._debugprint("%s\n" %(self.error))
        self._CACHE[k] = value
        return(True)
    #--------------------------------------------------------------------------
    def undefcache(self, nodename, property):
        """undefcache

        Remove a existing cache key by given nodename and property.

        Args:
            nodename(string): stars nodename used for generating the name of key.
            property(string): property name used for generating the name of key.
 
        Returns:
            (bool) True if a cache removed, False if not.

        """
        k = self.makekey(nodename, property)
        if(k is None):
            return(False)
        orgv = self.getcache(nodename, property)
        if(orgv is None):
            return(False)
        else:
            self._CACHE[k] = None
            self.error = self.error.replace(' found in',' removed from')
        self._debugprint("%s\n" %(self.error))
        return(True)
    #--------------------------------------------------------------------------
    def setcache(self, nodename, property, value, allownewkey=False):
        """setcache

        Set a value of cache by given nodename and property.

        Args:
            nodename(string): stars nodename used for generating the name of key.
            property(string): property name used for generating the name of key.
            value(string): a updating value.
            allownewkey(optional bool): True to allow creating new cache by given nodename and property. False is the default.

        Returns:
            (bool) True if the value cached, False if not.

        """
        k = self.makekey(nodename, property)
        if(k is None):
            return(False)
        v = str(value)
        orgv = self.getcache(nodename, property)
        if(orgv is None):
            if(allownewkey==True):
                b = self._createcache(nodename, property,v)
                if(b == False):
                    return(b)
            else:
                return(False)
        elif(v == orgv):
            self.error  = 'Value already cached.'
        else:
            if(k in self._CACHEORIGINAL):
                if(self._CACHEORIGINAL[k]==v):
                    del(self._CACHE[k])
                else:
                    self._CACHE[k] = v
            else:
                self._CACHE[k] = v
            self.error      = 'Cache updated with new value.'
        return(True)
    #--------------------------------------------------------------------------
#--------------------------------------------------------------------------
# setcach2  for "SetConfig setting Vch=Rch" 20220525
    def setcach2(self, nodename, property, value, allownewkey=False): 
        """setcache

        Set a value of cache by given nodename and property.

        Args:
            nodename(string): stars nodename used for generating the name of key.
            property(string): property name used for generating the name of key.
            value(string): a updating value.
            allownewkey(optional bool): True to allow creating new cache by given nodename and property. False is the default.

        Returns:
            (bool) True if the value cached, False if not.

        """
        k = self.makekey(nodename, property)
        if(k is None):
            return(False)
        v = str(value)
        orgv = self.getcache(nodename, property)
        if(orgv is None):
            if(allownewkey==True):
                b = self._createcache(nodename, property,v)
                if(b == False):
                    return(b)
            else:
                return(False)
        elif(v == orgv):
            self.error  = 'Value already cached.'
        else:
            if(k in self._CACHEORIGINAL):
                if(self._CACHEORIGINAL[k]==v):
                    del(self._CACHE[k])
                else:
                    self._CACHE[k] = v
            else:
                self._CACHE[k] = v
            self.error      = 'Cache updated with new value.'
        return(True)
    #--------------------------------------------------------------------------

    def iscacheChanged(self):
        """iscacheChanged

        Return True if cache changed from original data or False.

        """
        if(len(self._CACHE.keys())>0):
            return True
        return False
    #--------------------------------------------------------------------------
    def getnodepropertybykey(self,key):
        """getnodepropertybykey

        Return nodename and property by given key.

        Args:
            key(string): key value.

        Returns:
            (string,string) (nodename,property).
            (None, None) if the given invalid key.

        """
        (node,prop)=(None,None)
        if(':' in key):
            (node,prop)= key.split(":",1)
        else:
            self.error = "Invalid key '%s'. " %(key)
        return(node,prop)
    #--------------------------------------------------------------------------
    def makekey(self,nodename,property):
        """makekey

        Return a key by given nodename and property.

        Args:
            nodename(string): stars nodename used for generating the name of key.
            property(string): property name used for generating the name of key.

        Returns:
            (string) key value.
            (object) None if the given invalid parameters.

        """
        if(nodename == ''):
            self.error      = "Missing stars nodename."
            return(None)
        elif(nodename.startswith("#")==True):
            self.error      = "Stars nodename '%s' starts with '#' characters." %(nodename)
            return(None)
        elif(':' in nodename):
            self.error      = "Stars nodename '%s' contains the delimiter ':' characters." %(nodename)
            return(None)
        elif(' ' in nodename):
            self.error      = "Stars nodename '%s' contains space characters." %(nodename)
            return(None)
        elif(property == ''):
            pass
        elif('=' in property):
            self.error      = "Property '%s' contains the delimiter '='." %(property)
            return(None)
        else:
            if((self._perlstregcompatible==False) and (' ' in property)):
                self.error  = "Property '%s' contains the space character." %(property)
                return(None)
            elif(property[0] == ' '):
                self.error = "Property '%s' starts with space characters." %(property)
                return(None)
        k = nodename + ':' + property
        if(property == ''):
            #Message template for not found.
            self.error = "'%s' is not found in the property list." %(nodename)
        else:
            #Message template for not found.
            self.error = "'%s' is not found in the property list." %(property)
        return(k)
