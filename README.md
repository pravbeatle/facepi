# facepi
facial detection door opener 

![facepi](https://user-images.githubusercontent.com/5251742/46936311-b15cbd80-d07b-11e8-91c9-2deec44b0028.jpg)

Install Openface and dlib libraries under lib/ 

<b>First</b>, do pose detection and alignment:  <br />
./lib/openface/util/align-dlib.py ./training-images/ align outerEyesAndNose ./aligned-images/ --size 96 <br />

This will create a new ./aligned-images/ subfolder with a cropped and aligned version of each of your test images.<br /><br />


<b>Second</b>, generate the representations from the aligned images:<br />
./lib/openface/batch-represent/main.lua -outDir ./generated-embeddings/ -data ./aligned-images/ <br />

After you run this, the ./generated-embeddings/ sub-folder will contain a csv file with the embeddings for each image.<br /><br />


<b>Third</b>, train your face detection model: <br />
./lib/openface/demos/classifier.py train ./generated-embeddings/ <br />

This will generate a new file called ./generated-embeddings/classifier.pkl. <br />
This file has the SVM model you'll use to recognize new faces. <br />
At this point, you should have a working face recognizer! <br /><br />


<b>Finally</b>, a new picture with an unknown face. <br />
Pass it to the classifier script like this:<br />
./lib/openface/demos/classifier.py infer ./generated-embeddings/classifier.pkl your_test_image.jpg<br />

You should get a prediction that looks like this:<br />
=== /test-images/bill-gates-1.jpg === <br />
Predict bill-gates with 0.73 confidence. <br />

From here it's up to you to adapt the ./demos/classifier.py python script to work however you want.
