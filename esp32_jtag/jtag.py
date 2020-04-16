# -*- coding: utf-8 -*-
"""
Created on Sun Aug 11 09:55:11 2019

@author: yann brengel
"""
from const_machx02 import *
from machine import Pin,SPI
import utime


# to manage jtag with SPI in mode bitbang
class jtag(object):
   def __init__(self,frequency):
      self.tck = Pin(18, Pin.OUT)
      self.tdi = Pin(23, Pin.OUT)
      self.tdo = Pin(19, Pin.IN)
      self.tms = Pin(21, Pin.OUT)
      self.spi_jtag_on(frequency)
      self.tck.off()
      self.tms.on()       
      self.tdi.on()
      self.frequency = frequency

   # setting bitbang mode
   def spi_jtag_on(self,frequency):
      self.hwspi=SPI(-1 , baudrate=frequency, polarity=1, phase=1, bits=8, firstbit=SPI.MSB, sck=self.tck, mosi=self.tdi, miso=self.tdo)
      self.swspi=SPI(-1 , baudrate=frequency, polarity=1, phase=1, bits=8, firstbit=SPI.MSB, sck=self.tck, mosi=self.tdi, miso=self.tdo)

   ##----------------------------------------------------------------------------------# 
   #pulse_tck 
   ##----------------------------------------------------------------------------------# 
   #This routine strobes the TCK pin (brings high then back low again) 
   # on the target system. # 
   def pulse_tck(self):
      #utime.sleep_us(50)
      self.tck.on()
      period = (1/self.frequency)
      period_us  = int(period * 1e6)
      utime.sleep_us(period_us)
      self.tck.off()
      utime.sleep_us(period_us)

   #-----------------------------------------------------------------------------------# 
   #JTAG_Reset #-----------------------------------------------------------------------------------
   # This routine places the JTAG state machine on the target system in 
   # the Test Logic Reset state by strobing TCK 5 times while leaving 
   # tms high.  Leaves the JTAG state machine in the Run_Test/Idle state. # 
   def jtag_reset (self): 
      #print("reset jtag with TCK")
      self.tms.on()
      for i in range(5):                  # reset state
         self.pulse_tck()        
      self.tms.off()
      self.pulse_tck()

   ##--------------------------------------------------------------------# 
   #  write_dr 
   #---------------------------------------------------------------------# 
   #This routine loads the supplied <data> of <num_bits> length into the JTAG
   @micropython.viper 
   def write_dr(self,instruction,num_bits):
      #print("write dr")
      retval = 0x0                          # run test idle
      self.tms.on()     
      self.pulse_tck()                      # move to SelectDR 
      self.tms.off()  
      self.pulse_tck()                      # move to Capture/DR
      self.tms.off()
      self.pulse_tck()                      # move to shift DR/State
      for i in range(num_bits):   
         if  (instruction & 0x01):          # shift DR, LSB-first
               self.tdi.on()        
         else:
               self.tdi.off()       
         instruction = instruction >> 1
         retval = retval >> 1     
         if (self.tdo.value()):        
               retval |= 0x01 << (num_bits - 1)    
         if i == (num_bits - 1):         
               self.tms.on()                   # move to Exit1_DR state 
         self.pulse_tck()
      self.tms.on()  
      self.pulse_tck()                     # move to Update_DR
      self.tms.off()
      self.pulse_tck()                      # move to RTI state
      
      return retval  


   ##--------------------------------------------------------------------# 
   #  write_ir 
   #---------------------------------------------------------------------# 
   #This routine loads the supplied <instruction> of <num_bits> length into the JTAG 
   ## Instruction Register on the target system.  Leaves in the Run_Test/Idle state. 
   ## The return value is the n-bit value read from the IR. 
   ## Assumes the JTAG state machine starts in the Run_Test/Idle state.
   @micropython.viper 
   def write_ir (self,instruction,num_bits):
      #print("write ir")
      retval = 0x0                         # run test idle
      self.tms.on()
      self.pulse_tck()                     # move to SelectDR 
      self.tms.on()
      self.pulse_tck()                     # move to SelectIR
      self.tms.off() 
      self.pulse_tck()                     # move to Capture/IR 
      self.tms.off() 
      self.pulse_tck()                     # move to shift_IR state        
      for i in range(num_bits):   
         if  (instruction & 0x01):          # shift IR, LSB-first
               self.tdi.on()        
         else:
               self.tdi.off()       
         instruction = instruction >> 1
         retval = retval >> 1     
         if (self.tdo.value()):        
               retval |= 0x01 << (num_bits - 1)    
         if i == (num_bits - 1):         
               self.tms.on()                   # move to Exit1_IR state 
         self.pulse_tck()   
      self.tms.on()  
      self.pulse_tck()                     # move to Update_IR
      self.tms.off() 
      self.pulse_tck()                      # move to RTI state
      
      return retval

   #----------------------------------------------------------------------------------# 
   #check_dr #------------------------------------------------------------------------
   # This routine shifts <num_bits> of <data> into the Data Register, and returns
   # up to 32-bits of data read from the Data Register. # Leaves in the Run_Test/Idle state. 
   # Assumes the JTAG state machine starts in the Run_Test/Idle state
    @micropython.viper
   def check_dr (self,dat,num_bits):
      #print("check dr")
      retval = 0x0
      self.tms.on()                  
      self.pulse_tck()                      # move to SelectDR 
      self.tms.off()
      self.pulse_tck()                      # move to CaptureDR  
      self.pulse_tck()                      # move to Shift_DR state
      for i in range(num_bits):
         if (dat & 0x01):                   # shift DR, LSB-first
            self.tdi.on()       
         else:
            self.tdi.off()                  # shift DR, LSB-first     
         dat = dat >> 1
         retval = retval >> 1
         if  (self.tdo.value()):       
            retval |= 0x01 << (num_bits - 1)
         if  i == (num_bits - 1):       
            self.tms.on()                   # move to Exit1_DR state                 
         self.pulse_tck() 
      self.tms.on()   
      self.pulse_tck()                      # move to Update_DR             
      self.tms.off()
      self.pulse_tck()                      # move to RTI state
      
      return retval







