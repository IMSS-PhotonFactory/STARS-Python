#! /usr/bin/python3
"""
  STARS python program Keithley model 2701, 2000 control
    Description: Connect to STARS server and commnicate with the device.
    History:
       0.1     Beta           2022.1.31      Yasuko Nagatani
       0.2     Beta           2022.3.11                         implementation for 7700
"""

# Define: program info
__author__ = 'Yasuko Nagatani' + ' + Yoshiaki Hashimoto'
__version__ = '2.0'
__date__ = '2022-6-2'
__license__ = 'KEK'

#----------------------------------------------------------------
# Class PyStarsDeviceKEITHLEY2701
#----------------------------------------------------------------
from functools import cmp_to_key
from http.client import CONTINUE
from shutil import register_unpack_format
import nportserv
import re
import time
#
import glob
#
import json
#

class PyStarsDeviceKEITHLEY2701(nportserv.nportserv):
    """ Class PyStarsDeviceKEITHLEY2701: Derived from nportserv to control the device of Keithley 2701
    """
    ##################################################################
    # Device control functions
    ##################################################################
    ## Device send
    def device_send(self,cmd):
        print(' point-A00 device-send -> SCPIcommand = ' + cmd +'\n')
        if(self.isconnected()==False):
            return 'Er : Disconnected'      # " " added for IsBusy
        rt=self.send(cmd)
        if(rt==False):
            return 'Er : ' + dc.getlasterrortext()  # " " added for IsBusy
        self._deviceCommandLastExecutedTime = time.time()
        return 'Ok:'

    ## Device act
    def device_act(self,cmd,timeout=''):
        rt=self.device_send(cmd)
        if('Er :' in rt):                   # " " added for IsBusy
            return(rt)
        rt=self.device_receive(timeout)
        return rt

    ## Device receive
    def device_receive(self,timeout=''):
        if(timeout==''):
            timeout=self.gettimeout()
        rt=self.receive(timeout)
        if(rt is None):
            return('Er : '+self.error)      # " " added for IsBusy
        if(rt == ''):
            return('Er : Timeout.')         # " " added for IsBusy
        return rt

    ## Device reset  20220413
    def device_reset(self):
        _cmd = ':*CLS'
        self.device_send(_cmd)
        _cmd = ':SYST:ERR?'
        _rt = self.device_act(_cmd)
        if('No error' not in _rt):
            _rt = '     Er: ' + _rt
            return(_rt)
        _cmd = ':*RST'
        self.device_send(_cmd)
        _cmd = ':SYST:ERR?'
        _rt = self.device_act(_cmd)
        if('No error' not in _rt):
            _rt = '     Er: ' + _rt
            return(_rt)
        _cmd = ':FORM:ELEM READ'
        self.device_send(_cmd)      
        return 'Ok:'

    ## Device stop  20220323
    def device_ch_open(self,chno=' '):
        _cmd = ':INIT:CONT OFF'
        self.device_send(_cmd)
        _cmd = ':ROUT:OPEN:ALL'
        self.device_send(_cmd)
        return 'Ok:'

    ## Device Run  20220413
    def device_ch_close(self,chno=' '):
        if( chno == ' '): 
            rt= 'Er: Bad channel discription'
            return (rt)
        elif(('(' not in chno) or ('),' not in chno)):
            rt = 'Er: Error in describing channel selection'
            return rt
        elif( 'CH' in chno):
            chno = chno.replace('CH','@')
        else:
            rt = 'Er: Bad channel discription'
            return(rt)
        _cmd = ':*CLS'
        self.device_send(_cmd)
        _cmd = ':TRAC:CLE'
        self.device_send(_cmd)
        _cmd = ':INIT:CONT OFF'
        self.device_send(_cmd)
        _cmd = ':ROUT:SCAN:LSEL NONE'
        self.device_send(_cmd)
        _cmd = ':TRIG:COUN 1'
        self.device_send(_cmd)
        _cmd = ':SAMP:COUN 1'
        self.device_send(_cmd)
        _chs = chno.split('),')[0]
        _scn = chno.split('),')[1]
        if(_scn == '1'):    # sensing at single channel input
            if('@FRONT' not in chno): 
                _cmd = ':ROUT:CLOS' + ' ' + str(_chs) +')'
                self.device_send(_cmd)
            _cmd = ':INIT:CONT ON'
            self.device_send(_cmd)
        else:
            if('@FRONT' not in chno):
                _cmd = ':ROUT:SCAN' + ' ' + str(_chs) + ')'
                self.device_send(_cmd)
                _cmd = ':ROUT:SCAN:TSO IMM'
                self.device_send(_cmd)
                _cmd = ':ROUT:SCAN:LSEL INT' 
                self.device_send(_cmd)
        _cmd = ':SAMP:COUN' + ' ' + str(_scn)
        self.device_send(_cmd)
        return 'Ok:'

    ##################################################################
    #       Initialization function by reg.txt
    ##################################################################
    def setstartup(self,cmkey,cmdc):
        _cmddictl = cmkey
        rt ='OK:'


        return(rt)


    ##################################################################
    # Command functions
    ##################################################################
    def is_commanddefined(self,level,starscommand):
        if(level == "CTL"):
            if(starscommand in self._deviceCTLSTARSCommand):
                 return(True)
        elif(level == "CH"):
            if(starscommand in self._deviceCHSTARSCommand):
                return(True)
        return(False)

    def get_commandlist(self,level):
         clist = []
         if(level == "CTL"):
             clist = self._deviceCTLSTARSCommand.keys()
         elif(level == "CH"):
             clist = self._deviceCHSTARSCommand.keys()
         return(clist)

    def get_commandhelp(self,level,starscommand):
         rt='-'
         if(self.is_commanddefined(level,starscommand) == True):
             if(level == "CTL"):
                 rt=self._deviceCTLSTARSCommand[starscommand]['help']
             elif(level == "CH"):
                 rt=self._deviceCHSTARSCommand[starscommand]['help']
         return(rt)

    def get_commandlastexecutedtime(self):
        return(self._deviceCommandLastExecutedTime);

    ##################################################################
    # Device info functions
    ##################################################################
    # imple for 7700 , 20220311
    def get_functionlist(self, targetchannel=''):
        rt = 'Er: Bad command or parameters.' 
        funccmdlist = self._deviceFUNCCommand.keys()
        funclist = self._deviceFUNCList.keys()
 		 
        # Message to starsnode: check if param startswith channelname.
        retlist=list()
        if(targetchannel == ''):
            retlist=funccmdlist
        # Destinatiosn: DMM:
        elif(targetchannel == self._frontchannelname):
            retlist=funccmdlist
        # Destination for rear optional channels.
        else:
            #Limited to function command.
            for k in (funccmdlist):
                for kf in (funclist):
                    if(k.startswith(kf+'.')):
                        retlist.append(k)
                        break
#        rt = ' '.join(retlist)
        _rt = ', '.join(retlist)
        rt = ' [' + _rt + ']'
        return(rt)
    #for 7700 , 20220311
    def get_setfunction(self, targetchannel='', paramname='Function', paramvalue='?',ischeckonly=False):
        rt = 'Er: Bad command or parameters.'
        # Message to starsnode: check if param startswith channelname. 
        if(targetchannel == ''):
            if(paramname in self._deviceFUNCCommand):
                pass
            # Destination: DMM
            elif(paramname.startswith(self._frontchannelname+'.')):
                paramname=paramname.replace(self._frontchannelname+'.','')
            # Destination for rear optional channels. add check.
            elif(paramname.startswith('CH')):                           #20220420
                paramname=paramname.split('.',1)[1]            #20220420
            else:
