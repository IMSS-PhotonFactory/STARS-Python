#! /usr/bin/python3

import sys
import time
import os
try:
    from configparser import ConfigParser, SafeConfigParser,NoSectionError
except ImportError:
    try:
        from ConfigParser import ConfigParser, SafeConfigParser,NoSectionError
    except ImportError:
        sys.stderr.write('Install configparser for python 3.x')
        sys.stderr.write('or ConfigParser for python 2.x')
        exit(1)

#----------------------------------------------------------------
# Class Python utility Config
#----------------------------------------------------------------
class PyStarsUtilConfig():
    """ Class PyStarsUtilConfig:
    """

    #----------------------------------------------------------------
    # Error functions
    #----------------------------------------------------------------
    def getlasterrortext(self):
        """ getlasterrortext: Return the last error message text.

              Returns:
                (string) the last error message text.
        """
        return(self._error)

    #----------------------------------------------------------------
    # debug functions
    #----------------------------------------------------------------
    def setdebug(self, b):
        """ setdebug: debug option.

              Parameters:
                b -- (bool) set True to print debug infomation text to stdout.
        """
        if(b is None):
            self._debug = False
        if(b == True):
            self._debug = b
        else:
            self._debug = False
        return

    def _debugprint(self,msg):
        if(self._debug == True):
            try:
                ct=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
                sys.stdout.write(ct+' '+msg)
            except Exception as e:
                return
        return

    #----------------------------------------------------------------
    # Properties:
    #----------------------------------------------------------------
    def gethandle(self):
        cfg = self._confighandle
        if(cfg is None):
            self._error="No handle."
            self._debugprint("%s\n" %(self._error))
            return(None)
        return(cfg)

    #----------------------------------------------------------------
    # Initialize:
    #----------------------------------------------------------------
    def __init__(self, configfilename, debug=False, default_section=''):
#        if(configfilename == ""):
#            configfilename = 'config.cfg'

        self._configfilename = configfilename

        self._confighandle = None
        if(default_section is not None):
            if(default_section == ''):
                default_section = "DEFAULT"
        self._defaultsection = default_section

        self._error = ''

#        print('\n' + '  <<<<<< >>>>>>>   Point-CFZ00   default_section = ' + str(default_section) + '\n')     # for making sure 20220905

        self.setdebug(debug)
        if(os.path.exists(configfilename)==False):
#            print('  <<<<<< >>>>>>>   Point-CF100')     # for making sure 20220905
            self._error="Configuration file not found. ('%s')" %(configfilename)
            self._debugprint("%s\n" %(self._error))
            return
        if(os.path.isfile(configfilename)==False):
#            print('  <<<<<< >>>>>>>   Point-CF200')     # for making sure 20220905
            self._error="Configuration file not not file. ('%s')" %(configfilename)
            self._debugprint("%s\n" %(self._error))
            return

        try:
            cfg = ConfigParser(default_section='')
            cfg.read(configfilename)
            self._debugprint("%s\n" %(cfg.defaults()))
            self._confighandle = cfg
        except Exception as e:
#            print('  <<<<<< >>>>>>>   Point-CF300')     # for making sure 20220905
            self._confighandle = None
            self._lastexception = sys.exc_info()
            self._debug = True
            self._error="Error occured in parsing configuration file. ('%s',%s)" %(configfilename,type(e))
            self._debugprint("%s\n" %(self._error))


