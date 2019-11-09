# wifi_lattice


![microPython1](https://user-images.githubusercontent.com/13630510/68531538-922e6f00-0313-11ea-8417-db9fad768f5f.png)


## this project allow the FPGA MACHX02 to connect to my Wifi network and programming jed

programming language : micropython for his clean syntax

i use a raspberry pi 3 to create a local network with a static adress (192.168.4.1)

  
  - esp32_spi 
  
  the spi machx02 must be configure in slave device with sysconfig register
  
  Pin CCLK)       →  GPIO  (pin 14 esp32)    
  Pin (SPISO)     →  GPIO  (pin 12 esp32)    
  pin (SN)        →  GPIO  (pin 15 esp32)         
  pin (SISPI)     →  GPIO  (pin 13 esp32) 
  
  - esp32_jtag
  
  Pin (TCK)       →  GPIO  (pin 18 esp32)    
  Pin (TDO)       →  GPIO  (pin 19 esp32)    
  pin (TDI)       →  GPIO  (pin 23 esp32)         
  pin (TMS)       →  GPIO  (pin 21 esp32) 
  
  CAUTION : if you are a fpga machx02 256 until 2000, you must use esp32 wroom-32 
            else use esp32 wrover with spi ram

usage 

to know the adress ip local use a command

- nmap -sP 192.168.4.*

in main.py, set your WIFI_SSID, WIFI_PASS and your deviceId (see const.py)

after set the command netcat 192.168.4.x  241 < demo.jed 
  
  
  
  
