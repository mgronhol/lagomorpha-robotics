# lagomorpha-robotics
This project contains code for team Lagomorpha's robot for Robot Uprising 2018.
We used a Lego EV3 robot with an ev3dev OS. We used Python and computer vision
for controlling the robot. A phone with camera
was connected to the robot, the data was streamed to a PC processing the
data using OpenCV. We implemented an UDP server on the robot to communicate
with and control it. We also wrote code to control the robot via an Xbox
controller.

The robot can cross brigdes and follow lines autonomously, and it can be
controlled with an Xbox gamepad. When we control the robot with the 
gamepad, we still use computer vision - the driver uses the stream
on the screen to move the robot and does not need to see the track at all.

## Challenge 1 (Labyrinth)

This challenge is solved completely autonomously by the robot. It detects 
the bridge and moves to it, then moves through the labyrinth. Using computer
vision, it detects the brigde, the line on the floor, and the yellow plate
in the labyrinth. 

## Challenge 2 (Forest)

The robot moves over the brigde to the forest by itself, otherwise this challenge is solved by a human driver using the robot's computer vision.
We can already detect that the robot is in the forest and did some work on 
an algorithm for the robot to move through it autonomously, but did not have time to 
complete it.

## Challenge 3 (Monolith)

The robot moves over the brigde to the challenge by itself, otherwise this challenge is solved by a human driver using the robot's computer vision. Our robot includes a crane
that we use to lift and drop objects.

## Challenge 4 (Assembly)

The robot moves over the brigde to the challenge by itself, otherwise this challenge is solved by a human driver using the robot's computer vision.

## Challenge 5 (Calibration)

The robot moves over the brigde to the challenge by itself, otherwise this challenge is solved by a human driver using the robot's computer vision.

## Challenge 6 (Entanglement)

The robot moves over the brigde to the challenge by itself, otherwise this challenge is solved by a human driver using the robot's computer vision and other robots
defeated through our human driver's great reflexes and cunning.

