
"""
Created on Mon Jan 11 20:08:27 2021
#! Python 3.8

@author: Francis Neequaye
         francis.neequaye@gmail.com
"""

"""
Script Instructions 
_____

1.Enter the remote IP's addresses of 
Cisco (or other) devices on each search
of the Hosts.dat file

2. Enter input commands on each line of
the Commands.dat file 

"""

import paramiko
import time
from multiprocessing.pool import ThreadPool
import re
import datetime
import psutil


start = time.time()

class ShellWork(object):
    def __init__(self):
        
        filepath = 'SetUp\\Hosts.dat'#list of ip addresses
        with open(filepath) as f:
            self.ips = f.read().splitlines()
        self.ips = [string for string in self.ips if string != ""]#Remove possible empty lines


        filepath = 'SetUp\\Commands.dat'#list of device commands
        with open(filepath) as f:
            self.commands = f.read().splitlines()

        self.cisco_term_length = "terminal length 0\n"


        self.date_time = datetime.datetime.now().strftime("%Y-%m-%d")

        self.cisco_Uexec = '>'
        self.cisco_Pexec = '#'

        self.username = username
        self.password = password

        self.count_threads = psutil.cpu_count(logical=True)#Count number of cores/threads in CPU
         
    
                
    def AutoShell(self,host):

        print('With threading')
        
        
        """
        -Attempt to connect to a remote host:
        1. If the host is unreachable, print
        the error and continue to the  next 
        host 
        """
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port=22, username=self.username, password=self.password, look_for_keys=False, timeout=None)
            connection = ssh.invoke_shell()
            
        except Exception as e:
            print(host,e.args)
            return 
      
        time.sleep(.3)  
        connection.send(self.cisco_term_length)#Sends the Cisco Terminal length0 Command
        

        """
        Once a  connection is established:
        1. send the shell input Commands
        by looping the self.commands list
        """
        for x in self.commands:
          connection.send(x+"\n")

        
        time.sleep(3)#The Buffer needs a little time to populate output
      
        file_output = connection.recv(9999).decode(encoding='utf-8') #Receive buffer output
        
  
        
        """
        For Cisco devices
        __________________
        1. Search for the hostname string 
        2.Strip the user mode prompt (>,#)
        from the hostname string 
        3. Save  
        """
        pat0 = [self.cisco_Uexec,self.cisco_Pexec]
        
        pat1 = ['(.+)'+self.cisco_Uexec,'(.+)'+self.cisco_Pexec]
        
        prompt0 =  re.compile( '|'.join(pat0)) 
        prompt1 =  re.compile( '|'.join(pat1)) 
        
        prompt_level = (re.search(prompt0, file_output)).group(0)

        hostname = (re.search(prompt1, file_output)).group().strip(prompt_level)
        
       
 
        with open('output\\'+hostname + "-" + str(self.date_time) + ".txt", "w") as f:
            f.writelines(file_output[678:-19])#This is a custom number, may need to be changed

        print('Done',host)

        ssh.close()


    def MultThreadConn(self):
        
        """
        The multiprocessing.pool module will spawn concurrent
        proceses , executing the AutoShell() module . On each
        occasion, the @arg (hosts) = self.ips list will be interated.
        Each thread will run for a seperate IP address from the
        Hosts.dat file 
        """

        THREADS = ThreadPool(self.count_threads)#Set the number of threads
        RESULTS = THREADS.map(self.AutoShell, self.ips)
        THREADS.close()
        

        
       
            
if __name__ == "__main__": 
    username = "cisco"
    password = "cisco"
    a = ShellWork()
    a.MultThreadConn()
    


end = time.time()
print(end - start)



    




 
    
     
