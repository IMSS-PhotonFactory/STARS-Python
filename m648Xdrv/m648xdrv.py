#! /usr/bin/python3
"""
  STARS python program Keithley model 6485 control
    Description: Connect to STARS server and commnicate with the device.
    History:
       0.1     Beta           2022.5.06      based on m2701drv
       1.*     Temporary release version
       2.*     comonization of model6485 and model6487
       2.11    common version of model6485 and model6487 ; correct replay commennt for GetValue'
       2.12    mistake correction
"""

# Define: program info
__author__ = 'Yasuko Nagatani' + ' + Yoshiaki Hashimoto'
__version__ = '2.12  ; mistake correction'
__date__ = '2022-8-10'
__license__ = 'KEK'

#----------------------------------------------------------------
# Class PyStarsDeviceKEITHLEY6485
#----------------------------------------------------------------
from shutil import register_unpack_format
import nportserv
import re
import time
#
import glob
#
import math

class PyStarsDeviceKEITHLEY6485(nportserv.nportserv):
    """ Class PyStarsDeviceKEITHLEY6485: Derived from nportserv to control the device of Keithley 6485
    """
    ##################################################################
    # Device control functions
    ##################################################################
    ## Device send
    def device_send(self,cmd):
        print(' >>>>>>                            point-S999 device-send SCPIcommand --> ' + cmd +'\n')  # for making sure
        _cmd = cmd + '\r\n'     # for gpib or RS232C controll
#        _cmd = cmd             # for use dummy
        if(self.isconnected()==False):
            return 'Er: Disconnected'
        rt=self.send(_cmd)
        if(rt==False):
            return 'Er: ' + dc.getlasterrortext()
        self._deviceCommandLastExecutedTime = time.time()
        return 'Ok:'

    ## Device act
    def device_act(self,cmd,timeout=''):
        rt=self.device_send(cmd)
        if('Er:' in rt):
            return(rt)
        rt=self.device_receive(timeout)
        return rt

    ## Device receive
    def device_receive(self,timeout=''):

        if(timeout==''):
            timeout=self.gettimeout()
        rt=self.receive(timeout)
        if(rt is None):
            return('Er: '+self.error)
        if(rt == ''):
            return('Er: Timeout.')
        rt = rt.replace('\r','')
        rt = rt.replace('\n','')
        return rt

##################################################################
# Preprocessing/Precheck routine
##################################################################
# dev2Idle / SetTriggerArmCount / SetTriggerCount
    def dev2Idle(self,cfg=0):
        _contf = cfg
        self.device_send(':SYST:REMOTE')
        _rt = self.donecheck()
        if('Ng' in _rt):
            return(_rt)
        if(_contf == 0):
            self.device_send(':SYST:LOCAL')
            _rt = self.donecheck()
            if( 'Ng' in _rt ):
                return(rt)
            self.device_send(':SYST:KEY 28')
            _rt = self.donecheck()
            if( 'Ng' in _rt ):
                return(rt)
            self.device_send(':SYST:KEY 32')
            _rt = self.donecheck()
            if( 'Ng' in _rt ):
                return(rt)
            self.device_send(':SYST:REMOTE')
            _rt = self.donecheck()
            if( 'Ng' in _rt ):
                return(rt)
        self.device_send(':ABORT')          # Reset trigger system (goes to idle state)
        _rt = self.donecheck()
        if('Ng' in _rt):
            return(_rt)
        self.device_send(':TRIG:CLE')
        _rt = self.donecheck()
        if('Ng' in _rt):
            return(_rt)
        if(_contf == 0):
            self.device_send(':TRAC:CLE')
            _rt = self.donecheck()
            if('Ng' in _rt):
                return(_rt)
        self.device_send(':*CLS')
        _rt = self.donecheck()
        if('Ng' in _rt):
            return(_rt)
        return ('Ok:')
# Golocal
    def Golocal(self):
        self.device_send(':SYST:KEY 32')
        _rt = self.donecheck()
        if('Ng' in _rt):
            return(_rt)        
        self.device_send(':SYST:KEY 1')
        _rt = self.donecheck()
        if('Ng' in _rt):
            return(_rt)
        self.device_send(':SYST:KEY 1')
        _rt = self.donecheck()
        if('Ng' in _rt):
            return(_rt)
        return('Ok:')

###############################################
### For obtaining correction data
##
    def sampleINIT(self):
        _cmd = ':TRIG:COUN?'
        _c_triggercount = self.device_act(_cmd)
        _cmd = ':ARM:COUN?'
        _c_armcount = self.device_act(_cmd)
        _cmd = ':TRIG:COUN 1'
        self.device_send(_cmd)
        _cmd = ':ARM:COUN 1'
        self.device_send(_cmd)
        _cmd = ':INIT'
        self.device_send(_cmd)
        time.sleep(2)
        _cmd = ':ARM:COUN ' + _c_armcount
        self.device_send(_cmd)
        _cmd = ':TRIG:COUN ' + _c_triggercount
        self.device_send(_cmd)
        return
# 

##########################################################################################
# Postprocessing rouyine
##########################################################################################
    def syncTRIGArmSource(self,autoflg='off',devt='6485'):
        _dtp = devt
        rt = 'STAT_OK:'
        _rt = self.device_act(':ARM:SOUR?')
        if('Er:' in _rt):
            _rt = 'STAT_ERR'
            return(_rt)
        _ckr = self._checkTRIGArmSource(_rt,None,_dtp)
        if('STAT_ERR' in _ckr):
            if(autoflg == 'on' ):
                self.device_send(':ARM:SOUR IMM')
                rt = 'STAT_OK'
            else:
                rt = _ckr
        return(rt)

    def syncTRIGArmCount(self,autoflg='off',devt='6485'):
        _dtp = devt
        rt = 'STAT_OK'
        _rt = self.device_act(':ARM:COUN?')
        if(_rt == ''):
            _rt = 'STAT_ERR'
            return(_rt)
        _ckr = self._checkTRIGArmCount(_rt,None,_dtp)
        if('STAT_ERR' in _ckr):
            if(autoflg == 'on'):
                self.device_send(':ARM:COUN 1')
            else:
                rt = _ckr
        return(rt)

    def syncTRIGSource(self,autoflg='off',devt='6485'):
        _dtp = devt
        rt = 'STAT_OK'
        _rt = self.device_act(':TRIG:SOUR?')
        if(_rt == ''):
            _rt = 'STAT_ERR'
            return(_rt)
        _ckr = self._checkTRIGSource(_rt,None,_dtp)
        if('STAT_ERR' in _ckr):
            if(autoflg == 'on'):
                self.device_send(':TRIG:SOUR IMM')
            else:
                rt = _ckr
        return(rt)

    def syncTRIGCount(self,autoflg='off',devt='6485'):
        _dtp = devt
        rt = 'STAT_OK:'
        _rt = self.device_act(':TRIG:COUN?')
        if(_rt == ''):
            _rt = 'STAT_ERR'
            return(_rt)
        _ckr = self._checkTRIGCount(_rt,None,_dtp)
        if('STAT_ERR' in _ckr):
            if(autoflg == 'on'):
                self.device_send(':TRIG:COUN 1')
            else:
                rt = _ckr
        return(rt)

    def syncLineFrequency(self):
        rt = self.device_act(':SYST:LFR?')
        if(rt == ''):
            return('STAT_ERR')
        else:
            return(rt)

##########################################################################################
# check functions
##########################################################################################

    def donecheck(self):
        self.device_send(':*OPC')
        rt = 'Ng: processing time over'
        _rt = self.device_act(':*OPC?')
        if( _rt == '1'):
            rt = 'Ok:'
        return(rt)
    
    def statuscheck(self):
        rt = self.device_act(':SYST:ERR:ALL?')
        if( 'No error' in rt):
            rt = 'Ok:'
        return(rt)


    def TriggerEnvCheck(self,autoflg,devt):
        _checktriggerflag = 'NG'
        _rt = self.syncTRIGArmSource(autoflg,devt)
        if('STAT_ERR' in _rt):
            return(_checktriggerflag)
        _rt = self.syncTRIGArmCount(autoflg,devt)
        if('STAT_ERR' in _rt):
            return(_checktriggerflag)
        _rt = self.syncTRIGSource(autoflg,devt)
        if('STAT_ERR' in _rt):
            return(_checktriggerflag)
        _rt = self.syncTRIGCount(autoflg,devt)
        if('STAT_ERR' in _rt):
            return(_checktriggerflag)
        _checktriggerflag = 'OK'
        return(_checktriggerflag) 
        


################################################################################
#
################################################################################

    def convEtoN(self,val):
        _ckval = str(val)
        _typcka = _ckval.isalpha()
        rt = 'STAT_ERR: Invalid character.'
        if( _typcka == True):
            if( val == 'DEF' or val == 'MIN' or val == 'MAX' ):
                _rt = 'Ok: Range specification ( DEFault, MINimum or MAXimun )'
            else:
                _rt = 'STAT_ERR: Invalid character.'
        else:
            try:
                _rt = float(val)
            except ValueError:
                return(rt)
        return(_rt)
