import io
import socket
import struct
from PIL import Image
from datetime import datetime
import subprocess

# Start the server and start listenning on port 8000
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8000))
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
            # Delete the temp directory
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
        filename = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.jpeg")
        image.save('temp/' + filename)
        ## Process the image
        result = subprocess.Popen("./lib/openface/demos/classifier.py infer {} ./generated-embeddings/classifier.pkl ./temp/{}".format("--multi", filename), stdout=subprocess.PIPE, shell=True)
        result_output = result.communicate()[0]
        print(':::: PRINTINT RESULT ::::', result_output)
        # Create result stream and write its length to connection
        connection.write(struct.pack('<L', len(result_output)))
        connection.flush()
        # Rewind the stream and write its contents to the connection
        connection.write(result_output)
        connection.flush()
finally:
    connection.close()
    server_socket.close()
