#!/usr/bin/env python2
from __future__ import print_function
import numpy as np
import cv2


import requests
import numpy as np

import time, json

import threading

import struct, socket


## Commands for robot control via UDP
CMD_MOVE = 1
CMD_ROTATE = 2
CMD_STOP = 3
CMD_JOG = 4
CMD_CRANE = 5

# create UDP socket
sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )

# function to pack and pad a control message for robot
def pack( cmd, flags, speed, value ):
	return struct.pack( ">BBhh", cmd, flags, int(speed), int(value) ) + b" "*10


# compute image entropy
def compute_entropy( img ):
	hist = cv2.calcHist([img], [0], None, [256], [0,256] ) 
	hist = hist.ravel() / hist.sum()
	logs = np.log2( hist + 1e-4 )
	entropy = -1 * (hist*logs).sum()
	return entropy
	
	

# Generate and test hypotheses wether image contains lines
def generate_line_hypotheses( img ):
	
	img[:,0:int(img.shape[1]*0.3)] = 0
	img[:, int(img.shape[1]*0.7):-1] = 0
	
	mu = cv2.moments( img )
	total_area = img.shape[0]*img.shape[1]
	
	fillrate = mu['m00'] / 256 / total_area
	hypothesis_no_track = fillrate < 0.05
	hypothesis_all_track = fillrate > 0.5
	hypothesis_some_track = not hypothesis_all_track and not hypothesis_no_track
	
	if mu['m00'] < 1:
		mu['m00'] = 1
	cx = int(mu['m10' ]/mu['m00'])
	cy = int(mu['m01']/mu['m00'])
	
	
	left_total = img[:,:img.shape[1]/2].sum()
	right_total = img[:,img.shape[1]/2:].sum()
	
	
	return {"no": hypothesis_no_track, "all": hypothesis_all_track, "some": hypothesis_some_track, "centroid": (cx,cy), "side": left_total < right_total}
	


# function to rotate robot
def rotate_robot( angle ):
	print( "Posting to robot")
	msg = pack( CMD_ROTATE, 0x00, 300, angle )
	sock.sendto( msg, ('192.168.43.123', 8123 ) )
	

# function to move the robot
def move_robot( dist ):
	print( "Posting to robot")
	msg = pack( CMD_MOVE, 0x00, 450, dist )
	sock.sendto( msg, ('192.168.43.123', 8123 ) )
	


# find image centroid (center of "mass" )
def find_centroid( img ):
	mom = cv2.moments(img)
	ret = False
	cx = 0
	cy = 0
	if mom['m00'] > 255*100:
		cx = int(mom['m01']/mom['m00'])
		cy = int(mom['m10']/mom['m00'])
		ret = True
	return ret, (cx, cy)

# Thread class for receiving and parsing the MJPEG stream from the phone
class StreamThread( threading.Thread ):
	def __init__( self ):
		threading.Thread.__init__( self )
		
		self.output = None
		self.cnt = 0
		self.setDaemon( True )
		
	def run( self ):
		try:
			while True:
				r = requests.get('https://192.168.43.100:8080/video', stream=True, verify = False)
				if r.status_code == 200:		
					data = bytes()
					
					for chunk in r.iter_content( chunk_size = 1024 ):
						data += chunk
						# search for jpeg boundaries
						a = data.find( b'\xff\xd8' )
						b = data.find( b'\xff\xd9' )
						if a != -1 and b != -1:
							jpg = data[ a:b+2 ]
							data = data[ b+2: ]
							self.output = jpg
							self.cnt += 1
		except:
			print( "Missing frame..." )


# negative feedback control for servoing the robot towards target
def servo_towards_centroid( mask, cx ):
	global servo_t
	dangle = cx - mask.shape[1]/2
	angle = int(dangle*1.1)
	print( "dangle", dangle, "angle", angle )
	
	# Measured: 3456 tacho steps per metre
	gain = 0.2893013100436681
	
	# if angular error is small enough -> move towards target
	if abs(dangle) < 15:
	#if abs(dangle) < 12:# for bridges
		move_robot( int( 35 / gain ) )
	else:
		rotate_robot( angle )
	time.sleep(0.55 )