#### m2701template original
#    def __init__(self, configfilename, debug=False, default_section=''):
#        if(configfilename == ""):
#            configfilename = 'config.cfg'
#        self._confighandle = None
#        self._configfilename = configfilename
#        if(default_section is not None):
#            if(default_section == ''):
#                default_section = "DEFAULT"
#        self._defaultsection = default_section
#        self._error = ''
#        self.setdebug(debug)
#        if(os.path.exists(configfilename)==False):
#            self._error="Configuration file not found. ('%s')" %(configfilename)
#            self._debugprint("%s\n" %(self._error))
#            return
#        if(os.path.isfile(configfilename)==False):
#            self._error="Configuration file not not file. ('%s')" %(configfilename)
#            self._debugprint("%s\n" %(self._error))
#            return
#        try:
#            cfg = ConfigParser(default_section='')
#            cfg.read(configfilename)
#            self._debugprint("%s\n" %(cfg.defaults()))
#            self._confighandle = cfg
#        except Exception as e:
#            self._confighandle = None
#            self._lastexception = sys.exc_info()
#            self._debug = True
#            self._error="Error occured in parsing configuration file. ('%s',%s)" %(configfilename,type(e))
#            self._debugprint("%s\n" %(self._error))

    #----------------------------------------------------------------
    # read: 
    #----------------------------------------------------------------
    def get(self, sectionname, paramname, alternate_value="", paramtype=str):
        paramname = paramname.lower()
        cfg = self.gethandle()
        if(cfg is None):
            return(None)
        p_seclist = []
        p_sec = ''
        add_default=False
        if(self._defaultsection is None):
            add_default=True
        if(isinstance(sectionname, list)):
            for p_sec in sectionname:
                if(p_sec == ''):
                    add_default=True
                elif(p_sec == self._defaultsection):
                    add_default=True
                p_seclist.append(p_sec)
        else:
            p_sec = sectionname
            if(p_sec == ''):
                add_default=True
            elif(p_sec == self._defaultsection):
                add_default=True
            p_seclist.append(p_sec)
        if(add_default==False):
            p_seclist.append(self._defaultsection)
        p_sec = ''
        try:
            for i in range(len(p_seclist)):
                p_sec=p_seclist[i]
                self._debugprint("Search section,param:'%s','%s'.\n" %(p_sec,paramname))
                if(p_sec is None):
                    continue
                if(p_sec == ''):
                    p_sec = self._defaultsection
                if(cfg.has_section(p_sec)==False):
                    self._debugprint("No section:'%s', search skip.\n" %(p_sec))
                    continue
                if(cfg.has_option(p_sec,paramname)==False):
                   self._debugprint("No param:'%s', search skip.\n" %(paramname))
                   continue
                value = None
                if(paramtype == bool):
                     value = cfg[p_sec].getboolean(paramname)
                else:
                    val = cfg[p_sec].get(paramname)
                    if(val is None):
                        continue
                    if((sys.version_info.major<3) and (paramtype == long)):
                        value = int(val)
                    elif(paramtype == int):
                        value = int(val)
                    elif(paramtype == float):
                        value = float(val)
                    else:
                        value=val
                if(value is None):
                    continue
                return(value)
        except ValueError:
            self._lastexception = sys.exc_info()
            self._error="Value error. ('%s','%s',%s,%s)" %(p_sec,paramname,val,paramtype)
            self._debugprint("%s\n" %(self._error))
            return(None)
        except Exception as e:
            self._lastexception = sys.exc_info()
            self._error="Error occured in getting configuration. ('%s','%s',%s)" %(p_sec,paramname,type(e))
            self._debugprint("%s\n" %(self._error))
            return(None)
        self._error="Value not found in configuration. (%s,'%s')" %(p_seclist,paramname)
        self._debugprint("%s\n" %(self._error))
        return(alternate_value)

    def set(self, sectionname, paramname, value, paramtype=str):
        cfg = self.gethandle()
        if(cfg is None):
            return(None)
        try:
            val = value
            if(paramtype == bool):
                if(val==True):
                    val="1"
                else:
                    val="0"
            elif((sys.version_info.major<3) and (paramtype == long)):
                val = int(str(val))
            elif(paramtype == int):
                val = int(str(val))
            elif(paramtype == float):
                val = float(str(val))
            cfg.set(sectionname,paramname,str(val))
        except:
            self._lastexception = sys.exc_info()
            self._error="Error occured in setting configutation. ('%s','%s',%s,%s)" %(sectionname,paramname,value,type(e))
            self._debugprint("%s\n" %(self._error))
            return(False)
        return(True)

    def save(self, configfilename=""):
        cfg = self.gethandle()
        if(cfg is None):
            return(None)
        if(configfilename == ""):
            configfilename = self._configfilename
        try:
            val=cfg.write(open(configfilename,'w'))
        except:
            self._lastexception = sys.exc_info()
            self._error="Error occured in saving to configuration file. ('%s',%s)" %(configfilename,type(e))
            self._debugprint("%s\n" %(self._error))
            return(False)
        return(True)

###############################################################################
# Main: Test
###############################################################################
if __name__ == "__main__":
    import sys
    
    debug=False

    starsNodeName = "term1"
    starsServerHost = '127.0.0.1'
    starsServerPort = 1001
    
    #Create instance
    defaultsection=""
    defaultsection="STARSDEFAULT"
    #defaultsection=None
    cfginstance= PyStarsUtilConfig("timepix.cfg",debug,defaultsection)
    if(cfginstance.gethandle() is None):
        sys.stdout.write(cfginstance.getlasterrortext()+'\n')
        exit(1)
        
    starsNodeName=cfginstance.get("", "StarsNodeName", starsNodeName)
    print("StarsNodeName#"+starsNodeName+"#")
    starsServerHost=cfginstance.get(starsNodeName, "StarsServerHost", starsServerHost)
    print("StarsServerHost#"+starsServerHost+"#")
    starsServerPort=cfginstance.get(starsNodeName, "StarsServerPort", starsServerPort, int)
    print("StarsServerPort#"+str(starsServerPort)+"#")
    rt=cfginstance.get("TEST", "floatvalue", None, float)
    if(rt is None):
        sys.stdout.write(cfginstance.getlasterrortext()+'\n')
        exit(1)
    print("floatvalue#"+str(rt)+"#")
    rt=cfginstance.get("TEST", "intvalue", -999, int)
    if(rt is None):
        sys.stdout.write(cfginstance.getlasterrortext()+'\n')
        exit(1)
    print("intvalue#"+str(rt)+"#")
    rt=cfginstance.get("TEST", "boolvalue", None, bool)
    if(rt is None):
        sys.stdout.write(cfginstance.getlasterrortext()+'\n')
        exit(1)
    print("boolvalue#"+str(rt)+"#")
    rt=cfginstance.set("TEST", "boolvalue", False, bool)
    if(rt is None):
        sys.stdout.write(cfginstance.getlasterrortext()+'\n')
        exit(1)
    rt=cfginstance.set("TEST", "intvalue", 3, int)
    if(rt is None):
        sys.stdout.write(cfginstance.getlasterrortext()+'\n')
        exit(1)
    rt=cfginstance.save()
    if(rt is None):
        sys.stdout.write(cfginstance.getlasterrortext()+'\n')
        exit(1)