#                rt = 'Er: Develop Add check at get_setfunction. E00'    #20220420
                return(rt)
        # Destination: DMM:
        elif(targetchannel == self._frontchannelname):
            targetchannel = ''
        # Destination for rear optional channels. add check.
        else:
            rt = 'Er: Develop Add check at get_setfunction. E01'    #20220420
            return(rt)

        # Param check
        if(paramname in self._deviceFUNCCommand):
            command = self._deviceFUNCCommand[paramname]['command']
            # Destination: DMM
            if(targetchannel == ''):
                pass
            # Destination in rear optional channels.
            else:
                if('channeloption' in self._deviceFUNCCommand[paramname]):
                    b = self._deviceFUNCCommand[paramname]['channeloption']
                    if(b==False):
                        return('Er: Bad command or parameters. E02');   #20220420
                if(paramvalue == '?'):
                     targetchannel=' '.targetchannel
                else:
                     targetchannel=','.targetchannel
            # Generate device command
            (rt,errormsg)=eval(self._deviceFUNCCommand[paramname]['checkfunc'])(command, [paramvalue])
            if(rt == ''):
                return(errormsg)
            cmd = rt + targetchannel
            if(ischeckonly):
                return(cmd)
                #return 'Ok:'
            if(paramvalue == '?'):
                rt = self.device_act(cmd)
            else:
                rt = self.device_send(cmd)
            # Edit reply
            rt=eval(self._deviceFUNCCommand[paramname]['postfunc'])(rt, cmd)
        return(rt)

# for (K03) 20220407 ->
    def get_setfunction2(self, targetchannel='', paramname='Function', paramvalue='?',ischeckonly=False):
        rt = 'Er: Bad command or parameters.'
        # Message to starsnode: check if param startswith channelname. 
        if((targetchannel == 'DMM') or ('CH' in targetchannel)):
            if(paramname != ' '):
                if(paramname in self._deviceFUNCCommand):
                    command = self._deviceFUNCCommand[paramname]['command']
                    rt = 'Ok:'
                else:
                    rt = 'Er: Item input error'
            else:
                rt= 'Ok:'
        elif(targetchannel == 'setting'):
            rt = 'Ok:'
            return(rt)
        else:
            rt = 'Er: Sensing Channels setting error'
        # Param check , only the case of (paramname != ' ')
        if(paramname in self._deviceFUNCCommand):
            command = self._deviceFUNCCommand[paramname]['command']
            if('channeloption' in self._deviceFUNCCommand[paramname]):
                b = self._deviceFUNCCommand[paramname]['channeloption']
                if(b==False):
                    return('Er: Bad command or parameters.');
            (rt,errormsg)=eval(self._deviceFUNCCommand[paramname]['checkfunc'])(command, [paramvalue])
            if(rt == ''):
                return(errormsg)
            cmd = rt
            if(ischeckonly):
                return(cmd)
                #return 'Ok:'
            if(paramvalue == '?'):
                rt = self.device_act(cmd)
            else:
                rt = self.device_send(cmd)
            # Edit reply
            rt=eval(self._deviceFUNCCommand[paramname]['postfunc'])(rt, cmd)
        return(rt)

# GetValue  20220323
    def device_Measured_value(self):
        _cmd = ':SYST:CLE'
        self.device_send(_cmd)
        _cmd = ':TRAC:CLE'
        self.device_send(_cmd)
        _cmd = ':INIT:CONT?'
        _concode = self.device_act(_cmd)
        _cmd = ':INIT:CONT OFF'
        self.device_send(_cmd)
        _cmd = ':TRIG:COUN 1'
        self.device_send(_cmd)
        _cmd = ':READ?'
        rt=self.device_act(_cmd,10)
        if(_concode == '1'):
            _cmd = ':INIT:CONT ON'
            self.device_send(_cmd)
        return(rt)
# GetValue 20220323
# SetDataFormatElements
    def set_device_readform(self,param):
        rt = 'Ok:'
        _cmd = ':SYST:CLE'
        self.device_send(_cmd)
        itms = ' ' + param      #for direct setting
        if(param == ''):
            itms = ' READ'
        if(param == 'all'):
            itms = ' READ,UNIT,TST,RNUM,CHAN,LIM'
        if(param == 'unichan'):
            itms = ' READ,UNIT,CHAN'
        if(param == 'value'):
            itms = ' READ'
        _cmd = ':FORM:ELEM' + itms
        self.device_send(_cmd)
        _cmd = ':SYST:ERR?'
        _rt= self.device_act(_cmd)
        if('No error' not in _rt):
            _rt = '     Er: ' + _rt
            return(_rt)
        return('Ok:')
    def get_device_readform(self):
        rt= self.device_act(':FORM:ELEM?')
        return(rt)
    def _retfuncvalue(self,rt,devcommand):
        if(rt.startswith('"') and rt.endswith('"')):
            rt = rt[1:-1]
        return(rt)

    def _checkfunctionlist(self,command,paramvalues):
        rtcommand = command
        paramvalue = paramvalues[0]
        if(paramvalue == '?'):
            rtcommand=rtcommand+paramvalue
        elif(paramvalue in self._deviceFUNCList):
            rtcommand = rtcommand +  ' "' + self._deviceFUNCList[paramvalue] + '"'
        else:
            return('', 'Er: Bad parameter.')
        return(rtcommand,'')

    def _checkrangevalue(self,command,paramvalues):
        rtcommand = command
        paramvalue = paramvalues[0]
        if(paramvalue == '?'):
            rtcommand=rtcommand+paramvalue
        elif((command.startswith(":VOLT:AC")) and (command.endswith(":Range"))):    #20220330 ":" added
            minvalue = 0
            maxvalue = 757.5
            (rtcommand, errormsg) = self._checkfloatrange(command,[paramvalue, minvalue, maxvalue])
            if(rtcommand == ''):
                return(rtcommand, errormsg)
        elif((command.startswith(":VOLT:DC")) and (command.endswith(":Range"))):    #20220330 ":" added
            minvalue = 0
            maxvalue = 1010
            (rtcommand, errormsg) = self._checkfloatrange(command,[paramvalue, minvalue, maxvalue])
            if(rtcommand == ''):
                return(rtcommand, errormsg)
        else:
            # Add Check required: just return now.
            rtcommand = rtcommand + ' ' + paramvalue
        return(rtcommand,'')

    def _checknplccycles(self,command,paramvalues):
        rtcommand = command
        paramvalue = paramvalues[0]
        if(paramvalue == '?'):
            rtcommand=rtcommand+paramvalue
        elif((command.endswith(":NPLC"))):
            minvalue = 0.01
            maxvalue = 10
            (rtcommand, errormsg) = self._checkfloatrange(command,[paramvalue, minvalue, maxvalue])
            if(rtcommand == ''):
                return(rtcommand, errormsg)
        else:
            # Add Check required: just return now.
            rtcommand = rtcommand + ' ' + paramvalue
        return(rtcommand,'')
            
    #TEMPLATE TEKITO
    def _checkfuncvalue(self,command,paramvalues):
        rtcommand = command
        paramvalue = paramvalues[0]
        if(paramvalue == '?'):
            rtcommand=rtcommand+paramvalue
        elif((command.endswith(":AUTO")) or (command.endswith(":STATE"))):
            (rtcommand, errormsg) = self._checkonoff(command, paramvalues)
            if(rtcommand == ''):
                return(rtcommand, errormsg)
            #Check paramvalue is float type and range.
        else:
            rtcommand = rtcommand + ' ' + paramvalue
        return(rtcommand,'')

#
    ##############################################################
    # Check additional card information
    ##############################################################
# GetCardInfo
    def getnumofch(self,slotnmb,funmb):
        _chnmb = 'Er: Bad parameter'
        _cmd = ':SYST:CLE'
        self.device_send(_cmd)
