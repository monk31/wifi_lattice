# -*- coding: utf-8 -*-
"""
Created on Fri May 17 22:23:12 2019
# yann brengel <ybrengel@gmail.com>
@author: ybren
"""
import os
import sys
import utime
import time
from ubinascii import *
from const import *
from machine import Pin, SPI
import gc

# class to manage spi MACHX02 
# 
# 
class machx02_spi(object):
  # bit12:busy, bit13:failed, bit9:enabled
  status={"busy":4096,"failed":8192,"enabled":512,"done":256}
  mask  = 0x00000000FFFFFFFF

  def __init__(self,baudrate):  
    self.cs = Pin(15, Pin.OUT)
    self.cs.on()
    self.hspi = SPI(1,baudrate=400000,sck=Pin(14), mosi=Pin(13), miso=Pin(12))
    self.deviceid = None
    
	
	
  # asessor
  def get_device(self,device):        
      if device == "MACHX02_DEVICE_ID_1200":
          self.deviceid = MACHXO2_DEVICE_ID_1200
      elif device == "MACHX02_DEVICE_ID_2000":
          self.deviceid = MACHXO2_DEVICE_ID_2000
      elif device == "MACHX02_DEVICE_ID_4000":
          self.deviceid = MACHXO2_DEVICE_ID_4000
      elif device == "MACHX02_DEVICE_ID_7000":
          self.deviceid = MACHXO2_DEVICE_ID_7000
      return self.deviceid	
                   
  # transfert spi
  def spiTrans(self,cmd,size):    
    resp_machx02_spi = bytearray(size)    
    self.hspi.init(baudrate=400000,sck=Pin(14), mosi=Pin(13), miso=Pin(12),firstbit=SPI.MSB ) # set the baudrate* 
    self.cs.off()
    self.hspi.write_readinto(cmd,resp_machx02_spi)    
    self.cs.on()
    return resp_machx02_spi
       
  # check idcode
  def check_idcode(self):    
    cmd = bytearray([MACHXO2_CMD_READ_DEVICEID, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    resp_machx02_spi = self.spiTrans(cmd,8)
    resp_machx02_spi_int = self.from_bytes_big(bytes(resp_machx02_spi))   
    result = resp_machx02_spi_int & self.mask   
    return result

  # disable
  def disable(self):
    #disable configuration
    cmd = bytearray([MACHXO2_CMD_DISABLE, 0x00, 0x00])
    resp_machx02_spi = self.spiTrans(cmd,3)
	# nop
    cmd = bytearray([MACHXO2_CMD_NOP, 0xFF, 0xFF, 0xFF])
    resp_machx02_spi = self.spiTrans(cmd,4)
 
    # refresh
    cmd = bytearray([MACHXO2_CMD_REFRESH, 0x00, 0x00])
    resp_machx02_spi = self.spiTrans(cmd,3)
    utime.sleep_ms(10000)  
    
  

  def wakeup_device(self):
    # refresh
    cmd = bytearray([MACHXO2_CMD_REFRESH, 0x00, 0x00])
    resp_machx02_spi = self.spiTrans(cmd,3)
    utime.sleep_ms(10000)  


  # enable offline configuration
  def enable(self):    
    cmd = bytearray([MACHXO2_CMD_ENABLE_OFFLINE, 0x08, 0x00,0x00])
    resp_machx02_spi = self.spiTrans(cmd,4)
    self.waitidle()

    # erase SRAM
    cmd = bytearray([MACHXO2_CMD_ERASE, 0x01, 0x00,0x00])
    resp_machx02_spi = self.spiTrans(cmd,4)
    self.waitidle()

    # bit 13 = fail
    # bit 9 = enabled
    resp = self.readstatus()
    print("status enable",resp)
    status_failed  = self.from_bytes_big(resp) & self.status["failed"]    
    status_enabled = self.from_bytes_big(resp) & self.status["enabled"]
    #print(status_failed,status_enabled)
    return (status_failed != self.status["failed"]) and (status_enabled == self.status["enabled"])
    
  # busy = bit12
  def waitidle(self):
    while True:
      resp = self.readstatus()
      # print("status=",resp)
      status_busy = self.from_bytes_big(resp) & self.status["busy"]
      #print("busy ",status_busy,type(status_busy))
      if status_busy == self.status["busy"]:
         #print("busy")
         utime.sleep_ms(1)   # datasheet = 200 us
      else:
         break
  
  
  def waitdone(self):
    while True:
      resp = self.readstatus()      
      status_done = self.from_bytes_big(resp) & self.status["done"]
      print("wait done status=",status_done)	  
      if status_done != self.status["done"]:
         print("wait done")
         utime.sleep_ms(1)   # datasheet = 200 us
      else:
         break
  
  
  def waitrefresh(self):
    while True:
      resp = self.readstatus()
      print("wait refresh=",resp)
      status_done = self.from_bytes_big(resp) & self.status["done"]
      print("status_done=",status_done)	  
      status_busy = self.from_bytes_big(resp) & self.status["busy"]	
      print("status_busy=",status_busy)	  
      if status_busy == self.status["busy"]:
        cmd = bytearray([MACHXO2_CMD_REFRESH, 0x00, 0x00])
        resp_machx02_spi = self.spiTrans(cmd,3)
        print("wait refresh")
        utime.sleep_ms(1)   # datasheet = 200 us
      else:
         break
  
  # read status
  def readstatus(self):
    cmd = bytearray([MACHXO2_CMD_READ_STATUS, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    resp_machx02_spi = self.spiTrans(cmd,8)
    return resp_machx02_spi
    
  # read features
  def readfeatures(self):
    cmd = bytearray([MACHXO2_CMD_READ_FEATURE, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    feature_row = self.spiTrans(cmd,12)
  #  read FEABITS
    cmd = bytearray([MACHXO2_CMD_READ_FEABITS, 0x00, 0x00, 0x00, 0x00, 0x00])
    feabits = self.spiTrans(cmd,6) 
    return self.from_bytes_big(feature_row),self.from_bytes_big(feabits)
 
 
 # to fill string      
  def zfl(self,s, width):
        # Pads the provided string with leading 0's to suit the specified 'chrs' length
        # Force # characters, fill with leading 0's
    return '{:0>{w}}'.format(s, w=width)
 
  # programm jedec file
  def program(self,fusetable):
  # erase flash
    cmd = bytearray([MACHXO2_CMD_ERASE, 0x04, 0x00, 0x00])
    resp_machx02_spi = self.spiTrans(cmd,4)
    print("erase flash ...")
    self.waitidle()
    resp = self.readstatus()    
    status_failed = self.from_bytes_big(resp) & self.status["failed"]
    if status_failed == self.status["failed"]:
      return False

  # set address to zero
    cmd = bytearray([MACHXO2_CMD_INIT_ADDRESS, 0x00, 0x00, 0x00])
    resp_machx02_spi = self.spiTrans(cmd,4)
    #print("set adress to 0")
    self.waitidle()		

  # program pages    
    sizefile = len(fusetable)
    nb_bit = sizefile * 128
    # not implemented, because ufm not programmed
    # if nb_bit != int(MACHXO2_SIZE_FUSETABLE_7000):
       # print("error size fusetable",nb_bit)
       # sys.exit()
    # else:
       # print("size fusetable",nb_bit)
    #lines = [i.strip() for i in fusetable]    
    numbit = 0    
    crc = 0
    nbdata = 16
    countline =0
    req    = bytearray(20)    
    for line in fusetable:
        #before = gc.mem_free()
        line_strip = line.strip()
        #print(line_strip,type(line_strip))
        line_bytes = bytearray(line_strip)
        size_line = len(line_strip)
        hex_as_int = int(line_strip, 16)                      
        hex_as_binary = bin(hex_as_int)        
        page_prog = self.zfl(hex_as_binary[2:],128)
        line_bytes = [page_prog[i:i+8] for i in range(0,128,8)]       
        # print("count",countline,size_line)
        countline = countline + 1
        for countbit_128 in range(128):
            valbit = page_prog[countbit_128]
            crc += int(valbit) << (numbit % 8)
            numbit=numbit+1           
        # for countbit_128 in range(size_line):
            # valbit = line_strip[countbit_128]
            # if valbit == "1":           
               # val = 1
            # else:
               # val = 0
            # crc += val << (numbit % 8)
            # numbit=numbit+1        
        # line_bytes = [line_strip[i:i+8] for i in range(0,size_line,8)]
                
      # transmit data with format  : cmd,0,0,1 <16* 8 bytes data>              
        req[0]=MACHXO2_CMD_PROG_INCR_NV
        req[1]=0x00
        req[2]=0x00
        req[3]=0x01
        # transmit Y*16 bytes        
        for i in range(nbdata):
           req[4+i]=self.str_to_byte(line_bytes[i])          
        resp_machx02_spi = self.spiTrans(req,nbdata+4)
        #after = gc.mem_free()
        #print("mem =",before - after ,"bytes")
        self.waitidle()        
    print("numbit programmed = ",numbit)    
  #  program DONE bit
    cmd = bytearray([MACHXO2_CMD_PROGRAM_DONE, 0x00, 0x00, 0x00])
    resp_machx02_spi = self.spiTrans(cmd,4)
    self.waitdone()
    status = self.readstatus()    
    status_failed = self.from_bytes_big(status) & self.status["failed"]
    error = (status_failed != self.status["failed"])
    return  error,crc 


  # read flash
  def checkflash(self):
    countpage = 0x0100 # 14 bits counter page
    cmd = bytearray([MACHXO2_CMD_READ_INCR_NV, 0x01,0x01, 0x00])
    self.cs.off()
    self.hspi.write(cmd)    
    self.cs.on()
    utime.sleep_us(500) 
    self.cs.off()
    resp_machx02_spi = self.hspi.read(int(countpage))  
    self.cs.on()
    return resp_machx02_spi
  # read ufm 
  def readufm(self):
    cmd = bytearray([MACHXO2_CMD_READ_UFM, 0x01, 0x00, 0x00])
    resp_machx02_spi = self.spiTrans(cmd,4)
    return resp_machx02_spi
    
  def from_bytes_big(self,b):
    n = 0
    for x in b:
        n <<= 8
        n |= x
    return n

  def str_to_byte(self,s):
    b=0
    for i in range(len(s)):
       b |= int(s[i]) << 7-i
    return b



