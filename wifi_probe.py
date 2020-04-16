# coding: utf-8
"""
Created on Sat Mar 28 15:02:57 2020

@author: yann brengel <ybrengel@gmail.com>
"""

import subprocess
import sys
import re
import time
from  socket import *
import os,fnmatch

BUFFER_SIZE = 4096
STX = '\x02*'
ETX = '\x03'
EOF = "*"
listdevice  = ["MACHX02_DEVICE_ID_1200","MACHX02_DEVICE_ID_2000","MACHX02_DEVICE_ID_4000","MACHX02_DEVICE_ID_7000"]


# search esp32 adress ip in network
def search_adress():
    adress = None
    batcmd = "nmap -sP 192.168.4.*"
    result = subprocess.check_output(batcmd, shell=True)
    result_str = result.decode("utf-8")
    dns_report = re.findall('\nNmap scan report for\s\w+\s\(\d\d\d.\d\d\d.\d.\d+\)', result_str)
    if len(dns_report) == 1:
      matchObj = re.search( r'espressif', dns_report[0], re.M|re.I)
      if matchObj:
        adress = re.findall('\d\d\d.\d\d\d.\d.\d+',dns_report[0])
      else:
        adress = None    
    return adress



# to build list pins NOT USED
def get_list_pins(file_jed):
  list_pins = []
  f = open(file_jed,"r")  
  while True:
      line       = f.readline()
      if "PINS" in line:
          matchObj = re.match(r'NOTE\sPINS\s(\w+)\s:\s(\d+)\s:\s(\w+)',line, re.M|re.I)
          if matchObj:         
            list_pins.append(matchObj.groups())
      elif "L000000" in line:
          break 
  f.close()
  return list_pins

# set only bit selected, this is just to demo a extest
def set_boundary_scan(list_bits,number):
  boundary_scan = [] 
  for bit,name,type_pin in list_bits:            
        boundary_scan.append("0")
  boundary_scan[number] = "1"
  return boundary_scan


# to list bits in transmit
def get_list_bits(file_bsm):
  f = open(file_bsm,"r")
  list_bits = []
  found = False
  while True:
      line       = f.readline()
      if  "end LCMXO2" in line:
          break
      else:        
          value = re.match(r'\tattribute\sBOUNDARY_REGISTER\sof\s',line, re.M|re.I)
          if value:
              found = True       
          if found:          
              new_line = line.replace("(","").replace('"', '').replace(')','')
              line_split = new_line.split(",")
              if len(line_split) >1:
                  value    = line_split[0].strip()
                  name     = line_split[1].strip()
                  type_pin = line_split[2].strip()
                  matchObj = re.match(r'\d+',value)
                  if matchObj:
                      number = matchObj.group(0)
                      element= int(number),name,type_pin
                      list_bits.append(element)
  f.close()
  
  return(list_bits)

def display_menu(list_step):
  # os.system('clear')
 
  print("select your choice :")
  if "SELECT_FILE" in list_step:
      print("1: select_your device --> OK")
  else:
      print("1: select_your device")
  if "EXTEST" in list_step:
      print("2: select your file   --> OK")
  else:
      print("2: select_your file")  
  print("3: extest")
  print("4: init prog")
  print("5: exit program")


def ack_server(socket):
   server_rcv = socket.recv(1024)
   print(server_rcv.decode()) 
   if "ACK" in server_rcv.decode():
     return True
   else:
     return False



if __name__ == '__main__':
  list_step = []
  port = 241
  EOF = 'EOF\n'
  res  = search_adress()
  if res == None:
    print("esp32 is not in network")
    sys.exit()
  else:
    host = res[0]
    print("adress ip esp32 is :",host)   
  socket = socket(AF_INET, SOCK_STREAM)
  socket.connect((host, port))
  print("Connection on port",port)

  next_state = "DEVICE"
  display_menu(list_step)
  
  while(True):  
    code = input()
    code_encode = code.encode()
    if code == "1" and next_state == "DEVICE":
      for i in range(len(listdevice)):
        print("select your device ",str(i), " : ",listdevice[i])
        select_ok = False
      while(select_ok == False):
        select_device = input()
        if int(select_device) <= len(listdevice):
          device = listdevice[int(select_device)]         
          time.sleep(1)
          socket.send(device.encode())
          print("send device",device.encode())
          if ack_server(socket):             
             next_state = "SELECT_FILE"
             list_step.append(next_state)           
          else:
             print(" MACHX02 device is different on the board  ")
          display_menu(list_step)
          select_ok = True
        else:
           print(" ERROR MACHX02 is not the device ")
           select_ok = True
           display_menu(list_step)
  

    # selection file
    if code == "2" and next_state == "SELECT_FILE":
      listfile = fnmatch.filter(os.listdir('.'), '*.bsm')     
      if listfile == None:
          print("file not found, program jed must be located in current directory")
      else:
          for i in range(len(listfile)):
            print("select your file ",str(i), " : ",listfile[i])
          select_ok = False
          while(select_ok == False):
            select_file = input()
            if int(select_file) <= len(listfile):
              bsm_file = listfile[int(select_file)]
              print("file selected =",bsm_file)
              list_bits = get_list_bits(bsm_file)                  
              next_state = "EXTEST"
              list_step.append(next_state)
              display_menu(list_step)
              select_ok = True
            else:
              print("error select file")
    # extest
    elif code == "3" and next_state == "EXTEST":            
      if bsm_file not in listfile:
         print("error file is unknown")
      else:
        for i in range(len(list_bits)):
          number,name,type_pin = list_bits[i]
          if name != "*":
            print("select bit  ",number, " : ",name)  
        select_ok = False
        while(select_ok == False):
          select_bit = input()
          if int(select_bit) <= len(list_bits):            
             list_data = set_boundary_scan(list_bits,int(select_bit))
             pin_name = [x[1] for x in list_bits   if x[0] == int(select_bit)]
             print("set bit from extest",pin_name[0]," bit : ",select_bit)
             select_ok = True
        data = ''.join(list_data)
        socket.send(next_state.encode())
        socket.sendall(data.encode())
        code_encode = EOF.encode()   
        socket.send(code_encode)                   
        ack_server(socket)
    # init prog
    elif code == "4":
      message = "INIT"
      socket.send(message.encode())
      if ack_server(socket):
        list_step = []
        next_state = "DEVICE"
        display_menu(list_step)
        print("init prog")
    # exit program
    elif code == "5":
      print(" good bye")
      break
    elif code == "1" and next_state != "DEVICE":
      print(" selected a device before ")
    elif code == "2" and next_state != "SELECT_FILE":
      print(" selected a device before ")
    elif code == "3" and next_state != "EXTEST":
      print(" selected deive and file before ")
    elif int(code) > 5:
      print("bad selected ...")
    # bad selected  
    
  socket.close()
