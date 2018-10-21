#!/usr/bin/env python



from inputs import get_gamepad

import socket, struct

import time


CMD_MOVE = 1
CMD_ROTATE = 2
CMD_STOP = 3
CMD_JOG = 4
CMD_CRANE = 5

def pack( cmd, flags, speed, value ):
	return struct.pack( ">BBhh", cmd, flags, int(speed), int(value) ) + b" "*10



sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )


prev_t = time.time()

left_speed = 0
right_speed = 0

has_crane = False
crane_speed = 0

try:
	while True:
		events = get_gamepad()
		for event in events:
			#print( event.ev_type, event.code, event.state)
			#print( str(event.code), repr(event.code), event.state ) 
			#print( event.code == "ABS_RY" )
			if event.code == "ABS_Y":
				value = int(event.state / 20 / 2)
				if abs(value) < 100:
					value = 0
				#print( value )
				#msg = pack( CMD_JOG, 0x01, int(value), 0 )
				#if time.time() - prev_t > 0.05:
				#	sock.sendto( msg, ('192.168.43.123', 8123 ) )
				#	prev_t = time.time()
				left_speed = value
			
			if event.code == "ABS_RY":
				value = int(event.state / 20 / 2)
				if abs(value) < 100:
					value = 0
				#print( value )
				#msg = pack( CMD_JOG, 0x02, 0, int(value) )
				#if time.time() - prev_t > 0.05:
				#	sock.sendto( msg, ('192.168.43.123', 8123 ) )
				#	prev_t = time.time()
				right_speed = value
			
			if event.code == "ABS_Z":
				crane_speed = event.state
				if crane_speed < 10:
					crane_speed = 0
				has_crane = True

			if event.code == "ABS_RZ":
				crane_speed = -event.state
				if crane_speed > -10:
					crane_speed = 0
				has_crane = True
				
			
			if time.time() - prev_t > 0.05:
				prev_t = time.time()
				if has_crane:
					msg = pack( CMD_JOG, 0x04, 0, int(crane_speed) )
					sock.sendto( msg, ('192.168.43.123', 8123 ) )
					has_crane = False
				else:
					msg = pack( CMD_JOG, 0x02 | 0x01, int(left_speed), int(right_speed) )
					sock.sendto( msg, ('192.168.43.123', 8123 ) )

except KeyboardInterrupt:
	pass