#        if('CARD' in slotnmb):
        _tmpcf = slotnmb + ':' + funmb
        _sln = slotnmb.split('D')[1]
        _cmd = 'SYST:' + _tmpcf + ':STAR?'
        _sch = self.device_act(_cmd)
        _cmd = ':SYST:ERR?'
        _rt = self.device_act(_cmd)
        if('No error' not in _rt):
            _rt = '     Er: ' + _rt
            return(_rt)
        _ck = str(_sch)
        if(_ck == '0'):
            _rt = ':  Not supported'
            return(_rt)
        if( len(_ck) == 1):
            _sch = '0' + _sch
        _cmd = 'SYST:' + _tmpcf + ':END?'
        _ech = self.device_act(_cmd)
        _chnmb = ': CH' + _sln + _sch + ' - ' + _sln + _ech
        return(_chnmb)



    def __init__(self, deviceHost, devicePost, inthandler=None):
        self._deviceInstance = nportserv.nportserv.__init__(self, deviceHost, devicePost)
        #self.setdelimiter('\r\n')
        self.settimeout(2)
        ##################################################################
        # Define command definitions
        ##################################################################
        lc_deviceCTLSTARSCommand = {}
        lc_deviceCHSTARSCommand  = {}

        lc_deviceFUNCLIST  = {'ACI':'CURR:AC','DCI':'CURR:DC','ACV':'VOLT:AC','DCV':'VOLT:DC','2OHM':'RES','4OHM':'FRES','FREQ':'FREQ','TEMP':'TEMP'}

        # Function command list
        lc_deviceFUNCCommand  = {} 
        lc_deviceFUNCCommand['Function']          ={"command":":FUNC", "help":"current function.","checkfunc":"self._checkfunctionlist","postfunc":"self._retfuncvalue", "postwaittime":0, "help":"function."}
        lc_deviceFUNCCommand['TriggerDelay']      ={"channeloption":False ,"command":":TRIG:DEL",        "checkfunc":"self._checkfuncvalue","postfunc":"self._retfuncvalue", "postwaittime":0, "help":"trigger delay."}
        lc_deviceFUNCCommand['DCV.Range.AUTO']    ={"func":"VOLT:DC", "command":":VOLT:DC:RANG:AUTO",   "checkfunc":"self._checkrangevalue","postfunc":"self._retfuncvalue", "postwaittime":0, "help":"range of DC voltage."}
        lc_deviceFUNCCommand['DCV.Range']         ={"func":"VOLT:DC", "command":":VOLT:DC:RANG",        "checkfunc":"self._checkrangevalue","postfunc":"self._retfuncvalue", "postwaittime":0, "help":"range of DC voltage."}
        lc_deviceFUNCCommand['ACV.Range.AUTO']    ={"func":"VOLT:AC", "command":":VOLT:AC:RANG:AUTO",   "checkfunc":"self._checkrangevalue","postfunc":"self._retfuncvalue", "postwaittime":0, "help":"range of AC voltage."}
        lc_deviceFUNCCommand['ACV.Range']         ={"func":"VOLT:AC", "command":":VOLT:AC:RANG",        "checkfunc":"self._checkrangevalue","postfunc":"self._retfuncvalue", "postwaittime":0, "help":"range of AC voltage."}
        lc_deviceFUNCCommand['DCV.NPLCycles']     ={"func":"VOLT:DC", "command":":VOLT:DC:NPLC",         "checkfunc":"self._checknplccycles","postfunc":"self._retfuncvalue", "postwaittime":0, "help":"line cycle integration rate of function 'DCV'."}
        lc_deviceFUNCCommand['DCV.AverageState']  ={"func":"VOLT:DC", "command":":VOLT:DC:AVER:STATE","checkfunc":"self._checkfuncvalue","postfunc":"self._retfuncvalue", "postwaittime":0, "help":"average function enable or not of function 'DCV'."}
        lc_deviceFUNCCommand['DCV.AverageCount']  ={"func":"VOLT:DC", "command":":VOLT:DC:AVER:COUNT","checkfunc":"self._checkfuncvalue","postfunc":"self._retfuncvalue", "postwaittime":0, "help":"average count of function 'DC voltage'."}
        lc_deviceFUNCCommand['TEMP.NPLCycles']    ={"func":"VOLT:DC", "command":":TEMP:NPLC",            "checkfunc":"self._checknplccycles","postfunc":"self._retfuncvalue", "postwaittime":0, "help":"line cycle integration rate of function 'TEMP'."}
        lc_deviceFUNCCommand['TEMP.AverageState'] ={"func":"TEMP", "command":":TEMP:AVER:STAT","checkfunc":"self._checkfuncvalue","postfunc":"self._retfuncvalue", "postwaittime":0, "help":"average function enable or not of function 'TEMP'."}
        lc_deviceFUNCCommand['TEMP.AverageCount'] ={"func":"TEMP", "command":":TEMP:AVER:COUN","checkfunc":"self._checkfuncvalue","postfunc":"self._retfuncvalue", "postwaittime":0, "help":"average count of funcion 'TEMP'."}

        lc_deviceCTLSTARSCommand['getversion']                  ={"help":"Return this program version."}
        lc_deviceCTLSTARSCommand['getversionno']                ={"help":"Return the version number of this program."}
        lc_deviceCTLSTARSCommand['terminate']                   ={"help":"Terminate this program."}
        lc_deviceCTLSTARSCommand['GetCardInfo']                 ={"help":"Return the information of a card inserted in the rear slot."}
        lc_deviceCTLSTARSCommand['IsBusy']                      ={"help":"Return the busy status."}
        lc_deviceCTLSTARSCommand['GetChannelNameList']          ={"help":"Return the list of STARS-channels."}
        lc_deviceCTLSTARSCommand['SetChannelNameList']          ={"help":"set the list of STARS-channels."}
        lc_deviceCTLSTARSCommand['hello']                       ={"help":"Return 'hello nice to meet you.'"}
        lc_deviceCTLSTARSCommand['help']                        ={"help":"Return the list or the explanation of stars command."}
        lc_deviceCTLSTARSCommand['GetFunction']                 ={"help":"Returns the function unit selected or the value used of function."}
        lc_deviceCTLSTARSCommand['SetFunction']                 ={"help":"Set the function unit or the value used of function."}
#        lc_deviceCTLSTARSCommand['CheckFunction']               ={"help":"Debug command Check the value of functions."}
        lc_deviceCTLSTARSCommand['GetValue']                    ={"help":"Returns the measured value in the defined format."}
#20220322 ->
        lc_deviceCTLSTARSCommand['Reset']                       ={"help":"A command to place default setup in DMM."}
        lc_deviceCTLSTARSCommand['Run']                         ={"help":"A command to prepare the measurement environment in DMM."}
        lc_deviceCTLSTARSCommand['Stop']                        ={"help":"A command to open the mesurement channel in DMM."}
        lc_deviceCTLSTARSCommand['SendChangedIsBusy']           ={"help":"A command to enable/disable notification of IsBusy chenge."}
# <- 20220322
#20220419 ->
        lc_deviceCTLSTARSCommand['GetFunctionList']             ={"help":"Return a list of available function."}
        lc_deviceCTLSTARSCommand['SetConfig']                   ={"help":"A command to write function in the current configfile."}
        lc_deviceCTLSTARSCommand['LoadConfig']                  ={"help":"A command to set the function written in the current configfile to DMM "}
        lc_deviceCTLSTARSCommand['GetConfig']                   ={"help":"Return a list of function written in the current configfile."}
        lc_deviceCTLSTARSCommand['GetConfigFiles']              ={"help":"Return a list of configfiles."}
        lc_deviceCTLSTARSCommand['GenerateConfigFile']          ={"help":"A command to generate a configfile."}
        lc_deviceCTLSTARSCommand['SelectConfigFile']            ={"help":"A command to select a configfile for use."}
        lc_deviceCTLSTARSCommand['SetDataFormatElements']       ={"help":"A command for setting a format regarding date from DMM."}
        lc_deviceCTLSTARSCommand['GetDataFormatElements']       ={"help":"A command for return a format regarding date from DMM."}
# <- 20220419

        self._deviceFUNCCommand = lc_deviceFUNCCommand
        self._deviceFUNCList = lc_deviceFUNCLIST

        self._frontchannelname = 'DMM'
        self._deviceCTLSTARSCommand = lc_deviceCTLSTARSCommand
        self._deviceCHSTARSCommand = lc_deviceCHSTARSCommand
        self._deviceBusyFlg = -1
        self._deviceNoed = None
        self._deviceCommandLastExecutedTime = time.time()
        self._inthandler = inthandler

    ##################################################################
    # Internal Functions
    ##################################################################
    def _set_commandlastwaittime(self,t):
        self._deviceCommandLastWaitTime=t;

    ##################################################################
    # Post functions(internal use)
    ##################################################################
    def _postonoff(self,rt,cmd=''):
        if(rt == ''):
            return('Er: No reply')
        elif('Er:' in rt):
            return(rt)
        elif(rt == 'ON'):  rt = '1'
        elif(rt == 'OFF'): rt = '0'
        else:
            pass
        return(rt)

    ##################################################################
    # Check functions(internal use)
    ##################################################################
    def _checkonoff(self,cmd,args):
        rt = ''
        errormsg=''
        val=args[0].upper()
        if(val == '1'):  val = 'ON'
        elif(val == '0'): val = 'OFF'
        if(val == 'ON' or val == 'OFF'):
            rt = cmd + ' ' + val
        else:
            errormsg='Er: Value must be 0 or 1.'
        return(rt,errormsg)

    def _checkfloatrange(self,cmd,args):
        rt = ''
        errormsg=''
        (rt2,errormsg) = self._sub_checkisfloat('',args)
        if(rt2 == ''): return(rt,errormsg)
        val = float(rt2)
        minval = args[1];
        maxval = args[2];
        if((minval<=val) and (val<=maxval)):
            rt = cmd + ' ' + str(val)
        else:
            errormsg = 'Er: Bad parameters. %s range is from %s to %s.' %(str(val), str(minval), str(maxval))
        return(rt,errormsg)

    def _sub_checkisfloat(self,cmd,args):
        val = args[0].upper()
        rt = ''
        errormsg = "Er: Bad parameters. Not float.(%s)" %(val)
        if(val == ''): return(rt,errormsg)
        try:
            n = float(val)
            rt = str(n)
        except ValueError:
            return('',errormsg)
        if(cmd == ''): return(rt,errormsg)
        return(cmd+" "+rt,errormsg)

    def _sub_checkisinteger(self,cmd,args):
        val = args[0].upper()
        rt = ''
        errormsg = "Er: Bad parameters. Not integer.(%s)" %(val)
        if(val == ''): return(rt,errormsg)
        try:
            n = float(val)
            if(n.is_integer()):
                rt = '%0.0lf' %(n)
        except ValueError:
            return('',errormsg)
        if(cmd == ''): return(rt,errormsg)
        return(cmd+" "+rt,errormsg)



