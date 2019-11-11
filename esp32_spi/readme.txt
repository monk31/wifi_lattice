## deploying firmware

windows :
esptool.py -p COMX erase_flash
esptool.py --chip esp32 --port COMX --baud 115200 write_flash -z 0x1000 esp32-20190125-v1.10.bin
linux : 
esptool.py --port /dev/ttyUSB0 erase_flash
esptool.py --port /dev/ttyUSB0 --baud 115200 write_flash --flash_size=detect 0 esp32-20190125-v1.10.bin

