
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
import dlib
from PIL import Image
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('-ip')
parser.add_argument('-server_port', type=int, help='server port to connect the socket to')
parser.add_argument('-ms_port', type=int, help='motion sensor input port')
parser.add_argument('-relay_port', type=int, help='relay switch input port')
args = parser.parse_args()
# Set relay port
output_port = getattr(args, 'relay_port') or 25
print(args.ip)
# Check if processig data on server
server_process =  False if args.ip == None else True
# Status of NC when ON aka closed
relay_off = True
# Set up dlib's face detection 
# HOG face detector 
face_detector = dlib.get_frontal_face_detector()

def find_face(image):
    detected_faces = face_detector(image, 1)
    return False if len(detected_faces) == 0 else True

def relay(delay):
    # Set status of the relay when OFF(NC is open aka OFF)
    relay_off = False
    GPIO.output(output_port, GPIO.HIGH)
    time.sleep(delay)
    GPIO.output(output_port, GPIO.LOW)
    # Set status of the relay when ON(NC is closed aka ON)
    relay_off = True


def result():
    print(':::: Inside Result ::::')
    # Receive and process the result
    p = re.compile(r'\d+\.\d+')
    try:
        while True:
            if connection is not None:
                result_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
                if not result_len:
                    continue
                result_stream = connection.read(result_len)
                print('RESULT FROM THE SERVER ::::  ', result_stream)
                for prediction in p.findall(result_stream.split('===\n')[1]):
                    if float(prediction) >= 0.80 and relay_off:
                        relay(5)
                    print(prediction)
    finally:
        print('result finally')

def set_up_socket_connection():
    # Get hostname from command line arguement
    server_hostname = args.ip
    server_port = getattr(args, 'server_port') or 8000
    # Connect a client socket to hostname:8000 (your server)
    client_socket = socket.socket()
    client_socket.connect((server_hostname, server_port))
    
    # Make a file-like object out of the connection
    connection = client_socket.makefile('wb')
    # Create thread for listening to result from the server
    thread = Thread(target=result, args=())
    thread.daemon = True
    # Thread start listening for eternity
    thread.start()
    return connection, client_socket

def send_stream_data_to_server(stream, connection):
    # Write the length of the capture to the stream and flush to
    # ensure it was actually sent.
    connection.write(struct.pack('<L', stream.tell()))
    connection.flush()
    # Rewind the stream and send the image data over the wire
    stream.seek(0)
    connection.write(stream.read())

def end_stream(connection):
    # Write a length of 0 to the stream to signal that we are done
    print('sending 0 to the connection!')
    connection.write(struct.pack('<L', 0))

# Set up GPIO for LED/Relay
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(output_port, GPIO.OUT)
# Create motion sensor and accept input on port
pir = MotionSensor(getattr(args, 'ms_port') or 17)

# If processing on a server then set up socket conenction
if server_process:
    connection, client_socket = set_up_socket_connection()
try:
    while True:
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
                    # Send stream to server
                    if server_process:
                        send_stream_data_to_server(stream, connection)
                    # If we've been capturing for more than 10s then quit
                    if time.time() - start > 10:
                        break
                    # Reset the stream for next capture
                    stream.seek(0)
                    # Consctruct an image and find a face
                    image = Image.open(stream)
		    print(np.shape(image))
		    image.save('./test.jpeg')
		    if find_face(image):
                        relay(5)
                    stream.truncate()

                if server_process:
        	    end_stream(connection)
                print('stopping camera')
finally:
    print('in finally')
    if server_process:
        connection.close()
        client_socket.close()
