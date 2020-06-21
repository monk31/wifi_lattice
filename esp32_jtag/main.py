# -*- coding: utf-8 -*-
"""
Created on Sat May 18 15:02:57 2019

@author: yann brengel <ybrengel@gmail.com>
"""

import gc
import os
import sys
import time
try:
    import usocket as socket
except:
    import socket
import network
import uselect as select


from const_machx02 import *
from svf import *
from ubinascii import *


WIFI_SSID = "YOUR SSID"
WIFI_PASS = "YOUR PASSWD"


BUFFER_SIZE    = 4096


# wifi configuration
def config_wifi():
    sta = network.WLAN(network.STA_IF)  # creation client d’acces WiFi
    sta.active(True)  # activation du client d’acces WiFi   
    sta.connect(WIFI_SSID, WIFI_PASS)  # connexion au point d’acces WiFi
    while(sta.isconnected() == False):
        time.sleep(1)
    ip = sta.ifconfig()[0]  # on recupere l’adresse IP
    return ip 

# program machx02
def program(file_transfered,machx02,client_stream):
    next_state = "PROGRAM"        
    f         = open(file_transfered)
    fusetable = f.readlines()
    listfile = os.listdir()
    if not file_transfered in listfile:
        message = "programm jed not found, programming is KO \n"
        print (message)
        client_stream.write(message)
    else:
        message = "ACK programm jed JTAG \n"
        print(message)          
        inst_svf  = svf(fusetable)                
        crc,error = inst_svf.erase_program_verify()
        message_crc = "crc = " + hex(crc) + "\n"
        print(message_crc)                 
        if  not error :
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
            machx02 =   machx02_jtag()
            deviceId  = machx02.get_device(recv_client_str)            
            machx02.reset_jtag()
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
            f = open("program_cfg.jed", "wb")
        elif next_state == "TRANSFERT":
            if 'EOF\n' in recv_client_str :
                recv_client_str = recv_client_str[:-4]  # remove EOF
                f.write(recv_client_str)
                next_state = "TRANSFERT_COMPLETE"
                message = "ACK transfert complete ....\n"
                print(message)
                f.close()                
                file_transfered = "program_cfg.jed"
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
        
    client_stream.close()
    sys.exit()       

#
# MAIN   
if __name__ == '__main__':
   
    ad_ip = config_wifi()
    print("adress ip",ad_ip)
    server_port = 241
    main(ad_ip,server_port)   

