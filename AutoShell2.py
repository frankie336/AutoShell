
"""
Created on Mon Jan 11 20:08:27 2021
#! Python 3.8

@author: Francis Neequaye
         francis.neequaye@gmail.com
"""


import os 
import logging
import socketserver
import re
import time
import select
import socket
import time
try:
    import paramiko
except ImportError:
    print("Trying to Install required module: paramiko\n")
    os.system('python -m pip install paramiko')
import paramiko
from paramiko import SSHClient, BadAuthenticationType
try:
    import pandas as pd 
except ImportError:
    print("Trying to Install required module: pandas\n")
    os.system('python -m pip install pandas')
import pandas as pd 
try:
    import sqlalchemy as sa
except ImportError:
    print("Trying to Install required module: sqlalchemy\n")
    os.system('python -m pip install sqlalchemy')
import sqlalchemy as sa
from sqlalchemy import create_engine
try:
    import pyodbc
except ImportError:
    print("Trying to Install required module: pyodbc\n")
    os.system('python -m pip install pyodbc')
import pyodbc





"""
An Interactive automated SSH Client:
 - Will connect to target device when triggered and run 
   specified commands
"""
PROMPT_PATTERN = r'\S+#'
logging.basicConfig(level=logging.DEBUG)
log = logging
paramiko.util.log_to_file('show_me_the_vlan_log.log')
class Channel(object):
    def __init__(self, host, commands, creds=None,
                 prompt_pattern=PROMPT_PATTERN, init_commands=None):
        if creds is None:
            raise RuntimeError('You must supply username and password!!')
        

        
        

        self.commands = commands

        username, password = creds
        self.creds = creds
        self.username = username
        self.password = password

        self.prompt = re.compile(prompt_pattern)
        if init_commands is None:
            init_commands = []
        self.init_commands = init_commands

        self.results = []
        self.host = host

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.ssh = ssh
        self.initialized = False

    def run(self):
  
        self.ssh.connect(self.host, username=self.username,
                         password=self.password,look_for_keys=False)

      
        shell = self.ssh.invoke_shell()
        shell.settimeout(0.0)
        self.shell = shell

      
        self.cmditer = iter(self.commands)

      
        self.data = ''

 
        results = self.interact()
        return results

    def interact(self):
        """Interact with the device using the SSH shell."""
        shell = self.shell

   
        while True:
         
            r, w, e = select.select([shell], [], [])
         
            if shell in r:
            
                try:
                 
                    bytes = shell.recv(1024)

                  
                    if len(bytes) == 0:
                        break
                    
                   
                    self.data_received(bytes)

               
                except (socket.timeout, socket.error) as err:
                    log.error(str(err))

          
            else:
                break

       
        shell.close()

       
        return self.results

    def data_received(self, bytes):
     
        log.debug('Got bytes: %r' % bytes)
        self.data += bytes.decode(encoding='UTF-8')
        log.debug(' Buffered: %r' % self.data)


        m = self.prompt.search(self.data)
        if not m:
            return None
        log.debug('STATE: prompt %r' % m.group())

        
        result = self.data
        #result = self.data[:m.start()]
        #result = result[result.find('\n')+1:]

      
        if self.initialized:
            self.results.append(result)
        
        """
        """
        self.mode  =  m.group()# A capture group for the current mode of the cli
        
       


        self.send_next()

    def send_next(self):

        """
        If the device is sitting at user exec mode 
        run these commands to bring it int enable mode
        """
        exec_promt = '>'
        is_in_user_exec = True if re.search(exec_promt, self.mode, re.MULTILINE) else False


        """
        To handle cisco enable mode uncomment this block of code
        """
        """
        if not self.initialized:
          if is_in_user_exec == True:
              while True:
                  mode_select = input('Cisco User exec mode sensed. Press "y" to enter enable mode or "n" to continue in user exec mode: ')
                  if mode_select =='y':
                      self.shell.send('enable\n')
                      time.sleep(.5)
                      self.shell.send('cisco\n')
                      break

                  if mode_select=='n':
                      break
          else:
              pass
        """ 

        
        

        

        self.data = ''

        if not self.initialized:
            if self.init_commands:
                next_init = self.init_commands.pop(0)
                self.shell.send(next_init)
                return None
            else:
                log.debug('Successfully initialized for command execution')
                self.initialized = True

       
        try:
            next_command = self.cmditer.__next__() # Get the next command
        except StopIteration:
            self.close() 
            return None

      
        if next_command is None:
            self.results.append(None) # Store a null command w/ null result
            self.send_next() # Fetch the next command
        else:
            log.debug('sending %r' % next_command)
            self.shell.send(next_command + '\n')  # Send this command

    def close(self):
        """Close the SSH connection."""
        self.ssh.close()


class LoopDevices:
    def __init__(self):
        
        """
        - Open the hosts.txt file and read each line into a list
        -  Make the list an object in this constructor function
        - Make the length of the self.hosts list an object 
        """
        with open("hosts.txt") as file:
             self.hosts = [line.strip() for line in file]

        self.host_len = len(self.hosts)
        
        """
        The Number of nested lists made is now tied to
        the length of the self.hosts list  
        """
        self.output = [[] for _ in range(self.host_len)]


        with open("commands.txt") as file:
             self.commands = [line.strip() for line in file]


    def ProcessOutput(self):


        """
        Searching for the hostname of the device:
        """
        host_pattern = r'(.*>)|(.*#)'
        self.find_host = re.compile(host_pattern)
        
        
        self.host_names = []

        for i in range(self.host_len):
             e = self.find_host.search(self.read_out[i][i][0])
             self.host_names.append(e.group())

        
        remove = removetable = str.maketrans('', '', '>')
        self.host_names = [s.translate(remove) for s in self.host_names]
        
             
        
        
        for i in range(self.host_len):
            self.diag=self.read_out[0][i]
            #self.diag =''.join(str(self.read_out[i][i]))
            print ('@@@@@@@@',self.diag)
            with open(self.host_names[i]+'_output.txt', 'w') as f:
                for item in self.diag:
                    f.write("%s\n" % item)



       
   
       


          
            


        
        
    def main(self):

        username = 'cisco'#NEEDS TO BE SET TO THE APPROPRIATE DEVICE MANAGEMENT USERNAME
        password = 'cisco'#NEEDS TO BE SET TO THE APPROPRIATE DEVICE MANAGEMENT PASSWORD
        creds = (username, password)


        pat1 = [r'\S+>$',r'\S+#$']
        prompt_pattern =  re.compile( '|'.join(pat1))
        init_commands = ['set cli scripting-mode on\n', 'terminal length 0\n']
        commands = self.commands
        host = self.hosts
        
        """
        1. Loop the following:
         - SSH Connect connect to each device in the hosts.txt file
         - Append the output of commands and diagnostics to the next nested 
         list in self.output, using the [i]index in the range loop
        """
        for i in range(self.host_len):
         for x in host:
            c = Channel(x, commands, creds, prompt_pattern, init_commands)
            results = c.run()
            self.output[i].append(results)

       
        self.read_out = self.output
        


        


if __name__ == "__main__":
    p1 = LoopDevices()
    p1.main()
    p1.ProcessOutput()
    
     
     
 
    
     
