#!/usr/bin/env python3

import socket
import struct

import ev3dev.ev3 as ev3

import time

MOTOR_A = ev3.LargeMotor( "outC" )
MOTOR_B = ev3.LargeMotor( "outD" )
MOTOR_C = ev3.MediumMotor( "outA" )


CMD_MOVE = 1
CMD_ROTATE = 2
CMD_STOP = 3
CMD_JOG = 4
CMD_CRANE = 5




#sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )

sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind( ('', 8123) )
#sock.listen(5)
print( "Server started" )
try:
	while True:
		#conn, addr = sock.accept()
		#print( "New connection:", addr )
		done = False
		while not done:
			data, addr = sock.recvfrom(1024)
			if not data:
				done = True
			else:
				print( "MSG recvd", time.time() )
				cmd, flags, speed, value = struct.unpack_from( ">BBhh", data )
				print( cmd, flags, speed, value )
				print( MOTOR_A.is_running, MOTOR_B.is_running )
				print( MOTOR_A.state, MOTOR_B.state )

				if (len(MOTOR_A.state) > 0 or len(MOTOR_B.state) > 0) and cmd in [CMD_MOVE, CMD_ROTATE]:
					print( "Moving, skipping command" )
					continue


				if cmd == CMD_MOVE:
					MOTOR_A.run_to_rel_pos( position_sp = value, speed_sp = speed, stop_action = 'coast' )
					MOTOR_B.run_to_rel_pos( position_sp = value, speed_sp = speed, stop_action = 'coast' )
					#MOTOR_A.wait_until_not_moving( timeout = 4000.0 )
					#MOTOR_B.wait_until_not_moving( timeout = 4000.0 )

				elif cmd == CMD_ROTATE:
					MOTOR_A.run_to_rel_pos( position_sp = value, speed_sp = speed, stop_action = 'coast' )
					MOTOR_B.run_to_rel_pos( position_sp = -value, speed_sp = speed, stop_action = 'coast' )
					#MOTOR_A.wait_until_not_moving( timeout = 4000.0 )
					#MOTOR_B.wait_until_not_moving( timeout = 4000.0 )

				elif cmd == CMD_STOP:
					MOTOR_A.stop()
					MOTOR_B.stop()
				elif cmd == CMD_JOG:
					if flags & 0x01:
						if abs(speed) > 2:
							MOTOR_A.run_forever( speed_sp = speed )
						else:
							MOTOR_A.stop()
					if flags & 0x02:
						if abs(value) > 2:
							MOTOR_B.run_forever( speed_sp = value )
						else:
							MOTOR_B.stop()
					
					if flags & 0x04:
						if abs(value) > 2:
							MOTOR_C.run_forever( speed_sp = value )
						else:
							MOTOR_C.stop()
				
except KeyboardInterrupt:
	pass
sock.close()
