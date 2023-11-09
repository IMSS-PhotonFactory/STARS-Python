#! /usr/bin/python3
""" STARS Python Interface: basic module of python STARS

    History:
        0.1    Beta version     2016.05.25    T.Kosuge

        0.11   +--bugfix        2016.11.18    Y.Nagatani

        0.2    Upgrade          2016.12.20    Y.Nagatani

        0.201  +--Change term 'read' to 'receive'   2017.02.17    Y.Nagatani
"""

# Define: program info
__author__ = 'T.Kosuge, Y.Nagatani'
__version__ = '0.201'
__date__ = '2017-02-17'
__license__ = 'MIT'

import sys
import socket
import threading
import time

#----------------------------------------------------------------
# Class StarsMessage
#----------------------------------------------------------------
class StarsMessage(str):
    """ Class StarsMessage: STARS Message object.

    Properties:
        allmessage (string) Full text of STARS message.

        nodefrom   (string) STARS nodename of sender.

        nodeto     (string) STARS nodename of destination.

        message    (string) Command and paramters part of STARS message text.

        command    (string) Command part of STARS message text.

        parameters (string) Paramters part of STARS message text.
    """
    def __init__(self, message):
        self.allmessage = message
        try:
            mess   = message.split(' ', 1)
            fromto = mess[0].split('>')
            self.nodefrom   = fromto[0]
            self.nodeto     = fromto[1]
            self.message    = mess[1]
            mess   = mess[1].split(' ', 1)
            self.command    = mess[0]
            if len(mess) > 1:
                self.parameters = mess[1]
            else:
                self.parameters = ''
        except:
            self.nodefrom   = ''
            self.nodeto     = ''
            self.command    = ''
            self.message    = ''
            self.parameters = ''

#----------------------------------------------------------------
# Class(internal) for STARS callback
#----------------------------------------------------------------
class _CallbackThread(threading.Thread):
    """ Class CallbackThread
         Thread for callback function. This function is internal.
    """
    def __init__(self, stars):
        threading.Thread.__init__(self)
        self.stars = stars

    def run(self):
        self.stars._callbackrunning = True
        while self.stars._callbackrunning:
            rt = self.stars.receive(None)
            self.stars.callback(rt)
            if rt == '':
                self.stars._callbackrunning = False

