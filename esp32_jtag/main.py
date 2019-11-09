# -*- coding: utf-8 -*-
"""
Created on Sat May 18 15:02:57 2019

@author: yann brengel <ybrengel@gmail.com>
"""

import os
import sys
import time
import struct
try:
    import usocket as socket
except:
    import socket
import network

from const import *
from machx02_jtag import *
from jedec import *
from ubinascii import *

WIFI_SSID = "your login"
WIFI_PASS = "your password"





def config_wifi():
    sta = network.WLAN(network.STA_IF)  # creation client d’acces WiFi
    sta.active(True)  # activation du client d’acces WiFi   
    sta.connect(WIFI_SSID, WIFI_PASS)  # connexion au point d’acces WiFi
    while(sta.isconnected() == False):
        time.sleep(1)
    ip = sta.ifconfig()[0]  # on recupere l’adresse IP
    return ip


# we recorded only configure_data
# recursive parser
def parseline(line,start_record,end_record):
    fusechecksum = ""
    if "NOTE END CONFIG DATA" in line:
        end_record =True
    if start_record == True and EOF in line:
       start_record = False
    elif line == STX: # test if fir st line = stx
        print ("STX OK")
    elif "NOTE" in line:
         start_record = False  
    elif ETX in line:
         start_record = False      
    elif "QF" in line:     # check QF       
        if  line[2:-2] != MACHXO2_SIZE_FUSETABLE_7000:
            print ("bad QF",line[2:-2])
            error = MACHXO2_JEDEC_ERROR[4]
            start_record = False              
    elif line[:-1] == "F0":
        start_record = False 
        # fusetable reset
    elif line[:-1] == "F1":
        start_record = False 
        # fusetable set
    elif line[0][0] == "C":          
        fusechecksum = line[1:-1]
        start_record =False  
    elif EOF in line:
        start_record =False        
    elif line[0][0] == "L" and not end_record:               
        start_record =True   
    return start_record,fusechecksum,end_record

# programmer machx02
def programm_machx02(file_transfered,machx02,client_stream,fusechecksum):
    error = False
    f = open(file_transfered)
    fusetable = f.readlines()  
    
    machx02.prog_bscan_register()
    
    status = machx02.check_status()
    status = machx02.check_key_prot()
    
    print("check_key_prot",hex(status))
    if not status:
        print ("problem check key prot")
    machx02.enable_flash()
    
    status =  machx02.check_otp_fuses()
    print("check_otp_fuses",hex(status))
    if not status:
        print ("problem check key prot")       
   
    read_feature,read_feabits = machx02.readfeatures()
    print("read_feature",hex(read_feature))
    print("read_feabits",hex(read_feabits))
    status =machx02.erase_flash()
    print("erase_flash",hex(status))
    if not status: 
        print ("problem erase flash")
    
  #  message = "Programming ... \n"    
  #  print (message)
 
    crc = machx02.program(fusetable)  
    value = unhexlify(fusechecksum)
    fusechecksum_int =  (value[0] << 8) + value[1]        
    if crc == fusechecksum_int:
        message = "checksum OK ="+fusechecksum+"\n"
        print (message)
        client_stream.write(message)
    else:      
        message = "checksum Failed"+str(crc)+"\n"
        print (message)
        client_stream.write(message)
        error = True

    machx02.disable()
    machx02.reset_jtag()
    f.close()
    return error
#
# main 
def main(micropython_optimize=False,ip="192.168.4.16",server_port=241,machx02=None):
    s = socket.socket()   
    #fusetable =[]
    # Binding to all interfaces - server will be accessible to other hosts!
    addr = socket.getaddrinfo(ip,int(server_port))[0][-1]
    print("Bind address info:", addr)  
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    print("Listening, connect your client")
    print ("la memoire alloue dans le heap est",gc.mem_alloc())
    print ("la memoire libre dans le heap est",gc.mem_free())
    # on test si l'on peut charger la version

    while True:
        res = s.accept()
        client_sock = res[0]
        client_addr = res[1]
        print("Client address:", client_addr)
        print("Client socket:", client_sock)

        if not micropython_optimize:
            # To read line-oriented protocol (like HTTP) from a socket (and
            # avoid short read problem), it must be wrapped in a stream (aka
            # file-like) object. That's how you do it in CPython:
            client_stream = client_sock.makefile("rwb")
        else:
            # .. but MicroPython socket objects support stream interface
            # directly, so calling .makefile() method is not required. If
            # you develop application which will run only on MicroPython,
            # especially on a resource-constrained embedded device, you
            # may take this shortcut to save resources.
            client_stream = client_sock

        message ="Download JEDEC File in progress ... \n"
        print (message)
        client_stream.write(message)
        count = 0 
        start_record = False
        end_record = False
        file_transfered = "programm.jed"
        fusetable = open(file_transfered,"w")
        while True:
            line       = client_stream.readline()            
            line_str   = line.decode("utf-8")
            # fusetable.write(line_str)
            line_strip = line_str.strip()
            start_record,crc,end_record = parseline(line_strip,start_record,end_record)
            if start_record  and  not end_record and line_strip != "L0000000":
                fusetable.write(line_str)                
            elif crc != "":
                fusechecksum = crc
                message="fusechecksum="+fusechecksum+"\n"
                print (message)
                client_stream.write(message)
            count = count + 1
            print("parse line number =",count)           
            if ETX in line:            
                message="end of transfert JEDEC File \n"
                print (message)
                client_stream.write(message)                
                fusetable.close()
                break                   

    
        message ="esp32_jtag LATTICE MACHX02 version 1.4 \n"
        print (message)
        client_stream.write(message)
        listfile = os.listdir()
        if not file_transfered in listfile:
           message = "programm jed not found \n"
           print (message)
           client_stream.write(message)
           sys.exit()

        message ="programming jedec... \n"
        print (message)
        client_stream.write(message)     
        error = programm_machx02(file_transfered,machx02,client_stream,fusechecksum)
        if  not error :
          message = "programming Success \n"
          print (message)
          client_stream.write(message)
        else:      
          message = "programming Failed \n"
          print (message)
          client_stream.write(message)
        client_stream.close()
        os.remove(file_transfered)
        if not micropython_optimize:
            client_sock.close()

if __name__ == '__main__':
   
    ad_ip = config_wifi()
    print("adress ip",ad_ip)
    
    deviceId = MACHXO2_DEVICE_ID_1200
    machx02 = machx02_jtag(deviceId)
    
    machx02.reset_jtag()
    
    idcode = machx02.check_idcode()
    print ("id=",hex(idcode))
    if idcode == deviceId:
        print( "idcode MACHX02 OK" )
    else:
        print( "idcode MACHX02 not found" )
        sys.exit()
   
    server_port = 241
    file_transfered = "programm.jed"
    
    main(False,ad_ip,server_port,machx02)
