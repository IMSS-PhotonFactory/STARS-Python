#! /usr/bin/python3
""" STARS Python Interface extended from 'stars.py': Support STARS perl-style functions.

    Description: In addition to basic Python STARS features, some APIs are added referring to the STARS perl library 'stars.pm'.

    History:
        0.1    Beta version     2016.11.09    Yasuko Nagatani
        
        0.2    Support STARS python library ver 0.201 or later    2017.02.17    Yasuko Nagatani
"""

# Define: program info
__author__ = 'Yasuko Nagatani'
__version__ = '0.2'
__date__ = '2017-02-17'
__license__ = 'MIT'

import sys
import socket
import select
import time
import types
import stars

#----------------------------------------------------------------
# Class StarsInterface
#----------------------------------------------------------------
class StarsInterface(stars.StarsInterface):
    """ Class StarsInterface: Derived from basic STARS Interface

          Parameters:
            nodename -- (string) is so-called 'STARS nodename'.

            srvhost  -- (string) is the IP address or the hostname of STARS server.
            
            keyfile  -- (optional string) is the filepath of the STARS keyfile. If omitted, nodename + '.key' will be used.

            srvport  -- (optional integer) is the port value of STARS server. If omitted, 6057(=DEFAULT_PORT) will be used.


    """
    
    DEFAULT_INTERVALTIME =    1

    #----------------------------------------------------------------
    # Initialize: Inherited from basic STARS Interface
    #----------------------------------------------------------------
    def __init__(self, nodename, srvhost, keyfile = '', srvport = stars.StarsInterface.DEFAULT_PORT):
        """ __init__ : Inherited from basic STARS Interface.

              Parameters:
                nodename -- (string) is so-called 'STARS nodename'.

                srvhost  -- (string) is the IP address or the hostname of STARS server.

                keyfile  -- (optional string) is the filepath of the STARS keyfile. If omitted, nodename + '.key' will be used.

                srvport  -- (optional integer) is the port value of STARS server. If omitted, 6057 will be used.
        """
        stars.StarsInterface.__init__(self, nodename, srvhost, keyfile, srvport)
        self._readable = []
        self._intervaltime = StarsInterface.DEFAULT_INTERVALTIME
        self._termsignal = False
        self._selfTest = False
        if(hasattr(self,'_handler')==False):
            self._handler = {}
        if(hasattr(self,'_mode')==False):
            self._mode = {}

    #****************************************************************
    # Property functions: Newly added in this library.
    #****************************************************************
    def setintervaltime(self, intervaltime):
        """ setintervaltime: Change interval time value referenced in the function Mainloop().

              Parameters:
                 intervaltime -- (float,int) is used as the interval time value(in seconds) at Mainloop(). The initialized value is 1 seconds(=DEFAULT_INTERVALTIME).
              Returns:
                (bool) True if the interval time value is valid, otherwise False.
        """
        if(isinstance(intervaltime, int) or isinstance(intervaltime, float) or (sys.version_info.major<3 and isinstance(intervaltime, long))):
            if(intervaltime>0):
                self._intervaltime = intervaltime
                return True;
            else:
                rt="setintervaltime value invalid. (%s)" %(intervaltime)
                self.error = "%s" %(rt)
                self._debugprint("[setintervaltime] (%s)\n" %(self.error))
                return(False)
        rt="setintervaltime type invalid. (%s)" %(type(intervaltime))
        self.error = "%s" %(rt)
        self._debugprint("[setintervaltime] (%s)\n" %(self.error))
        return(False)

    def getintervaltime(self):
        """ getintervaltime: Return the current interval time value(in seconds) referenced in the function Mainloop().

              Returns:
                (numeric) the current interval time value(in seconds). 
        """
        return(self._intervaltime)

    #----------------------------------------------------------------
    # act: Newly added in this library.
    #----------------------------------------------------------------
    def act(self, sendmesg, timeout = '', exceptionret = stars.StarsMessage('')):
        """ act: Send STARS message and receive from STARS Server.

              Parameters:
                timeout -- (optional float,int) is the requested timeout(in seconds). If omitted, the value of stars.getdefaultreceivetimeout() will be used..

                exceptionret -- (optional object) is used as the return value when the fatal error deteceted. StarsMessage('') is the default value.

              Returns:
                (StarsMessage object) received data.

                (StarsMessage object) if the socket timeout detected, return StarsMessage('').

                The value of 'exceptionret' when the fatal error(kind of connection lost, timeout value error...) detected. 
        """
        fh = self.gethandle()
        if(fh is not None):
            if(hasattr(self,'_handler')):
                hd=self._handler.get(fh, None)

            ### Set timeout.
            if(timeout is None):
                self.error = "timeout value invalid. (None)"
                self._debugprint("[act] (%s)\n" %(self.error))
                return(exceptionret)
            elif(timeout == ''):
                timeout = self.getdefaultreceivetimeout()
            try:
                self.s.settimeout(timeout)
            except Exception as e:
                self._lastexception = sys.exc_info()
                rt="settimeout failure. (%s)" %(type(e))
                self.error = "%s" %(rt)
                self._debugprint("[Recv] (%s)\n" %(self.error))
                return(exceptionret)

            ### Send
            rt=self.send(sendmesg)
            if(rt == False):
                return(exceptionret)

            ### Receive
            lap=0
            while(True):
                if((timeout-lap)<=0):
                    break
                timebase = time.time()
                rmsg = self.receive(timeout-lap, None)
                lap=lap + time.time()-timebase
                if(rmsg is None):
                    return(exceptionret)
                if(rmsg == ''):
                    continue
                if(rmsg.command.startswith('@')):
                    return(rmsg)
                if(hd is not None):
                    hd(rmsg, fh)
            self.error = 'Timeout'
            return(stars.StarsMessage(''));
        return(exceptionret)

    #----------------------------------------------------------------
    # Callback functions: Newly added in this library.
    #----------------------------------------------------------------
    def addcallback(self, handler, fh=None, mode=None):
        """ addcallback: Assosiates the callback function to the socket readable event. See also removecallback() and Mainloop().

              Parameters:
                hander is a python 'callable' function. See the 'mode' parameter about the arguments of the function.

                fh -- (optional socket object) is the socket to be monitored. If omitted or None, use the STARS socket. When the socket 'fh' gets readable, the function 'handler' will be called.

                mode -- (optional) The arguments of the handler depends on the mode value as follows.

                    If mode value is 'STARS', the handler takes arguments (STARSMessage stmess, (socket object) fh)

                    If mode value is 'DIRECT', the handler takes arguments (string mess, (socket object) fh)

                    If mode value is 'DETECT', the handler takes arguments ((socket object) fh)

                    If omitted or None, same as 'STARS'.

              Returns:
                (bool) True if set properly, otherwise False.
        """
        if(fh is None):
            fh = self.gethandle()
            if(fh is None):
                rt="The STARS socket not found."
                self.error = "%s" %(rt)
                return(False)
        if(mode is None):
            mode = 'STARS'
        mode = mode.upper()
        if(mode == 'DIRECT'):
            rt=True
        elif(mode == 'DETECT'):
            rt=True
        elif(mode == 'STARS'):
            rt=True
        else:
            self.error="Set mode from among 'DETECT','DIRECT','STARS'"
            return(False)
        self._handler.update({fh:handler})
        self._mode.update({fh:mode})
        self._readable.append(fh)
        if(self._selfTest):
            self._debugprint("[addcallback] Assosiate handler to %s as %s\n" %(fh,mode))
        return(True)

    def removecallback(self,fh=None):
        """ removecallback: Removes from the socket readable monitoring list. See also addcallback() and Mainloop().

              Parameters:
                fh -- (optional socket object) is the socket object to be removed from the monitoring list. If omitted or None, use the STARS socket.

              Returns:
                (bool) True if the socket object has removed from the monitoring list. If False returned, it means the socket object 'fh' is not on the monitoring list.
        """
        rt=True
        if(fh is None):
            fh = self.gethandle()
            if(fh is None):
                rt="The STARS socket not found."
                self.error = "%s" %(rt)
                return(False)
        try:
            self._readable.remove(fh)
        except ValueError:
            pass
        except Exception as e:
            self._lastexception = sys.exc_info()
            self.error="Unable to remove socket from the monitoring list. (%s)" %(type(e))
            self._debugprint("%s\n" %self.error)
            self._debugprint("%s\n" %(e))
            rt=False
        if(hasattr(self,'_handler')==True):
            hd=self._handler.get(fh, None)
            if(hd is not None):
                self._handler.pop(fh)
        if(hasattr(self,'_mode')==True):
            md=self._mode.get(fh, None)
            if(md is not None):
                self._mode.pop(fh)
        return(rt)

    #----------------------------------------------------------------
    # Mainloop: Newly added in this library.
    #----------------------------------------------------------------
    def terminateMainloop(self):
        """ terminateMainloop: Terminate(Exit from) the socket monitoring loop in the function Mainloop().
        """
        self._termsignal = True
        return

    def Mainloop(self, inthandler=None, intervaltime = ''):
        """ Mainloop: Start monitoring the readable sockets and executes the assosiated callback function. To terminate this function, use the function terminateMainloop(). See also addcallback() and removecallback().

              Attention: Mainloop() runs in the same thread. (Not multi-thread)

              Parameters:
                inthander is a python 'callable' function executed at intervals. If omitted, no function will be executed at intervals. See the 'intervaltime' parameter about the interval time.

                intervaltime -- (float,int) is the interval time value(in seconds) used for executing the function 'inthandler'. If omitted, the value of the function getintervaltime() will be used. Furthermore the interval time value can be changable by the function setintervaltime() after call Mainloop().

              Returns:
                (bool) False if the error detected before start monitoring the socket, othewise True.

        """
        originalintervaltime=self.getintervaltime()
        if(intervaltime == ''):
            intervaltime=originalintervaltime
        else:
            rt=self.setintervaltime(intervaltime)
            if(rt == False):
                return(rt)

        bufsize = StarsInterface.TCP_BUFFER_SIZE
        readfds = self._readable;

        prevtimeout= intervaltime
        fintimeout = -1
        timeoutbuf = 0.04

        timebase = time.time()
        while(self._termsignal==False):
            #Check existing no socket
            if(len(readfds) <= 0):
                #self._debugprint("No socket. force exit\n")
                #self.terminateMainloop()
                #continue
                if(self._intervaltime>0):
                    time.sleep(self._intervaltime)
                    self._debugprint("No reable socket. Sleep:%s sec\n" %self._intervaltime)
                if(inthandler is not None):
                    timelap= time.time()-timebase
                    if(self._selfTest):
                        self._debugprint("Call INT handler Lap:%s>=Int:%s.\n" %(timelap,self._intervaltime))
                    timebase =  time.time()
                    inthandler()
                continue
            if(fintimeout<=0 or (self._intervaltime != prevtimeout)):
                fintimeout=self._intervaltime
            while(fintimeout>=0):
                if(self._termsignal):
                    break
                if(fintimeout>0.04):
                    timeoutval = 0.04
                else:
                    timeoutval = fintimeout
                try:
                    rready, wready, xready = select.select(readfds, [], [], timeoutval)
                    if(len(rready) <= 0):
                        fintimeout=fintimeout-0.04
                        continue
                    break
                except Exception as e:
                    self._lastexception = sys.exc_info()
                    self.error="Socket select error. (%s)" %(type(e))
                    self._debugprint("%s\n" %(self.error))
                    self.terminateMainloop()
                    break
            if(self._termsignal):
                continue
            if(len(rready) <= 0):
                if(inthandler is not None):
                    timelap=time.time()-timebase
                    if(self._selfTest):
                        self._debugprint("Call INT2 handler Lap:%s>=Int:%s.\n" %(timelap,self._intervaltime))
                    timebase = time.time()
                    ### execute inthandler
                    inthandler()
                continue
            #Process read socket
            rmsg = ''
            for sock in rready:
                ### terminate force loop
                if(self._termsignal==True):
                    break
                hd = None
                md = None
                sbuf = ''
                if(hasattr(self,'_handler')):
                    hd=self._handler.get(sock, None)
                if(hasattr(self,'_mode')):
                    md=self._mode.get(sock, 'STARS')

                #Mode DETECT: skip read and just call handler to notify.
                if(md == 'DETECT'):
                    if(hd is not None):
                        if(self._selfTest):
                            self._debugprint("Call DETECT handler\n")
                        hd(sock)
                    continue

                #Read socket
                rmsg = ''
                try:
                    sock.settimeout(stars.StarsInterface.DEFAULT_TIMEOUT)
                except Exception as e:
                    pass
                try:
                    rmsg = sock.recv(stars.StarsInterface.TCP_BUFFER_SIZE).decode()
                except Exception as e:
                    self._lastexception = sys.exc_info()
                    self.error="Socket recv error. (%s)" %(type(e))
                    self._debugprint("%s\n" %(self.error))
                    rmsg=''
                    if(md == 'STARS'):
                        rmsg = stars.StarsMessage(rmsg)
                    if(hd is not None):
                        hd(rmsg, sock)
                    continue
                if(len(rmsg) == 0):
                    self.error = 'Lost connection.'
                    self._debugprint("Connection closed from remote.\n")
                    rmsg=''
                    if(md == 'STARS'):
                        rmsg = stars.StarsMessage(rmsg)
                    if(hd is not None):
                        hd(rmsg, sock)
                    continue
                #Mode STARS
                if(md == 'STARS'):
                    while(True):
                        rmsg = self._process_message(rmsg)
                        if(rmsg == ''):
                             break
                        else:
                            rmsg = rmsg.replace('\r', '')
                            if(hd is not None):
                                if(self._selfTest):
                                    self._debugprint("Call STARS handler: message=[%s]\n" %rmsg)
                                hd(stars.StarsMessage(rmsg), sock)
                                rmsg='';
                #Mode DIRECT
                elif(md == 'DIRECT'):
                    if(hd is not None):
                        if(self._selfTest):
                            self._debugprint("Call DIRECT handler: message=[%s]\n" %rmsg)
                        hd(rmsg, sock)
        if(self._termsignal == True):
            self._debugprint("terminateMainloop detected.")
        return True