#----------------------------------------------------------------
# Program m2701drv.py
#----------------------------------------------------------------
if __name__ == "__main__":
    ##################################################################
    # Import modules
    ##################################################################
    import sys
    import os
    from collections import OrderedDict,defaultdict
    import re
    from singlestars import StarsInterface
    from stars import StarsMessage
    from pystarsutil import pystarsutilconfig, pystarsutilargparser
    import libstreg     #for 7700, 20220311
    ##################################################################
    # Define program parameters
    ##################################################################
    # Initialize: Global parameters
    gb_ScriptName = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    #ScriptPath = os.path.dirname(os.path.abspath(sys.argv[0]))
    gb_Debug = False
    gb_NumberOfChannels = 1  # Set default number of channels.
    # Unused ----> delete gb_ChannelNameSeqList
    #gb_ChannelNameSeqList = []
    # Use parameter: channelnamelist, add gb_DefaultInputSelection default front or rear.
    gb_ChannelNameList = OrderedDict()
    gb_DefaultInputSelection = 1  # 1 for FRONT or 0 for REAR
    gb_StarsInstance = None
    gb_DeviceInstance = None
    gb_RegInstance = None         # Cache instance  for 7700, 20220311
    # Unused ----> delete 4 lines follow as
    #gb_StarsLocalBusyFlg   = 0
    #gb_StarsLastSendBusyFlg = -1
    #gb_DelimiterOfGetValues = ','
    #gb_DelimiterApplyNodeList = {}
    #
    gb_cnltmp = None            #for loading ChannelNameList from selected configfile
    #

    # Define: Appliction default parameters
    starsServerHost = 'localhost'
    starsNodeName   = 'tdkzplus'
    starsServerPort = 6057
    deviceHost = '172.16.0.53' #169.254.9.35
    devicePort = 1394  #8003
    modeofgetsetvalue = 'CC'

# a flg for IsBusy 20220315
    Is_busyflg = 0
    Is_eventsE = 'ON'
# <- 20220315
# configfile 20220414
    gb_userconfigfile = ''
# <- 20220414

    ##################################################################
    # Define local functions: print
    ##################################################################
    # Define: print function
    #from logging import NOTSET,DEBUG,INFO,WARN,WARNING,ERROR,CRITICAL,FATAL
    DEBUG = 10
    INFO = 20
    WARN = 30
    def _outputlog(level, mesg, outstderronly=False):
        global gb_ScriptName
        global gb_Debug
        head = gb_ScriptName
        
        if(gb_Debug==False):
            if(level<=INFO):
                return(1)
        if(outstderronly == True):
            if(mesg[-1:] != '\n'):
               mesg=mesg+'\n'
            sys.stderr.write(mesg)
        else:
            if(mesg[-1:] != '\n'):
               mesg=mesg+'\n'
            sys.stderr.write(mesg)
            #logger.log(level,'['+ head + '] ' + mesg)
        return(1)

    ##################################################################
    # Callback functions:
    ##################################################################
    ## Device socket handler: DETECT
    def device_sockhandler(sock):
        global gb_StarsInstance
        st = gb_StarsInstance
        global gb_DeviceInstance
        dc = gb_DeviceInstance

        destsendstr="Device_detected %s.\n" %(st.nodename)
        _outputlog(WARN, destsendstr)
        rt=st.send('System _Msg '+destsendstr)

        rt = dc.isconnected()
        while rt==True:
            rt = dc.receive(0.01)
            if(rt is None):
                dc.disconnect()
                destsendstr="Device_disconnected %s.\n" %(st.nodename)
                _outputlog(WARN, destsendstr)
                rt=st.send('System _Msg '+destsendstr)
                st.terminateMainloop()
            elif(rt != ''):
                destsendstr="Device_read#%s#\n" %(rt)
                continue
            rt = dc.isconnected()
            break
        return(rt)


    ## STARS interval handler:
    def interval():
        global gb_StarsInstance
        st = gb_StarsInstance
        global gb_DeviceInstance
        dc = gb_DeviceInstance

        # Check device connectection
        if(dc.isconnected() == False):
            destsendstr="Terminate STARS %s. [Device disconnection]\n" %(st.nodename)
            _outputlog(WARN, destsendstr)
            rt=st.send('System _Msg '+destsendstr)
            st.terminateMainloop()
        return

    ## STARS socket handler
    def handler(allmess,sock):
        global gb_ScriptName
        global gb_StarsInstance
        global gb_ChannelNameList
        global gb_ChannelNameSeqList
        global gb_DeviceInstance
        global gb_Debug
# for treat to the IsBusy 20220316
        global Is_busyflg
        global Is_eventsE
# <- 20220316
#
        global gb_RegInstance       #20220415, to add GenerateConfigFile
        global gb_userconfigfile    #20220415, to add GenerateConfigFile 
#
        global gb_cnltmp            #for loading ChannelNameList from selected configfile
        global gb_DefaultInputSelection
#
        dc = gb_DeviceInstance
        st = gb_StarsInstance
        destsendstr='';
        if allmess == '':
            st.terminateMainloop()
            return
        elif(allmess.parameters == ''):
            message = allmess.command
        else:
            message = allmess.command + ' ' + allmess.parameters
        command   = allmess.command
        parameter = allmess.parameters
        parameters = []
        if(allmess.parameters != ''):
            parameters = allmess.parameters.split(" ")
        if(gb_Debug==True):
            print("STARS ALL MESSAGE "+allmess)
            print("STARS FROMNODE "+allmess.nodefrom)
            print("STARS TONODE "+allmess.nodeto)
            print("STARS COMMAND "+allmess.command)
            print("STARS ALL PARAMETER "+allmess.parameters)
        _outputlog(INFO, 'STARS Recv[' +st.nodename + "]:"+allmess)
        topnode = st.nodename
        channelname = ''
        rt = ''

#        print('\n' + ' <><><><><><><><> point-S000 message= ' + str(message) + '\n')        # for making sure

        if(allmess.nodeto.startswith(st.nodename+'.')):
             channelname=allmess.nodeto.replace(st.nodename+'.','')
             _outputlog(DEBUG, "Debug: Channel coming" + channelname)

        elif(allmess.nodeto == st.nodename):
            if(message.startswith('@')):
                return
            elif(message.startswith('_')):
                return
            elif(message == 'getversion'):
                rt = gb_ScriptName + ' Ver.'+__version__+', '+__date__+', '+__author__
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' '+rt
            elif(message == 'getversionno'):
                rt = __version__
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Ver.'+rt
            elif(message == 'hello'):
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Nice to meet you.'
            elif(message == 'help'):
                clist1=sorted(dc.get_commandlist('CTL'))
                clist2=sorted(dc.get_commandlist('CH'))
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + ' '.join(clist1) + ' ' + ' '.join(clist2)
            elif(command == 'help' and len(parameters) == 1):
                rt=parameters[0]
                if(dc.is_commanddefined('CH',parameters[0])==True):
                     rt=dc.get_commandhelp('CH',parameters[0])
                elif(dc.is_commanddefined('CTL',parameters[0])==True):
                     rt=dc.get_commandhelp('CTL',parameters[0])
                else:
                     rt='Er: Command not found'
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + rt
            elif(message == 'terminate'):
                st.terminateMainloop()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Ok:'
            # Return STARS channelname list delimiter , --> GetChannelNameList return style using ,
            elif(message in ['GetChannelNameList']):
                rt=','.join(gb_ChannelNameList.keys())
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
# 20220311 for 7700 ->
            # Suggestion: change command  current listnodes to other. 
            elif(command == 'SetChannelNameList' and len(parameters)==1):
