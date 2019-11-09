# -*- coding: utf-8 -*-
"""
Created on Sat May 18 15:02:57 2019
# yann brengel <ybrengel@gmail.com>
@author: ybren
"""

import os
import sys
import utime
import struct
try:
    import usocket as socket
except:
    import socket
import network

from const import *
from machine import Pin, SPI
from machx02_spi import *
from ubinascii import *

WIFI_SSID = "your_login"
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
    elif line == STX: # test if first line = stx
        print ("STX OK")
    elif "NOTE" in line:
         start_record = False  
    elif ETX in line:
         start_record = False      
    elif "QF" in line:     # check QF
        if  line[2:-1] != MACHXO2_SIZE_FUSETABLE_7000:
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



def main(micropython_optimize=False,ip="192.168.0.21",server_port=241):
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
            line_strip = line_str.strip()
            start_record,crc,end_record = parseline(line_strip,start_record,end_record)
            if start_record  and  not end_record and line_strip != "L0000000":
                fusetable.write(line_str)                
            elif crc != "":
                fusechecksum = crc
                message="fusechecksum="+fusechecksum+"\n"
                print (message)
                #client_stream.write(message)
            count = count + 1
            #print("parse line number =",count)           
            if ETX in line:            
                message="end of transfert JEDEC File \n"
                print (message)
                client_stream.write(message)                
                fusetable.close()
                break                   

        
 
        message ="esp32_spi LATTICE MACHX02 version 1.4 \n"
        print (message)
        client_stream.write(message)
        listfile = os.listdir()
        if not file_transfered in listfile:
           message = "programm jed not found \n"
           print (message)
           client_stream.write(message)
           sys.exit()
        
        f = open(file_transfered)
        if (not machx02.enable()):
           message = "Cannot enable configuration mode, status: "+machx02.readstatus()+"\n"
           print(message)
           client_stream.write(message)
           sys.exit()
      
        # read featureRows
        feature_row,feabits = machx02.readfeatures()
        message = "feature_row ="+hex(feature_row)+"\n"
        print (message)
        client_stream.write(message)
        message = "feabits     ="+hex(feabits)+"\n"
        print (message)
        client_stream.write(message)
      
        fusetable = f.readlines()
        message = "Programming ... \n"    
        print (message)
        client_stream.write(message)
        result,crc = machx02.program(fusetable)
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
          sys.exit()        
        if  result :
          message = "programming Success \n"
          print (message)
          client_stream.write(message)
        else:      
          message = "programming Failed \n"
          print (message)
          client_stream.write(message)


        message = "refresh \n"
        print (message)
        client_stream.write(message)   
        machx02.wakeup_device()
        f.close()
        client_stream.close()
        os.remove(file_transfered)
        if not micropython_optimize:
            client_sock.close()
    
if __name__ == '__main__':    
         
    ad_ip = config_wifi()    
    print("adress ip",ad_ip)

    baudrate=400000
    deviceId = MACHXO2_DEVICE_ID_7000
    machx02 = machx02_spi(baudrate,deviceId)
    utime.sleep(1)
    if (not machx02.check_idcode()):
        print( "idcode MACHX02 not found" )
        sys.exit()
    else:
        print( "idcode MACHX02 OK" )

    server_port = 241
    main(False,ad_ip,server_port)
    
    