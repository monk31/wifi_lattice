# -*- coding: utf-8 -*-
"""
Created on Sat May 18 15:02:57 2019

@author: yann brengel <ybrengel@gmail.com>
"""
from machx02_jtag import machx02_jtag


# ! Lattice Semiconductor Corp.
# ! Serial Vector Format (.SVF) File.
# ! User information:
class svf(machx02_jtag):
    def __init__(self,fusetable):       
        machx02_jtag.__init__(self)
        self.fusetable = fusetable
            
    def erase_program_verify(self):
        error = False
        # ! Check the IDCODE
        # already check
        
        # ! Program Bscan register
        self.prog_bscan_register()
        
        # ! Check the Key Protection fuses        
        status = self.check_key_prot()
        print("check_key_prot")        
        
        # ! Enable the Flash
        self.enable_flash()
        
        # ! Check the OTP fuses
        status = self.check_otp_fuses()
        print("check_otp_fuses") 
        
        # ! Erase the Flash        
        status =self.erase_flash()
        print("erase_flash")        
        
        # ! Read the status bit
        self.check_status()    
     
        # ! Program CFG
        print("program jed") 
        crc = self.program_machx02(self.fusetable) 
        #print("crc =",crc)
        # ! Read the status bit
        self.check_status()
        
        # ! Program DONE bit
        self.programm_done_bit()
        
        # ! Exit the programming mode
        self.exit_program()
        
        # ! Verify SRAM DONE Bit
        self.verify_sram()
        
        return crc,error

    # todo    
    def verify_only(self):
        pass

    # todo    
    def program(self):
        pass

    