# format of parameter  DMM:0.ch01:101,ch05:121
                rt = 'Ok:'
                _tmpcnl = parameters[0]
                _tmpcnl2 = _tmpcnl.split(',')
                for dsc in _tmpcnl2:
                    if( ':' not in dsc ):
                        rt = 'Er: Bad parameter'
                        break
                    else:
                        continue
                if( 'Er:' not in rt):
                    _tmpcnl3 = '{"' + _tmpcnl + '"}'
                    _tmpcnl4 = _tmpcnl3.replace(',','","')
                    tmpcnl = _tmpcnl4.replace(':','":"')
                    gb_ChannelNameList = json.loads(tmpcnl)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(command == 'GetCardInfo' and len(parameters)==2):               # listnodes -> GetCardInfo
                rt = 'Er: Bad parameter'
                if('CARD' in parameters[0]):
                    rt = dc.getnumofch(parameters[0],parameters[1])
                if('setting' == parameters[0]):
                    if(('CARD' in parameters[1]) or ('CHFRONT' == parameters[1])):
                        rt = getconfig2(parameters[0],parameters[1])
                    elif('Vch2Rch' in parameters[1]):
                        rt = str(gb_ChannelNameList)
                    else:
                        rt = 'Er: Bad parameter'
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(message == 'GetCardInfo'):
                if(gb_DefaultInputSelection == 1):
                    rt = 'CH0'
                else:
                    rt = 'Er: parameter error'
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(message == 'GetFunctionList'):
                rt=dc.get_functionlist('')
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif((command == 'SetConfig') and ('=' in parameter)):
                if('.' in parameter):
                    (k,v)=parameter.split('=',1)
                    (c,kt)=k.split('.',1) 
                    rt = setconfig2(c,kt,v)
                else:
                    rt = 'Er: Parameter error'
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif((command == 'SetConfig') and ('Vch2Rch' in parameter)):        # added on 20220526 
                (c,kt)=parameter.split('.',1)
                v = str(gb_ChannelNameList)
                rt = setconfig2(c,kt,v)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif((command == 'GetConfig') and (parameter != '')):   # alterlation 20220414
                c = parameter
                kt = ' '
                if('.' in parameter):
                    (c,kt)=parameter.split('.',1)
                else:
                    kt = c
                if('setting' == str(c)):
                    c = 'badch'
                rt = getconfig2(c, kt)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif((command == 'LoadConfig') and (parameter != '')):  # alterlation 20220414
                clist=[]
                cl=parameter
                if(',' in parameter):
                    clist = parameter.split(',')
                    for cki in clist:
                        cki0 = cki.split('.')[0]
                        if(('DMM' in cki0) or ('CH' in cki0) or ('ch' in cki0)):
                            rt = 'Ok:'
                        else:
                            rt ='Er: Bad parameter'
                            break
                else:
                    clist=[parameter]
                    rt = 'Ok:'
                if('Ok:' in rt):
                    for param in clist:
                        rt = loadconfig2(cl, param)
                        if('Er:' in rt):
                            break
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
# <- for 7700 20220311
            elif(command == 'SendChangedIsBusy' and len(parameters)==1 ):
                rt = 'Er: Bad parameter'
                if(('ON' in str(parameters[0])) or ('OFF' in str(parameters[0]))):
                    Is_eventsE = parameters[0]
                    rt ='Ok:'
                destsendstr=allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(message == 'IsBusy'):
                _flgb= checkbusyflg()
                destsendstr=allmess.nodeto + '>' + allmess.nodefrom+' @' + message + str(_flgb)
            elif(command == 'Reset'):
                isbusyflgon()
                rt = dc.device_reset()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
                isbusyflgoff()
            elif(command == 'SetFunction' and len(parameters)==2):
                isbusyflgon()
                rt=dc.get_setfunction('',parameters[0], parameters[1]);
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
                isbusyflgoff(rt)
            elif(command == 'SetFunction' and len(parameters)==1):
                rt = 'Er: Bad parameter'
                if('=' in str(parameters)):
                    isbusyflgon()
                    parameter0 = parameters[0].split('=')[0]
                    parameter1 = parameters[0].split('=')[1]
                    if('AUTO' in parameter1):
                        parameter0 = parameter0 + '.AUTO'
                        parameter1 = 'ON' 
                    rt=dc.get_setfunction('',parameter0, parameter1);
                    isbusyflgoff(rt)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt                
            elif(command == 'GetFunction' and len(parameters)==1):
                isbusyflgon()
                rt=dc.get_setfunction('',parameters[0]);
                if('AUTO' in message or 'State' in message):
                    if( rt == '0'):
                        rt = ': OFF'
                    elif(rt == '1'):
                        rt = ': ON'
                    else:
                        rt = 'Er'
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
                isbusyflgoff(rt)
            elif(command == 'CheckFunction' and len(parameters)==2):
                rt=dc.get_setfunction('',parameters[0], parameters[1], ischeckonly=True);
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(command == 'CheckFunction' and len(parameters)==1):
                rt=dc.get_setfunction('',parameters[0],'', ischeckonly=True);
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(command == 'GetValue'):
                isbusyflgon()
                rt=dc.device_Measured_value()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
                isbusyflgoff(rt)
            elif(command == 'Stop'):
                isbusyflgon()
                rt=dc.device_ch_open(parameter)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
                isbusyflgoff()
            elif(command == 'Run'):
                isbusyflgon()
                #Convert STARS channelname to device channel format
                parameter = stars_channel_conversion(parameter,command)
                #print(parameter)
                rt = dc.device_ch_close(parameter)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
                isbusyflgoff()
            elif(command == 'SetDataFormatElements'):
                isbusyflgon()
                rt = dc.set_device_readform(parameter)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
                isbusyflgoff()
            elif(command == 'GetDataFormatElements'):
                isbusyflgon()
                rt = dc.get_device_readform()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
                isbusyflgoff()
            elif(command == 'GenerateConfigFile' and len(parameters)==1):
                _dirnewfilename = './configfiles/' + parameters[0]
                open(_dirnewfilename, 'w')
                gb_RegInstance = libstreg.libstreg(_dirnewfilename)
                rt = 'Ok:'
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(command == 'SelectConfigFile' and len(parameters)==1):
                rt = 'Er: Bad filename'
                _search_file = '\'./configfiles\\\\' + parameters[0] +'\''
                _checkfile = glob.glob('./configfiles/*.txt')
                _rt = str(_checkfile)
                if(_search_file in _rt):
                    _diruseconfigfile = './configfiles/' + parameters[0]
                    gb_RegInstance._filename = _diruseconfigfile
                    rt = loadcache()
                    loadCNL()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(command == 'GetConfigFiles'):
                _tmpname = glob.glob('./configfiles/*.txt')
                _rt = str(_tmpname)
                rt = _rt.replace('./configfiles\\\\','')
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(command == 'SendRawCommand' and parameter != ''):
                isbusyflgon()
                if('?' in parameter):
                    rt=dc.device_act(parameter)
                else:
                    rt=dc.device_send(parameter)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
                isbusyflgoff(rt)
            else:
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Er: Bad command or parameters.'
        else:
            if(message.startswith('@')):
                return
            elif(message.startswith('_')):
                return
            else:
                destsendstr = st.nodename + '>' + allmess.nodefrom+' @' + message + ' Er: Bad node.'
            if(destsendstr != ''):
                _outputlog(INFO,'STARS Send[' +st.nodename + "]:"+destsendstr)
                rt=st.send(destsendstr)
            else:
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Er: Bad command or parameters.'
        if(destsendstr != ''):
            _outputlog(INFO,'STARS Send[' +st.nodename + "]:"+destsendstr)
            rt=st.send(destsendstr)
            if(rt==False):
                st.terminateMainloop()
        return

    def isbusyflgon():
        global Is_busyflg
        global Is_eventsE
        Is_busyflg = 1
        if( Is_eventsE == 'ON'):
            st.send('System _ChangedIsBusy 1')
        return
    def isbusyflgoff(rtc = ' '):
        global Is_busyflg
        global Is_eventsE
        if( 'Er :' in rtc):
            rtc.replace('Er :','Er:')
            return
        Is_busyflg = 0
        if( Is_eventsE == 'ON'):
            st.send('System _ChangedIsBusy 0')
        return
    def checkbusyflg():
        global Is_busyflg
        return(Is_busyflg)

    ##################################################################
    # streg functions: for 7700, 20220311
 	##################################################################
    def loadcache():
        global gb_RegInstance
        reg = gb_RegInstance
        fname = reg.getfilename()
        dname = os.path.dirname(os.path.abspath(fname))
        rt = 'Ok;' 
        if(not os.path.isdir(dname)):
            rt = "Er: Directory not found for the registry file '%s'." %(fname)
        elif(os.path.isdir(fname)):
            rt = "Er: Registry file '%s' is a directory." %(fname)
        elif(os.path.isfile(fname)):
            b = reg.loadcache()
            if(not b):
                rt = 'Er: %s' %(reg.getlasterrortext())
        else:
            pass
        return(rt)

    ##################################################################
    # streg functions: for SelectConfigFile 20220526
 	##################################################################
    def loadCNL():
        global gb_RegInstance
        global gb_ChannelNameList
        reg = gb_RegInstance
        b = reg.loadCNL()
        _chkb = str(b)
        if('False' in _chkb):
            return
        if('OrderedDict' in _chkb):
            _tmpdic1 = b.replace('OrderedDict(','')
            _tmpdic2 = _tmpdic1.replace('[(','{')
            _tmpdic3 = _tmpdic2.replace(')])','}')
            _tmpdic4 = _tmpdic3.replace('\', \'','\':\'')
            _tmpdic5 = _tmpdic4.replace('), (',',')
            _tmpdic6 = _tmpdic5.replace('\'','\"')
        else:
            _tmpdic6 = b.replace('\'','\"')
        gb_ChannelNameList = json.loads(_tmpdic6)
        return
    ##################################################################


    def savecache():
        global gb_RegInstance
        reg = gb_RegInstance
        b = reg.savecache()
        if(b):
            rt='Ok:' 
        else:
            rt = 'Er: %s' %(reg.getlasterrortext())
        return(rt)
 		 
 	#Read cache and set to device.
    def loadconfig(targetchannel,paramname):
        global gb_RegInstance
        global gb_DeviceInstance
        global gb_StarsInstance
        reg = gb_RegInstance
        dc = gb_DeviceInstance
        st = gb_StarsInstance
        nodename = st.nodename
        frontchannelname = dc._frontchannelname
        dicfunclist = dc._deviceFUNCList
        skey = '' 
        pcheckparam = paramname
        pchecktargetch = frontchannelname
        if(targetchannel == ''):
            # Check target
            if(pcheckparam==''):
                # DMM
                skey = frontchannelname + '.' 
            elif(pcheckparam==frontchannelname):
                # DMM
                skey = pcheckparam+'.' 
                pcheckparam = '' 
            elif(pcheckparam.endswith('.') and (pcheckparam[:-1] == frontchannelname)):
                # also DMM
                skey = pcheckparam
                pcheckparam = '' 
            elif(pcheckparam.startswith(frontchannelname+'.')):
                # Check as kind of DMM command
                skey = pcheckparam
                pcheckparam = pcheckparam.replace(frontchannelname+'.','')
            #
            # future add channel of model7700
            # set pchecktargetch = model7700name
            #
            else:
                # Check as kind of DMM command
                skey = pcheckparam
        elif(targetchannel == frontchannelname):
            if(pcheckparam==''):
                # DMM
                skey = frontchannelname + '.' 
            else:
                # Check as kind of DMM command
                skey = pcheckparam
        #
        # future add channel of model7700
        # set pchecktargetch = model7700name
        #
        else:
            rt = "Er: Bad channel '%s'." %(targetchannel)
            return(rt)
 		 
        if(pcheckparam == ''):
            # Already checked
            pass
        elif(pcheckparam in dicfunclist.keys()):
            # DMM with FUNC
            skey = pchecktargetch+'.'+pcheckparam+'.' 
            pcheckparam = '' 
        elif(pcheckparam.endswith('.') and (pcheckparam[:-1] in dicfunclist.keys())):
            # also DMM with FUNC
            skey = pchecktargetch+'.'+pcheckparam
            pcheckparam = '' 
        elif(pchecktargetch == frontchannelname):
            # CHECK AS COMMAND
            rt=getconfig(pchecktargetch,pcheckparam)
            if('Er:' in rt):
                return(rt)
            skey = pchecktargetch+'.'+pcheckparam
            pcheckparam = '' 
        #elif(targetchannel in m7700 channels):
        #    pass
        else:
            rt = 'Er: Bad command or parameters.' 
            return(rt)
        reglist = reg.getcacheregex(nodename, skey)
        if(reglist is None):
            #No list
            return('Ok:')
        for kv in reglist:
            (k,v)=kv.split('=',1)
            rt=dc.get_setfunction('', k, v, ischeckonly=True)
            if('Er:' in rt):
                #_outputlog(WARN, rt)
                rt = "Parameter '%s' skipped by check %s" %(kv,rt)
                _outputlog(WARN, rt )
                continue
            rt = "Updating device '%s' with %s." %(k,v)
            _outputlog(DEBUG, rt)
            rt=dc.get_setfunction('', k, v)
            if('Er:' in rt):
                return(rt)
        return('Ok:')

