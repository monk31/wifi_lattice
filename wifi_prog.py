# coding: utf-8
import subprocess
import sys
import re
import time
from  socket import *
import os,fnmatch
from const import *

BUFFER_SIZE = 4096

# to extract checksum jed file
def extract_checksum(file):
    jed = open(file,"r")
    while True:
        line       = jed.readline()
        if line[0][0] == "C":          
            fusechecksum = line[1:-2]
            print("crc jed file is ",fusechecksum)
            break 
    jed.close()   
    return fusechecksum


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

# transfert  file socket
def transfert_file(socket,file_jed):
    EOF = 'EOF\n'
    with open(file_jed, "rb") as f:
        while (True):
          # read the bytes from the file
          bytes_read = f.read(BUFFER_SIZE)
          if not bytes_read:             
              code_encode = EOF.encode()   
              socket.send(code_encode)
                # file transmitting is done
              break                   
          socket.sendall(bytes_read)
    f.close()


# to check file jed compatible
def check_program_jed(file_jed,device):
  f = open(file_jed,"r")
  device_ok = False
  while True:
    line       = f.readline()
    if "NOTE DEVICE NAME:" in line:
        matchObj = re.search( r'NOTE\sDEVICE\sNAME:\t\w+-\w+', line, re.M|re.I)
        if matchObj:
          device_name = re.findall('LCMXO2-\d\d\d\d',line)          
          device_file = device_name[0]
          device_type = device[18:]
          if device_type == device_file[7:]:
             device_ok = True
          else:
             device_ok = False         
        else:
          device_ok = False
        break 
  f.close()
  return device_ok


# to generate only cfg_data
def build_program_jed(file_jed):
    ETX = '\x03'    
    f = open(file_jed,"r")
    record_line = False
    file_cfg = "program_cfg.jed"
    fusetable = open(file_cfg,"w")
    while True:
        line  = f.readline()
        line_strip = line.strip()
        if len(line_strip) != 0:
            if ETX in line:
                #print("only transfert cfg data for ",file_jed)
                fusetable.close()
                f.close()
                break
            elif line_strip == "L000000":
                record_line =True
            elif line_strip == "*":
                record_line = False        
            elif "NOTE END CONFIG DATA" in line_strip:
                record_line =False
            elif record_line:
                fusetable.write(line)

# to check crc
def check_crc(mess,file_prog):    
    matchObj = re.search( r'0x\w+', mess, re.M|re.I)
    if matchObj:
      value = matchObj.group()      
      if len(value) != 6:
        crc = value[3:]
      else:
        crc = value[2:]    
      crc_file = extract_checksum(file_prog)    
      if crc.upper() == crc_file:
          return True,crc
      else:
          return False,crc
    else:
      print("error check crc")
      return False,0

def display_menu(list_step):
  # os.system('clear')
 
  print("select your choice :")
  if "SELECT_FILE" in list_step:
      print("1: select_your device --> OK")
  else:
      print("1: select_your device")
  if "PROGRAM" in list_step:
      print("2: select your file   --> OK")
  else:
      print("2: select_your file")
  if "CRC" in list_step:
      print("3: program            --> OK")
  else:
      print("3: program")
  if "INIT" in list_step:
      print("4: check crc          --> OK")
  else:
      print("4: check crc")
  print("5: init prog")
  print("6: exit program")


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
      listfile = fnmatch.filter(os.listdir('.'), '*.jed')
      if "program_cfg.jed" in listfile:
        listfile.remove("program_cfg.jed")
      if listfile == None:
          print("file not found, program jed must be located in current directory")
      else:
          for i in range(len(listfile)):
            print("select your file ",str(i), " : ",listfile[i])
          select_ok = False
          while(select_ok == False):
            select_file = input()
            if int(select_file) <= len(listfile):
              prog_file = listfile[int(select_file)]
              print("file selected =",prog_file)
              if check_program_jed(prog_file,device):
                build_program_jed(prog_file)
                next_state = "PROGRAM"
                list_step.append(next_state)
                display_menu(list_step)
                select_ok = True
              else:
                print("bad file selected, select with type : ",device)                
            else:
              print("error select file")
    # program
    elif code == "3" and next_state == "PROGRAM":
      if prog_file not in listfile:
         print("error file is unknown")
      else:                          
        socket.send(next_state.encode())       
        print("programming in progress ...")             
        transfert_file(socket,"program_cfg.jed")
        ack_server(socket)      # transfert complete      
        if ack_server(socket):
            next_state = "CRC"
            list_step.append(next_state)
            display_menu(list_step)
        else:
          print("error transfert")
          display_menu(list_step)
    # check CRC
    elif code == "4" and next_state == "CRC":     
      message = "VERIFY_CRC"
      socket.send(message.encode())
      server_rcv = socket.recv(1024)    
      if prog_file:
          crc_ok,crc = check_crc(server_rcv.decode(),prog_file)
          if crc_ok:
            next_state = "INIT"
            list_step.append(next_state)
            display_menu(list_step)
            print("crc programmed ",crc," is ok")
          else:
            print("error crc ",crc)  
    # init prog
    elif code == "5":
      message = "INIT"
      socket.send(message.encode())
      if ack_server(socket):
        list_step = []
        next_state = "DEVICE"
        display_menu(list_step)
        print("init prog")
    # exit program
    elif code == "6":
      print(" good bye")
      break
    elif code == "1" and next_state != "DEVICE":
      print(" selected a device before ")
    elif code == "2" and next_state != "SELECT_FILE":
      print(" selected a device before ")
    elif code == "3" and next_state != "PROGRAM":
      print(" selected deive and file before ")
    elif int(code) > 6:
      print("bad selected ...")
    # bad selected  
    
  socket.close()
