''"""
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
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from io import StringIO 


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
                callable(subclass.create_set_up) and
                hasattr(subclass, 'find_interfaces') and 
                callable(subclass.find_interfaces) and
                hasattr(subclass, 'find_mac_addresses') and 
                callable(subclass.find_mac_addresses) and
                hasattr(subclass, 'uni_shell') and 
                callable(subclass.uni_shell) and
                hasattr(subclass, 'find_ipv4') and 
                callable(subclass.find_ipv4) or
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
    def save_list_output(self, path: str, list_name: str):
        """Save output from lists"""
        
        raise NotImplementedError


    @abc.abstractmethod
    def create_set_up(self, path: str ):
        """If a SetUp file does not exist create it"""
        
        raise NotImplementedError
    

    @abc.abstractmethod
    def find_interfaces(self, input_string: str ):
       """Search for Interfaces"""
       raise NotImplementedError

    @abc.abstractmethod
    def find_mac_addresses(self, input_string: str ):
        """Search for Mac addrress"""
        raise NotImplementedError

    @abc.abstractmethod
    def find_ipv4(self, input_string: str ):
        """Search for ipv4"""
        raise NotImplementedError


    @abc.abstractmethod
    def find_mac_interfaces(self, input_string: str ):
        """Search for Mac addrress interfaces"""
        raise NotImplementedError

    @abc.abstractmethod
    def uni_shell(self, host_ip: list,command_set: str ):
        """Univeral SSH conection"""
        raise NotImplementedError

    
    @abc.abstractmethod
    def command_sets(self, device_id: str,command_set: str ):
        """Select deice type and automated commands to exexute"""
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
        For live Cisco devices
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



    
    def find_interfaces(self, input_string: str ):
        """Search for Interfaces"""
   
        all_interfaces = []    
        
        pat = r"(^(interface (?P<intf_name>\S+))"
        found_interfaces = re.finditer(pat,input_string,re.MULTILINE)

        for intf_part in found_interfaces:
            a = ((intf_part.group("intf_name")))
            all_interfaces.append(a)

        return all_interfaces


    
    def find_ipv4(self, input_string: str ):
        """Search for ipv4"""

        pat = r"(\d\d?\d?\.\d\d?\d?\.\d\d?\d?\.\d\d?\d?)"
        ipv4_address = re.findall(pat, input_string)
        return ipv4_address

 
    
    def find_mac_addresses(self, input_string: str ):
         """Search for Mac addrress"""
         
         pat = r"([0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4})"
         mac_address =  re.findall(pat, input_string)
         return mac_address


    def find_mac_interfaces(self, input_string: str ):
        """Search for Mac addrress interfaces"""
        
        pat = r"(?<=ARPA).*"
        mac_int =  re.findall(pat, input_string)
        mac_int = [x.strip(' ') for x in mac_int]#remove spaces

        rem = ['\r']
        pat =  '|'.join(rem)
        mac_int= [re.compile(pat).sub("", m) for m in mac_int]  

        return(mac_int)



    
    def uni_shell(self, host_ip: list,command_set: str,select_term_zero: str ):
        """Univeral SSH conection"""
        
        #terminal_length = self.term_zero(device_id=select_term_zero)
        

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host_ip, port=22, username=self.username, password=password, look_for_keys=False, timeout=None)        
            channel = ssh.get_transport().open_session() 
            channel.invoke_shell()
        except Exception as e:
            print(host_ip,e.args)
            return

        #channel.sendall(terminal_length)#Send terminal length zero command
        time.sleep(.2)



        """
        Once a  connection is established:
        1. send the shell input Commands
        by looping the self.commands list
        """
        for x in command_set:
            channel.sendall(x+"\n")
            time.sleep(.5)

        time.sleep(3)#Time to wait to receive channel bytes

        shell_output = channel.recv(9999).decode(encoding='utf-8') #Receive buffer output



        ssh.close()
        return  shell_output


    
    def command_sets(self, device_id: str,command_set: str ):
        """Select deice type and automated commands to exexute"""

        if device_id == 'Cisco_IOS':
            if command_set == 'arp_table':
                commands = ['enable','terminal length 0','show arp']

                return commands


            if command_set == 'cef_table':
                commands = ['enable','terminal length 0','show ip cef']

                return commands

            
         

        



class ChannelClass(LoadDataToList):
    
    count_cores = psutil.cpu_count(logical=True)#Count number of cores/threads in CPU

    def __init__(self):

        self.date_time = datetime.datetime.now().strftime("%Y-%m-%d")
        self.username = username
        self.password = password
        self.single_host = single_host


    
    def HyperShell(self,host_ip):

        """Use this for looping large numbers of devices"""
       
        terminal_length = self.term_zero(device_id='Cisco')
        
        commands = self.load_data_source(path='Setup\\Cisco_commands.dat')

        
        
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
        

    
    

    def SendCommands(self,selected_device,
                     selected_commands,term_zero):

        
        commands = self.command_sets(device_id=selected_device,
                                     command_set=selected_commands)

       
        for x in self.single_host:
            command_output = self.uni_shell(host_ip=x,command_set=commands,
                                             select_term_zero=term_zero)

        
  
        return command_output


        
            
    
    def SortCommandOutPut(self,output_type):

        """
        Selects command set to send to remote devices
        """
        
        if output_type == 'cisco_arp':
            
            command_output = self.SendCommands('Cisco_IOS','arp_table','Cisco')#<---
            
            all_macs_address, all_interfaces, all_ipv4_address, all_host_names = [],[],[],[]
            
            host_name = self.find_host_name(device_id='Cisco_IOS',search=str(command_output))
            mac_address = self.find_mac_addresses(input_string=str(command_output))
            interface = self.find_mac_interfaces(input_string=str(command_output))
            ipv4_address = self.find_ipv4(input_string=str(command_output))
            all_macs_address.append(mac_address)
            all_host_names.append(host_name)
            all_interfaces.append(interface)
            all_ipv4_address.append(ipv4_address)
            
            return all_host_names,all_macs_address,all_interfaces,all_ipv4_address 
        
        else:
            pass


    
        if output_type =='cisco_cef':

            command_output = self.SendCommands('Cisco_IOS','cef_table','Cisco')#<---

            


            return command_output

            
            
    

    def DrawArpTable(self,device_id):

        if device_id=='Cisco_IOS':
            all_host_names,all_macs_address,all_interfaces,all_ipv4_address = self.SortCommandOutPut('cisco_arp')
    
            
            mac_len = len(all_macs_address)
    
    
            G=nx.Graph()
    
            G.add_node(all_host_names[0])
    
    
            for i in range (len(all_interfaces[0])):
                G.add_edges_from([(all_host_names[0], all_interfaces[0][i])])
    
    
            for i in range (len(all_macs_address[0])):
                G.add_edges_from([(all_macs_address[0][i], all_interfaces[0][i])])
    
    
            for i in range (len(all_macs_address[0])):
                G.add_edges_from([(all_macs_address[0][i], all_ipv4_address[0][i])])

            

            
            """
            #Set Colors:
            #Nodes = green
            #Edges = Blue
            """
            node_color_map = []
            edge_color_map = ['Red']


            for node in G:
                if node ==all_host_names[0]:
                    node_color_map.append('green')

                else:
                    node_color_map.append('blue')

            nx.edge_connectivity(G)

            random_pos = nx.random_layout(G, seed=42)
            pos = nx.spring_layout(G, pos=random_pos)
            plt.figure(3,figsize=(46,12)) 
            plt.subplot(121)
            nx.draw(G, node_color=node_color_map,edge_color=edge_color_map, with_labels=True)


    

    def DrawCefTable(self):

        #pat = r"(\d\d?\d?\.\d\d?\d?\.\d\d?\d?\.\d\d?\d?)(.*)(\n)"
        pat = r"(.*)(receive)(.*)"

        command_output = self.SortCommandOutPut('cisco_cef')
          
        ip_column = re.findall(pat,
                               #r"( .*\n)*"
                               #r"( transport input telnet\n)",
                               command_output,
                               re.MULTILINE)


        #print(ip_column)

        not_active_routes = ['drop']

        p =  re.compile( '|'.join(not_active_routes))


        list_of_lists = [list(elem) for elem in ip_column]

        print(list_of_lists)
        


       


                   
                     


        

        


   

        

        



         
       
         
         # command_output = self.SortCommandOutPut('cisco_cef')

         #new = StringIO(command_output) 

         #print(new)

         #df = pd.read_csv(new, sep ="\n") 

         #print(df.columns)

         



        



         



       

    
    
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
        
        SHELL_OUT = THREADS.map(self.HyperShell, loop_hosts)

        self.SaveToFile(SHELL_OUT)#Save output to file


        THREADS.close()



        


    def main(self):
        
        #self.MultiThreading()
        
        #self.DrawArpTable('Cisco_IOS')
        self.DrawCefTable()
        
        #self.SendCommands('Cisco_IOS')
        #self.test() 
        #self.SortCommandOutPut('cisco_arp')
        #self.DrawCefTable()

        

        
        
              
if __name__ == "__main__": 
    single_host = ['172.19.1.251']
    username = 'cisco'#Enter network device username temp solution
    password = 'cisco' #temp solution 
    a = ChannelClass()
    a.main()
    
   
 
  
   
end = time.time()
print(end - start)

    
