# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 15:20:37 2019

@author: yann brengel
"""
import re
import utime
from const import *
from jtag import jtag

#   class to manage MACHX02 jtag
#
# 
#   
class machx02_jtag(jtag):
    # bit16 : protection fuse ?
    # bit13:failed, bit12:busy, bit9:enabled , bit8:Flash or SRAM Done flag 
    #  [25:23] configuration check status
    #  000 : No Error
    #  001 : ID ERR
    #  010 : CMD ERR
    #  011 : CRC ERR
    #  100 : Preamble ERR
    #  101 : Abort ERR
    #  110 : Overflow ERR
    #  111 : SDM EOF
    # the busy bit should be checked following  all enable,erase or programm operations 
    status={"failed":8192,"busy":4096,"enabled":512,"done":256,"security":8192}
    IDCODE_LEN = 32
    OPCODE_LEN = 8
    FREQUENCY = 10000
    
    def __init__(self,device):
        jtag.__init__(self,self.FREQUENCY)
        self.device=device        
        

    def prog_bscan_register(self):
        ### program bscan register
        self.write_ir(JTAG_CMD_SAMPLE,self.OPCODE_LEN)
        if self.device == MACHXO2_DEVICE_ID_1200:
           self.write_dr(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,JTAG_BSC_LENGTH_1200)
        elif self.device == MACHXO2_DEVICE_ID_4000:           
            self.write_dr(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,JTAG_BSC_LENGTH_4000)
           
        self.runtest(1000,"ms",2)
    
    def check_key_prot(self):
        # check the Key Protection fuses
        self.write_ir(MACHXO2_CMD_READ_STATUS,self.OPCODE_LEN)
        self.runtest(1000,"us",2)
        status = self.check_dr(0x00000000,32)
        mask = 0x00010000
        return (status & mask)
        
                            
    # enable flash
    def enable_flash(self):
        ### enable the flash
        # ISC ENABLE
        print("enable flash")
        self.check_status()
        self.write_ir(MACHXO2_CMD_ENABLE_OFFLINE,self.OPCODE_LEN)
        self.write_dr(0x00,8)              
        self.runtest(1000,"us",2)
        
        # ISC ERASE, SRAM
        self.write_ir(MACHXO2_CMD_ERASE,self.OPCODE_LEN)
        self.write_dr(0x01,8)    
        self.runtest(1000,"ms",2)
        # BYPASS (MASK CO)
        result = self.write_ir(JTAG_CMD_BYPASS,self.OPCODE_LEN)
        bypass = self.check_dr(0x00,8)
        # mask = 0xC0

        # ISC ENABLE
        self.write_ir(MACHXO2_CMD_ENABLE_OFFLINE,self.OPCODE_LEN)
        self.write_dr(0x08,8) 
        self.runtest(1000,"us",2)
        self.check_status()


    def erase_flash(self):
        #progress("Erasing configuration flash")
        ### erase the flash
        # ISC ERASE
        self.write_ir(MACHXO2_CMD_ERASE,self.OPCODE_LEN)
        self.write_dr(0x0E,8)      
        self.runtest(3000,"ms",2)
        # LSC_CHECK_BUSY
        self.check_busy_flag()
        self.check_status()
        self.write_ir(MACHXO2_CMD_READ_STATUS,self.OPCODE_LEN)
        self.runtest(1000,"us",2)
        status = self.check_dr(0x00000000,32)
        mask = 0x00003000
        return (mask & status)



    def check_otp_fuses(self):
        # LSC_READ_STATUS Check the OTP fuses
        self.write_ir(MACHXO2_CMD_READ_STATUS,self.OPCODE_LEN)
        self.runtest(1000,"us",2)
        status = self.check_dr(0x00000000,32)
        mask = 0x00024040
        return (status & mask)        
   
     ### check idcode      
    def check_idcode(self):        
        self.write_ir(MACHXO2_CMD_READ_DEVICEID,self.OPCODE_LEN)
        idcode = self.check_dr(0x00000000, self.IDCODE_LEN)
        return idcode  

    ## check usercode
    def check_usercode(self):
        self.write_ir(MACHXO2_CMD_READ_USERCODE,self.OPCODE_LEN)
        usercode = self.check_dr(0x00000000,32)
        mask = 0xFFFFFFFF
        return (usercode & mask)


    def check_status(self):
         # LSC_CHECK_STATUS        
        while True:
            self.write_ir(MACHXO2_CMD_READ_STATUS,self.OPCODE_LEN)          
            self.runtest(1000,"us",2)
            status = self.check_dr(0x00000000, 32)
            print ("status ",hex(status))
            if (status & self.status["busy"]  == self.status["busy"]):
               print("busy")
               utime.sleep_ms(1000)   # datasheet = 200 us
            else:
               break
    # read status bit ?
    
        # ### read the status bit
        # # LSC_READ_STATUS
        # self.write_ir(MACHXO2_CMD_READ_STATUS,self.OPCODE_LEN)
        # self.runtest(1000)
        # status = self.check_dr(0x00000000,32)
        #                                  # self.status["busy"] 
    def check_busy_flag(self):
         # LSC_CHECK_BUSY        
        loop =10
        while loop >0:
            self.write_ir(MACHXO2_CMD_CHECK_BUSY,self.OPCODE_LEN)          
            self.runtest(1000,"us",2)
            loop = loop-1
            status_busy = self.check_dr(0, 1)
            print ("status busy",status_busy)
            if (status_busy == 1):
               print("busy")
               utime.sleep_us(200)
            else:
               break

    # read features
    def readfeatures(self):
        # LSC_READ_FEATURE
        self.write_ir(MACHXO2_CMD_READ_FEATURE,self.OPCODE_LEN)
        self.runtest(1000,"us",2)
        read_feature = self.check_dr(0xFFFFFFFF,48)
        # LSC_READ_FEABITS
        self.write_ir(MACHXO2_CMD_READ_FEABITS,self.OPCODE_LEN)
        self.runtest(1000,"us",2)
        read_feabits = self.check_dr(0xFFFF,16)
        return read_feature,read_feabits


     # disable 
    def disable(self):
        self.check_status()
        ### programm done bit
        self.write_ir(MACHXO2_CMD_PROGRAM_DONE,self.OPCODE_LEN)
        self.runtest(1000,"us",2)
        status = self.check_dr(0x00, 8)
        mask = 0xC4
        done = (mask & status)
        print ("done",done)

        ### exit programming mode
        # ISC DISABLE
        self.write_ir(MACHXO2_CMD_DISABLE,self.OPCODE_LEN)
        self.runtest(1000,"ms",2)
        # ISC BYPASS
        self.write_ir(JTAG_CMD_BYPASS,self.OPCODE_LEN)
        self.runtest(100,"ms",2)

        ### verify sram done bit A voir dans datasheet
        self.runtest(5000,"ms",2)
        # LSC_READ_STATUS
        self.write_ir( MACHXO2_CMD_READ_STATUS,self.OPCODE_LEN)
        status = self.check_dr(0x0000000,32)
        mask = 0x00002100
        return (status & mask)

  
    # parameters : time + number of clocks
    def runtest(self,time,unit,nb_clock):        
        #self.reset_jtag()
        if unit == "us":
           utime.sleep_us(time)
        elif unit == "ms":
           utime.sleep_ms(time)
        for i in range(nb_clock):
            self.pulse_tck()


    def reset_jtag(self):
        self.jtag_reset()



    def check_sram_done(self):
        self.runtest(5000,"ms",2)
        status = self.write_ir( MACHXO2_CMD_READ_STATUS,self.OPCODE_LEN)
        self.runtest(1000,"us",2)
        return status


    def check_config_data(self):
    ### verify config flash
        # LSC_INIT_ADDRESS
        self.write_ir(MACHXO2_CMD_INIT_ADDRESS,self.OPCODE_LEN)
        self.write_dr(0x04,8)
        self.runtest(1000,"us",2)

        # LSC_READ_INCR_NV
        self.write_ir(MACHXO2_CMD_READ_INCR_NV,self.OPCODE_LEN)
        self.feature_row = None
        self.feature_bits = None

        for line in cfg_data:
            self.runtest(1000,"us",2)
            status = self.check_dr(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,128)

        if jed_file.ufm_data is not None:
            ### verify user flash
            # LSC_INIT_ADDRESS
            self.write_ir(MACHXO2_CMD_INIT_ADDR_UFM,self.OPCODE_LEN)
            self.runtest(1000,"us",2)

            # LSC_READ_INCR_NV
            self.write_ir(MACHXO2_CMD_READ_INCR_NV,self.OPCODE_LEN)

            for line in jed_file.ufm_data:
                self.runtest(1000,"us",2)
                status = self.check_dr(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,128)




    def programm_feature_rows(self):
        ### program feature rows
        # LSC_INIT_ADDRESS
        self.write_ir(MACHXO2_CMD_INIT_ADDRESS,self.OPCODE_LEN)
        self.write_dr(0x02,8)
        self.runtest(1000,"us",2)
        # LSC_PROG_FEATURE
        # on ne programme pas feature
        # self.write_ir(MACHXO2_CMD_PROG_FEATURE,self.OPCODE_LEN)
        # self.write_dr(jed_file.feature_row,64)
        # self.runtest(2)
        
        # self.waitidle()
        # programming FEABITS
        # LSC_PROG_FEABITS
        # not implemented, too critic
#        self.write_ir(8, MACHXO2_CMD_PROG_FEABITS)
#        self.write_dr(16, jed_file.feature_bits)
#        self.runtest(2)

    def shift_bits(self,line):
        retval = ""        
        line_strip = line.strip()
        size_line = len(line_strip)       
        for countbit_128 in range(size_line):   
            valbit = line_strip[127-countbit_128]
            retval = retval + valbit
        return retval

    def compute_crc(self,line,crc):
        line_strip = line.strip()
        size_line = len(line_strip)
        countline = countline + 1
        for countbit_128 in range(size_line):
            valbit = line_strip[countbit_128]
            if valbit == "1":           
               val = 1
            else:
               val = 0
            crc += val << (numbit % 8)
        return crc            

    #####################################
    # programm jedec file
    #####################################
    def program(self, fusetable):            
        print("programm jed")   
        ### program config flash
        # LSC_INIT_ADDRESS
        self.write_ir(MACHXO2_CMD_INIT_ADDRESS,self.OPCODE_LEN)
        self.write_dr(8, 0x04)
        self.runtest(1000,"us",2)
       
        #cfg_data = jed_file.get_cfg_data()
        # print(cfg_data)
        first_line = True
        crc = 0
        for line in fusetable:
            # LSC_PROG_INCR_NV
            if not first_line:
                line_shift = self.shift_bits(line)
                crc = self.compute_crc(line,crc)
                data = int(line_shift, 2)
                value = hex(data)
                self.write_ir(MACHXO2_CMD_PROG_INCR_NV,self.OPCODE_LEN)            
                #print("line=",value)
                self.write_dr(data,128)
                self.runtest(1000,"us",2)
                self.check_busy_flag()
            first_line = False
        return crc
            # check busy      
        # test if ufm must be programmed   
        # if jed_file.ufm_data is not None:
        #     ### program user flash
        #     # LSC_INIT_ADDRESS
        #     self.write_ir(MACHXO2_CMD_INIT_ADDR_UFM, self.OPCODE_LEN)
        #     self.runtest(1000,"us")

        #     for line in jed_file.ufm_data:
        #         # LSC_PROG_INCR_NV
        #         self.write_ir(MACHXO2_CMD_PROG_INCR_NV,self.OPCODE_LEN)
        #         self.write_dr(line,128)
        #         self.runtest(10,"ms")