def compute_sparsest_area( img ):
	#values = cv2.reduce( img, 0, cv2.REDUCE_SUM, dtype=cv2.CV_32S ).ravel()
	values = [row.sum() for row in cv2.transpose(img)]
	print( "len(values)", len(values) )
	w = [values[0]]*40
	flt = []
	for v in values:
		w.append( v )
		w = w[1:]
		flt.append( sum(w)*1.0/len(w) )
	
	mf = max(flt)
	flt2 = []
	for v in flt:
		flt2.append( 1 - v/mf )
	
	Xflt2 = 0.0
	Aflt2 = 0.0
	for i in range( len(flt2) ):
		Xflt2 += i*flt2[i]
		Aflt2 += flt2[i]
	
	print( "XFlt2", Xflt2, "Aflt2", Aflt2 )
	
	return Xflt2 / (Aflt2 + 1)

stream = StreamThread()
stream.start()

prev_cnt = 0

t_last_servo = time.time()


ROBOT_STATE = "IDLE"

#move_robot(300)

STATE_HISTORY = []

bridge_cnt = 5


while True:
		try:
			#if stream.output is None:
			#	continue
			if prev_cnt == stream.cnt:
				continue
			prev_cnt = stream.cnt
			
			t0 = time.time()
			img = cv2.imdecode( np.fromstring( stream.output, dtype = np.uint8 ), cv2.IMREAD_COLOR )
			bw = cv2.cvtColor( img, cv2.COLOR_BGR2GRAY )
			rows, cols = bw.shape
			M = cv2.getRotationMatrix2D( (cols/2, rows/2), -90, 1 )
			bw = cv2.warpAffine( bw, M, (cols, rows) )
			bw = cv2.flip( bw, 1 )
			
			hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
			hsv = cv2.warpAffine( hsv, M, (cols, rows) )
			#hsv = cv2.flip( hsv, 1 )
			true_color = cv2.warpAffine( img, M, (cols, rows) )
			
			cv2.imshow( "True", true_color )
			
			cv2.imshow( "HSV", hsv )
			
			if ROBOT_STATE != "IDLE":
				print( ROBOT_STATE )
			
			
			hsv = hsv[int(hsv.shape[0]*0.3):, :]
			found_viivat = False
			# viiva lattiassa
			if True:
				limit1 = np.array([0, 0, 220])
				limit2 = np.array([180, 15, 255])
				
				mask = cv2.inRange( hsv, limit1, limit2 )
				
				ret, centroid = find_centroid( mask )
				
				if ret:
					cx, cy = centroid
					cv2.circle(mask, (cy,cx), 10, (255,0,0), 1)
					
					left = mask[:, :int(1*mask.shape[1]/3)].sum()
					#print( "left", left )
					
					centre = mask[:, int(1*mask.shape[1]/3):int(2*mask.shape[1]/3)].sum()
					#print( "centre", centre )
					
					right = mask[:, int(2*mask.shape[1]/3):].sum()
					#print( "right", right )
					
					q_left = left*1.0/centre
					q_right = right*1.0/centre
					
					#print( "q_left", q_left, "q_right", q_right )
					
					if False:
						if q_left > 0.4:
							# turn left
							print( "TURN LEFT!" )
							pass
						
						elif q_right > 0.4:
							#turn right
							print( "TURN RIGHT!" )
							pass
					
					viivat_lattiassa_mask = mask.copy()
					found_viivat = True
					bridge_cnt = 5
					
				
				mask = cv2.cvtColor( mask, cv2.COLOR_GRAY2BGR )
				cv2.imshow( "Mask, viiva lattiassa", mask )
			
			# Labyrinttinappula
			if True:
				limit1 = np.array([25, 220, 220])
				limit2 = np.array([35, 255, 255])
				
				mask = cv2.inRange( hsv, limit1, limit2 )
				ret, centroid = find_centroid( mask )
				mask = cv2.cvtColor( mask, cv2.COLOR_GRAY2BGR )
				
				if ret:
					if ROBOT_STATE == "BRIDGE":
						ROBOT_STATE = "LABYRINTH_BUTTON"
						move_robot(300)
						time.sleep(0.25)
					cx, cy = centroid
					cv2.circle(mask, (cy,cx), 10, (255,0,0), 1)
					
					if ROBOT_STATE == "LABYRINTH_BUTTON":
						servo_towards_centroid( mask, cy )
				
				else:
					if ROBOT_STATE == "LABYRINTH_BUTTON":
						STATE_HISTORY.append( ROBOT_STATE )
						time.sleep(1.0)
						rotate_robot(-80)
						time.sleep(0.55)
						move_robot(800)
						time.sleep(0.55)
						
						print( "Changing to BRIDGE")
						ROBOT_STATE = "BRIDGE"
						
				
				
				cv2.imshow( "Mask, labyrinttinappula", mask )
			
			# Silta
			if True:
				limit1 = np.array([0, 50, 150])
				limit2 = np.array([35, 255, 255])
				
				mask = cv2.inRange( hsv, limit1, limit2 )
				
				if found_viivat:
					#mask = cv2.bitwise_or( mask, viivat_lattiassa_mask )
					print( mask.shape, viivat_lattiassa_mask.shape )
					mask = cv2.add( mask, viivat_lattiassa_mask )
				
				mask = mask[:mask.shape[0], :]
				ret, centroid = find_centroid( mask )
				mask = cv2.cvtColor( mask, cv2.COLOR_GRAY2BGR )
				
				if ret:
					cx, cy = centroid
					#print( "centroid", centroid )
					cv2.circle(mask, (cy,cx), 10, (255,0,0), 1)
					
					if ROBOT_STATE == "BRIDGE":
						servo_towards_centroid( mask, cy )
				else:
					if ROBOT_STATE == "BRIDGE":
						STATE_HISTORY.append( ROBOT_STATE )
						bridge_cnt -= 1
						if bridge_cnt < 1:
							ROBOT_STATE = "IDLE"
				
				cv2.imshow( "Mask, silta", mask )
			
			# Tolpat
			if True:
				#limit1 = np.array([0, 0, 80])
				#limit2 = np.array([180, 50, 250])
				limit1 = np.array([0, 0, 0])
				limit2 = np.array([180, 50, 80])
				
				mask = cv2.inRange( hsv, limit1, limit2 )
				ret, centroid = find_centroid( mask )
				mask = cv2.cvtColor( mask, cv2.COLOR_GRAY2BGR )
				
				if ret:
					cx, cy = centroid
					cv2.circle(mask, (cy,cx), 10, (255,0,0), 1)
					
					h,s,v = cv2.split( hsv )
					img2 = 255 - v
					
					img2 = cv2.resize( img2, None, fx = 2.0, fy = 2.0 )
					
					cv2.imshow( "Mask, tolpat, v2", img2 )
					
					
					if ROBOT_STATE == "FOREST":
						
						#sparsest = compute_sparsest_area( mask )
						sparsest = compute_sparsest_area( img2 )
						print("sparsest", sparsest)
						#servo_towards_centroid( mask, int(sparsest) )
						#time.sleep(0.5)
						#move_robot(200)
						#time.sleep(0.5)
					
				#cv2.imshow( "Mask, tolpat", mask )
			
			
			
			
		except IOError:
			print( "Missing frame.." )
		
		key = cv2.waitKey(25)
		if key & 0xff == 27:
			exit(0)
		
		if key & 0xff == ord( 'a' ):
			ROBOT_STATE = "BRIDGE"
		
		if key & 0xff == ord(' '):
			ROBOT_STATE = "IDLE"
		
		
