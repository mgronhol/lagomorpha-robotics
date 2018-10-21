#!/usr/bin/env python



from inputs import get_gamepad

import socket, struct

import time

# Remote control for the robot, using an Xbox controller.
# Communicate with an UDP server running on the robot. 


CMD_MOVE = 1
CMD_ROTATE = 2
CMD_STOP = 3
CMD_JOG = 4
CMD_CRANE = 5

ROBOT_ADDRESS = '192.168.43.123'
ROBOT_PORT = 8123

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
			if event.code == "ABS_Y":
				# Left stick
				value = int(event.state / 20 / 2)
				if abs(value) < 100:
					value = 0
				left_speed = value
			
			if event.code == "ABS_RY":
				# Right stick
				value = int(event.state / 20 / 2)
				if abs(value) < 100:
					value = 0
				right_speed = value
			
			if event.code == "ABS_Z":
				# Left bumper - crane 
				crane_speed = event.state
				if crane_speed < 10:
					crane_speed = 0
				has_crane = True

			if event.code == "ABS_RZ":
				# Right bumper - crane
				crane_speed = -event.state
				if crane_speed > -10:
					crane_speed = 0
				has_crane = True
				
			
			if time.time() - prev_t > 0.05:
				# Have a small delay between messages
				prev_t = time.time()
				if has_crane:
					msg = pack( CMD_JOG, 0x04, 0, int(crane_speed) )
					sock.sendto( msg, (ROBOT_ADDRESS, ROBOT_PORT ) )
					has_crane = False
				else:
					msg = pack( CMD_JOG, 0x02 | 0x01, int(left_speed), int(right_speed) )
					sock.sendto( msg, (ROBOT_ADDRESS, ROBOT_PORT ) )

except KeyboardInterrupt:
	pass
