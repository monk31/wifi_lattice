
from micropyhon import const
# attribute INSTRUCTION_OPCODE of LCMXO2_1200HC_XXMG132 : entity is
		# "              IDCODE		(11100000)," &
		# "          ISC_ENABLE		(11000110)," &
		# "    ISC_PROGRAM_DONE		(01011110)," &
		# " LSC_PROGRAM_SECPLUS		(11001111)," &
		# "ISC_PROGRAM_USERCODE		(11000010)," &
		# "ISC_PROGRAM_SECURITY		(11001110)," &
		# "         ISC_PROGRAM		(01100111)," &
		# "        LSC_ENABLE_X		(01110100)," &
		# "              BYPASS		(11111111)," &    0xff  (NOP)
		# "      ISC_DATA_SHIFT		(00001010)," &
		# "       ISC_DISCHARGE		(00010100)," &
		# "            USERCODE		(11000000)," &
		# "      ISC_ERASE_DONE		(00100100)," &
		# "               CLAMP		(01111000)," &
		# "   ISC_ADDRESS_SHIFT		(01000010)," &
		# "             PRELOAD		(00011100)," &
		# "            ISC_READ		(10000000)," &
		# "         ISC_DISABLE		(00100110)," &
		# "           ISC_ERASE		(00001110)," &
		# "            ISC_NOOP		(00110000)," &
		# "              SAMPLE		(00011100)," &   0x1c
		# "               HIGHZ		(00011000)," &
		# "              EXTEST		(00010101)," &   0x15
	
# SAMPLE: Monitoring Normal Device Operation
# The SAMPLE instruction is designed for monitoring the pins of a working device. In this mode, TopJTAG Probe repeatedly takes snapshots of the state of boundary-scan device pins, without interfering with the normal device operation.

# BYPASS: Skip Device
# The BYPASS instruction allows to 'skip' device when you don't care about it. It minimizes device presence in a JTAG chain allowing for faster scan. You don't need to specify a package and in some cases even a BSDL file for the device.
JTAG_CMD_BYPASS                 =   const(0xFF)
JTAG_CMD_EXTEST                 =   const(0x15)
JTAG_CMD_SAMPLE                 =   const(0x1C)


# definition attribute length
JTAG_BSC_LENGTH_1200 = const(208)
JTAG_BSC_LENGTH_2000 = const(424)
JTAG_BSC_LENGTH_4000 = const(552)
JTAG_BSC_LENGTH_7000 = const(664)


# definition constantes  command com SPI and JTAG

MACHXO2_CMD_READ_DEVICEID       =   const(0xE0)    # Data is 4 byte device id code
MACHXO2_CMD_ENABLE_TRANSPARENT  =	const(0x74)    # Enable flash programming in transparent mode
MACHXO2_CMD_ENABLE_OFFLINE      =	const(0xC6)    # Enable flash programming in offline mode
MACHXO2_CMD_CHECK_BUSY          =	const(0xF0)   # Busy bit
MACHXO2_CMD_READ_STATUS         =	const(0x3C)    # 4 data bytes, bit12=busy, bit13=error
MACHXO2_CMD_ERASE               =	const(0x0E)    # Erase the part  use 0x0F
MACHXO2_CMD_ERASE_UFM          	=   const(0xCB)    # Erase user flash memory (UFM) section only
MACHXO2_CMD_INIT_ADDRESS        =	const(0x46)    # Set address to beginning of configuration flash
MACHXO2_CMD_WRITE_ADDRESS       =	const(0xB4)    # Set a specific address using data bytes
MACHXO2_CMD_PROG_INCR_NV        =	const(0x70)    # Program a flash page  with 16 bytes of data and increment the address
MACHXO2_CMD_INIT_ADDR_UFM       =	const(0x47)    # Set address to beginning of UFM
MACHXO2_CMD_PROG_TAG            =	const(0xC9)    # Program one UFM page with 16 bytes of data
MACHXO2_CMD_PROGRAM_USERCODE    =	const(0xC2)    # Program the user code with 4 bytes of data
MACHXO2_CMD_READ_USERCODE       =   const(0xC0)    # Read byte 4 bytes of data from the user code
MACHXO2_CMD_PROG_FEATURE        =	const(0xE4)    # Write 8 bytes of data to the feature row
MACHXO2_CMD_READ_FEATURE        =	const(0xE7)    # Read 8 bytes of data from the feature row
MACHXO2_CMD_PROG_FEABITS        =	const(0xF8)    # Write 2 bytes of data to the feabits
MACHXO2_CMD_READ_FEABITS        =	const(0xFB)    # Read 2 bytes of data from the feabits
MACHXO2_CMD_READ_INCR_NV        =	const(0x73)    # Read flash, using byte count and parameters
MACHXO2_CMD_READ_UFM            =	const(0xCA)    # Read UFM, using byte count and parameters
MACHXO2_CMD_PROGRAM_DONE        =	const(0x5E)    # Set the DONE bit
MACHXO2_CMD_PROG_OTP            =	const(0xF9)    # Program the OTP fuses
MACHXO2_CMD_READ_OTP            =	const(0xFA)    # Read the OTP fused
MACHXO2_CMD_DISABLE             =	const(0x26)    # 
MACHXO2_CMD_NOP                 =	const(0xFF)    # No operation
MACHXO2_CMD_REFRESH             =	const(0x79)    # 
MACHXO2_CMD_PROGRAM_SECURITY    =	const(0xCE)    # Program the security bit to restrict access to flash
MACHXO2_CMD_PROGRAM_SECPLUS     =	const(0xCF)    # Program the security plus bit to restrict access to flash  
MACHXO2_CMD_READ_UIDCODE        =   const(0x19)    # Read 8 bytes of data representing a unique code per chip
MACHXO2_CMD_EXTEST              =   const(0x15)    # probing test

# definition constant size fusetable

MACHXO2_SIZE_FUSETABLE_1200 =  "343936"
MACHXO2_SIZE_FUSETABLE_2000 =  "491264"
MACHXO2_SIZE_FUSETABLE_4000 =  "835328"
MACHXO2_SIZE_FUSETABLE_7000 =  "1441280"



# definition constant device ID

MACHXO2_DEVICE_ID_1200 = const(0x12BA043)
MACHXO2_DEVICE_ID_2000 = const(0x12BB043)
MACHXO2_DEVICE_ID_4000 = const(0x12BC043)
MACHXO2_DEVICE_ID_7000 = const(0x12B5043)


# definition error jedec file parse

MACHXO2_JEDEC_ERROR = {0: "OK",            
               1: "NO_STX",
               2: "NO_ETX",
               3: "BAD_QF",
               4: "BAD_F",
               5: "BAD_L",
               6: "BAD_C",
               7: "WRONG_CHECKSUM"
              }

# definition constant jedec file parse

STX = '\x02*'
ETX = '\x03'
EOF = "*"



listdevice  = ["MACHX02_DEVICE_ID_1200","MACHX02_DEVICE_ID_2000","MACHX02_DEVICE_ID_4000","MACHX02_DEVICE_ID_7000"]


