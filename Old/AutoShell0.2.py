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
import logging




start = time.time()

class AutoShellInterface:
    def LoadDataToList(self, path: str, file_name: str) -> str:
        """Load in files as lists."""
        pass

    
    def SaveDataFromList(self, path: str, file_name: str) -> str:
        """Save list elements as files"""
        pass




class ShellWork(AutoShellInterface):
    
    count_cores = psutil.cpu_count(logical=True)#Count number of cores/threads in CPU
    
    def __init__(self):

        self.date_time = datetime.datetime.now().strftime("%Y-%m-%d")
        
        self.username = username

        self.password = password
        

    def LoadDataToList(self, path: str, file_name: str) -> str:
        """Overrides AutoShellInterface.SaveDataFromList()"""
        
        with open(path+file_name) as f:
            lines = f.read().splitlines()

        lines = [string for string in lines if string != ""]#Remove possible empty lines
        return lines


    
    def SaveDataFromList(self, path: str, file_name: str,
                         list_name: str) -> str:
        """Overrides AutoShellInterface.LoadDataToList()"""
        
        with open(path+str(self.date_time)+'_'+file_name+'.txt', "w") as f:
            f.writelines(list_name)
    



    def SetUpCommands(self):


        commands = self.LoadDataToList(path='SetUp\\',file_name='Commands.dat')

        return commands 

    
    def TeminalZero(self):
        
        device = 'Cisco'

        term_zero_list = ['terminal length 0\n']

        if device == 'Cisco':
            
            terminal_length = term_zero_list[0]
            
            return terminal_length




    def Connect(self,host_ip):

    
        terminal_length = self.TeminalZero()
        commands = self.SetUpCommands()
        
        """
        -Attempt to connect to a remote host:
        1. If the host is unreachable, print
        the error and continue to the  next 
        host 
        """
     

        try:
            ssh = paramiko.SSHClient()
            
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh.connect(host_ip, port=22, username=self.username, password=self.password, look_for_keys=False, timeout=None)        
            
            channel = ssh.get_transport().open_session()
            
            channel.invoke_shell()
        except Exception as e:
            
            print(host_ip,e.args)
            
            return
        

        channel.sendall(terminal_length)#Send terminal length zero command
        time.sleep(.2)

        """
        Once a  connection is established:
        1. send the shell input Commands
        by looping the self.commands list
        """
        for x in commands:
            channel.sendall(x+"\n")

        time.sleep(1)

        self.shell_output = channel.recv(9999).decode(encoding='utf-8') #Receive buffer output

        ssh.close()

        return self.shell_output# Return to threads




    def SaveToFile(self,files):
        
        
        """
        For Cisco devices
        __________________
        1. Search for the hostname string 
        2.Strip the user mode prompt (>,#)
        from the hostname string 
        3. Save  
        """


        mode_prompt_patterns = ['>','#']

        look_behind_prompt = ['(.+)'+mode_prompt_patterns[0],'(.+)'+mode_prompt_patterns[1]]

        hostname_pat =  re.compile( '|'.join(look_behind_prompt))

        to_strip =  re.compile( '|'.join(mode_prompt_patterns)) 


        
        for ele in files:

            stripped = (re.search(to_strip, str(ele))).group(0) 

            hostname = (re.search(hostname_pat, str(ele))).group().strip(stripped)

            self.SaveDataFromList(path='Output\\',file_name=hostname,list_name=ele)

            print(hostname,'done',stripped)




    def MultThreadConn(self):
        
        """
        The multiprocessing.pool module will spawn concurrent
        proceses , executing the AutoShell() module . On each
        occasion, the @arg (hosts) = self.ips list will be interated.
        Each thread will run for a seperate IP address from the
        Hosts.dat file 
        """

        obj =  ShellWork()


        loop_hosts = self.LoadDataToList(path='SetUp\\',file_name='Hosts.dat')

        THREADS = ThreadPool(obj.count_cores)#Set the number of threads
        
        SHELL_OUT = THREADS.map(self.Connect, loop_hosts)

        #print(SHELL_OUT)        
        
        self.SaveToFile(SHELL_OUT)


        THREADS.close()




if __name__ == "__main__": 
    username = 'cisco'
    password = 'cisco'
    a = ShellWork()
    a.MultThreadConn()

    
end = time.time()
print(end - start)
    