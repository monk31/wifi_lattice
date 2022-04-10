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
from machine import I2C
import gc

# class to manage i2c MACHX02 
# 
# setting hardware I2C
# I2C0 : scl=18,sda=19
# I2C1 : scl=25,sda=26 
# 
class machx02_i2c(object):
 
  address=0x51
  def __init__(self,deviceid): 
    self.sda      = Pin(21, Pin.OUT)
    self.scl      = Pin(22, Pin.OUT)    
    self.sda.on()
    self.i2c      = I2C(freq=400000,sda=sda_pin, scl=scl_pin)
    self.addr_i2c = self.scanning()
    self.deviceid = deviceid
    
                   
  # transfert i2c
  def i2cTrans(self,cmd,size):    
    resp_machx02_i2c = bytearray(size)      
    self.i2c.writeto(self.addr_i2c, cmd)
    resp_machx02_i2c=self.i2c.readfrom(addr_i2c, 1) 
    self.i2c.writeto_mem(self.addr_i2c, eeaddress, buf, addrsize=16)
    return resp_machx02_i2c
       
  # check idcode
  def check_idcode(self):    
    cmd = bytearray([MACHXO2_CMD_READ_DEVICEID, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    resp_machx02_spi = self.i2cTrans(cmd,8)
    resp_machx02_spi_int = self.from_bytes_big(bytes(resp_machx02_spi))   
    result = resp_machx02_spi_int & self.mask
    return (self.deviceid == result)

  # disable
  def disable(self):
    #disable configuration
    cmd = bytearray([MACHXO2_CMD_DISABLE, 0x00, 0x00])
    resp_machx02_spi = self.i2cTrans(cmd,3)
	# nop
    cmd = bytearray([MACHXO2_CMD_NOP, 0xFF, 0xFF, 0xFF])
    resp_machx02_spi = self.i2cTrans(cmd,4)
 
    # refresh
    cmd = bytearray([MACHXO2_CMD_REFRESH, 0x00, 0x00])
    resp_machx02_spi = self.i2cTrans(cmd,3)
    utime.sleep_ms(10000)  
    
  def scanning(self):
      return self.i2c.scan()

  def wakeup_device(self):
    # refresh
    cmd = bytearray([MACHXO2_CMD_REFRESH, 0x00, 0x00])
    resp_machx02_spi = self.i2cTrans(cmd,3)
    utime.sleep_ms(10000)  


  # enable offline configuration
  def enable(self):    
    cmd = bytearray([MACHXO2_CMD_ENABLE_OFFLINE, 0x08, 0x00,0x00])
    resp_machx02_spi = self.i2cTrans(cmd,4)
    self.waitidle()

    # erase SRAM
    cmd = bytearray([MACHXO2_CMD_ERASE, 0x01, 0x00,0x00])
    resp_machx02_spi = self.i2cTrans(cmd,4)
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
        resp_machx02_spi = self.i2cTrans(cmd,3)
        print("wait refresh")
        utime.sleep_ms(1)   # datasheet = 200 us
      else:
         break
  
  # read status
  def readstatus(self):
    cmd = bytearray([MACHXO2_CMD_READ_STATUS, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    resp_machx02_spi = self.i2cTrans(cmd,8)
    return resp_machx02_spi
    
  # read features
  def readfeatures(self):
    cmd = bytearray([MACHXO2_CMD_READ_FEATURE, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    feature_row = self.i2cTrans(cmd,12)
  #  read FEABITS
    cmd = bytearray([MACHXO2_CMD_READ_FEABITS, 0x00, 0x00, 0x00, 0x00, 0x00])
    feabits = self.i2cTrans(cmd,6) 
    return self.from_bytes_big(feature_row),self.from_bytes_big(feabits)
 
  # programm jedec file
  def program(self,fusetable):
  # erase flash
    cmd = bytearray([MACHXO2_CMD_ERASE, 0x04, 0x00, 0x00])
    resp_machx02_spi = self.i2cTrans(cmd,4)
    print("erase flash ...")
    self.waitidle()
    resp = self.readstatus()    
    status_failed = self.from_bytes_big(resp) & self.status["failed"]
    if status_failed == self.status["failed"]:
      return False

  # set address to zero
    cmd = bytearray([MACHXO2_CMD_INIT_ADDRESS, 0x00, 0x00, 0x00])
    resp_machx02_spi = self.i2cTrans(cmd,4)
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
        size_line = len(line_strip)        
        # print("count",countline,size_line)
        countline = countline + 1
        for countbit_128 in range(size_line):
            valbit = line_strip[countbit_128]
            if valbit == "1":           
               val = 1
            else:
               val = 0
            crc += val << (numbit % 8)
            numbit=numbit+1        
        line_bytes = [line_strip[i:i+8] for i in range(0,size_line,8)]
                
      # transmit data with format  : cmd,0,0,1 <16* 8 bytes data>              
        req[0]=MACHXO2_CMD_PROG_INCR_NV
        req[1]=0x00
        req[2]=0x00
        req[3]=0x01
        # transmit Y*16 bytes        
        for i in range(nbdata):
           req[4+i]=self.str_to_byte(line_bytes[i])      
        resp_machx02_spi = self.i2cTrans(req,nbdata+4)
        #after = gc.mem_free()
        #print("mem =",before - after ,"bytes")
        self.waitidle()        
    print("numbit programmed = ",numbit)    
  #  program DONE bit
    cmd = bytearray([MACHXO2_CMD_PROGRAM_DONE, 0x00, 0x00, 0x00])
    resp_machx02_spi = self.i2cTrans(cmd,4)
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
    resp_machx02_spi = self.i2cTrans(cmd,4)
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