#
    def _checkONOFF(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        if( _val == '0' or _val == '1' or _val == 'OFF' or _val == 'ON'):
            rt = 'STAT_OK'
        else:
            rt = 'STAT_ERR: Bad Parameter. Specify 1|ON to enable the operation, or 0|OFF to disable the operation.'
        return(rt)

    def _checkRangeMinMax2(self,val1,val2,val3):
        _compv = 9.99999*10**20
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        _tval = self.convEtoN(_val)
        _cktf = isinstance(_tval,float)
        rt = 'STAT_ERR: Specify the number: -9.99999e20 to 9.99999e20 or Specyfy the Range: DEFault, MINimun or MAXimum.'
        if( _cktf == False):
            if( 'Ok:' in _tval):
                rt = 'STAT_OK'
        elif( _cktf == True):
            if(abs(_tval) <= _compv):
                rt = 'STAT_OK'
        return(rt)

    def _checkMathFormat(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        if(_val == 'MXB' or _val == 'REC' or _val == 'LOG10'):
            rt = 'STAT_OK'
        else:
            rt = 'STAT_ERR: Specyfy MXB, REC or LOG10'
        return(rt)

    def _checkKMathMBFactor(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        _ckr = self._checkRangeMinMax2(_val,_ch,_dtp)
        return(_ckr)

    def _checkKMathUnits(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specyfy "A"-"Z","\[","\]" or "\\"'
        if('\"' in _val):
            _ckcara = _val.replace('\"','')
            _res = re.match("[A-Z]",str(_ckcara))
            if( (_res != None) or (str(_ckcara) == '[') or (str(_ckcara) == ']') or (str(_ckcara) == '\\')):
                rt = 'STAT_OK'
        return(rt)

    def _checkPreGetValueKMath(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STATA_ERR: Ng: Set MathEnable ON before.'
        _rt = self.device_act(':CALC:STAT?')
        if( _rt == 'ON' or _rt == '1'):
            _ckr = self._checkPreGetValue()
            if(_ckr == 'STAT_OK'):
                rt = _ckr
        return(rt)

    def _checkPreGetValue(self):
        rt = 'STAT_OK'
        _rt = self.device_act(':TRAC:POIN:ACT?')
        _ckdtf = _rt.isdecimal()
        if(_ckdtf == True):
            if( int(_rt) <= 0):
                rt = 'STAT_ERR: Ng: Nodata'
        return(rt)

    def _checkCalc2InputPath(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        if( _val == 'CALC' or _val == 'CALC1' or _val == 'SENS' or _val == 'SENS1'):
            rt = 'STAT_OK'
        else:
            rt = 'STAT_ERR: Specify CALC(ulate[1]) or SENS(e[1]).'
        return(rt)

    def _checkCalc2Range(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        _ckr = self._checkRangeMinMax2(_val,_ch)
        return(_ckr)

    def _checkPreGetValueREL(self,val1,val2,val3):
        rt = 'STAT_ERR'
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        _rt = self.device_act(':CALC2:NULL:STAT?')
        if( _rt == 'ON' or _rt == '1'):
            _ckr = self._checkPreGetValue()
            if( _ckr == 'STAT_OK'):
                rt = _ckr
        else:
            rt = 'STAT_ERR: Ng: Set RELEnable ON before.'
        return(rt)

    def _checkTRCSTATICTYPE(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        if( _val == 'MIN' or _val == 'MAX' or _val == 'MEAN' or _val == 'SDEV' or _val == 'PKPK'):
            rt = 'STAt_Ok'
        else:
            rt = 'STAT_ERR: Specify MEAN , SDEV(iation) , MAX(imum) , MIN(imum) or PKPK.'
        return(rt)

    def _checkDisplayDigits(self,val1,val2,val3):
        _val = val1.upper()
        _ch =val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the Number: 4 to 7 or Specyfy either DEF(ault), MIN(imun) or MAX(imum).'
        _tval = self.convEtoN(_val)
        _cktf = isinstance(_tval,float)
        if( _cktf == False):
            if( 'Ok:' in _tval):
                rt = 'STAT_OK'
        else:
            try:
                _ckdti = int(_val)
            except ValueError:
                return(rt)
            if( ( int(_ckdti) >= 4) and ( int(_ckdti) <= 7) ):
                rt = 'STAT_OK'
        return(rt)

    def _checkDATAFORMAT(self,val1,val2,val3):
        _val = val1.upper()
        _ch =val2
        _dtp = val3
        if( _val == 'ASC' or _val == 'REAL' or _val == '32' or _val == 'SRE'):
            rt = 'STAT_OK'
        else:
            rt = 'STAT_ERR: Specify ASC(ii) or REAL or 32 or SRE(al).'
        return(rt)

    def _checkDATAELEMENTS(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        _elements = _val.split(',')
        rt = 'STAT_OK'
        if(_dtp == '6485'):
            for i in _elements:
                if( i == 'READ' or i == 'UNIT' or i == 'TIME' or i == 'STAT'):
                    continue
                else:
                    rt = 'STAT_ERR: Specify among READ(ing),UNIT(s),TIME and STAT(us).'
                    break
        elif(_dtp == '6487'):
            if(_val == 'DEF' or _val == 'ALL'):
                return(rt)
            for i in _elements:
                if( i == 'READ' or i == 'UNIT' or i == 'TIME' or i == 'STAT' or i == 'VSO' ):
                    continue
                else:
                    rt = 'STAT_ERR: Specify among READ(ing),UNIT(s),TIME,STAT(us),VSOurce or either DEF(ault) or ALL.'
                    break
        else:
            rt = 'STAT_ERR: It may be an unsupported model.'
        return(rt)


    def _checkLineFrequency(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        if(_val == '50' or _val == '60'):
            rt = 'STAT_OK'
        else:
            rt = 'STAT_ERR: Specify the number: 50 or 60.'
        return(rt)

    def _checkAmpNPLC(self,val1,val2,val3):
        _val = val1
        _ch = val2
        _dtp = val3
        _ckfg = ''
        _lfq = self.syncLineFrequency()
        if(_lfq == 'STAT_ERR'):
            rt = 'STAT_ERR: not available.'
            return(rt)
        rt = 'STAT_ERR: Specify the number: 0.01 to 60.0 (LineFrequency:60Hz) or 50.0 (LineFrequency:50Hz), or Specyfy either DEF(ault), MIN(imun) or MAX(imum).'
        _tval = self.convEtoN(_val)
        _cktf = isinstance(_tval,float)
        if( _cktf == True):
            if( _tval >= 0.01 and _tval <= float(_lfq)):
                rt = 'STAT_OK'
        elif( 'Ok:' in _tval):
            rt = 'STAT_OK'
        return(rt)

    def _checkAmpRANGE(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the number: 2.1E-9(amps) to 2.1E-2(amps) or specyfy either DEF(ault), MIN(imun) or MAX(imum).'
        _tval = self.convEtoN(_val)
        _cktf = isinstance(_tval,float)
        if( _cktf == True):
            if( _tval>=2.1*10**(-9) and _tval <= 2.1*10**(-2)):
                rt = 'STAT_OK'
        elif( 'Ok:' in _tval):
            rt = 'STAT_OK'
        return(rt)

    def _checkTCON(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        if(_val == 'MOV' or _val == 'REP'):
            rt = 'STAT_OK'
        else:
            rt = 'STAT_ERR: Specify REP(eat) or MOV(ing).'
        return(rt)

    def _checkAVGCOUNT(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the number: 2 to 100 or specyfy either DEF(ault), MIN(imun) or MAX(imum).'
        _tval = self.convEtoN(_val)
        _ckdtf = isinstance(_tval,float)
        if( _ckdtf == False):
            if( 'Ok:' in _tval):
                rt = 'STAT_OK'
                return(rt)
        else:
            try:
                _ckdti = int(_val)
            except ValueError:
                return(rt)
            if( _ckdti >= 2 and _ckdti <= 100):
                rt = 'STAT_OK'
        return(rt)

    def _checkADVNTOL(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the number: 0 to 105 or specyfy either DEF(ault), MINi(mun) or MAX(imum).'
        _tval = self.convEtoN(_val)
        _ckdtf = isinstance(_tval,float)
        if( _ckdtf == False):
            if( 'Ok:' in _tval):
                rt = 'STAT_OK'
        elif( _ckdtf == True):
            if( _tval >= 0 and _tval <= 105):
                rt = 'STAT_OK'
        return(rt)

    def _checkMEDRANK(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the number: 1 to 5 or specyfy either DEFault, MINimun or MAXimum.'
        _tval = self.convEtoN(_val)
        _ckdtf = isinstance(_tval,float)
        if( _ckdtf == False):
            if( 'Ok:' in _tval):
                rt = 'STAT_OK'
        elif( _ckdtf == True):
            try:
                _ckdti = int(_val)
            except ValueError:
                return(rt)
            if( _ckdti >= 1 and _ckdti <=5):
                rt = 'STAT_OK'
        return(rt)

    def _checkDataStatistic(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        _rt = self.device_act(':TRAC:POIN:ACT?')
        _ckdtfi = _rt.isdigit()
        if( _ckdtfi == True):
            _ridt = int(_rt)
            if( _ridt <= 0):
                rt = 'STAT_ERR : No Data in buffer'
            elif( _ridt == 1):
                rt = 'STST_ERR:  Only 1 data in buffer. More than 2 Data needed.'
            else:
                rt = 'STAT_OK'
        else:
            rt = 'STAT_ERR: Iliegal responce'

#        if( _rt <= '0'):
#            rt = 'STAT_ERR : No Data in buffer'
#        elif( _rt == '1'):
#            rt = 'STST_ERR:  Only 1 data in buffer. More than 2 Data needed.'
#        elif( _ckdtfi == True ):
#            if( int(_rt) >= 2):
#                rt ='STAT_OK'
#        else:
#            rt = 'STAT_ERR: Iliegal responce'

        return(rt)

    def _checkTRCFEED(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        if( _val == 'SENS' or _val == 'SENS1' or _val == 'CALC' or _val == 'CALC1' or _val == 'CALC2'):
            rt = 'STAT_OK'
        else:
            rt = 'STAT_ERR: Specify either SENS(SENSe[1]), CALC(ulate[1]) or CALC2(CALCulate2).'
        return(rt)

    def _checkTRCTIMEFORMAT(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        if(_val == 'ABS' or _val == 'ABSOLUTE' or _val == 'DELT' or _val == 'DELTA' ):
            rt = 'SATA_OK'
        else:
            rt = 'STAT_ERR: Specify ABS(olute) or DELT(a).'
        return(rt)

    def _checkTRCPOINTS(self,val1,val2,val3):
        rt = 'STAT_ERR'
        _val = val1.upper()
        _ch = val2
        _dtp = val3

        rt = 'or specyfy either DEF(ault), MIN(imun) or MAX(imum).'
        _tval = self.convEtoN(_val)
        _cktf = isinstance(_tval,float)
        if( _cktf == False):
            if( 'Ok:' in _tval):
                rt = 'STAT_OK'
            else:
                rt = 'STAT_ERR: Specify the size of buffer ' + rt + ' The size depends on the model'
        else:
            try:
                _ckdti = int(_val)
            except ValueError :
                rt = 'STAT_ERR: Specify the size of buffer ' + rt + ' The size depends on the model'
                return(rt)
            if(_dtp == '6487'):
                if( _ckdti >= 1 and _ckdti <= 3000):
                    rt = 'STAT_OK'
                else:
                    rt = 'STAT_ERR: Specify size of buffer (1 to 3000) ' + rt
            elif(_dtp == '6485'):
                if( _ckdti >= 1 and _ckdti <= 2500):
                    rt = 'STAT_OK'
                else:
                    rt = 'STAT_ERR: Specify size of buffer (1 to 2500) ' + rt
            else:
                rt = 'STAT_ERR: check the device-type. It may be an Supported model.'
        return(rt)

    def _checkTRCFEEDCONTROL(self,val1,val2,val3):
#        rt = 'STAT_ERR'
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        if(_val == 'NEV' or _val == 'NEXT'):
            rt = 'STAT_OK'
        else:
            rt = 'STAT_ERR: Specify buffer control mode ; either NEV(er) or NEXT.'
        return(rt)

    def _checkUSERMemory(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR : Specify memory location:0 to 2 (0 = USR0. 1 = USR1, 2 = USR2)'
        try:
            _dtcki = int(_val)
        except ValueError:
            return(rt)
        if( _dtcki == 0 or _dtcki == 1 or _dtcki == 2):
            rt = 'STAT_OK'


#        _res = re.match("[0-2]",str(_val))
#        if( _res != None):
#            rt = 'STAT_OK'
#        else:
#            rt = 'STAT_ERR: Specify memory location:0 to 2 (0 = USR0. 1 = USR1, 2 = USR2)'
        return(rt)


#####

    def _checkTRIGArmSource(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Only IMM and TIM are supported.'
        if('IMM' in _val or 'TIM' in _val):
            rt = 'STAT_OK'
        elif(('BUS' in _val) or ('TLIN' in _val) or ('MAN' in _val)):
            rt = 'STAT_ERR: Sorry. BUS,TLIN(k),MAN(aual) this program not supported.'
        return(rt)

    def _checkTRIGArmTimer(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the number(sec): 0.001 to 99999.999, or specify either DEF(ault), MIN(imum) or MAX(imum).'
        _tval = self.convEtoN(_val)
        _ckdtf = isinstance(_tval,float)
        if( _ckdtf == False):
            if( 'Ok:' in _tval):
                rt = 'STAT_OK'
        if( _ckdtf == True):
            if( float(_val) >= 0.001 and float(_val) <= 99999.999):
                rt = 'STAT_OK' 
        return(rt)

    def _checkTRIGArmCount(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        if(_dtp == '6485'):
            rt0 = ' Specify the integer value : 1 to 2500'
            _ckdh = 2500
        else:
            rt0 = ' Specify the integer value : 1 to 2048'
            _ckdh = 2048
        _ckdtalp = _val.isalpha()
        if(_ckdtalp == True):
            if( 'INF' in _val):
                rt = 'STAT_ERR: INF(inite) is not supported.' + rt0
        else:
            if( '9\.9E37' in _val):
                rt = 'STAT_ERR: Overflow occurred.' + rt0
            else:
                try:
                    _ckdti = int(_val)
                except ValueError:
                    rt = 'STAT_ERR:' + rt0
                    return(rt)
            if( (_ckdti >= 1) and (_ckdti <= _ckdh) ):
                    rt = 'STAT_OK'
            else:
                rt = 'STAT_ERR:' + rt0
        return(rt)

    def _checkTRIGSource(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Only IMM is supported.'
        if('IMM' in _val):
            rt = 'STAT_OK'
        elif('TLIN' in _val):
            rt = 'STAT_ERR: Sorry. TLIN(k) this program not supported.'
        return(rt)

    def _checkTRIGCount(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3

        rt = 'or specyfy the Range: DEF(ault), MIN(imun) or MAX(imum).'

        _tval = self.convEtoN(_val)
        _cktf = isinstance(_tval,float)
        if( _cktf == False):
            if( 'Ok:' in _tval):
                rt = 'STAT_OK'
            elif('INF' == _val):
                rt = 'No supported in this program.'
            else:
                rt = 'STAT_ERR: Specify the count number ' + rt + ' The size depends on the model'
        else:
            if(_dtp == '6487'):
                if(int(_tval) >= 1 and int(_tval) <= 2048):
                    rt = 'STAT_OK'
                else:
                    rt = 'STAT_ERR: Specify the count number (1 to 2048) ' + rt
            elif(_dtp == '6485'):
                if(int(_tval) >= 1 and int(_tval) <= 2500):
                    rt = 'STAT_OK'
                else:
                    rt = 'STAT_ERR: Specify the count number (1 to 2500) ' + rt
            else:
                rt = 'STAT_ERR: check the device-type. It may be an Supported model.'
        return(rt)

#####

    def _checkTRIGDELAY(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the number(sec): 0 to 999.9999, or specify either DEF(ault), MIN(imum) or MAX(imum).'
        _tval = self.convEtoN(_val)
        _ckdtf = isinstance(_tval,float)
        if( _ckdtf == False):
            if( 'Ok:' in _tval):
                rt = 'STAT_OK'
        if( _ckdtf == True):
            if( _tval >= 0 and _tval <= 999.9999):
                rt = 'STAT_OK' 
        return(rt)

    def _checkSourceCleaeAutoMode(self,val1,val2,val3):
#        rt = 'STAT_ERR'
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        if(_val == 'ALW' or _val == 'ALWAYS' or _val == 'TCO' or _val == 'TCOUNT'):
            rt = 'STAT_OK'
        else:
            rt = 'STAT_ERR: Specify ALW(ays) or TCO(unt).'
        return(rt)


########################## Check procedure for model 6487

    def _convNDN(self,val1):
        rt = 'Ng:'
        _ckval = val1
        try:
            _rt = int(_ckval)
        except ValueError:
            return(rt)
        return(_rt)
    
    def _checkSource2(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the number: 1 to 15 by dec,hex(#Hx),oct(#Qxx) or bin(#Bxxxx).'
        _ckdn = _val.isdigit()
        if( _ckdn == True):
            _rt = int(_val)
        else:
            if( '#H' in _val):
                _dti = _val.replace('#H','0x')
                try:
                    _rt = int(_dti,16)
                except TypeError:
                    return(rt)
            elif( '#B' in _val):
                _dti = _val.replace('#B','0b')
                try:
                    _rt = int(_dti,2)
                except TypeError:
                    return(rt)
            elif( '#Q' in _val):
                _dti = _val.replace('#Q','0o') 
                try:
                    _rt = int(_dti,8)
                except TypeError:
                    return(rt)
            else:
                return(rt)
        if( _rt >=1 and _rt <= 15):
            rt = 'STAT_OK'
        return(rt)

    def _checkDataFormatSource2(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        if(_val == 'ASC' or _val == 'HEX' or _val == 'OCT' or _val == 'BIN' ):
            rt = 'STAT_OK'
        else:
            rt = 'STAT_ERR: Specify either ASC(ii), HEX(adecimal), OCT(al) or BIN(ary).'
        return(rt)

    def _checkVoltage(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the number: -505 to 505 (V).'
        try:
            _ckdtf = float(_val)
        except ValueError:
            return(rt)
        if( (_ckdtf >= -505) and (_ckdtf <= 505)):
                rt = 'STAT_OK'
        return(rt)

    def _checkVoltSourceAmplitude(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the number: -500 to 500. It may be able to set DEF(ault), MIN(imum) or MAX(imum).'
        _tval = self.convEtoN(_val)
        _ckdtf = isinstance(_tval,float)
        if( _ckdtf == False):
            if( 'Ok:' in _tval):
                rt = 'STAT_OK'
        if( _ckdtf == True):
            if( (_tval >= -500) and (_tval <= 500)):
                rt = 'STAT_OK'
        return(rt)

    def _checkOHMSAVTimeInterval(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Set to a positive value. And if the value is not desirable, an error message will be returned. It may be able to set DEF(ault), MIN(imum) or MAX(imum).'
        _tval = self.convEtoN(_val)
        _ckdtf = isinstance(_tval,float)
        if( _ckdtf == False):
            if( 'Ok:' in _tval):
                rt = 'STAT_OK'
        if( _ckdtf == True):
            if( _tval >=0 ):
                rt = 'STAT_OK'
        return(rt)

    def _checkOHMSAVCycles(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the number: 1 to 9999'
        try:
            _ckdti = int(_val)
        except ValueError:
            return(rt)
        if( _ckdti >=1 and _ckdti <= 9999):
            rt = 'STAT_OK'
        return(rt)

    def _checkOHMSUnits(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        if(_val == 'AMPS' or _val == 'OHMS'):
            rt = 'STAT_OK'
        else:
            rt = 'STAT_ERR: Specify AMPS or OHMS.'
        return(rt)

    def _checkVoltSourceRange(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify 10(V),50(V)) or 500(V). It may be able to set DEF(ault), MIN(imum) or MAX(imum).'
        _tval = self.convEtoN(_val)
        _ckdtf = isinstance(_tval,float)
        if( _ckdtf == False):
            if( 'Ok:' in _tval):
                rt = 'STAT_OK'
        if( _ckdtf == True):
            if( (_tval == 10) or (_tval == 50) or (_tval == 500)):
                rt = 'STAT_OK'         
        return(rt)

    def _checkVoltSourceILimit(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt0 = 'STAT_ERR: Specify the number: 2.5En(n=-5 to -2) (amps). '
        rt1 = 'STAT_ERR: Specify the number: 2.5En(n=-5 to -3) (amps). '
        _rts = 'It may be able to set DEF(ault), MIN(imum) or MAX(imum).'

        _lvol = self.device_act(':SOUR:VOLT:RANG?')
        if( _lvol != '10' and _lvol != '50' and _lvol != '500'):
            rt = 'STAT_ERR: The voltage range is not set correctly. Try setting the voltage range.'
            return(rt)
        _tval = self.convEtoN(_val)
        _ckdtf = isinstance(_tval,float)
        if( _ckdtf == False):
            if( 'Ok:' in _tval):
                rt = 'STAT_OK'
        if( _ckdtf == True):
            if(str(_lvol) == '10'):
                if( (_tval == 2.5*10**(-5)) or (_tval == 2.5*10**(-4)) or (_tval == 2.5*10**(-3)) or (_tval == 2.5*10**(-2))):
                    rt = 'STAT_OK'
                else:
                    rt = rt0 + _rts
            else:
                if( (_tval == 2.5*10**(-5)) or (_tval == 2.5*10**(-4)) or (_tval == 2.5*10**(-3))):
                    rt = 'STAT_OK'
                else:
                    rt = rt1 + _rts
        return(rt)

    def _checkVoltageSweepDelay(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the number: 0 to 999.9999(s). It may be able to set DEF(ault), MIN(imum) or MAX(imum).'
        _tval = self.convEtoN(_val)
        _ckdtf = isinstance(_tval,float)
        if( _ckdtf == False):
            if( 'Ok:' in _tval):
                rt = 'STAT_OK'
        if( _ckdtf == True):
            if( _tval >= 0 and _tval <= 999.9999):
                rt = 'STAT_OK'         
        return(rt)

    def _checkTTLOutputPatern(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the number: 1 to 15 by dec,hex(#Hx),oct(#Qxx) or bin(#Bxxxx).'
        _ckdn = _val.isdigit()
        if( _ckdn == True):
            _rt = int(_val)
        else:
            if( '#H' in _val):
                _dti = _val.replace('#H','0x')
                try:
                    _rt = int(_dti,16)
                except TypeError:
                    return(rt)
            elif( '#B' in _val):
                _dti = _val.replace('#B','0b')
                try:
                    _rt = int(_dti,2)
                except TypeError:
                    return(rt)
            elif( '#Q' in _val):
                _dti = _val.replace('#Q','0o') 
                try:
                    _rt = int(_dti,8)
                except TypeError:
                    return(rt)
            else:
                return(rt)
        if( _rt >=1 and _rt <= 15):
            rt = 'STAT_OK'
        return(rt)


    def _checkTTLDelayPatern(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the number(sec): 0 to 60, or specify either DEF(ault), MIN(imum) or MAX(imum).'
        _tval = self.convEtoN(_val)
        _ckdtf = isinstance(_tval,float)
        if( _ckdtf == False):
            if( 'Ok:' in _tval):
                rt = 'STAT_OK'
        if( _ckdtf == True):
            if( _tval >= 0 and _tval <= 60):
                rt = 'STAT_OK' 
        return(rt)

    def _checkTTL4Mode(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify EOT(est) or BUSY.'
        if(_val == 'EOT' or _val == 'BUSY'):
            rt = 'STAT_OK'
        return(rt)

    def _checkTTL4ActiveBusyStatus(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the number: 0(meae LO) or 1(mean HI).'
        if(_val == '0' or _val == '1'):
            rt = 'STAT_OK'
        return(rt)


    def _checkTRIGArmCount2(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_OK'
        if( ('INF' in _val) or ('9\.9E37' in _val)):
            rt = 'STAT_ERR: INF(inite) is not supported.'
        return(rt)

    def _checkTracePoints(self,val1,val2,val3):
        _val = val1.upper()
        _ch = val2
        _dtp = val3
        rt = 'STAT_ERR: Specify the number: 1 to 3000'
        _tval = self.convEtoN(_val)
        try:
            _ckdti = int(_tval)
        except ValueError:
            return(rt)
        if( _ckdti >= 1 and _ckdti <= 3000):
            rt = 'STAT_OK'
        return(rt)



##########################################################################################
#  Initialization functions
##########################################################################################


    def setstartup(self,cmkey,cmdc):
        _cmddicl = cmkey
        rt = 'Ok:'
        for cs in _cmddicl:
            _cknodename = cs.split(':')[0]
            if( starsNodeName == _cknodename):
                _precmd = cs.split(':')[1]
                _starscmd = 'Set' + _precmd
                _cmdparam = cmdc[cs]
                _cmd = self._deviceCTLSTARSCommand[_starscmd]["command"] + ' ' + _cmdparam
                self.device_send(_cmd)
                _rt = self.donecheck()
                if('Ng' in _rt):
                    rt = 'Failure'
                    self.error = 'set up the device '
                    break
        return(rt)

    def devReset(self,lc,autoset,cmd,devt):
        self.dev2Idle()
        self.device_send(cmd)
        _dck = self.donecheck()
        if( 'Ng' in _dck):
            _rt = 'Er:' + _dck
            return(_rt)
        _rt = self.statuscheck()
        if( _rt == 'Ok:'):
            if(lc == 'on'):
                _rt = self.setstartup(dictk,dictd)
            if(_rt == 'Ok:'):
                gb_CheckTriggerFlag = self.TriggerEnvCheck(autoset,devt)
                if( gb_CheckTriggerFlag == 'Ng'):
                    _rt = 'Er: not ready for mesurement'
            else:
                _rt = 'Er: reset failed A'
        else:
            _rt = 'Er: reset failed B'
        return(_rt)

    #######
    def loadUReset(self,lc,autoset,cmd,devt):
        rt = 'Er: missing userload'
        self.dev2Idle()
        self.device_send(cmd)
        _dck = self.donecheck()
        _rt = self.device_act(':*OPC?')     # Need to send check command twice
        if(_rt == '1'):
            rt = 'Ok:'
        _rt = self.statuscheck()
        if( _rt == 'Ok:'):
            if(lc == 'on'):
                rt = self.setstartup(dictk,dictd)
            if(rt == 'Ok:'):
                gb_CheckTriggerFlag = self.TriggerEnvCheck(autoset,devt)
                if( gb_CheckTriggerFlag == 'Ng'):
                    _rt = 'Er: not ready for mesurement'
            else:
                _rt = 'Er: reset failed A'
        else:
            _rt = 'Er: reset failed B'
        return(rt)
    ########

    ##################################################################
    # Command functions
    ##################################################################
    def is_commandfined(self,starscommand):
        _sc=str(starscommand)
        if(_sc in self._deviceCTLSTARSCommand):
#            _acs = self._deviceCTLSTARSCommand[_sc]["WoA"]
            try:                                                    # Do not access the device without the key.
                _acs = self._deviceCTLSTARSCommand[_sc]["WoA"]
            except KeyError:
                return(False)
#
            _scmd = self._deviceCTLSTARSCommand[_sc]["command"]
            _rt = _acs + '_' + _scmd
            if( '?' in str(_scmd)):
                return(_rt)
            if(self._deviceCTLSTARSCommand[_sc]["Parl"]):
                _paral = self._deviceCTLSTARSCommand[_sc]["Parl"]
                if(_paral != '0'):
                    _rt = _rt + '_' + _paral
            return(_rt)
        return(False)

    def get_starscommandlist(self,model):           # corrected on 20220715
        clist = []
        for com in self._deviceCTLSTARSCommand.keys():
            _typ = self._deviceCTLSTARSCommand[com]["model"]
            if( model == _typ or _typ == '648X'):
                clist.append(com)
        return(clist)

    def get_starscommandhelp(self,starscommand,model):    # corrected on 20220715
        _sc=str(starscommand)
        rt = False
        if(_sc in self._deviceCTLSTARSCommand):
            _typ = self._deviceCTLSTARSCommand[_sc]["model"]
            if( model == _typ or _typ == '648X'):
                _rt=self._deviceCTLSTARSCommand[_sc]['help']
                return(_rt)
        return(rt)

    def get_commandlastexecutedtime(self):
        return(self._deviceCommandLastExecutedTime);

    ##################################################################
    # Device info functions
    ##################################################################

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
# 20220421 addition to listnodes
    def getnumofch(self,slotnmb,funmb):
        _chnmb = 'ER: Bad parameter'
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
#
#               added on 20220608 for file of reg.txt   ->
#
    def checkstart(self):
        _mdn = self.device_act(':*IDN?')
        print('   <<>>>>><<>>>>>  Model ID = ' + str(_mdn) + '\n')         # for making sure 20220705
        rt = False
        if(('6485' in _mdn) and ('6485' in starsNodeName)):
            self.device_send(':SYST:CLE')
            rt = '6485'
        elif(('6487' in _mdn) and ('6487') in starsNodeName):
            self.device_send(':SYST:CLE')
            rt = '6487'
        else:
            self.error = 'The device is different.'
#
        rt = '6487'                                     # temporary for debug model6487
#
        return(rt)
#
#               <-   added on 20220608 for file of reg.txt
#

    def __init__(self, deviceHost, devicePost, inthandler=None):
        self._deviceInstance = nportserv.nportserv.__init__(self, deviceHost, devicePost)
        #self.setdelimiter('\r\n')
        self.settimeout(2)
        ##################################################################
        # Define command definitions
        ##################################################################
        lc_deviceCTLSTARSCommand = {}
        lc_deviceCHSTARSCommand  = {}

# Description of commands and helps
        lc_deviceCTLSTARSCommand['SetMathFormat']					={"model":"648X","command":":CALC1:FORM", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkMathFormat","postfunc":None, "help":"[CALC1]Select math format; MXB (mX+b) or RECiprocal(m/X+b), or LOG10."}
        lc_deviceCTLSTARSCommand['GetMathFormat']					={"model":"648X","command":":CALC1:FORM?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC1]Query math format."}
        lc_deviceCTLSTARSCommand['SetKMathMFactor']					={"model":"648X","command":":CALC1:KMAT:MMF", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkKMathMBFactor","postfunc":None, "help":"[CALC1]Configure math calculations: Set  gm h for mX+b and m/X+b calculation; -9.99999e20 to 9.99999e20."}
        lc_deviceCTLSTARSCommand['GetKMathMFactor']					={"model":"648X","command":":CALC1:KMAT:MMF?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC1]Configure math calculations: Query  gm h factor."}
        lc_deviceCTLSTARSCommand['SetKMathBFactor']					={"model":"648X","command":":CALC1:KMAT:MBF", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkKMathMBFactor","postfunc":None, "help":"[CALC1]Configure math calculations: Set  gb h for mX+b and m/X+b calculation; -9.99999e20 to 9.99999e20."}
        lc_deviceCTLSTARSCommand['GetKMathBFactor']					={"model":"648X","command":":CALC1:KMAT:MBF?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC1]Configure math calculations: Query  gb h factor."}
        lc_deviceCTLSTARSCommand['SetKMathUnits']					={"model":"648X","command":":CALC1:KMAT:MUN", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkKMathUnits","postfunc":None, "help":"[CALC1]Configure math calculations: Specify units for mX+b or m/X+b result: 1 character: A?Z,  e[ e=.,  e\ f=  ,  e] f=%."}
        lc_deviceCTLSTARSCommand['GetKMathUnits']					={"model":"648X","command":":CALC1:KMAT:MUN?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC1]Configure math calculations: Query units."}
        lc_deviceCTLSTARSCommand['SetMathEnable']					={"model":"648X","command":":CALC1:STAT", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None, "help":"[CALC1]Enable or disable selected math calculation."}
        lc_deviceCTLSTARSCommand['GetMathEnable']					={"model":"648X","command":":CALC1:STAT?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC1]Query state of selected math calculation."}
        lc_deviceCTLSTARSCommand['GetValueMath']					={"model":"648X","command":":CALC1:DATA?", "WoA":"AT","prefunc":None,"checkfunc":"dc._checkPreGetValueKMath","postfunc":None, "help":"[CALC1]Return all math calculation results triggered by INITiate."}
        lc_deviceCTLSTARSCommand['SetLimitTestInputPath']			={"model":"648X","command":":CALC2:FEED", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkCalc2InputPath","postfunc":None, "help":"[CALC2]Select input path for limit testing; CALCulate[1]or SENSe[1]."}
        lc_deviceCTLSTARSCommand['GetLimitTestInputPath']			={"model":"648X","command":":CALC2:FEED?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC2]Query input path for limit tests."}
        lc_deviceCTLSTARSCommand['SetRELInputPath']					={"model":"648X","command":":CALC2:FEED", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkCalc2InputPath","postfunc":None, "help":"[CALC2]Select input path for limit testing; CALCulate[1]or SENSe[1]."}
        lc_deviceCTLSTARSCommand['GetRELInputPath']					={"model":"648X","command":":CALC2:FEED?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC2]Query input path for limit tests."}
        lc_deviceCTLSTARSCommand['SetLimitTest1Max']				={"model":"648X","command":":CALC2:LIM:UPP", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkCalc2Range","postfunc":None, "help":"[CALC2]Limit 1 Testing: Configure upper limit: Set limit; -9.99999e20 to 9.99999e20."}
        lc_deviceCTLSTARSCommand['GetLimitTest1Max']				={"model":"648X","command":":CALC2:LIM:UPP?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC2]Limit 1 Testing: Query upper limit."}
        lc_deviceCTLSTARSCommand['SetLimitTest1Min']				={"model":"648X","command":":CALC2:LIM:LOW", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkCalc2Range","postfunc":None, "help":"[CALC2]Limit 1 Testing: Configure lower limit: Set limit; -9.99999e20 to 9.99999e20."}
        lc_deviceCTLSTARSCommand['GetLimitTest1Min']				={"model":"648X","command":":CALC2:LIM:LOW?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC2]Limit 1 Testing: Query lower limit."}
        lc_deviceCTLSTARSCommand['SetLimitTest1Enable']				={"model":"648X","command":":CALC2:LIM:STAT", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None, "help":"[CALC2]Limit 1 Testing: Enable or disable limit 1 test."}
        lc_deviceCTLSTARSCommand['GetLimitTest1Enable']				={"model":"648X","command":":CALC2:LIM:STAT?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC2]Limit 1 Testing: Query state of limit 1 test."}
        lc_deviceCTLSTARSCommand['IsLimitTest1FailStatus']			={"model":"648X","command":":CALC2:LIM:FAIL?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC2]Limit 1 Testing: Return result of limit 1 test; 0 (pass) or 1 (fail)"}
        lc_deviceCTLSTARSCommand['SetLimitTest2Max']				={"model":"648X","command":":CALC2:LIM2:UPP", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkCalc2Range","postfunc":None, "help":"[CALC2]Limit 2 Testing: Configure upper limit: Set limit; -9.99999e20 to 9.99999e20."}
        lc_deviceCTLSTARSCommand['GetLimitTest2Max']				={"model":"648X","command":":CALC2:LIM2:UPP?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC2]Limit 2 Testing: Query upper limit."}
        lc_deviceCTLSTARSCommand['SetLimitTest2Min']				={"model":"648X","command":":CALC2:LIM2:LOW", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkCalc2Range","postfunc":None, "help":"[CALC2]Limit 2 Testing: Configure lower limit: Set limit; -9.99999e20 to 9.99999e20."}
        lc_deviceCTLSTARSCommand['GetLimitTest2Min']				={"model":"648X","command":":CALC2:LIM2:LOW?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC2]Limit 2 Testing: Query lower limit."}
        lc_deviceCTLSTARSCommand['SetLimitTest2Enable']				={"model":"648X","command":":CALC2:LIM2:STAT", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None, "help":"[CALC2]Limit 2 Testing: Enable or disable limit 1 test."}
        lc_deviceCTLSTARSCommand['GetLimitTest2Enable']				={"model":"648X","command":":CALC2:LIM2:STAT?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC2]Limit 2 Testing: Query state of limit 1 test."}
        lc_deviceCTLSTARSCommand['IsLimitTest2FailStatus']			={"model":"648X","command":":CALC2:LIM2:FAIL?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC2]Limit 2 Testing: Return result of limit 1 test; 0 (pass) or 1 (fail)"}
        lc_deviceCTLSTARSCommand['AcquireRELOffset']				={"model":"648X","command":":CALC2:NULL:ACQ", "Parl":"0", "WoA":"WR","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC2]Configure and control Rel: Use input signal as Rel value."}
        lc_deviceCTLSTARSCommand['SetRELOffset']					={"model":"648X","command":":CALC2:NULL:OFFS", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkCalc2Range","postfunc":None, "help":"[CALC2]Configure and control Rel: Specify Rel value; -9.999999e20 to 9.999999e20."}
        lc_deviceCTLSTARSCommand['GetRELOffset']					={"model":"648X","command":":CALC2:NULL:OFFS?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC2]Configure and control Rel: Query Rel value."}
        lc_deviceCTLSTARSCommand['SetRELEnable']					={"model":"648X","command":":CALC2:NULL:STAT", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None, "help":"[CALC2]Configure and control Rel: Enable or disable Rel."}
        lc_deviceCTLSTARSCommand['GetRELEnable']					={"model":"648X","command":":CALC2:NULL:STAT?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC2]Configure and control Rel: Query state of Rel."}
        lc_deviceCTLSTARSCommand['GetValueREL']						={"model":"648X","command":":CALC2:DATA?", "WoA":"AT","prefunc":None,"checkfunc":"dc._checkPreGetValueREL","postfunc":None, "help":"[CALC2]Return all [CALC2]readings triggered by INITiate."}
        lc_deviceCTLSTARSCommand['SetTraceStatisticType']			={"model":"648X","command":":CALC3:FORM", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkTRCSTATICTYPE","postfunc":None, "help":"[CALC3]Select buffer statistic; MEAN, SDEViation, Maximum, MINimum or PKPK."}
        lc_deviceCTLSTARSCommand['GetTraceStatisticType']			={"model":"648X","command":":CALC3:FORM?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[CALC3]Query selected statistic."}
        lc_deviceCTLSTARSCommand['GetValueStatistic']				={"model":"648X","command":":CALC3:DATA?", "WoA":"AT","prefunc":None,"checkfunc":"dc._checkDataStatistic","postfunc":None, "help":"[CALC3]: Read the selected buffer statistic."}
        lc_deviceCTLSTARSCommand['SetDisplayDigits']				={"model":"648X","command":":DISP:DIG", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkDisplayDigits","postfunc":None, "help":"[DISPLAY]Set display resolution; 4 to 7."}
        lc_deviceCTLSTARSCommand['GetDisplayDigits']				={"model":"648X","command":":DISP:DIG?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[DISPLAY]Query display resolution."}
        lc_deviceCTLSTARSCommand['SetDisplayEnable']				={"model":"648X","command":":DISP:ENAB", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None, "help":"[DISPLAY]Turn fron panel display enable or disable."}
        lc_deviceCTLSTARSCommand['GetDisplayEnable']				={"model":"648X","command":":DISP:ENAB?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[DISPLAY]Query state of display."}
        lc_deviceCTLSTARSCommand['SetDataFormatElements']			={"model":"648X","command":":FORM:ELEM", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkDATAELEMENTS","postfunc":None, "help":"[FORMAT]Specify data elements; READing, UNITs, TIME, and STATus."}
        lc_deviceCTLSTARSCommand['GetDataFormatElements']			={"model":"648X","command":":FORM:ELEM?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[FORMAT]Query data format elements."}
        lc_deviceCTLSTARSCommand['SetNPLCycles']					={"model":"648X","command":":SENS:CURR:DC:NPLC", "Parl":"1","prefunc":None, "WoA":"WR","checkfunc":"dc._checkAmpNPLC","postfunc":None, "help":"[SENSE]Amps function: Set integration rate in line cycles (PLC); 0.01 to 6.0 (60 Hz) or 5.0 (50Hz)."}
        lc_deviceCTLSTARSCommand['GetNPLCycles']					={"model":"648X","command":":SENS:CURR:DC:NPLC?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query NPLC."}
        lc_deviceCTLSTARSCommand['SetRange']						={"model":"648X","command":":SENS:CURR:DC:RANGe", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkAmpRANGE","postfunc":None, "help":"[SENSE]Amps function: Configure measurement range: Select range; 2.1E-9 to 2.1E-2 (amps)."}
        lc_deviceCTLSTARSCommand['GetRange']						={"model":"648X","command":":SENS:CURR:DC:RANGe?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query range value."}
        lc_deviceCTLSTARSCommand['SetAutoRangeEnable']				={"model":"648X","command":":SENS:CURR:DC:RANGe:AUTO", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None, "help":"[SENSE]Amps function: Enable or disable autorange."}
        lc_deviceCTLSTARSCommand['GetAutoRangeEnable']				={"model":"648X","command":":SENS:CURR:DC:RANGe:AUTO?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query state of autorange."}
        lc_deviceCTLSTARSCommand['SetAutoRangeMax']					={"model":"648X","command":":SENS:CURR:DC:RANGe:AUTO:ULIM", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkAmpRANGE","postfunc":None, "help":"[SENSE]Amps function: Select autorange upper limit; 2.1E-9 to 2.1E-2 (amps)."}
        lc_deviceCTLSTARSCommand['GetAutoRangeMax']					={"model":"648X","command":":SENS:CURR:DC:RANGe:AUTO:ULIM?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query upper limit for autorange."}
        lc_deviceCTLSTARSCommand['SetAutoRangeMin']					={"model":"648X","command":":SENS:CURR:DC:RANGe:AUTO:LLIM", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkAmpRANGE","postfunc":None, "help":"[SENSE]Amps function: Select autorange lower limit; 2.1E-9 to 2.1E-2 (amps)."}
        lc_deviceCTLSTARSCommand['GetAutoRangeMin']					={"model":"648X","command":":SENS:CURR:DC:RANGe:AUTO:LLIM?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query lower limit for autorange."}
        lc_deviceCTLSTARSCommand['SetAverageEnable']				={"model":"648X","command":":SENS:AVER", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None, "help":"[SENSE]Amps function: Query state of digital filter."}
        lc_deviceCTLSTARSCommand['GetAverageEnable']				={"model":"648X","command":":SENS:AVER?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query state of advanced filter."}
        lc_deviceCTLSTARSCommand['SetAverageTControl']				={"model":"648X","command":":SENS:AVER:TCON", "Parl":"1","WoA":"WR","prefunc":None, "checkfunc":"dc._checkTCON","postfunc":None, "help":"[SENSE]Amps function: Select Digital filter control; MOVing or REPeat. MOV"}
        lc_deviceCTLSTARSCommand['GetAverageTControl']				={"model":"648X","command":":SENS:AVER:TCON?", "WoA":"AT","prefunc":None,"checkfunc":None, "postfunc":None,"help":"[SENSE]Amps function: Query filter control."}
        lc_deviceCTLSTARSCommand['SetAverageCount']					={"model":"648X","command":":SENS:AVER:COUN", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkAVGCOUNT","postfunc":None, "help":"[SENSE]Amps function: Specify filter count; 2 to 100."}
        lc_deviceCTLSTARSCommand['GetAverageCount']					={"model":"648X","command":":SENS:AVER:COUN?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query filter count."}
        lc_deviceCTLSTARSCommand['SetAverageADVEnable']				={"model":"648X","command":":SENS:AVER:ADV", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None, "help":"[SENSE]Amps function: Enable or disable advanced filter."}
        lc_deviceCTLSTARSCommand['GetAverageADVEnable']				={"model":"648X","command":":SENS:AVER:ADV?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query state of advanced filter."}
        lc_deviceCTLSTARSCommand['SetAverageADVNTolarance']			={"model":"648X","command":":SENS:AVER:ADV:NTOL", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkADVNTOL","postfunc":None, "help":"[SENSE]Amps function: Specify noise tolerance (in %); 0 to 105."}
        lc_deviceCTLSTARSCommand['GetAverageADVNTolarance']			={"model":"648X","command":":SENS:AVER:ADV:NTOL?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query noise tolerance."}
        lc_deviceCTLSTARSCommand['SetMedianEnable']					={"model":"648X","command":":SENS:MED", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None, "help":"[SENSE]Amps function:Enable or disable median filter."}
        lc_deviceCTLSTARSCommand['GetMedianEnable']					={"model":"648X","command":":SENS:MED?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query state of median filter."}
        lc_deviceCTLSTARSCommand['SetMedianRank']					={"model":"648X","command":":SENS:MED:RANK", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkMEDRANK","postfunc":None, "help":"[SENSE]Amps function: Specify  gn h for rank; 1 to 5 (rank = 2n+1)."}
        lc_deviceCTLSTARSCommand['GetMedianRank']					={"model":"648X","command":":SENS:MED:RANK?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query rank."}
        lc_deviceCTLSTARSCommand['SetZeroCheckEnable']				={"model":"648X","command":":SYST:ZCH", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None, "help":"[SENSE]Amps function: Enable or disable zero check."}
        lc_deviceCTLSTARSCommand['GetZeroCheckEnable']				={"model":"648X","command":":SYST:ZCH?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query state of zero check."}
        lc_deviceCTLSTARSCommand['SetZeroCorrectEnable']			={"model":"648X","command":":SYST:ZCOR", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None, "help":"[SENSE]Amps function: Enable or disable zero correct."}
        lc_deviceCTLSTARSCommand['GetZeroCorrectEnable']			={"model":"648X","command":":SYST:ZCOR?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query state of zero correct."}
        lc_deviceCTLSTARSCommand['AcquireZeroCorrect']				={"model":"648X","command":":SYST:ZCOR:ACQ", "Parl":"0", "WoA":"WR","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Acquire a new zero correct value."}
        lc_deviceCTLSTARSCommand['SetLineFrequency']				={"model":"648X","command":":SYST:LFR", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkLineFrequency", "postfunc":"dc.syncLineFrequency", "help":"[SENSE]Amps function: Select power line frequency; 50 or 60 (Hz)."}
        lc_deviceCTLSTARSCommand['GetLineFrequency']				={"model":"648X","command":":SYST:LFR?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query frequency setting."}
        lc_deviceCTLSTARSCommand['SetLineFrequencyAutoEnable']		={"model":"648X","command":":SYST:LFR:AUTO", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF", "postfunc":"dc.syncLineFrequency", "help":"[SENSE]Amps function: Enable or disable auto frequency."}
        lc_deviceCTLSTARSCommand['GetLineFrequencyAutoEnable']		={"model":"648X","command":":SYST:LFR:AUTO?", "WoA":"AT","prefunc":None, "postfunc":"dc.syncLineFrequency","checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query state of auto frequency."}
        lc_deviceCTLSTARSCommand['SetAutoZeroEnable']				={"model":"648X","command":":SYST:AZERO", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None, "help":"[SENSE]Amps function: Enable or disable autozero."}
        lc_deviceCTLSTARSCommand['GetAutoZeroEnable']				={"model":"648X","command":":SYST:AZERO?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Query state of autozero."}
        lc_deviceCTLSTARSCommand['ResetTimeStamp']					={"model":"648X","command":":SYST:TIME:RES", "Parl":"0", "WoA":"WR","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Reset timestamp to 0 seconds."}
        lc_deviceCTLSTARSCommand['SetTraceFeed']					={"model":"648X","command":":TRAC:FEED", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkTRCFEED","postfunc":None, "help":"[TRACE]Select source of readings for buffer.; CALCulate[1]orCALCulate[2]orSENSe[1]."}
        lc_deviceCTLSTARSCommand['GetTraceFeed']					={"model":"648X","command":":TRAC:FEED?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[TRACE]Query source of readings for buffer."}
        lc_deviceCTLSTARSCommand['SetTraceTimeFormat']				={"model":"648X","command":":TRAC:TST:FORM", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkTRCTIMEFORMAT","postfunc":None, "help":"[TRACE]Select timestamp format; ABSolute or DELta. ABS"}
        lc_deviceCTLSTARSCommand['GetTraceTimeFormat']				={"model":"648X","command":":TRAC:TST:FORM?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[TRACE]Query timestamp format."}
        lc_deviceCTLSTARSCommand['SetTriggerArmSource']				={"model":"648X","command":":ARM:SOUR", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkTRIGArmSource", "postfunc":"dc.syncTRIGArmSource", "help":"[TRIGGER]Select control source; IMMediate, TIMer, BUS,TLINk, or MANual."}
        lc_deviceCTLSTARSCommand['GetTriggerArmSource']				={"model":"648X","command":":ARM:SOUR?", "WoA":"AT","prefunc":None,"checkfunc":None, "postfunc":"dc.syncTRIGArmSource", "help":"[TRIGGER]Query arm control source."}
        lc_deviceCTLSTARSCommand['SetTriggerArmTimer']				={"model":"648X","command":":ARM:TIM", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkTRIGArmTimer","postfunc":None, "help":"[TRIGGER]Set timer interval; 0.001 to 99999.9998 (sec)."}
        lc_deviceCTLSTARSCommand['GetTriggerArmTimer']				={"model":"648X","command":":ARM:TIM?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[TRIGGER]Query timer interval."}
        lc_deviceCTLSTARSCommand['SetTriggerSource']				={"model":"648X","command":":TRIG:SOUR", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkTRIGSource","postfunc":None, "help":"[TRIGGER]Select control source; IMMediate or TLINk."}
        lc_deviceCTLSTARSCommand['GetTriggerSource']				={"model":"648X","command":":TRIG:SOUR?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[TRIGGER]Query trigger control source."}
        lc_deviceCTLSTARSCommand['SetTriggerDelay']				    ={"model":"648X","command":":TRIG:DEL", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkTRIGDELAY","postfunc":None, "help":"[TRIGGER]Set trigger delay; 0 to 999.9999 (sec)."}
        lc_deviceCTLSTARSCommand['GetTriggerDelay']					={"model":"648X","command":":TRIG:DEL?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[TRIGGER]Query trigger delay value."}
        lc_deviceCTLSTARSCommand['SetTriggerAutoDelayEnable']		={"model":"648X","command":":TRIG:DEL:AUTO", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None, "help":"[TRIGGER]Enable or disable auto delay."}
        lc_deviceCTLSTARSCommand['GetTriggerAutoDelayEnable']		={"model":"648X","command":":TRIG:DEL:AUTO?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[TRIGGER]Query state of auto delay."}
        lc_deviceCTLSTARSCommand['SetTriggerArmCount']				={"model":"648X","command":":ARM:COUN", "Parl":"1", "WoA":"WR","prefunc":"dc.dev2Idle", "checkfunc":"dc._checkTRIGArmCount", "postfunc":"dc.syncTRIGArmCount", "help":"[TRIGGER]Set measure count of arm control; 1 to 2500."}
        lc_deviceCTLSTARSCommand['GetTriggerArmCount']				={"model":"648X","command":":ARM:COUN?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[TRIGGER]Query measure count of arm control."}
        lc_deviceCTLSTARSCommand['SetTriggerCount']					={"model":"648X","command":":TRIG:COUN", "Parl":"1", "WoA":"WR","prefunc":"dc.dev2Idle", "checkfunc":"dc._checkTRIGCount", "postfunc":"dc.syncTRIGCount", "help":"[TRIGGER]Set measure count of trigger control; 1 to 2500."}
        lc_deviceCTLSTARSCommand['GetTriggerCount']					={"model":"648X","command":":TRIG:COUN?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[TRIGGER]Query measure count of trigger control."}
#
        lc_deviceCTLSTARSCommand['ClearTraceBuffer']				={"model":"648X","command":":TRAC:CLEAR", "Parl":"0", "WoA":"WR","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[TRACE]Clear readings from buffer."}
        lc_deviceCTLSTARSCommand['GetTraceData']					={"model":"648X","command":":TRAC:DATA?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[TRACE]Read the contents of the buffer (data store)."}
        lc_deviceCTLSTARSCommand['SetTracePoints']					={"model":"648X","command":":TRAC:POIN", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkTRCPOINTS","postfunc":None, "help":"[TRACE]Specify size of buffer: 1 to 3000."}
        lc_deviceCTLSTARSCommand['GetTracePoints']					={"model":"648X","command":":TRAC:POIN?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[TRACE]Query buffer size."}
        lc_deviceCTLSTARSCommand['SetTraceFeedControl']				={"model":"648X","command":":TRAC:FEED:CONT", "Parl":"1", "WoA":"WR","prefunc":None,"checkfunc":"dc._checkTRCFEEDCONTROL","postfunc":None, "help":"[TRACE]Specify buffer control mode (NEVER or NEXT)."}
        lc_deviceCTLSTARSCommand['GetTraceFeedControl']				={"model":"648X","command":":TRAC:FEED:CONT?", "WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[TRACE]Query buffer control mode."}
        lc_deviceCTLSTARSCommand['Local']							={"model":"648X","command":":SYST:LOC", "Parl":"0", "WoA":"WR","prefunc":None,"checkfunc":None,"postfunc":None, "help":"[SENSE]Amps function: Goto Local"}
        lc_deviceCTLSTARSCommand['SaveToUserSetup']                 ={"model":"648X","command":":*SAV", "Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkUSERMemory","postfunc":None,"help":"Save Command. Saves the current setup to the specified memory location:0 to 2 ; 0 = USR0. 1 = USR1, 2 = USR2"}
#
        lc_deviceCTLSTARSCommand['getversion']                      ={"model":"648X","help":"Return this program version."}
        lc_deviceCTLSTARSCommand['getversionno']                    ={"model":"648X","help":"Return the version number of this program."}


        lc_deviceCTLSTARSCommand['hello']                           ={"model":"648X","help":"Return 'hello nice to meet you.'"}
        lc_deviceCTLSTARSCommand['help']                            ={"model":"648X","help":"Return the list or the explanation of stars command."}
        lc_deviceCTLSTARSCommand['Reset']                           ={"model":"648X","help":"A command to place default setup in model6485."}
        lc_deviceCTLSTARSCommand['Preset']                          ={"model":"648X","help":"Preset Command. Return the Model 6485 to the :SYST:PRES defaults, optimized for front panel operation. "}
        lc_deviceCTLSTARSCommand['LoadUserSetup']                   ={"model":"648X","help":"Recall Command. Return the Model 6485 to the setup configuration stored in the specified memory location."}
        lc_deviceCTLSTARSCommand['GoIdle']                          ={"model":"648X","help":"Reset Trigger system(goes to idle state)."}
        lc_deviceCTLSTARSCommand['TriggerRun']						={"model":"648X","help":"Initiate one trigger cycle. Run measurement. "}
        lc_deviceCTLSTARSCommand['Run']						        ={"model":"6487","help":"[TRACE]The event flag is reset for the measurement is executed. "}
        lc_deviceCTLSTARSCommand['GetValue']						={"model":"648X","help":"[TRACE]Returns the measured value in the defined format."}
        lc_deviceCTLSTARSCommand['SendRawCommand']					={"model":"648X","help":"Send device command. Option -rawenable required."}
        lc_deviceCTLSTARSCommand['terminate']                       ={"model":"648X","help":"Terminate this program."}
#####################################################################
##### Commands for model6587
#####################################################################
        lc_deviceCTLSTARSCommand['AbortOHMSAVMode']			        ={"model":"6487","command":":SENS:OHMS:AVOL:ABOR","Parl":"0","WoA":"WR","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Abort A-V ohms mode."}
        lc_deviceCTLSTARSCommand['AbortVoltageSweep']			    ={"model":"6487","command":":SOUR:VOLT:SWE:ABORT","Parl":"0","WoA":"WR","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE1]Sweep commands: Abort sweep. Put source in standby."}
        lc_deviceCTLSTARSCommand['ActivateOHMSAVMode']			    ={"model":"6487","command":":SENS:OHMS:AVOL","Parl":"0","WoA":"WR","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Arm A-V ohms mode."}
        lc_deviceCTLSTARSCommand['ActivateVoltageSweep']			={"model":"6487","command":":SOUR:VOLT:SWE:INIT","Parl":"0","WoA":"WR","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE1]Sweep commands: Arm sweep. Put source in operate."}
        lc_deviceCTLSTARSCommand['ClearDigitalIOTTL']			    ={"model":"6487","command":":SOUR2:CLE","Parl":"0","WoA":"WR","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE2]Clear Digital I/O port immediately."}
        lc_deviceCTLSTARSCommand['ClearOHMSAVBuffer']			    ={"model":"6487","command":":SENS:OHMS:AVOL:CLE","Parl":"0","WoA":"WR","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Clear A-V ohms buffer."}
        lc_deviceCTLSTARSCommand['GetAnalogFilterDampEnable']		={"model":"6487","command":":SENS:DAMP?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SENSE]Amps function: Query analog filter damping: Enable or disable."}
        lc_deviceCTLSTARSCommand['GetCompositeLimitAutoClearEnable']={"model":"6487","command":":CALC2:CLIM:CLE:AUTO?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[CALC2]Composit limits: Query auto-clear state"}
        lc_deviceCTLSTARSCommand['GetCompositeLimitSource2']		={"model":"6487","command":":CALC2:CLIM:PASS:SOURCE2?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[CALC2]Composit limits: Qurey digital I/O output pattern."}
        lc_deviceCTLSTARSCommand['GetDigitalIOTTL4ActiveLevel']		={"model":"6487","command":":SOUR2:TTL4:BST?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE2]Query active TTL level."}
        lc_deviceCTLSTARSCommand['GetDigitalIOTTL4Mode']			={"model":"6487","command":":SOUR2:TTL4:MODE?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE2]Query output line 4 mode."}
        lc_deviceCTLSTARSCommand['GetDigitalIOTTLAutoClearEnable']	={"model":"6487","command":":SOUR2:CLE:AUTO?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE2]Query enable or disable Digital I/O port auto-clear."}
        lc_deviceCTLSTARSCommand['GetDigitalIOTTLDelay']			={"model":"6487","command":":SOUR2:CLE:AUTO:DEL?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE2]Query delay(pulse width) for pass/fail pattern (0 to 60 sec)."}
        lc_deviceCTLSTARSCommand['GetDigitalIOTTLLevel']			={"model":"6487","command":":SOUR2:TTL?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE2]Query specify Digital I/O output value."}
        lc_deviceCTLSTARSCommand['GetLimitTest1MaxSource2']		    ={"model":"6487","command":":CALC2:LIM:UPP:SOURCE2?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[CALC2]Limit 1 Testing: Query upper limit: 4-bit I/O \"fail\" pattern."}
        lc_deviceCTLSTARSCommand['GetLimitTest1MinSource2'] 		={"model":"6487","command":":CALC2:LIM:LOW:SOURCE2?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[CALC2]Limit 1 Testing: Query lower limit: 4-bit I/O \"fail\" pattern."}
        lc_deviceCTLSTARSCommand['GetLimitTest2MaxSource2'] 		={"model":"6487","command":":CALC2:LIM2:UPP:SOURCE2?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[CALC2]Limit 2 Testing: Query upper limit: 4-bit I/O \"fail\" pattern."}
        lc_deviceCTLSTARSCommand['GetLimitTest2MinSource2'] 		={"model":"6487","command":":CALC2:LIM2:LOW:SOURCE2?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[CALC2]Limit 2 Testing: Query lower limit: 4-bit I/O \"fail\" pattern."}
        lc_deviceCTLSTARSCommand['GetOHMSAVBufferAutoClearEnable']	={"model":"6487","command":":SENS:OHMS:AVOL:CLE:AUTO?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Enable or disable auto clear."}
        lc_deviceCTLSTARSCommand['GetOHMSAVCounts']     			={"model":"6487","command":":SENS:OHMS:AVOL:BCO?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SENSE]Amps function: Query filter damping OHMS: number of A-V cycles that have been completed and are averaged to make up present buffer."}
        lc_deviceCTLSTARSCommand['GetOHMSAVCycles']     			={"model":"6487","command":":SENS:OHMS:AVOL:CYCL?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Query number of A-V cycles."}
        lc_deviceCTLSTARSCommand['GetOHMSAVHighVoltage']			={"model":"6487","command":":SENS:OHMS:AVOL:VOLT?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Query high voltage value."}
        lc_deviceCTLSTARSCommand['GetOHMSAVOneshotEnable']  		={"model":"6487","command":":SENS:OHMS:AVOL:ONES?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Query enable or disable one-shot mode."}
        lc_deviceCTLSTARSCommand['GetOHMSAVPoints']			        ={"model":"6487","command":":SENS:OHMS:AVOL:POIN?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Query number of points."}
        lc_deviceCTLSTARSCommand['GetOHMSAVTimeInterval']		    ={"model":"6487","command":":SENS:OHMS:AVOL:TIME?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Query time interval for each phase."}
        lc_deviceCTLSTARSCommand['GetOHMSAVUnits']	    			={"model":"6487","command":":SENS:OHMS:AVOL:UNIT?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Query units."}
        lc_deviceCTLSTARSCommand['GetOHMSModeEnable']   			={"model":"6487","command":":SENS:OHMS?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Query enable or disable."}
        lc_deviceCTLSTARSCommand['GetTraceMode']    				={"model":"6487","command":":TRAC:MODE?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"Query buffer mode: DC(normal) or AVOLtage(A-V ohms)."}
        lc_deviceCTLSTARSCommand['GetVoltageInterlockEnable']		={"model":"6487","command":":SOUR:VOLT:INT?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE1]Query enable or disable voltage interlock state."}
        lc_deviceCTLSTARSCommand['GetVoltageSourceAmplitude']		={"model":"6487","command":":SOUR:VOLT?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE1]Query voltage source amplitude."}
        lc_deviceCTLSTARSCommand['GetVoltageSourceEnable']  		={"model":"6487","command":":SOUR:VOLT:STAT?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE1]Query enable or disable voltage source output state."}
        lc_deviceCTLSTARSCommand['GetVoltageSweepCenterVoltage']	={"model":"6487","command":":SOUR:VOLT:SWE:CENTER?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE1]Sweep commands: Query program center voltage."}
        lc_deviceCTLSTARSCommand['GetVoltageSweepDelay']			={"model":"6487","command":":SOUR:VOLT:SWE:DELAY?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE1]Sweep commands: Query delay."}
        lc_deviceCTLSTARSCommand['GetVoltageSweepSpanVoltage']		={"model":"6487","command":":SOUR:VOLT:SWE:SPAN?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE1]Sweep commands: Query program span voltage."}
        lc_deviceCTLSTARSCommand['GetVoltageSweepStartVoltage']		={"model":"6487","command":":SOUR:VOLT:SWE:STAR?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE1]Sweep commands: Query program start voltage."}
        lc_deviceCTLSTARSCommand['GetVoltageSweepStepVoltage']		={"model":"6487","command":":SOUR:VOLT:SWE:STEP?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE1]Sweep commands: Query program step voltage."}
        lc_deviceCTLSTARSCommand['GetVoltageSweepStopVoltage']		={"model":"6487","command":":SOUR:VOLT:SWE:STOP?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE1]Sweep commands: Query program stop voltage."}
        lc_deviceCTLSTARSCommand['InitTrigger']				        ={"model":"6487","command":"","Parl":"","WoA":"","prefunc":None,"checkfunc":None,"postfunc":None,"help":"Initiate one trigger cycle. Run measurement."}
        lc_deviceCTLSTARSCommand['IsOHMSAVModeActivate']			={"model":"6487","command":":SENS:OHMS:AVOL?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Query if A-V ohms is armed. (1=armed)."}
        lc_deviceCTLSTARSCommand['IsVoltageInterlockFailStatus']	={"model":"6487","command":":SOUR:VOLT:INT:FAIL?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE1]Query voltage interlock state (1 = interlock asserted)."}
        lc_deviceCTLSTARSCommand['IsVoltageSweepStatus']			={"model":"6487","command":":SOUR:VOLT:SWE:STAT?","Parl":"0","WoA":"AT","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[SOURCE1]Sweep commands: Query if sweep running (1 = sweep in progress)."}
        lc_deviceCTLSTARSCommand['ResetCompositeLimit'] 			={"model":"6487","command":":CALC2:CLIM:CLE","Parl":"0","WoA":"WR","prefunc":None,"checkfunc":None,"postfunc":None,"help":"[CALC2]Composit limits: Clear I/O port and restore it back to SOURCE2:TTL settings."}
        lc_deviceCTLSTARSCommand['RunOHMSAVMode']				    ={"model":"6487","command":"","Parl":"","WoA":"","prefunc":None,"checkfunc":None,"postfunc":None,"help":"Arm A-V ohms mode and init."}
        lc_deviceCTLSTARSCommand['RunVoltageSweep']			        ={"model":"6487","command":"","Parl":"","WoA":"","prefunc":None,"checkfunc":None,"postfunc":None,"help":"Arm sweep and init."}
        lc_deviceCTLSTARSCommand['SetAnalogFilterDampEnable']		={"model":"6487","command":":SENS:DAMP","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None,"help":"[SENSE]Amps function: Analog filter damping: Enable or disable."}
        lc_deviceCTLSTARSCommand['SetCompositeLimitAutoClearEnable']={"model":"6487","command":":CALC2:CLIM:CLE:AUTO","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None,"help":"[CALC2]Composit limits: When enabled, I/O port clears when INITiate is sent."}
        lc_deviceCTLSTARSCommand['SetCompositeLimitSource2']		={"model":"6487","command":":CALC2:CLIM:PASS:SOURCE2","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkTTLOutputPatern","postfunc":None,"help":"[CALC2]Composit limits: Define \"pass\" Digital I/O output pattern."}
        lc_deviceCTLSTARSCommand['SetDigitalIOTTL4ActiveLevel']		={"model":"6487","command":":SOUR2:TTL4:BST","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkTTL4ActiveBusyStatus","postfunc":None,"help":"[SOURCE2]Select active TTL level for busy 1 = ON or 0 = OFF."}
        lc_deviceCTLSTARSCommand['SetDigitalIOTTL4Mode']			={"model":"6487","command":":SOUR2:TTL4:MODE","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkTTL4Mode","postfunc":None,"help":"[SOURCE2]Specify output line 4 mode: EOTest ot BUSY."}
        lc_deviceCTLSTARSCommand['SetDigitalIOTTLAutoClearEnable']	={"model":"6487","command":":SOUR2:CLE:AUTO","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None,"help":"[SOURCE2]Enable or disable Digital I/O port auto-clear."}
        lc_deviceCTLSTARSCommand['SetDigitalIOTTLDelay']			={"model":"6487","command":":SOUR2:CLE:AUTO:DEL","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkTTLDelayPatern","postfunc":None,"help":"[SOURCE2]Specify delay(pulse width) for pass/fail pattern (0 to 60 sec)."}
        lc_deviceCTLSTARSCommand['SetDigitalIOTTLLevel']			={"model":"6487","command":":SOUR2:TTL","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkTTLOutputPatern","postfunc":None,"help":"[SOURCE2]Specify specify Digital I/O pattern (0 to 15)."}
        lc_deviceCTLSTARSCommand['SetLimitTest1MaxSource2'] 		={"model":"6487","command":":CALC2:LIM:UPP:SOURCE2","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkSource2","postfunc":None,"help":"[CALC2]Limit 1 Testing: Configure upper limit: Specify 4-bit I/O \"fail\" pattern; 0 to 15."}
        lc_deviceCTLSTARSCommand['SetLimitTest1MinSource2'] 		={"model":"6487","command":":CALC2:LIM:LOW:SOURCE2","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkSource2","postfunc":None,"help":"[CALC2]Limit 1 Testing: Configure lower limit: Specify 4-bit I/O \"fail\" pattern; 0 to 15."}
        lc_deviceCTLSTARSCommand['SetLimitTest2MaxSource2'] 		={"model":"6487","command":":CALC2:LIM2:UPP:SOURCE2","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkSource2","postfunc":None,"help":"[CALC2]Limit 2 Testing: Configure upper limit: Specify 4-bit I/O \"fail\" pattern; 0 to 15."}
        lc_deviceCTLSTARSCommand['SetLimitTest2MinSource2'] 		={"model":"6487","command":":CALC2:LIM2:LOW:SOURCE2","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkSource2","postfunc":None,"help":"[CALC2]Limit 2 Testing: Configure lower limit: Specify 4-bit I/O \"fail\" pattern; 0 to 15."}
        lc_deviceCTLSTARSCommand['SetOHMSAVBufferAutoClearEnable']	={"model":"6487","command":":SENS:OHMS:AVOL:CLE:AUTO","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Enable or disable A-V buffer auto clear."}
        lc_deviceCTLSTARSCommand['SetOHMSAVCycles']     			={"model":"6487","command":":SENS:OHMS:AVOL:CYCL","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkOHMSAVCycles","postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Set number of A-V cycles (1 to 9999)."}
        lc_deviceCTLSTARSCommand['SetOHMSAVHighVoltage']			={"model":"6487","command":":SENS:OHMS:AVOL:VOLT","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkVoltage","postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Set high voltage value (-505 to 505V)."}
        lc_deviceCTLSTARSCommand['SetOHMSAVOneshotEnable']  		={"model":"6487","command":":SENS:OHMS:AVOL:ONES","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Enable or disable one-shot mode."}
        lc_deviceCTLSTARSCommand['SetOHMSAVTimeInterval']   		={"model":"6487","command":":SENS:OHMS:AVOL:TIME","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkOHMSAVTimeInterval","postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Set time interval for each phase."}
        lc_deviceCTLSTARSCommand['SetOHMSAVUnits']  				={"model":"6487","command":":SENS:OHMS:AVOL:UNIT","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkOHMSUnits","postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Select AMPS or OHMS units."}
        lc_deviceCTLSTARSCommand['SetOHMSModeEnable']   			={"model":"6487","command":":SENS:OHMS","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None,"help":"[SENSE]Amps function: OHMS mode command: Enable or disable."}
        lc_deviceCTLSTARSCommand['SetVoltageInterlockEnable']		={"model":"6487","command":":SOUR:VOLT:INT","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None,"help":"[SOURCE1]Enable or disable voltage interlock for 10V range."}
        lc_deviceCTLSTARSCommand['SetVoltageSourceAmplitude']		={"model":"6487","command":":SOUR:VOLT","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkVoltSourceAmplitude","postfunc":None,"help":"[SOURCE1]Set voltage source amplitude (-500 to 500)."}
        lc_deviceCTLSTARSCommand['SetVoltageSourceCurrentLimit']	={"model":"6487","command":":SOUR:VOLT:ILIM","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkVoltSourceILimit","postfunc":None,"help":"[SOURCE1]Set voltage source current limit."}
        lc_deviceCTLSTARSCommand['SetVoltageSourceEnable']  		={"model":"6487","command":":SOUR:VOLT:STAT","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkONOFF","postfunc":None,"help":"[SOURCE1]Enable or disable voltage source output state."}
        lc_deviceCTLSTARSCommand['SetVoltageSourceRange']   		={"model":"6487","command":":SOUR:VOLT:RANG","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkVoltSourceRange","postfunc":None,"help":"[SOURCE1]Set voltage source range."}
        lc_deviceCTLSTARSCommand['SetVoltageSweepCenterVoltage']	={"model":"6487","command":":SOUR:VOLT:SWE:CENTER","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkVoltage","postfunc":None,"help":"[SOURCE1]Sweep commands: Set program center voltage (-505 to 505V)."}
        lc_deviceCTLSTARSCommand['SetVoltageSweepDelay']			={"model":"6487","command":":SOUR:VOLT:SWE:DELAY","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkVoltageSweepDelay","postfunc":None,"help":"[SOURCE1]Sweep commands: Set delay (0 to 999.9999s)."}
        lc_deviceCTLSTARSCommand['SetVoltageSweepSpanVoltage']		={"model":"6487","command":":SOUR:VOLT:SWE:SPAN","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkVoltage","postfunc":None,"help":"[SOURCE1]Sweep commands: Set program span voltage (-505 to 505V)."}
        lc_deviceCTLSTARSCommand['SetVoltageSweepStartVoltage'] 	={"model":"6487","command":":SOUR:VOLT:SWE:STAR","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkVoltage","postfunc":None,"help":"[SOURCE1]Sweep commands: Set program start voltage (-505 to 505V)."}
        lc_deviceCTLSTARSCommand['SetVoltageSweepStepVoltage']		={"model":"6487","command":":SOUR:VOLT:SWE:STEP","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkVoltage","postfunc":None,"help":"[SOURCE1]Sweep commands: Set program step voltage (-505 to 505V)."}
        lc_deviceCTLSTARSCommand['SetVoltageSweepStopVoltage']		={"model":"6487","command":":SOUR:VOLT:SWE:STOP","Parl":"1","WoA":"WR","prefunc":None,"checkfunc":"dc._checkVoltage","postfunc":None,"help":"[SOURCE1]Sweep commands: Set program stop voltage (-505 to 505V)."}



#        self._frontchannelname = 'DMM'
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
            errormsg = 'Er: Bad parameter. %s range is from %s to %s.' %(str(val), str(minval), str(maxval))
        return(rt,errormsg)

    def _sub_checkisfloat(self,cmd,args):
        val = args[0].upper()
        rt = ''
        errormsg = "Er: Bad parameter. Not float.(%s)" %(val)
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
        errormsg = "Er: Bad parameter. Not integer.(%s)" %(val)
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
# Program m6485drv.py
#----------------------------------------------------------------
if __name__ == "__main__":
    ##################################################################
    # Import modules
    ##################################################################
    import sys
    import os
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
    gb_ChannelNameSeqList = []
    gb_ChannelNameList = {}
    gb_StarsInstance = None
    gb_DeviceInstance = None
    gb_RegInstance = None         # Cache instance  for 7700, 20220311
    gb_StarsLocalBusyFlg   = 0
    gb_StarsLastSendBusyFlg = -1
    gb_DelimiterOfGetValues = ','
    gb_DelimiterApplyNodeList = {}
    gb_RawCommandEnable = False
    gb_rawE = False

    gb_CheckTriggerFlag = ''             # 20220616
    gb_devicetype = ''                  # 20220708

    # Define: Appliction default parameters
    starsServerHost = 'localhost'
    starsNodeName   = 'tdkzplus'
    starsServerPort = 6057
    #deviceHost = '192.168.11.122'  # m6485drv IP-address     20220509
    deviceHost = '172.16.0.101' #169.254.9.35
    devicePort = 4001  # m6485drv Port    20220509
    #devicePort = 1394  #8003
    modeofgetsetvalue = 'CC'

# a flg for IsBusy 20220315
#    Is_busyflg = 0
#    Is_eventsE = 'ON'
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
#
        global gb_RegInstance       #20220415, to add GenerateConfigFile
        global gb_userconfigfile    #20220415, to add GenerateConfigFile 
#
        global gb_RawCommandEnable              # 20220613  setting information written in config.cfg
        global gb_rawE                          # 20220614  setting information by input option 
#
        global gb_CheckTriggerFlag              # 20220616 
#
        global gb_devicetype

        dc = gb_DeviceInstance
        st = gb_StarsInstance
        dtp = gb_devicetype
        destsendstr='';
#
        _devacc = 0
        _cmd =''
        _cmdd = ''
#
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
        print('\n' + ' <<<   ---  command parameter  ---   >>>>>>>>>> ' + str(message) + '\n')     # for making sure 20220704
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
        if(allmess.nodeto.startswith(st.nodename+'.')):
             channelname=allmess.nodeto.replace(st.nodename+'.','')
             _outputlog(DEBUG, "Debug: Channel coming" + channelname)

        elif(allmess.nodeto == st.nodename):    # correct 20220509
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
                clist1=sorted(dc.get_starscommandlist(dtp))                                                 # corrected on 20220715 for shared support for 6485 and 6487
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + ' '.join(clist1)
            elif(command == 'help' and len(parameters) == 1):
                _rt=parameters[0]
                rt=dc.get_starscommandhelp(_rt,dtp)                                                         # corrected on 20220715 for shared support for 6485 and 6487
                if(str(rt) == 'False'):
                    destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Er: Bad command or no supported command'
                else:
                    destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + rt
            elif(message == 'Local'):
                rt = dc.Golocal()
                _devacc = 1
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(message == 'Reset'):
                _loadconfig = 'on'
                _autoset = 'on'
                _cmd = ':*RST'
                rt = dc.devReset(_loadconfig,_autoset,_cmd,dtp)
                _devacc = 1
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(message == 'Preset'):
                _loadconfig = 'off'
                _autoset = 'on'
                _cmd = ':SYST:PRES'
                rt = dc.devReset(_loadconfig,_autoset,_cmd,dtp)
                _devacc =1
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(command == 'LoadUserSetup' and len(parameters) == 1 ):
                _loadconfig = 'off'
                _autoset = 'on'
                _parack = dc._checkUSERMemory(parameters[0],'','')
                if(_parack == 'STAT_OK'):
                    _cmd = ':*RCL ' + parameters[0]
                    rt = dc.loadUReset(_loadconfig,_autoset,_cmd,dtp)       # 20220711
                else:
                    rt = _parack
                _devacc = 1
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(message == 'GoIdle'):
                rt = dc.dev2Idle()
                _devacc =1
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(message == 'TriggerRun'):
                _autoset = 'on'
                dc.dev2Idle()
                if( gb_CheckTriggerFlag == 'NG' ):
                    gb_CheckTriggerFlag = dc.TriggerEnvCheck(_autoset,dtp)
                if( gb_CheckTriggerFlag == 'OK' ):
#                    dc.device_send(':INIT')
                    dc.sampleINIT()
                    rt = dc.donecheck()
                else:
                    rt = 'Er: not ready for mesurement'
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(message == 'InitTrigger'):
                if( dtp != 6487):
                    rt = 'Er: not supported'
                else:
                    rt = dc.dev2Idle(cfg=1)
                    rt = dc.device_send(':INIT')
#                    rt = dc.donecheck()            # temp 20220805
                _devacc = 0             # after (:INIT)command, not checked due to processing time issues
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt + 'Please wait for the prescribed time required for INIT processing.'
            elif(message == 'RunVoltageSweep'):
                if( dtp != '6487'):
                    rt = 'Er: not supported'
                else:
                    rt = dc.device_send(':SOUR:VOLT:SWE:INIT')
                    rt = dc.donecheck()
                    rt = dc.device_send(':INIT')
#                    rt = dc.donecheck()            # temp 20220805
                _devacc = 0             # after (:INIT)command, not checked due to processing time issues
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt + 'Please wait for the prescribed time required for INIT processing.'
            elif(message == 'RunOHMSAVMode'):
                if( dtp != '6487'):
                    rt = 'Er: not supported'
                else:
                    rt = dc.device_send(':SENS:OHMS:AVOL')
                    rt = dc.donecheck()
                    rt = dc.device_send(':INIT')
#                    rt = dc.donecheck()            # temp 20220805
                _devacc = 0             # after (:INIT)command, not checked due to processing time issues
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt + 'Please wait for the prescribed time required for INIT processing.'

            elif( message == 'Run' ):
                _rtc = 2500
                if( dtp == '6487'):
                    _rtc = 3000
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Er: Bad parameter. As a parameter, specify value of tracepoint(s) ; 1 to ' + str(_rtc) +'.'
            elif(command == 'Run' and len(parameters) == 1):
                _rtc = 2500
                if( dtp == '6487'):
                    _rtc = 3000
                _autoset = 'off'
                rt = dc.dev2Idle()
                gb_CheckTriggerFlag = dc.TriggerEnvCheck(_autoset,dtp)
                if( gb_CheckTriggerFlag == 'Ng:'):
                    destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ER: not ready for mesurement'
                else:
                    try:
                        _ckdti = float(parameters[0])
                    except TypeError:
                        destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Er: Bad parameter. As a parameter, specify value of tracepoint(s) ; 1 to ' + str(_rtc) +'.'
                    if( _ckdti >=1 and _ckdti <= _rtc):
                        _cmd = ':TRAC:FEED:CONT NEV'
                        rt = dc.device_send(_cmd)
                        rt = dc.donecheck()
                        _cmd = ':TRAC:POIN ' + parameters[0]
                        rt = dc.device_send(_cmd)
                        rt = dc.donecheck()
                        rt = dc.device_send(':TRAC:FEED:CONT NEXT')
                        rt = dc.donecheck()
                        rt = dc.device_send(':INIT')
#                            rt = dc.donecheck()            # temp 20220805
                        _devacc = 0             # after (:INIT)command, not checked due to processing time issues
                        destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt + 'Please wait for the prescribed time required for INIT processing.'
                    else:
                        destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Er: Bad parameter. As a parameter, specify value of tracepoint(s) ; 1 ' + str(_rtc) +'.'


            elif(message == 'GetValue' ):
                _autoset = 'on'
                if( gb_CheckTriggerFlag == 'NG' ):
                    gb_CheckTriggerFlag = dc.TriggerEnvCheck(_autoset,dtp)
                if( gb_CheckTriggerFlag == 'OK' ):
                    rt = dc.device_act(':READ?')
                else:
                    rt = 'Er: not ready for measurement'
                _devacc = 1
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(command == 'SendRawCommand'):
#            elif(command == 'SRawC'):
                if((parameter != '') and (gb_RawCommandEnable == True)):
                    if('?' in parameter):
                        rt=dc.device_act(parameter)
                    else:
                        rt=dc.device_send(parameter)
                    destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
                else:
                    destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Er: Bad command or parameter.'
                _devacc = 1
            elif(message == 'terminate'):
                st.terminateMainloop()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Ok:'              
## for m6485 20220509 ->
            else:
                _sstl = dc.is_commandfined(command)
                val1 = ''
                val2 = ''
                _rt = 'Ok:'
                _devacc =1
                if( _sstl != False ):
########################## devicetype check
                    _modeltypc = dc._deviceCTLSTARSCommand[command]["model"]
                    if ( dtp != _modeltypc and _modeltypc != '648X'):
                        _rt = 'Er: The command set not supported by the current device.'
                        destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
#########################
                    else:
                        _scpcmd = _sstl.split('_')
                        _cmd = _scpcmd[1]
                        if(parameter != ''): 
                            if( '?'in _cmd):
                                _rt = 'Er: parameter not required'
                                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
                            # case with some parameters
                            elif((len(parameters) == 1) and (_scpcmd[2] == '1')):
                                _cmd = _cmd + ' ' + parameters[0]
                                val1 = parameters[0]
                                val2 = None
                            elif((len(parameters) == 2) and (_scpcmd[2] == '2')):                                   # It corresponds to two parameters,but there are no case two parameters in the command table.
                                _cmd = _cmd + ' ' + parameters[0] + ' ' + parameters[1]
                                val1 = parameters[0]
                                val2 = parameters[1]
                            else:
                                _rt = 'Er: Bad command or parameter.'
                                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
                        else:                                                                                       # case with no parameter
                            if(len(_scpcmd) == 3 ):
                                _rt = 'Er: Parameter are required.'
                                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
############################ pri-function , check-function
                    if(_rt == 'Ok:'):
                        if(dc._deviceCTLSTARSCommand[command]["prefunc"] != None):
                            _ckr = eval(dc._deviceCTLSTARSCommand[command]["prefunc"])()
                            if('STAT_ERR' in str(_ckr)):
                                _rt = 'Er: ' + _ckr
                                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
                    if(_rt == 'Ok:'):
                        if(dc._deviceCTLSTARSCommand[command]["checkfunc"] != None):
                            _ckr = eval(dc._deviceCTLSTARSCommand[command]["checkfunc"])(val1,val2,dtp)
                            if('STAT_ERR' in str(_ckr)):
                                _rt = 'Er: ' + _ckr
                                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
############################ command excution
                    if( _rt == 'Ok:' ): 
                        _cmdd = _cmd
                        if(_scpcmd[0] == 'WR'):
                            dc.device_send(_cmdd)
                            rt = dc.donecheck()
                            destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
                        elif(_scpcmd[0] == 'AT'):
                            rt = dc.device_act(_cmdd)
                            destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
############################ postfunction
                            if(dc._deviceCTLSTARSCommand[command]["postfunc"] != None):
                                _ckr = eval(dc._deviceCTLSTARSCommand[command]["postfunc"])(rt)
                                if('STAT_ERR' in _ckr):
                                    rt = 'Er: ' + _ckr
                else:
                    destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Er: Bad command or parameter.'
##################################################################################################################################################
# device command processing error check ;_devacc = 1 : Check command processing result, _devacc = 0 : Do not check command processing results
########################### After (:INIT)command, not checked due to processing time issues
        if(':INIT' in _cmdd):
            _devacc = 0
            destsendstr = destsendstr + 'Please wait for the prescribed time required for INIT processing.'
        if( (command == 'SRawC') and ':INIT' in parameters[0]):
            _devacc = 0 
            destsendstr = destsendstr + 'Please wait for the prescribed time required for INIT processing.'
########################### excution check #######################################################################################################
        if( ('Er:' not in destsendstr) and (_devacc == 1)):
            _eck = dc.device_act(':SYST:ERR?')
            if('No error' not in _eck):
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '  Er: ' + _eck
            if( 'Timeout' in _eck):
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '  Er: Unable to get Error Status due to device timeout.'
        elif( ('Timeout' in destsendstr) and (_devacc == 1)):
            _eck = dc.device_act(':SYST:ERR?')
            if('No error' not in _eck):
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '  Er: Timeout caused by ' + _eck
            if( 'Timeout' in _eck):
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '  Er: Unable to get Error Status due to device timeout.'
############################### 20220711
                
        if(destsendstr != ''):
            _outputlog(INFO,'STARS Send[' +st.nodename + "]:"+destsendstr)
            rt=st.send(destsendstr)
            if(rt==False):
                st.terminateMainloop()
        return


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
 		 
    def savecache():
        global gb_RegInstance
        reg = gb_RegInstance
        b = reg.savecache()
        if(b):
            rt='Ok:' 
        else:
            rt = 'Er: %s' %(reg.getlasterrortext())
        return(rt)
 		 


 	##################################################################    

    # Define program arguments
    ##################################################################
    
    lc_RegFileName = None                   # added on 20220607 for the file of reg.txt 

#    optIO=pystarsutilargparser.PyStarsUtilArgParser(numberOfDeviceServer=1)    # 20220613
    optIO=pystarsutilargparser.PyStarsUtilArgParser()                           # 20220613
    parser=optIO.generate_baseparser(prog=gb_ScriptName,version=__version__)

    ##################################################################
    # Parse program arguments
    ##################################################################
    args=parser.parse_args()

    gb_rawE = args.rawenable                # 20220614

    gb_Debug=args.debug
    if(gb_Debug==True):
        sys.stdout.write(str(args)+'\n')
    # Fix StarsNodename
    starsNodeName = optIO.get(args.StarsNodeName,starsNodeName)

    # Read configfile if detected
    configfilename = None                   # added on 20220608 for the file of reg.txt
    if(os.path.isfile('./config.cfg')):     # added on 20220608 for the file of reg.txt
        configfilename = './config.cfg'     # added on 20220608 for the file of reg.txt
    configFileName = optIO.get(args.Config,configfilename)  # chenged on 20220608 for the filr of reg.txt
    lc_numberOfChannels=-1                 # corrected on 20220608
    lc_ChannelNameList=None                # corrected on 20220608
    lc_ChannelTargetNoList=None            # corrected on 20220608
    lc_DelimiterApplyNodeList = None       # corrected on 20220608
    lc_DelimiterOfGetValues = None         # corrected on 20220608

#    if(configFileName == ' '):     # alterlation 20220411 '' -> ' '    # corrected on 20220608
    if(configFileName is not None):
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
        lc_numberOfChannels    = cfgIO.get(starsNodeName, 'NumberOfChannels'    , lc_numberOfChannels, int)    # corrected on 20220608
        lc_ChannelNameList     = cfgIO.get(starsNodeName, 'ChannelNameList'     , lc_ChannelNameList)          # corrected on 20220608
        lc_ChannelTargetNoList = cfgIO.get(starsNodeName, 'ChannelTargetNoList' , lc_ChannelTargetNoList)      # corrected on 20220608

        lc_RegFileName = cfgIO.get(starsNodeName, 'RegFileName', lc_RegFileName)        # added on 20220608 for the file of reg.txt
        gb_RawCommandEnable = cfgIO.get(starsNodeName,'RawEnable', gb_RawCommandEnable, bool)   #added on 20220613
    # Fix optional parameters
    if(gb_rawE == False):
        gb_rawE = None
    gb_RawCommandEnable = optIO.get(gb_rawE,gb_RawCommandEnable)
    starsServerHost = optIO.get(args.StarsServerHost,starsServerHost)
    starsServerPort = optIO.get(args.StarsServerPort,starsServerPort)
    deviceHost      = optIO.get(args.DeviceHost,deviceHost)
    devicePort      = optIO.get(args.DevicePort,devicePort)

    if(gb_Debug==True):
        sys.stdout.write("starsNodeName#"+str(starsNodeName)+"#"+'\n')
        sys.stdout.write("starsServerHost#"+str(starsServerHost)+"#"+'\n')
        sys.stdout.write("starsServerPort#"+str(starsServerPort)+"#"+'\n')
        sys.stdout.write("deviceHost#"+str(deviceHost)+"#"+'\n')
        sys.stdout.write("devicePort#"+str(devicePort)+"#"+'\n')
        sys.stdout.write("numberOfChannels#"+str(gb_NumberOfChannels)+"#"+'\n')
        sys.stdout.write("channelNameList#"+str(gb_ChannelNameList)+"#"+'\n')

    ##################################################################
    # Main process: Start
    ##################################################################
    ######!!!!!!!!!!!!!
    # Regarding the handling of Reg.txt, it is necessary to review and fix it.
    ######
    regFileName = lc_RegFileName                    # added on 20220608 for the file of reg.txt
    if(regFileName is None):                        # added on 20220608 for the file of reg.txt
        regFileName = './reg.txt'                   # corrected on 20220608 for the file of reg.txt
    rc = libstreg.libstreg(regFileName)             # corrected on 20220608 for the file of reg.txt
    gb_RegInstance = rc                             # corrected on 20220608 for the file of reg.txt
    rt = rc.loadcache()                             # corrected on 20220608 for the file of reg.txt
    if('Er:' in str(rt)):                           # if(rt == False): # ? 20230330
        if(lc_RegFileName is not None):             # added on 20220608 for the file of reg.txt
            sys.stdout.write(rt+'\n')               # corrected on 20220608 for the file of reg.txt
            exit(1)                                 # corrected on 20220608 for the file of reg.txt
    dictd = rc._CACHEORIGINAL                       # added on 20220610 for the file of reg.txt
    dictk = rc.getallkeys()                         # added on 20220610 for the filr of reg.txt
    ######!!!!!!!!!!!!!
   
    #Create device instance with devserver:devport 
    dc=PyStarsDeviceKEITHLEY6485(deviceHost, devicePort)
    gb_DeviceInstance=dc

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
###
#   access start
######################
    tpckrt = dc.checkstart()
    if(tpckrt==False):
        sys.stdout.write('  --->> The device is different.'+'\n')
        exit(1)
    else:
        gb_devicetype = tpckrt          # gb_devicetype = 85 or 87 ; 85:device=model6485,  87:device=model6485
######################
#
################################################################
# setting at startup  ~~ load SCPIcommand from {ex).reg.txt} and set to device  20220610  -->
###
    rt = dc.setstartup(dictk,dictd)
    if(rt=='Failure'):
        sys.stdout.write(st.getlasterrortext()+'\n')
###
#     <-- 20220610
#################################################################
#  setting a suitable enviroment to measure  20220616 -->
###
    _autoset = 'off'         # Automatic set instruction flag in case of error
    gb_CheckTriggerFlag = dc.TriggerEnvCheck(_autoset,tpckrt)
###
#  <-- 20220616
#################################################################

    #Start Mainloop()
#for check into mainloop
    print('<<<<<< mainloop started >>>>>>' + '\n')    # for making sure 20220704
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
