import io
import socket
import struct
from PIL import Image
from datetime import datetime

# Start the server and start listenning on port 8000
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(0)
print('Listenning for the client...')
# Accept a single connection and make a file like object out of it
connection = server_socket.accept()[0].makefile('rb')
try:
    while True:
        # Read the length of the image as a 32-bit unsigned int
        # If the length is 0, then quit the loop
        image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
        if not image_len:
            break
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
finally:
    connection.close()
    server_socket.close()
