
"""
Created on Mon Jan 11 20:08:27 2021
#! Python 3.8

@author: Francis Neequaye
         francis.neequaye@gmail.com
"""



"""
***IMPORTANT***
Update the hosts.txt file with target host devices

"""
import time
start_time = time.time()

import sys
import os 
import logging
import socketserver
import re
import time
import socket
import pandas as pd
from datetime import datetime

try:
    import paramiko
except ImportError:
    print("Trying to Install required module: paramiko\n")
    os.system('python -m pip install paramiko')
import paramiko
from paramiko import SSHClient, BadAuthenticationType


try:
    import select
except ImportError:
    print("Trying to Install required module: select\n")
    os.system('python -m pip install select')
import select




read_out = []
"""
An Interactive automated SSH Client:
 - Will connect to target device when triggered and run 
   specified commands
"""
PROMPT_PATTERN = r'\S+#'
logging.basicConfig(level=logging.DEBUG)
log = logging
paramiko.util.log_to_file('Auto_Shell_log.log')
class Ssh(object):
    def __init__(self, host, commands, creds=None,
                 prompt_pattern=PROMPT_PATTERN, init_commands=None):
        if creds is None:
            raise RuntimeError('Username or Password not correctly entered')
        

        
        

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
        - Remove any blank lines that may mistakenly be included
        -  Make the list an object in this constructor function
        - Make the length of the self.hosts list an object 
        """
        with open("hosts.txt") as file:
             self.hosts = [line.strip() for line in file]
             self.hosts = [x for x in self.hosts if x != '']

        self.host_len = len(self.hosts)
        
        """
        The Number of nested lists made is now tied to
        the length of the self.hosts list  
        """
        self.output = [[] for _ in range(self.host_len)]

        
        """
        - Open the commands.txt file and read each line into a list
        -  Make the list an object in this constructor function
        """
        with open("commands.txt") as file:
             self.commands = [line.strip() for line in file]

        self.log_file = "Auto_Shell_log.log"


    def ProcessOutput(self):

        #start = time()

        print(read_out[0])
       
        host_pattern = r'(.*>)|(.*#)'
        self.find_host = re.compile(host_pattern)

        self.host_names = []

        firstele = read_out[0][0]
        host = self.find_host.search(firstele)
        host = host.group()
        self.host_names.append(host)

        remove = ['>','#']
        pat =  '|'.join(remove)
        self.host_names = [re.compile(pat).sub("", m) for m in self.host_names]
        print(host,self.host_names)

        
        with open(self.host_names[0]+'_output.txt', 'w') as filehandle:
            filehandle.writelines("%s\n" % place for place in read_out[0])


        read_out.clear()
        
      
        
        

        
        

                   
  
    
    def ParseTheLogs(self):
 

        try:
            open_file = open(self.log_file)
            log_read = open_file.read()
            open_file.close()

        except Exception as ex:
            print("Cannot read log file, termninating")
            sys.exit(1)

        
        adding_host_key =   re.findall(r"(.*)(Adding ssh-rsa host key(.*)\n)",
                                  
                                     log_read,
                                     re.MULTILINE)

        authentication_state =   re.findall(r"(Authentication \(password\) successful!(.*)|Authentication \(password\) failed.(.*))",
                                  
                                     log_read,
                                     re.MULTILINE)


        reachable_hosts =   re.findall(r".*?key for(.*)\:.*",
                                  
                                     log_read,
                                     re.MULTILINE)
        


        log_date =   re.findall(r".*?INF \[(.*)](.*)Authentication.*",
                                
                                   log_read,
                                   re.MULTILINE)


        #2021-01-22 20:11:11.666281 : Unable to connected to the following hosts on port 22:172.19.1.253
        failed_connect =   re.findall(r"(FAI)(.*)(.*)( : )(Unable to connect to the host on port 22:)(.*)(.*)",
                                
                                   log_read,
                                   re.MULTILINE)
        
        #log_date = [item for t in log_date  for item in t]
        authentication_state = [item for t in authentication_state  for item in t]
        authentication_state = [x for x in authentication_state if x != '']
        log_date = [x[0] for x in log_date]
        #log_date = [x for x in log_date if x != '']
        
        """
        Parsing the logs for failed connects
        """
        failed_connect0 = failed_connect
        failed_connect1 = failed_connect
        failed_connect2 = failed_connect
        failed_date = failed_connect0 = [x[1] for x in failed_connect0]
        failed_date = [re.compile(r'\[|\]').sub("", m) for m in failed_date]
        failed_hosts = failed_connect1 = [x[5] for x in failed_connect1]
        failed_message = failed_connect2 = [x[4] for x in failed_connect2]
        
        
        log_date = log_date+failed_date
        reachable_hosts = reachable_hosts+failed_hosts
        authentication_state = authentication_state+failed_message



        log_dict = {'Date':log_date,'Reachable_Hosts':reachable_hosts,'Authentication_State':authentication_state}
        dflogs = pd.DataFrame.from_dict(log_dict)
        print(dflogs)
        dflogs.to_csv('Connection_Logs.csv', encoding='utf-8', index=False)


        



if __name__ == "__main__":

    pat1 = [r'\S+>$',r'\S+#$']
    prompt_pattern =  re.compile( '|'.join(pat1))
    init_commands = ['set cli scripting-mode on\n', 'terminal length 0\n']

    username = 'cisco'#NEEDS TO BE SET TO THE APPROPRIATE DEVICE MANAGEMENT USERNAME
    password = 'cisco'#NEEDS TO BE SET TO THE APPROPRIATE DEVICE MANAGEMENT PASSWORD
    creds = (username, password)

    with open("hosts.txt") as file:
             hosts = [line.strip() for line in file]
             hosts = [x for x in hosts if x != '']

    with open("commands.txt") as file:
             commands = [line.strip() for line in file]
    
    for x in hosts:
        c = Ssh(x, commands, creds, prompt_pattern, init_commands)
        results = c.run()

        print(len(results))
        read_out.append(results)
        print(len(read_out))
        p1 = LoopDevices()
        p1.ProcessOutput()
      
    
print("--- %s seconds ---" % (time.time() - start_time))
   
 
    
     