# for (K03) 20220407 ->
    def loadconfig2(targetchannel,paramname):
        global gb_RegInstance
        global gb_DeviceInstance
        global gb_StarsInstance
        reg = gb_RegInstance
        dc = gb_DeviceInstance
        st = gb_StarsInstance
        nodename = st.nodename
        frontchannelname = dc._frontchannelname
        dicfunclist = dc._deviceFUNCList
        skey = '' 
        pcheckparam = paramname
        pchecktargetch = targetchannel
        skey = pcheckparam
        reglist = reg.getcacheregex(nodename, skey)
        if(reglist is None):
            #No list
            #if no match return error or Ok:? which used in perl version ?
            return(' : no setting information')
        for kv in reglist:
            (k,v)=kv.split('=',1)
            (c,kt)=k.split('.',1)
            if(v == "AUTO"):   # alterlation 20220413
                kt = kt + '.AUTO'
                v = 'ON'
            # Convert STARS channel to device channel format
            c = stars_channel_conversion(c,'Config')
            #print("CONV:"+c)
            rt=dc.get_setfunction2(c, kt, v, ischeckonly=True)
            if('Er:' in rt):
                #_outputlog(WARN, rt)
                rt = "Parameter '%s' skipped by check %s" %(kv,rt)
                _outputlog(WARN, rt )
                continue
            rt = "Updating device '%s' with %s." %(k,v)
            _outputlog(DEBUG, rt)
            rt=dc.get_setfunction2(c, kt, v)
            if('Er:' in rt):
                return(rt)
        return('Ok:')    # alterlation 20220406

    #Set cache only no action to device.
    def setconfig(targetchannel, paramname , value):
        global gb_RegInstance
        global gb_DeviceInstance
        global gb_StarsInstance
        reg = gb_RegInstance
        dc = gb_DeviceInstance
        st = gb_StarsInstance
        nodename = st.nodename
        frontchannelname = dc._frontchannelname
        skey = '' 
        #To starsnode if targetchannel == ''
        #  paramname Ok: if parameter of SetFunction.
        if(targetchannel == ''):
            if(paramname.startswith(frontchannelname+'.')):
            # also DMM
                skey = paramname
            #
            # future add channel of model7700
            #
            else:
            # check as command
                skey = frontchannelname+'.'+paramname
        elif(targetchannel == frontchannelname):
        # check as command
            skey = frontchannelname+'.'+paramname
        else:
            rt = 'Er: Bad command or parameters.' 
            return(rt)
        # Check command
        rt=dc.get_setfunction('', skey, ischeckonly=True);
        if('Er:' in rt):
            rt = 'Er: Bad command or parameters.' 
            return(rt)
        # Check value
        rt=dc.get_setfunction('', skey, ischeckonly=True)
        if('Er:' in rt):
            rt = 'Er: Bad command or parameters.' 
            return(rt)
        # Write config file
        rt = reg.setcache(nodename,skey,value,allownewkey=True)
        if(rt is None):
            rt = 'Er: %s' %(reg.getlasterrortext())
        else:
            rt = savecache()
        return(rt)

    def setconfig2(targetchannel, paramname , value):   # 20220407
        global gb_RegInstance
        global gb_DeviceInstance
        global gb_StarsInstance
        global gb_ChannelNameList           #20220525
        reg = gb_RegInstance
        dc = gb_DeviceInstance
        st = gb_StarsInstance
        cnl = gb_ChannelNameList            #20220525
        nodename = st.nodename
        frontchannelname = dc._frontchannelname
        skey = '' 
        # Judge setting parameter first

        if(targetchannel == 'setting'):           # alterlation 20220422
            skey = targetchannel+'.'+paramname
            rt = reg.setcache(nodename,skey,value,allownewkey=True)
            if(rt is None):
                rt = 'Er: %s' %(reg.getlasterrtext())
            else:
                rt = savecache()
            return(rt)
        else:
            # Convert STARS channel to device channel format
            starschannel = targetchannel
            intch = stars_channel_conversion(targetchannel,'Config')
            if((intch == 'DMM') or ('CH' in intch)):
                cfunc = paramname
            else:
                rt = 'Er: Bad command or parameters.' 
                return(rt)
        # Check command
        # Pass device channel parameter intch
        rt=dc.get_setfunction2(intch, cfunc, ischeckonly=True);
        if('Er:' in rt):
            rt = 'Er: Bad command or parameters.' 
            return(rt)
        # Check value
        # Pass device channel parameter intch
        rt=dc.get_setfunction2(intch, cfunc, ischeckonly=True)
        if('Er:' in rt):
            rt = 'Er: Bad command or parameters.' 
            return(rt)
        # Write config file
        # Use STARS channel for reg.txt
        skey = starschannel+'.'+paramname
        rt = reg.setcache(nodename,skey,value,allownewkey=True)
        if(rt is None):
            rt = 'Er: %s' %(reg.getlasterrortext())
        else:
            rt = savecache()
        return(rt)
