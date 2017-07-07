from gpiozero import MotionSensor
import sys
import io
import socket
import struct
import time
import picamera

server_hostname = sys.argv[1]
server_port = 8000
# Connect a client socket to hostname:8000 (your server)
client_socket = socket.socket()
client_socket.connect((server_hostname, server_port))
pir = MotionSensor(6)
# Make a file-like object out of the connection
connection = client_socket.makefile('wb')
try:
    with picamera.PiCamera() as camera:
        camera.hflip = True
        camera.vflip = True
        camera.resolution = (640, 460)
        if pir.motion_detected:
            # Start the camera and let it stabilize for 2 seconds
            time.sleep(2)

            # Note the start time and construct a stream to hold image data temporarily
            # (instead of direcrly writing to the connection, we first find out the size)
            start = time.time()
            stream = io.BytesIO()
            for c in camera.capture_continuous(stream, 'jpeg'):
                # Write the length of the capture to the stream and flush to
                # ensure it was actually sent.
                connection.write(struct.pack('<L', stream.tell()))
                connection.flush()
                # Rewind the stream and send the image data over the wire
                stream.seek(0)
                connection.write(stream.read())
                # If we've been capturing for more than 30s then quit
                if time.time() - start > 30:
                    break
                # Reset the stream for next capture
                stream.seek(0)
                stream.truncate()
            # Write a length of 0 to the stream to signal that we are done
            connection.write(struct.pack('<L', 0))
        time.sleep(30)
finally:
    connection.close()
    client_socket.close()
