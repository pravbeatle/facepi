import io
import socket
import struct
from PIL import Image
from datetime import datetime
import subprocess
import argparse
from os import listdir
from platform import system
import dlib
import numpy as np

# Set up dlib's face detection 
# # HOG face detector 
face_detector = dlib.get_frontal_face_detector()

def find_person(image):
    filename = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.jpeg")
    image.save('temp/' + filename)
    result = subprocess.Popen("./lib/openface/demos/classifier.py infer {} ./generated-embeddings/classifier.pkl ./temp/{}".format("--multi", filename), stdout=subprocess.PIPE, shell=True)
    return result.communicate()[0]

def find_face(image):
    detected_faces = face_detector(np.array(image, dtype=np.uint8), 1)
    print('no of faces found :::: ', len(detected_faces))
    return False if len(detected_faces) == 0 else True


parser = argparse.ArgumentParser()
parser.add_argument('-server_port', type=int, help='server port to connect the socket to')
args = parser.parse_args()

# Start the server and start listenning on port 8000
server_socket = socket.socket()
port = getattr(args, 'server_port')
server_socket.bind(('0.0.0.0', port or 8000))
server_socket.listen(0)
print('Listenning for the client...')
# Accept a single connection and make a file like object out of it
connection = server_socket.accept()[0].makefile('wb')
try:
    while True:
        # Read the length of the image as a 32-bit unsigned int
        # If the length is 0, then keep looping
        image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
        if not image_len:
            # Delete the temp directory if not empty
            files = listdir('./temp')
            if system() == 'Darwin' and len(files) > 1:
                subprocess.Popen("rm ./temp/*", shell=True)
            elif system() == 'Linux' and len(files) == 0:
                subprocess.Popen("rm ./temp/*", shell=True)
            continue
        # Construct a stream to hold the image data and read the image data from the connection
        image_stream = io.BytesIO()
        image_stream.write(connection.read(image_len))
        # Rewind the stream, open it as an image file with PIL and do some processing!
        image_stream.seek(0)
        image = Image.open(image_stream)
        print('Image is %d%d' % image.size)
        image.verify()
        print('Image is verified')
        image = Image.open(image_stream)
        ## Process the image
        result_output = find_face(image)
        print(':::: PRINTINT RESULT ::::', result_output)
        # Create result stream and write its length to connection
        connection.write(struct.pack('<L', len(str(result_output))))
        connection.flush()
        # Rewind the stream and write its contents to the connection
        connection.write(str(result_output))
        connection.flush()
finally:
    connection.close()
    server_socket.close()