# <- (K03)

    #Read cache only no action to device.
    def getconfig(targetchannel, paramname):
        global gb_RegInstance
        global gb_DeviceInstance
        global gb_StarsInstance
        reg = gb_RegInstance
        dc = gb_DeviceInstance
        st = gb_StarsInstance
        nodename = st.nodename
        frontchannelname = dc._frontchannelname
        skey = '' 
        #To starsnode if targetchannel == ''
        #  paramname Ok: if parameter of SetFunction.
        if(targetchannel == ''):
            if(paramname.startswith(frontchannelname+'.')):
                # also DMM
                skey = paramname
                #
                # future add channel of model7700
                #
            else:
                # check as command
                skey = frontchannelname+'.'+paramname
        elif(targetchannel == frontchannelname):
            # check as command
            skey = frontchannelname+'.'+paramname
        else:
            rt = 'Er: Bad command or parameters.' 
            return(rt)
        # Check command
        rt=dc.get_setfunction('', skey, ischeckonly=True);
        if('Er:' in rt):
            rt = 'Er: Bad command or parameters.' 
            return(rt)
        # Read config file
        rt = "Er: Parameter '%s' is correct but no configuration. A stored value on device will be used." %(paramname)
        rt = reg.getcache(nodename,skey,rt)
        if(rt is None):
            rt = 'Er: %s' %(reg.getlasterrortext())
        return(rt)
    def getconfig2(targetchannel, paramname):   # 20220414
        global gb_RegInstance
        global gb_DeviceInstance
        global gb_StarsInstance
        reg = gb_RegInstance
        dc = gb_DeviceInstance
        st = gb_StarsInstance
        nodename = st.nodename
        frontchannelname = dc._frontchannelname
        skey = '' 
        # Judge setting parameter first

        if('setting' == targetchannel):     # alterlation 20220422
            if('CARD' in paramname):
                skey = targetchannel + '.' + paramname
                reglist = reg.getcacheregex(nodename, skey)
                rt = str(reglist)
                return(rt)
            else:
                rt = 'Er: Bad parameters'
                return(rt)

        # Convert STARS channel to device channel format
        starschannel = targetchannel
        intch = stars_channel_conversion(targetchannel,'Config')
        if((intch == 'DMM') or ('CH' in intch)):
            cfunc = paramname
            skey = intch + '.' + paramname
        else:
            rt = 'Er: Bad parameters.' 
            return(rt)

        #Change the if judge order
        if(targetchannel == paramname):
            skey = targetchannel
            reglist = reg.getcacheregex(nodename, skey)
            rt = str(reglist)
            return(rt)

        # Check command
        # Pass device channel parameter intch
        rt=dc.get_setfunction2(intch, cfunc, ischeckonly=True);
        if('Er:' in rt):
#            rt = 'Er: Bad command or parameters.' 
            return(rt)
        # Read config file
        rt = "Er: Parameter '%s' is correct but no configuration. A stored value on device will be used." %(paramname)
        # Pass STARS channel name for reg.txt
        rt = reg.getcache(nodename,skey,rt)
        if(rt is None):
            rt = 'Er: %s' %(reg.getlasterrortext())
        return(rt)


    ##################################################################
    # STARS channel conversion: for 7700, 20220510
    ##################################################################
    def stars_channel_conversion(parameter,retformat):
        global gb_ChannelNameList;
        global gb_DefaultInputSelection
        global gb_DeviceInstance
        dc = gb_DeviceInstance
        p = parameter.strip()

        #Ret Run parameter

        if(retformat=='Run'):
            if p == '':
                if gb_DefaultInputSelection == 0:
#                    params = list(gb_ChannelNameList.keys())[1:]   # comment out 20220601
                    params_tmp = list(gb_ChannelNameList.values())[1:]
                    parameter = "(CH%s),%d" % (','.join(params_tmp),len(params_tmp))                #  params -> params_tmp
                elif gb_DefaultInputSelection == 1:
                    parameter = "(CHFRONT),1"
            elif ',' in p:
                if all(x in list(gb_ChannelNameList.keys())[1:] for x in p.split(',')):
                    params = [gb_ChannelNameList[x] for x in p.split(',')]
                    parameter = "(CH%s),%d" % (','.join(params),len(params))
            else:
                if p in list(gb_ChannelNameList.keys())[1:]:
                    parameter = "(CH%s),1" % (gb_ChannelNameList[p])
                elif p == list(gb_ChannelNameList.keys())[0]:
                    parameter = "(CHFRONT),1"
        else:
            #Expected DMM
            dmm = dc._frontchannelname
            if p == '':
                pass
            elif ',' in p:
                if all(x in list(gb_ChannelNameList.keys())[0:] for x in p.split(',')):
                    params = [gb_ChannelNameList[x] for x in p.split(',')]
                    params = [dmm if x == '0' else 'CH'+x for x in params]
                    print(params)
                    parameter = "%s" % (','.join(params))
            else:
                if p in list(gb_ChannelNameList.keys())[1:]:
                    parameter = "CH%s" % (gb_ChannelNameList[p])
                elif p == list(gb_ChannelNameList.keys())[0]:
                    parameter = dmm
        return(parameter)

 	##################################################################    
    # Define program arguments
    ##################################################################
    lc_FrontChannelName='DMM'    # Default front name
    lc_RearChannelNameList=None
    lc_DefaultInputSelection=gb_DefaultInputSelection
    lc_RegFileName = None       # added on 20220607

    optIO=pystarsutilargparser.PyStarsUtilArgParser(numberOfDeviceServer=1)
    parser=optIO.generate_baseparser(prog=gb_ScriptName,version=__version__)
    parser.add_argument('--rearchannelnamelist',  dest="RearChannelNameList",   help='List of channel identifier of REAR inputs setup on device.')
    parser.add_argument('--defaultinputselection', type=int, dest="DefaultInputSelection", help='Choose default input selection, 1 for FRONT, 0 for REAR channels. (Default:'+str(lc_DefaultInputSelection)+')')
    ##################################################################
    # Parse program arguments
    ##################################################################
    args=parser.parse_args()
    gb_Debug=args.debug
    if(gb_Debug==True):
        sys.stdout.write(str(args)+'\n')
    # Fix StarsNodename
    starsNodeName = optIO.get(args.StarsNodeName,starsNodeName)
    # Read configfile if detected
    configfilename = None
