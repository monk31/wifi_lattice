# -*- coding: utf-8 -*-
"""
Created on Sat May 18 15:02:57 2019

@author: ybren
"""
import os
from const_machx02 import *
import ubinascii
import ustruct

class jedec(object):
    def __init__(self,fusetable):
        self.jed          = fusetable
        self.cfg_data     = []
        self.ebr_data     = []
        self.ufm_data     = []
        self.feature_row  = None
        self.feature_bits = None
        self.last_note    = ""
        self.data         = []
        self._parse(self.jed)

    def compute_checksum(self,fusetable):
        crc = 0
        for i in range(len(fusetable)):
            crc += fusetable[i] << (i % 8)
        return crc

    # mutator
    def get_ebr_data(self):
        return self.ebr_data
     # mutator
    def get_ufm_data(self):
        return self.ufm_data
     # mutator
    def get_cfg_data(self):
        return self.cfg_data       
        
    def shift_bits(self,line):
        retval = ""
        line_strip = line.strip()
        size_line = len(line_strip)
        for countbit_128 in range(size_line):   
            valbit = line_strip[127-countbit_128]
            retval = retval + valbit
        return retval

    def endianness(self,line):
        packed_data = ubinascii.unhexlify(line)
        value = int.from_bytes(packed_data, 'little')
        fmt = hex(value)   
        result = fmt[2:] # remove 0x
        return result.upper()
   
    # private method, to parse jed file
    def _parse(self,jed):
        
        def process_line(line,field):
#            data = []
            #print(field)
            if EOF in line:
               field = ""            
            elif  field == "CONFIG DATA":
                line_shift = self.shift_bits(line)
                #print("line",line_shift)           
                data = int(line_shift, 2)
                value = hex(data)                
                #print(hex(data))                                                  
                self.cfg_data.append(value)                
            elif field == "UFM_DATA":
                line_shift = self.shift_bits(line)    
                data = int(line_shift, 2)
                value = hex(data)
                self.ufm_data.append(value)
            elif "L000000" in line:             
                field="CONFIG DATA"
                #print("CONFIG DATA")
            elif "L" in line:
                field=""                        
            elif "END CONFIG DATA" in line:              
                field="UFM_DATA"
            elif "TAG DATA" in line:               
                field="CONFIG DATA"
            elif "FEATURE_ROW" in line:               
                field="FEATURE_ROW"           
            return field
        num_row      = 0      
        loop         = True
        # lines = [i.strip() for i in jed]  # remove  char endline \n
        # print(len(lines))  
        print(len(jed))
        print(jed[0])    
        line  = ""
        field = ""
        while(loop):
            line = jed[num_row+1]                   
            if ETX in line:
                print("finishhhhhhhhhhhhhhhhhhhh")
                loop = False
            field  = process_line(line,field)           
            num_row=num_row+1            
