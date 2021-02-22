import abc 
import paramiko
import time
from multiprocessing.pool import ThreadPool
import re
import datetime
import psutil
import logging

start = time.time()

class FormalAutoShellInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'load_data_source') and 
                callable(subclass.load_data_source) and
                hasattr(subclass, 'term_zero') and 
                callable(subclass.term_zero) and
                hasattr(subclass, 'find_host_name') and 
                callable(subclass.find_host_name) or
                NotImplemented)

    @abc.abstractmethod
    def load_data_source(self, path: str):
        """Load in the data set"""
        raise NotImplementedError

    @abc.abstractmethod
    def term_zero(self, device_id: str):
        """Load in the data set"""
        raise NotImplementedError


    @abc.abstractmethod
    def find_host_name(self, device_type: str):
        """Load in the data set"""
        raise NotImplementedError


    @abc.abstractmethod
    def save_list_output(self, path: str, str,list_name: str):
        """Save output from a single list element"""
        
        raise NotImplementedError



class LoadDataToList(FormalAutoShellInterface):
 
    def load_data_source(self, path: str) -> str:
        
        with open(path) as f:
            lines = f.read().splitlines()

        lines = [string for string in lines if string != ""]#Remove possible empty lines
        return lines


    
    def term_zero(self, device_id: str):
        
        term_zero_list = ['terminal length 0\n']
    
        if device_id == 'Cisco':
            terminal_length = term_zero_list[0]
            
            return terminal_length

    
    def find_host_name(self, device_id: str, search: str) -> str:
        """Extract the host name of the device"""
        

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
        """Save output from a single list element"""

        with open(path+'_'+self.date_time+'.txt', "w") as f:
            f.writelines(list_name)
     
       




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

        commands = self.load_data_source(path='Setup\\Cisco_Commands.dat')

        return commands

    

    
    
    def MakeConnection(self,host_ip):
       
        terminal_length = self.term_zero(device_id='Cisco')
        commands = self.SetUpCommands()
        
        
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

        time.sleep(.1)

        shell_output = channel.recv(9999).decode(encoding='utf-8') #Receive buffer output

        ssh.close()

        return  shell_output

    
    
    def SaveToFile(self,files):
        
        
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


        loop_hosts = self.load_data_source(path='Setup\\Hosts.dat')
        
        THREADS = ThreadPool(obj.count_cores)#Set the number of threads
        
        SHELL_OUT = THREADS.map(self.MakeConnection, loop_hosts)

     
        self.SaveToFile(SHELL_OUT)


        THREADS.close()
        

        
    
        

    
    



   

if __name__ == "__main__": 
    username = 'cisco'
    password = 'cisco' 
    a = ChannelClass()
    a.MultiThreading()
  
   
end = time.time()
print(end - start)

    
