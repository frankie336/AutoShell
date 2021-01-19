
"""
Created on Mon Jan 11 20:08:27 2021
#! Python 3.8

@author: Francis Neequaye
         francis.neequaye@gmail.com

Small tool that sync the VLAN’s on any given machine with database table.
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
        """
        This is what we call do actually connect and start the event loop
        """
        # Establish the SSH connection
        self.ssh.connect(self.host, username=self.username,
                         password=self.password,look_for_keys=False)

        # Create an SSH shell descriptor. This is how we're going to interact
        # with the remote device.
        shell = self.ssh.invoke_shell()
        shell.settimeout(0.0)
        self.shell = shell

        # Turn the list of commands into an iterator, so we know when we've run
        # out of commands
        self.cmditer = iter(self.commands)

        # Establish the data buffer we'll use to store output between commands
        self.data = ''

        # And start the event loop to store the results of the commands and
        # return them when we're done.
        results = self.interact()
        return results

    def interact(self):
        """Interact with the device using the SSH shell."""
        shell = self.shell

        # Start an infinite while loop, and use the select.select async I/O
        # handler to detect when data has been received by the SSH shell.
        while True:
            # The ``r`` variable names the object that has received data. See:
            # http://docs.python.org/2/library/select.html#select.select
            r, w, e = select.select([shell], [], [])
            # If 'shell' has received data, try to retreive it:
            if shell in r:
                #log.debug("HEY LET'S DO SOMETHING WITH SHELL")
                try:
                    # Fetch 1K off the socket.
                    bytes = shell.recv(1024)

                    # If it's no data, we're done. 
                    if len(bytes) == 0:
                        break
                    
                    # Try to process the data we received.
                    self.data_received(bytes)

                # If we timeout or get an error, log it and carry on.
                except (socket.timeout, socket.error) as err:
                    log.error(str(err))

            # If the socket has not received any data after we sent somethign,
            # disconnect.
            else:
                break

        # The explicit call to disconnect
        shell.close()

        # And finally return the output of the results.
        return self.results

    def data_received(self, bytes):
        """
        This is what we do when data is received from the socket.
        :param bytes:
            Bytes that are received.
        """
        # This is our buffer. Until we get a result we want, we keep appending
        # bytes to the data buffer.
        log.debug('Got bytes: %r' % bytes)
        self.data += bytes.decode(encoding='UTF-8')
        log.debug(' Buffered: %r' % self.data)

        # Check if the prompt pattern matches. Return None if it doesn't so the
        # event loop continues to try to receive data. 
        # 
        # Basicaly this means:
        # - Loop until the prompt matches
        # - Trim off the prompt
        # - Store the buffer as the result of the last command sent
        # - Zero out the buffer
        # - Rinse/repeat til all commands are sent and results stored
        m = self.prompt.search(self.data)
        if not m:
            return None
        log.debug('STATE: prompt %r' % m.group())

        # The prompt matched! Strip the prompt from the match result so we get
        # the data received withtout the prompt. This is our result.
        # 
        result = self.data[:m.start()]
        result = result[result.find('\n')+1:]

        # Only keep results once we've started sending commands
        if self.initialized:
            self.results.append(result)

        #time.sleep(.5)
        # And send the next command in the stack.
        self.send_next()

    def send_next(self):
        """
        Send the next command in the command stack.
        """
        # We're sending a new command, so we zero out the data buffer.
        self.data = ''

        # Check if we can safely initialize. This is a chance to do setup, such
        # as turning off console paging, or changing up CLI settings. 
        if not self.initialized:
            if self.init_commands:
                next_init = self.init_commands.pop(0)
                self.shell.send(next_init)
                return None
            else:
                log.debug('Successfully initialized for command execution')
                self.initialized = True

        # Try to fetch the next command in the stack. If we're out of commands,
        # close the channel and disconnect.
        try:
            next_command = self.cmditer.__next__() # Get the next command
        except StopIteration:
            self.close() # Or disconnect
            return None

        # Try to send the next command
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


    def ProcessOutput(self):
        
        for i in range(self.host_len):
            self.diag =''.join(str(self.test[i][1][1]))
            print (self.diag)
            
            f = open('output.txt', 'wt', encoding='utf-8')
            f.write(self.diag)




 

        
        
    def main(self):


        
        username = 'cisco'#NEEDS TO BE SET TO THE APPROPRIATE DEVICE MANAGEMENT USERNAME
        password = 'cisco'#NEEDS TO BE SET TO THE APPROPRIATE DEVICE MANAGEMENT PASSWORD
        creds = (username, password)


        pat1 = [r'\S+>$',r'\S+#$']
        prompt_pattern =  re.compile( '|'.join(pat1))
        init_commands = ['set cli scripting-mode on\n', 'terminal length 0\n']
        commands = ['terminal length 0','sh ip int brie']
        
       
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

       

        self.test = self.output
        


        

    

        


        


if __name__ == "__main__":
    p1 = LoopDevices()
    p1.main()
    p1.ProcessOutput()
    
     
     
 
    
     


      #vlandat =''.join(results)
      #print(results)

