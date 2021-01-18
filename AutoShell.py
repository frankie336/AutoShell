# -*- coding: utf-8 -*-
"""
Created on Sat Jan 16 11:39:36 2021

@author: Thanos
"""

import socket
import paramiko
import select
import re  
import logging
import time

PROMPT_PATTERN = r'\S+#'
logging.basicConfig(level=logging.DEBUG)
log = logging
paramiko.util.log_to_file('show_me_the_vlan_log.log')

class Channel:
    def __init__(self):

        with open("commands.txt") as file:
             self.commands = [line.strip() for line in file]

        self.cmditer = iter(self.commands)
        
       
     


        pat1 = [r'\S+>$',r'\S+#$',r'\S+:$']
        self.prompt =  re.compile( '|'.join(pat1))

      
        self.results = []

        

   
    def setup(self):
     """
     Settting up the connection:
     """
     
     ssh = paramiko.SSHClient()
     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
     self.ssh = ssh
     self.initialized = False



     self.port = 22
     self.username = 'cisco'
     self.password = 'cisco'
     self.init_commands = ['terminal length 0\n','sh clock\n','conf t\n','int GigabitEthernet1/0\n','shut\n']

     
    

    def connect(self):
    
        self.ssh.connect(self.ip,self.port,self.username,self.password,look_for_keys=False
                  )
        shell = self.ssh.invoke_shell()
        shell.settimeout(0.0)
        self.shell = shell
        
        self.resp = ''
        print("Device")
        self.interact()





    def interact(self):
        """Interact with the device using the SSH shell."""
        shell = self.shell
        while True:
      
            r, w, e = select.select([shell], [], [])
        
            if shell in r:
                try:
               
                    bytes = shell.recv(16000)

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
        self.resp += bytes.decode(encoding='UTF-8')
        log.debug(' Buffered: %r' % self.resp)


        m = self.prompt.search(self.resp)
        if not m:
            return None

        log.debug('STATE: prompt %r' % m.group())


        result = self.resp[:m.start()]
        result = result[result.find('\n')+1:]

        if self.initialized:
            self.results.append(result)
            
        
        self.mode  =  m.group()
        self.send_next()


    def send_next(self):

        self.resp = ''
        

        """
        If the device is sitting at user exec mode 
        run these commands to bring it int enable mode
        """
        exec_promt = '>'
        is_in_user_exec = True if re.search(exec_promt, self.mode, re.MULTILINE) else False
     

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

       

          
        print("******************starting main commands************************")

        try:
            time.sleep(1)
            next_command = self.cmditer.__next__() # Get the next command
        except StopIteration:
            self.close() # Or disconnect
            #return None
            pass


        # Try to send the next command
        if next_command is None:
            self.results[0].append(None) # Store a null command w/ null result
            self.send_next() # Fetch the next command
        else:
            log.debug('sending %r' % next_command)
            self.shell.send(next_command + '\n')  # Send this command 

        
        



    
    def CommandOutput(self):

        
        #print('++++++++++++++++++++++',self.output)
        #print(len(self.output))#

        print("++++++++++RESULTS+++++++++",self.results)

      

       
        
       

    def close(self):
        """Close the SSH connection."""
        self.ssh.close()

    def main(self): 
        
        self.output = []
    
        with open("hosts.txt") as file:
         hosts = [line.strip() for line in file]

        
        
        for x in hosts:
            self.ip = x
            p1 = Channel
            p1.setup(self)
            p1.connect(self)
            
            #p1.send_next(self)
            #self.output.append(self.results)
            
        p1.CommandOutput(self)
    

if __name__ == "__main__":
    
     run = Channel()
     run.main()
    



