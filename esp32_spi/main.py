# -*- coding: utf-8 -*-
"""
Created on Sat May 18 15:02:57 2019
# yann brengel <ybrengel@gmail.com>
@author: ybren
"""
# version compatible wifi prog
import gc
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
from machx02_spi import *
from ubinascii import *
import micropython

WIFI_SSID = "raspi-webgui"
WIFI_PASS = "ChangeMe"

BUFFER_SIZE    = 4096

def config_wifi():
    wlan = network.WLAN(network.STA_IF)  # creation client d’acces WiFi
    if not wlan.isconnected():
        wlan.active(True)  # activation du client d’acces WiFi       
        wlan.config(dhcp_hostname='amixngs')       
        wlan.connect(WIFI_SSID, WIFI_PASS)  # connexion au point d’acces WiFi
        while not wlan.isconnected():
            pass                     
    ip = wlan.ifconfig()[0]  # on recupere l’adresse IP
    host = wlan.config('dhcp_hostname')
    print('Wifi connected as {}/{}, net={}, gw={}, dns={}'.format(host, *wlan.ifconfig()))
    return ip


# we recorded only configure_data
# recursive parser
# def parseline(line,start_record,end_record):
#     fusechecksum = ""
#     if "NOTE END CONFIG DATA" in line:
#         end_record =True
#     if start_record == True and EOF in line:
#        start_record = False
#     elif line == STX: # test if first line = stx
#         print ("STX OK")
#     elif "NOTE" in line:
#          start_record = False  
#     elif ETX in line:
#          start_record = False      
#     elif "QF" in line:     # check QF
#         if  line[2:-1] != MACHXO2_SIZE_FUSETABLE_7000:
#             print ("bad QF",line[2:-2])
#             error = MACHXO2_JEDEC_ERROR[4]
#             start_record = False              
#     elif line[:-1] == "F0":
#         start_record = False 
#         # fusetable reset
#     elif line[:-1] == "F1":
#         start_record = False 
#         # fusetable set
#     elif line[0][0] == "C":          
#         fusechecksum = line[1:-1]
#         start_record =False  
#     elif EOF in line:
#         start_record =False        
#     elif line[0][0] == "L" and not end_record:               
#         start_record =True   
#     return start_record,fusechecksum,end_record


# program machx02
@micropython.native
def program(file_transfered,machx02,client_stream):
    next_state = "PROGRAM"        
    f  = open(file_transfered)
    if (not machx02.enable()):
           message = "Cannot enable configuration mode, status: "+machx02.readstatus()+"\n"
           print(message)
           client_stream.write(message)
           sys.exit()
      
    # read featureRows
    feature_row,feabits = machx02.readfeatures()
    message = "feature_row ="+hex(feature_row)+"\n"
    print (message)
   # client_stream.write(message)
    message = "feabits     ="+hex(feabits)+"\n"
    print (message)
  #  client_stream.write(message)	
    fusetable = f.readlines()
    listfile = os.listdir()    
    if not file_transfered in listfile:
        message = "programm jed not found, programming is KO \n"
        print (message)
        client_stream.write(message)
    else:
        message = "ACK programm jed  \n"
        print(message)
        result,crc = machx02.program(fusetable)        
        message_crc = "crc = " + hex(crc) + "\n"
        print(message_crc)                 
        if  result :
            message = "ACK programming Success \n"
            print (message)
            client_stream.write(message)
            next_state = "CRC"
        else:      
            message = "NAK programming Failed \n"
            print (message)
            client_stream.write(message) 
        f.close()
    return next_state,crc






#
# main  to accept request from client
# @micropython.native
def main(ip="192.168.4.16",server_port=241):
    s = socket.socket()
    boundaryscan_register = []  
    # Binding to all interfaces - server will be accessible to other hosts!
    addr = socket.getaddrinfo(ip,int(server_port))[0][-1]
    print("Bind address info:", addr)  
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   
    s.bind(addr)
    s.listen(5)
    print("Listening, connect your client")
    print ("la memoire alloue dans le heap est",gc.mem_alloc())
    print ("la memoire libre dans le heap est",gc.mem_free())
    res = s.accept()
    client_sock = res[0]
    client_addr = res[1]
    print("Client address:", client_addr)
    print("Client socket:", client_sock)
    client_stream = client_sock.makefile("rwb")
    next_state = "INIT"
    while True:        
        # reception client 
        recv_client       = client_stream.recv(BUFFER_SIZE)
        if not recv_client: break
        print("next_state",next_state)
        recv_client_str   = recv_client.decode("utf-8")
        #print(recv_client_str)
        # select machx02 fpga
        if "MACHX02" in recv_client_str and next_state == "INIT":
            print("reception device id \n")
            baudrate=400000            
            machx02 = machx02_spi(baudrate)
            deviceId  = machx02.get_device(recv_client_str)                   
            idcode = machx02.check_idcode()
            print ("id=",hex(idcode))
            if idcode == deviceId:
                message ="ACK idcode MACHX02 OK \n"
                print(message)
                client_stream.write(message)
                next_state = "PROGRAM"
            else:
                message = "NAK idcode MACHX02 not found \n"
                print(message,idcode,deviceId)
                client_stream.write(message)
                next_state = "INIT"
        
   # transfert and program
        elif "PROGRAM" in recv_client_str and next_state == "PROGRAM":            
            message = "ACK programing in progress ....\n"
            print (message)
            client_stream.write(message)         
            next_state = "TRANSFERT"
            file_transfered = "program_cfg.jed"	
            f = open(file_transfered, "wb")            
        elif next_state == "TRANSFERT":
            if 'EOF\n' in recv_client_str :
                recv_client_str = recv_client_str[:-4]  # remove EOF
                f.write(recv_client_str)
                next_state = "TRANSFERT_COMPLETE"
                message = "ACK transfert complete ....\n"
                print(message)                
                f.close()
                next_state,crc  = program(file_transfered,machx02,client_stream)   
            else:
                f.write(recv_client_str)
          # probing jtag
        elif "EXTEST" in recv_client_str and next_state == "PROGRAM":
            message = "RECEIVING EXTEST ....\n"
            print (message)
            next_state = "EXTEST"           
        elif  next_state == "EXTEST":
            message = "MESSAGE EXTEST ....\n"
            print (message)
            if 'EOF\n' in recv_client_str :
                recv_client_str = recv_client_str[:-4]  # remove EOF
                boundaryscan_register.append(recv_client_str)                
                machx02.send_extest(boundaryscan_register)
                boundaryscan_register = []
                message = "ACK send EXTEST ....\n"
                print (message)
                client_stream.write(message)
                next_state = "INIT"
            else:
                boundaryscan_register.append(recv_client_str)

        # check crc
        elif "VERIFY_CRC" in recv_client_str and next_state == "CRC":
            print (recv_client_str)                           
            message_crc = "crc programmed from esp32 is " + hex(crc) + "\n"
            print(message_crc)
            client_stream.write(message_crc)          
        elif "INIT" in recv_client_str:
            next_state = "INIT"
            message = "ACK init programm " + "\n" 
            client_stream.write(message)           
            message = "refresh \n"
            print (message)
            client_stream.write(message)   
            machx02.wakeup_device()            
            client_sock.close()         
    
    client_stream.close()
    sys.exit()       


#
# MAIN   
if __name__ == '__main__':
    micropython.alloc_emergency_exception_buf(100)
    ad_ip = config_wifi()
    print("adress ip",ad_ip)
    server_port = 241
    main(ad_ip,server_port)   

    
    