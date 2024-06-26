#!/usr/bin/python3

import ctypes
import getopt
import getpass
import re
import readchar
import serial
import serial.tools.list_ports
import signal
import socket
import sys
import threading
import time

def printHelp():
	print("""serialClient [-i initial text] [-e codec] [-r regex] [-s] [-v] [-h] <port> [[-b] <baud rate>]
-b: baud rate
-d: daemon mode
-e <codec>: use connecting with specified codec
-i <initial text>: send initial text just after connect
-l: list ports
-r <regex>: print text specified by regex
-s: telnets mode
-v: verbose print
-h: print this help
""")
	exit(1)

# option parse
optlist, args = getopt.gnu_getopt(sys.argv[1:], 'i:de:lr:vh')

#if len(args) == 0:
#	printHelp()

# default value
initialText = ""
daemonMode = False
codec = 'UTF8'
#codec = 'SJIS'
baudrate = 38400
timeout = 3
textRegex = ""

def printVerbose(*message, file=sys.stderr):
	pass

def listPorts():
	ports = list(serial.tools.list_ports.comports())
	for p in ports:
		print(p)

# assign argments to variables
if len(args) >= 1:
	port = args[0]

if len(args) >= 2:
	baudrate = args[1]

# for each option
for opt, arg in optlist:
	if opt == '-i':
		initialText = arg
	elif opt == '-b':
		baudrate = arg
	elif opt == '-d':
		daemonMode = True
	elif opt == '-e':
		codec = arg
	elif opt == '-l':
		listPorts()
		exit(0)
	elif opt == '-r':
		textRegex = arg
	elif opt == '-v':
		printVerbose = print
	elif opt == '-h':
		printHelp()


if sys.platform in ("win32", "cygwin"):
	# Windows APIのライブラリを読み込む
	user32 = ctypes.windll.user32
	# Altキーの仮想キーコード
	VK_MENU = 0x12
	def isAltkeyPressed():
		alt_key_state = user32.GetAsyncKeyState(VK_MENU)
		return alt_key_state
else:
	def isAltkeyPressed():
		return False


# receive thread function definition
def receive(client):
	# logging
	#with open('koukoku2.log', 'a', encoding='UTF8') as logFile:
	# receive message
		
	response = b""
	while True:
		try:
			#response = client.read(4096).decode(codec)
			response += client.readline(-1)
			#print(response.decode(codec), end='')
			if textRegex:
				#talk = re.findall("(?<=>> )[^<]*(?=<<)", response.decode(codec))
				talk = re.findall(textRegex, response)
				if talk:
					message = talk[0]
				else:
					continue
			else:
				message = response.decode('UTF8')
			print(message, flush=True, end='')
			response = b""
			#logFile.write(message + '\n')
		except ConnectionAbortedError:
			return
		except (AttributeError, serial.serialutil.SerialException):
			return
		except UnicodeDecodeError:
			#print("UnicodeDecodeError", response)
			continue

# main routine
if __name__ == '__main__':
	try:
		printVerbose(port, baudrate, file=sys.stderr)
		# connect to target port
		#printVerbose("connect {} port {} from {} port {}, timeout = {}".format(*client.getpeername(), *client.getsockname(), client.gettimeout()), file=sys.stderr)
		#client = serial.Serial(port, baudrate, timeout=timeout)
		client = serial.Serial(port, baudrate, timeout=0)

		# initial text
		if initialText:
			initialText += '\n'
			client.send(initialText.encode(codec))

		## signal handler
		#def signalHandler(signum, frame):
		#	signame = signal.Signals(signum).name
		#	printVerbose(f'Signal handler called with signal {signame} ({signum})', file=sys.stderr)
		#	client.write("".encode(codec))

		## Set the signal handler and a 5-second alarm
		#signal.signal(signal.SIGINT, signalHandler)

		# thread start
		receiveThread = threading.Thread(target=receive, args=(client, ), daemon=True)
		receiveThread.start()

		while True:
			try:
				if daemonMode:
					time.sleep(60)
					continue
				#message = input("")
				message = readchar.readkey()
				#if message == 'pass':
				#	message = getpass.getpass("")
				#message += '\n'
				if message == '':
					if readchar.readkey() == 'q':
						break
				if isAltkeyPressed():
					message = '' + message

				# send message
				client.write(message.encode(codec))
				#printVerbose(message, file=sys.stderr)
			except UnicodeEncodeError:
				print("UnicodeEncodeError: cannot encode the input")
			except KeyboardInterrupt:
				client.write("".encode(codec))
	finally:
		receiveThread.join(timeout=0.3)
		client.close()
