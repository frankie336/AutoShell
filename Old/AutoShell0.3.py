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
import abc 
import paramiko
import time
from multiprocessing.pool import ThreadPool
import re
import datetime
import psutil
import logging
import getpass
import os

start = time.time()#Temp timing

class FormalAutoShellInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'load_data_source') and 
                callable(subclass.load_data_source) and
                hasattr(subclass, 'term_zero') and 
                callable(subclass.term_zero) and
                hasattr(subclass, 'find_host_name') and 
                callable(subclass.find_host_name) and
                hasattr(subclass, 'create_set_up') and 
                callable(subclass.create_set_up) or
                NotImplemented)

    @abc.abstractmethod
    def load_data_source(self, path: str):
        """Load data to be read into list"""
        raise NotImplementedError

    @abc.abstractmethod
    def term_zero(self, device_id: str):
        """The Command for to make terminal length zero"""
        raise NotImplementedError


    @abc.abstractmethod
    def find_host_name(self, device_type: str):
        """Search for device hostname string and strip the prompt"""
        raise NotImplementedError


    @abc.abstractmethod
    def save_list_output(self, path: str, str,list_name: str):
        """Save output from lists"""
        
        raise NotImplementedError


    @abc.abstractmethod
    def create_set_up(self, path: str ):
        """If a SetUp file does not exist create it"""
        
        raise NotImplementedError



class LoadDataToList(FormalAutoShellInterface):
 
    def load_data_source(self, path: str) -> str:
        """Load data to be read into list"""

        EMPTY_FILE = 'Unable to process: The '+path+' file is empty'
        
        with open(path) as f:
            lines = f.read().splitlines()

       
        lines = [string for string in lines if string != ""]#Remove possible empty lines

        if len(lines) == 0:
            print(EMPTY_FILE)
              
    
        return lines


    
    def term_zero(self, device_id: str):
        """The Command for to make terminal length zero"""
        
        term_zero_list = ['terminal length 0\n']
    
        if device_id == 'Cisco':
            terminal_length = term_zero_list[0]
            
            return terminal_length

    
    def find_host_name(self, device_id: str, search: str) -> str:
        """Search for device hostname string and strip the prompt"""
        

        """
        For Cisco devices
        __________________
        1. Search for the hostname string 
        2.Strip the user mode prompt (>,#)
        from the hostname string 
        3. Save  
        """
        
        if device_id=='Cisco_IOS':

            prompts = ['>','#']
            look_behind_prompt = ['(.+)'+prompts[0],'(.+)'+prompts[1]]
            hostname_pat =  re.compile( '|'.join(look_behind_prompt))
            to_strip =  re.compile( '|'.join(prompts))

            stripped = (re.search(to_strip, str(search))).group(0)
            
            hostname = (re.search(hostname_pat, str(search))).group(0).strip(stripped)

            return hostname


     
    def save_list_output(self, path: str, list_name: str) -> str:
        """Save output from  lists"""

        with open(path+'_'+self.date_time+'.txt', "w") as f:
            f.writelines(list_name)



    
    def create_set_up(self, path: str ):
        """If the SetUp folder does not exist create it"""
        
        find_file = os.path.isfile(path)
        
        if find_file == False:
            print(path+' does not exist, creating.')
            file = open(path, 'w+')
        


      
        
     


class ChannelClass(LoadDataToList):
    
    count_cores = psutil.cpu_count(logical=True)#Count number of cores/threads in CPU

    def __init__(self):

        self.date_time = datetime.datetime.now().strftime("%Y-%m-%d")
        self.username = username
        self.password = password
        


  

        
                

    
    def SetUpCommands(self):

        """
        Basic method to open commands file
        allowing for more sophisticated method in the future
        """
        self.create_set_up(path='Setup\\Cisco_Commands.dat')#Check if file exists

        commands = self.load_data_source(path='Setup\\Cisco_Commands.dat')

        return commands

    

    
    
    def MakeConnection(self,host_ip):
       
        terminal_length = self.term_zero(device_id='Cisco')
        
        commands = self.SetUpCommands()

        
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host_ip, port=22, username=self.username, password=password, look_for_keys=False, timeout=None)        
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

        time.sleep(.1)#Time to wait to receive channel bytes

        shell_output = channel.recv(9999).decode(encoding='utf-8') #Receive buffer output

        ssh.close()

        return  shell_output

    
    
    def SaveToFile(self,files):
        
        """
        1.Extract the device hostname from channe shell_output
        2. Save the channel output, Affixing the hostname to the
        saved file  
        """
        for ele in files:

            hostname = self.find_host_name(device_id='Cisco_IOS',search=ele)    
            save = self.save_list_output(path='Output\\'+hostname,list_name=ele)
              
            print('Done',hostname)




    def MultiThreading(self):
        
        """
        The multiprocessing.pool module will spawn concurrent
        proceses , executing the AutoShell() module . On each
        occasion, the @arg (hosts) = self.ips list will be interated.
        Each thread will run for a seperate IP address from the
        Hosts.dat file 
        """

        obj =  ChannelClass()

        self.create_set_up(path='Setup\\Hosts.dat')

        loop_hosts = self.load_data_source(path='Setup\\Hosts.dat')
        
        THREADS = ThreadPool(obj.count_cores)#Set the number of threads
        
        SHELL_OUT = THREADS.map(self.MakeConnection, loop_hosts)

     
        self.SaveToFile(SHELL_OUT)#Save output to file


        THREADS.close()



  
if __name__ == "__main__": 
    username = 'cisco'#temp solution
    password = 'cisco' #temp solution 
    a = ChannelClass()
    a.MultiThreading()
   
 
  
   
end = time.time()
print(end - start)

    
