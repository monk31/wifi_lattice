# wifi_lattice


![microPython1](https://user-images.githubusercontent.com/13630510/68531538-922e6f00-0313-11ea-8417-db9fad768f5f.png)


## this project allow the ESP32  to connect to my Wifi network and programming,probing FPGA MACHX02

programming language : micropython for his clean syntax

CAUTION : tested with ESP32 model WROVER and machx02 4000
firmware micropython version = esp32spiram-20220117-v1.18.bin
            
            
i use a raspberry pi 3 to create a local network with a static adress (192.168.4.1)
congfiguration use raspap.com to set a wifi hotspot access

 
  ### esp32_jtag
  
  Pin (TCK)       →  GPIO  (pin 18 esp32)    
  Pin (TDO)       →  GPIO  (pin 19 esp32)    
  pin (TDI)       →  GPIO  (pin 23 esp32)         
  pin (TMS)       →  GPIO  (pin 21 esp32) 
  
  ## programming (wifi_prog)
  
  in main.py (line 25 and 26), set your WIFI_SSID, WIFI_PASSWD , default is set raspap.com 
  1. download the code in the esp32 flash with esp32tools (folder esp32_jtag)
  2. download wifi_prog.py and your file jed on your raspberry 
  3. set command "python3 wifi_prog.py" and follow instructions
  (caution if the message "esp32 is not in the network" 
   display, try again because sometimes request network response is longer)
   
   benchmark : MACHX02-4000 => programming = 1 mn 38 s
   
   ![wifi_prog](https://user-images.githubusercontent.com/13630510/77827370-7803fa80-7115-11ea-8a05-791cb7dd1f30.png)
   
   ## probing (wifi_probe)
   this tool allow to change the state of a pin for test
   
  in main.py (line 25 and 26), set your WIFI_SSID, WIFI_PASSWD
  1. download the code in the esp32 flash with esp32tools (folder esp32_jtag)
  2. download wifi_probe.py and your file bsm on your raspberry (see example)
  3. set command "python3 wifi_probe.py" and follow instructions
   
   ![wifi_probe](https://user-images.githubusercontent.com/13630510/78492832-46a8b180-7749-11ea-811b-571501010a23.png)
 
  
  ### esp32_spi 
  
  the spi machx02 must be configure in slave device with sysconfig register
  
  Pin CCLK)       →  GPIO  (pin 14 esp32)    
  Pin (SPISO)     →  GPIO  (pin 12 esp32)    
  pin (SN)        →  GPIO  (pin 15 esp32)         
  pin (SISPI)     →  GPIO  (pin 13 esp32) 
  
  usage 

to know the adress ip local use a command

- nmap -sP 192.168.4.*

in main.py, set your WIFI_SSID, WIFI_PASS and your deviceId line 206 (see const.py)

upload the code with esp32tools

after on your raspberry,  set the command netcat 192.168.4.x  241 < demo.jed 

benchmark : MACHX02 7000 => programming = 50 s
lattice diamond : programming ftdi = 40 s

 ### esp32_i2c is under construct 
  
  

 
  
  
  
  