#----------------------------------------------------------------
# Class StarsInterface
#----------------------------------------------------------------
class StarsInterface():
    """ Class StarsInterface: Basis of STARS Interface

          Parameters:
            nodename -- (string) is so-called 'STARS nodename'.

            srvhost  -- (string) is the IP address or the hostname of STARS server.
            
            keyfile  -- (optional string) is the filepath of the STARS keyfile. If omitted, nodename + '.key' will be used.

            srvport  -- (optional integer) is the port value of STARS server. If omitted, 6057(=DEFAULT_PORT) will be used.


    """
    
    DEFAULT_PORT    = 6057
    DEFAULT_TIMEOUT =   10
    TCP_BUFFER_SIZE = 4096

    #----------------------------------------------------------------
    # Error functions
    #----------------------------------------------------------------
    def getlasterrortext(self):
        """ getlasterrortext: Return the last error message text.

              Returns:
                (string) the last error message text.
        """
        return(self.error)

    #----------------------------------------------------------------
    # debug functions
    #----------------------------------------------------------------
    def setdebug(self, b):
        """ setdebug: debug option.

              Parameters:
                b -- (bool) set True to print debug infomation text to stdout.
        """
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
    # Initialize
    #----------------------------------------------------------------
    def __init__(self, nodename, srvhost, keyfile = '', srvport = DEFAULT_PORT):
        self.nodename = nodename
        self.srvhost  = srvhost
        if keyfile == '':
            self.keyfile = nodename + '.key'
        else:
            self.keyfile  = keyfile
        self.srvport    = srvport
        self.keywords   = ''
        self.error      = ''
        self.readbuffer = ''

        #Added by Y.Nagatani
        self.s = None
        self._connectiontimeout = socket.getdefaulttimeout()
        self._readtimeout = StarsInterface.DEFAULT_TIMEOUT
        self._lastexception = sys.exc_info()
        self._debug=False
        self._callbackrunning = False

    #****************************************************************
    # Property functions: STARS socket
    #****************************************************************
    def gethandle(self):
        """ gethandle: Return STARS socket object.

              Returns:
                (socket object) STARS socket object.

                (None) If no socket is assinged for STARS.
        """
        if hasattr(self,'s'):
            return(self.s)
        return(None)

    #****************************************************************
    # Property functions: Socket timeout
    #****************************************************************
    def setdefaultconnectiontimeout(self, timeout):
        """ setdefaultconnectiontimeout: Set the socket connection timeout value referenced in connect().

              Parameters:
                 timeout -- (float,int) is used as the socket connection timeout value(in seconds).
                        This value will be used at connect() function.
              Returns:
                (bool) True if the timeout value is valid, otherwise False.
        """
        if(isinstance(timeout, int) or isinstance(timeout, float) or (sys.version_info.major<3 and isinstance(timeout, long))):
            if(timeout>0):
                self._connectiontimeout = timeout
                return True;
            else:
                rt="setdefaultconnectiontimeout value invalid. (%s)" %(timeout)
                self.error = "%s" %(rt)
                self._debugprint("[setdefaultconnectiontimeout] (%s)\n" %(self.error))
                return(False)
        rt="setdefaultconnectiontimeout type invalid. (%s)" %(type(timeout))
        self.error = "%s" %(rt)
        self._debugprint("[setdefaultconnectiontimeout] (%s)\n" %(self.error))
        return(False)

    def setdefaultreceivetimeout(self, timeout):
        """ setdefaultreceivetimeout: Set the socket receive timeout value(in seconds).

              Parameters:
                 timeout -- (float,int or None) is used as the socket receive timeout value(in seconds).
                         This value will be used at receieve() function.
                         See also getdefaultreceivetimeout(), receive() functions.

              Returns:
                (bool) True if the timeout value is valid, otherwise False.
        """
        if(timeout is None):
            self._readtimeout = timeout
            return True;
        if(isinstance(timeout, int) or isinstance(timeout, float) or (sys.version_info.major<3 and isinstance(timeout, long))):
            if(timeout>0):
                self._readtimeout = timeout
                return True;
            else:
                rt="setdefaultreceivetimeout value invalid. (%s)" %(timeout)
                self.error = "%s" %(rt)
                self._debugprint("[setdefaultreceivetimeout] (%s)\n" %(self.error))
                return(False)
        rt="setdefaultreceivetimeout type invalid. (%s)" %(type(timeout))
        self.error = "%s" %(rt)
        self._debugprint("[setdefaultreceivetimeout] (%s)\n" %(self.error))
        return(False)

    def getdefaultreceivetimeout(self):
        """ getdefaultreceivetimeout: Return the socket receive timeout value(in seconds).

              Returns:
                (numeric or None) the socket receive timeout value(in seconds). 
        """
        return(self._readtimeout)

    #----------------------------------------------------------------
    # Connect/Disconnect
    #----------------------------------------------------------------
    def connect(self):
        """ connect: Connect to STARS server

              Returns:
                (bool) True if the STARS connection established, otherwise False.
        """

        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.settimeout(self._connectiontimeout)
        except Exception as e:
            self._lastexception = sys.exc_info()
            rt="socket.settimeout failure. (%s, %s)\n" %(str(self._connectiontimeout), type(e))
            self.error = "%s" %(rt)
            self._debugprint("%s\n" %(self.error))
            self.s = None
            return(False)
        #self._debugprint("settimeout %s\n" %(str(self._connectiontimeout)))

        try:
            self.s.connect((self.srvhost, self.srvport))
        except Exception as e:
            self._lastexception = sys.exc_info()
            rt="Connection failure. (%s:%s, %s)" %(self.srvhost, self.srvport, type(e))
            self.error = "%s" %(rt)
            self._debugprint("%s\n" %(self.error))
            self.s = None
            return(False)
        #self._debugprint("STARS server detected.\n")
 
        try:
            rt = self.s.recv(StarsInterface.TCP_BUFFER_SIZE).decode()
            rt = rt.strip('\r\n')
            keynum = int(rt)
            node_and_key = self.nodename + ' ' + self._get_keyword(keynum) + '\n'
            self.s.sendall(node_and_key.encode())
            rt = self.s.recv(StarsInterface.TCP_BUFFER_SIZE).decode()
        except Exception as e:
            self._lastexception = sys.exc_info()
            rt="Connection process failure. (%s)" %(type(e))
            self.error = "%s" %(rt)
            self._debugprint("%s\n" %(self.error))
            self._debugprint("%s\n" %(e))
            self.disconnect()
            return(False)

        rt = rt.strip('\r\n')
        if rt.startswith('System>'):
            if rt.endswith(' Ok:'):
                rt="[Connected] %s:%s" %(self.srvhost, self.srvport)
                self._debugprint("%s\n" %(rt))
                return 'Ok:'
            rt = rt.replace('System>', '')
            rt = rt.replace('Er:','')
        rt = rt.strip()
        self.error = rt
        self._debugprint("%s\n" %(rt))
        self.disconnect()
        return(False)

    def disconnect(self):
        """ disconnect: Disconnect from STARS server
        """
        fh = self.gethandle()
        if(fh is not None):
            try:
                fh.close()
                self.s = None
            except Exception as e:
                self._lastexception = sys.exc_info()
                rt="Disconnection failure. (%s)" %(type(e))
                self.s = None
        return

    def _get_keyword(self, keynum):
        k = []
        if self.keywords != '':
            k = self.keywords.split()
        else:
            f = open(self.keyfile)
            k = f.readlines()
            f.close()
        p = k[keynum % len(k)]
        p = p.replace('\n', '')
        p = p.replace('\r', '')
        return p

    #----------------------------------------------------------------
    # Send
    #----------------------------------------------------------------
    def send(self, arg1, arg2 = '', arg3 = ''):
        """ send: Send STARS message to STARS server.

              Parameters:
                arg1 -- (string) used as follows.

                arg2 --  (optional string) used as follows. If omitted, '' will be used.

                arg3 --  (optional string) used as follows. If omitted, '' will be used.

              Use parameters as follows:
                Send arg1 as STARS message if arg2==''.

                Send arg1 + ' ' + arg2 as STARS message if arg2!=''and arg3==''.

                Send arg1 + '>' + arg2 + ' ' + arg3 as STARS message if arg2!='' and arg3!=''.

              Returns:
                (bool) True if sended, otherwise False.
        """
        fh = self.gethandle()
        if(fh is not None):
            msg = ''
            if arg2 != '':
                if arg3 !='':
                    msg = arg1 + '>' + arg2 + ' ' + arg3
                else:
                    msg = arg1 + ' ' + arg2
            else:
                msg = arg1
            msg += '\n'

            try:
                fh.sendall(msg.encode())
            except Exception as e:
                self._lastexception = sys.exc_info()
                rt="Send failure. (%s, %s)" %(msg, type(e))
                self.error = "%s" %(rt)
                self._debugprint("%s\n" %self.error)
                self._debugprint("%s\n" %(e))
                return(False)
            self._debugprint("[Send] %s" %(msg))
            return(True)
        self.error="No socket."
        return(False)

    #----------------------------------------------------------------
    # Receive
    #----------------------------------------------------------------
    def _process_message(self, msg):
        self.readbuffer += msg
        dp = self.readbuffer.find('\n')
        if dp < 0:
            return ''
        rtmess = self.readbuffer[:dp]
        self.readbuffer = self.readbuffer[dp+1:]
        return rtmess

    def receive(self, timeout = '', exceptionret = StarsMessage('')):
        """ receive: Read STARS message from STARS Server.

              Parameters:
                timeout -- (optional float,int or None) is the requested timeout(in seconds). If omitted, the value of getdefaultreceivetimeout() will be used. See also getdefaultreceivetimeout(), setdefaultreceivetimeout().

                exceptionret -- (optional object) is used as the return value when the fatal error deteceted. StarsMessage('') is the default value.

              Returns:
                (StarsMessage object) received data.

                (StarsMessage object) if the socket timeout detected, return StarsMessage('').

                The value of 'exceptionret' when the fatal error(kind of connection lost, timeout value error...) detected. 
        """
        fh = self.gethandle()
        if(fh is not None):
            ### Check read buffer.
            if self.readbuffer != '':
                rtmsg = self._process_message('')
                if rtmsg != '':
                    rtmsg = rtmsg.replace('\r', '')
                    return StarsMessage(rtmsg)

            ### Set timeout.
            if(timeout == ''):
                timeout = self.getdefaultreceivetimeout()
            try:
                self.s.settimeout(timeout)
            except Exception as e:
                self._lastexception = sys.exc_info()
                rt="settimeout failure. (%s)" %(type(e))
                self.error = "%s" %(rt)
                self._debugprint("[Recv] (%s)\n" %(self.error))
                return(exceptionret)

            ### Read socket
            msg = ''
            try:
                msg = self.s.recv(StarsInterface.TCP_BUFFER_SIZE).decode()
                ### Disconnect deteceted.
                if(len(msg) == 0):
                    self.error = 'Lost connection.'
                    self._debugprint("[Recv] (%s)\n" %(self.error))
                    return(exceptionret)
            except socket.timeout:
                self.error = 'Timeout'
                self._debugprint("[Recv] (%s)\n" %(self.error))
                return(StarsMessage(''))
            except Exception as e:
                self._lastexception = e
                rt="Receive failure. (%s)" %(type(e))
                self.error = "%s" %(rt)
                self._debugprint("[Recv] (%s)\n" %(self.error))
                self._debugprint("%s\n" %(e))
                return(exceptionret)

            ### Process STARS message
            rtmsg = self._process_message(msg)
            if rtmsg != '':
                rtmsg = rtmsg.replace('\r', '')
                self._debugprint("[Recv] %s\n" %(rtmsg))
                return StarsMessage(rtmsg)
            self.error = 'Timeout'
            self._debugprint("[Recv] (%s)\n" %(self.error))
            return(StarsMessage(rtmsg))
        self.error="No socket."
        return(exceptionret)

    #----------------------------------------------------------------
    # Callback
    #----------------------------------------------------------------
    def iscallbackrunning(self):
        """ iscallbackrunning: Return if the callback is running or not. See also start_cb_handler().

              Returns:
                (bool)   True if the callback is running, otherwise False.
        """
        return(self._callbackrunning)

    def start_cb_handler(self, callback):
        """ start_cb_handler

              Parameters:
                callback is a python 'callable' function which takes arguments (StarsMessage stmess).
        """     
        self.callback = callback
        th = _CallbackThread(self)
        th.setDaemon(True)
        th.start()
