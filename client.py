from gpiozero import MotionSensor
import sys
import io
import socket
import struct
import time
import picamera
import RPi.GPIO as GPIO
from threading import Thread
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-ip')
parser.add_argument('-server_port', type=int, help='server port to connect the socket to')
parser.add_argument('-ms_port', type=int, help='motion sensor input port')
parser.add_argument('-relay_port', type=int, help='relay switch input port')
args = parser.parse_args()
# Set relay port
output_port = getattr(args, 'relay_port') or 25

def relay(delay):
    GPIO.output(output_port, GPIO.HIGH)
    time.sleep(delay)
    GPIO.output(output_port, GPIO.LOW)

def result(connection):
    print(':::: Inside Result ::::')
    # Receive and process the result
    p = re.compile(r'\d+\.\d+')
    r = True
    while r:
        if connection is not None:
            result_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
            if not result_len:
                continue
            result_stream = connection.read(result_len)
            print('RESULT FROM THE SERVER ::::  ', result_stream)
            for prediction in p.findall(result_stream.split('===\n')[1]):
                if float(prediction) >= 0.90:
                    relay(2)
 		    print(prediction)
                r = False

# Set up GPIO for LED/Relay
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(output_port, GPIO.OUT)
# Get hostname from command line arguement
server_hostname = args.ip
server_port = getattr(args, 'server_port') or 8000
# Connect a client socket to hostname:8000 (your server)
client_socket = socket.socket()
client_socket.connect((server_hostname, server_port))
pir = MotionSensor(getattr(args, 'ms_port') or 17)
# Make a file-like object out of the connection
connection = client_socket.makefile('wb')
try:
    while True:
        print('in while')
        if pir.motion_detected:
            print('Motion Detected!')
            with picamera.PiCamera() as camera:
                camera.hflip = True
                camera.vflip = True
                camera.resolution = (640, 460)
                # Start the camera and let it stabilize for 2 seconds
                time.sleep(2)

                # Note the start time and construct a stream to hold image data temporarily
                # (instead of direcrly writing to the connection, we first find out the size)
                start = time.time()
                stream = io.BytesIO()
                print('about to capture')
                for c in camera.capture_continuous(stream, 'jpeg'):
                    # Write the length of the capture to the stream and flush to
                    # ensure it was actually sent.
                    connection.write(struct.pack('<L', stream.tell()))
                    connection.flush()
                    # Start thread to receive result for this image
                    thread = Thread(target=result, args=(connection))
                    thread.start()
                    # Rewind the stream and send the image data over the wire
                    stream.seek(0)
                    connection.write(stream.read())
                    # If we've been capturing for more than 30s then quit
                    if time.time() - start > 10:
                        break
                    # Reset the stream for next capture
                    stream.seek(0)
                    stream.truncate()
        	    # Write a length of 0 to the stream to signal that we are done
                print('sending 0 to the connection!')
                connection.write(struct.pack('<L', 0))
                print('stopping camera')
finally:
    print('in finally')
    connection.close()
    client_socket.close()