#    if(os.path.isfile('./config.cfg')):
#        configfilename = './config.cfg'
    configFileName = optIO.get(args.Config,configfilename)
    #Sorry template missing whether configfile ./config.cfg exists.
    if(configFileName is not None): # re-alterlation 20220510
    #if(configFileName == ' '):     # alterlation 20220411 '' -> ' '
        cfgIO= pystarsutilconfig.PyStarsUtilConfig(configFileName,gb_Debug)
        if(cfgIO.gethandle() is None):
            sys.stdout.write(cfgIO.getlasterrortext()+'\n')
            exit(1)
        if(not optIO.has_value(args.StarsNodeName)):
            starsNodeName = cfgIO.get('', 'StarsNodeName', starsNodeName)
        if(gb_Debug == False):
            gb_Debug        = cfgIO.get(starsNodeName, 'Debug'          , gb_Debug, bool)
        starsServerHost = cfgIO.get(starsNodeName, 'StarsServerHost', starsServerHost)
        starsServerPort = cfgIO.get(starsNodeName, 'StarsServerPort', starsServerPort, int)
        deviceHost      = cfgIO.get(starsNodeName, 'DeviceHost'     , deviceHost)
        devicePort      = cfgIO.get(starsNodeName, 'DevicePort'     , devicePort, int)
        lc_RearChannelNameList  = cfgIO.get(starsNodeName, 'RearChannelNameList', lc_RearChannelNameList)
        lc_DefaultInputSelection = cfgIO.get(starsNodeName, 'DefaultInputSelection', lc_DefaultInputSelection, int)
        lc_RegFileName = cfgIO.get(starsNodeName, 'RegFileName', lc_RegFileName)        # added on 20220607

    # Fix optional parameters
    starsServerHost = optIO.get(args.StarsServerHost,starsServerHost)
    starsServerPort = optIO.get(args.StarsServerPort,starsServerPort)
    deviceHost      = optIO.get(args.DeviceHost,deviceHost)
    devicePort      = optIO.get(args.DevicePort,devicePort)
    lc_RearChannelNameList   = optIO.get(args.RearChannelNameList,  lc_RearChannelNameList)
    lc_DefaultInputSelection = optIO.get(args.DefaultInputSelection, lc_DefaultInputSelection)

    # SET FrontChannelName(=DMM)  to global channel list, using dummy channel no 0.
    gb_ChannelNameList[lc_FrontChannelName] = str(0)

    # Check RearChannelNameList then SET to global channel list with channel no.
    if(lc_RearChannelNameList is None):
        lc_RearChannelNameList=[]
    else:
        lc_RearChannelNameList=lc_RearChannelNameList.split(',')
    lc_chname = ''
    lc_targetno = 101 #Model 7700 begin channel no with 101
    p = '[12]\d\d'


    for i in range(len(lc_RearChannelNameList)):
        buf = lc_RearChannelNameList[i]
        if(':' in buf):
            (lc_chname,lnostr) = buf.split(':',1)
            if(lnostr.strip()==''):
                pass
            elif re.fullmatch(p, lnostr.strip()):
                lc_targetno = int(lnostr.strip())
            else:
                sys.stdout.write("Er: Invalid channel no '%s' assigned at rear channel name parameter '%s'.\n", lnostr, buf)
                exit(1)
        else:
            lc_chname = buf
        lc_chname = lc_chname.strip()
        if(lc_chname == ''):
            sys.stdout.write("Er: Rear channel name is empty of parameter '%s'.\n" %(buf))
            exit(1)
        elif any(x in lc_chname for x in ['(', ')',',',' ',':']):
            sys.stdout.write("Er: Invalid characters [,() :] involved in rear channel name parameter '%s'.\n", lc_chname)
            exit(1)
        elif lc_chname in gb_ChannelNameList.keys():
            sys.stdout.write("Er: Duplicate channel name '%s' detected.\n",lc_chname)
            exit(1)
        elif(str(lc_targetno) in gb_ChannelNameList.values()):
            sys.stdout.write("Er: Duplicate channel no '%s' assgined to channel name parameter '%s'.\n", str(lc_targetno), lc_chname)
            exit(1)
        gb_ChannelNameList[lc_chname] = str(lc_targetno)
        lc_targetno = lc_targetno + 1 # Increment lc_targetno for Next


    # Check default channel selection then set globals
    if(str(lc_DefaultInputSelection) in ['0']):
        if(len(gb_ChannelNameList)<=1):
            sys.stdout.write("Er: Default selection is 'REAR' however rear channel list is empty.\n")
            exit(1)
    elif(str(lc_DefaultInputSelection) in ['1']):
        pass
    else:
        sys.stdout.write("Er: Value should be 0(=REAR) or 1(=FRONT) for parameter 'DefaultInputChannel'.\n")
        exit(1)
    gb_DefaultInputSelection = lc_DefaultInputSelection

    if(gb_Debug==True):
        sys.stdout.write("starsNodeName#"+str(starsNodeName)+"#"+'\n')
        sys.stdout.write("starsServerHost#"+str(starsServerHost)+"#"+'\n')
        sys.stdout.write("starsServerPort#"+str(starsServerPort)+"#"+'\n')
        sys.stdout.write("deviceHost#"+str(deviceHost)+"#"+'\n')
        sys.stdout.write("devicePort#"+str(devicePort)+"#"+'\n')
        for i in range(1,len(gb_ChannelNameList.keys())):
            k=list(gb_ChannelNameList.keys())[i]
            v=gb_ChannelNameList[k]
            sys.stdout.write("RearChannelNameList#"+k+' for CH'+v+"#"+'\n')

    ##################################################################
    # Main process: Start
    ##################################################################
    # for 7700, 20220311 ->
    # regfile and configfile are different
    regFileName = lc_RegFileName                # added on 20220607
    if(regFileName is None):                    # corrected on 20220607
        regFileName = './reg.txt'               # corrected on 20220607
    gb_RegInstance = libstreg.libstreg(regFileName)
    #gb_RegInstance.setdebug(True)
    rt = loadcache()
    if('Er:' in rt):
        if(lc_RegFileName is not None):         # added on 20220607
            sys.stdout.write(rt+'\n')           # corrected on 20220607
            exit(1)                             # corrected on 20220607
    # <- for 7700, 20220311
    #Create device instance with devserver:devport 
    dc=PyStarsDeviceKEITHLEY2701(deviceHost, devicePort)
    gb_DeviceInstance=dc
    #print(dc._deviceFUNCCommand)
    #exit(1)

    #Set properties for device instance
    dc.setdebug(gb_Debug)
    if(gb_Debug == True):
        gb_DeviceInstance.printinfo()

    #Connect to device
    rt = dc.connect()
    if(rt==False):
        sys.stdout.write(dc.getlasterrortext()+'\n')
        exit(1)

    #Create Stars instance
    st  = StarsInterface(starsNodeName, starsServerHost, '', starsServerPort)
    gb_StarsInstance = st

    #Set properties for Stars instance
    st.setdebug(gb_Debug)

    rt = st.setdefaultreceivetimeout(3)
    if(rt==False):
        sys.stdout.write(st.getlasterrortext()+'\n')
        exit(1)

    #Connect to Stars
    rt=st.connect()
    if(rt==False):
        sys.stdout.write(st.error+'\n')
        exit(1)

    #Send device info
    time.sleep(3)

    #Add callback handler
    rt=st.addcallback(handler)
    if(rt==False):
        sys.stdout.write(st.getlasterrortext()+'\n')
        exit(1)
    rt=st.addcallback(device_sockhandler,dc.gethandle(),'DETECT')
    if(rt==False):
        sys.stdout.write(st.getlasterrortext()+'\n')
        exit(1)

    #Start Mainloop()
#for check into mainloop
#    print('           >>>>>  point-F020  : mainloop started' + '\n')                   #for making sure 20220520
    rt=st.Mainloop(interval,0.01)
    if(rt==False):
        sys.stdout.write(st.error+'\n')
        exit(1)

    #Device close
    #*** sleep for callback terminate wait
    time.sleep(1)
    dc.disconnect()
    st.removecallback()
    st.disconnect()
    exit(0)
