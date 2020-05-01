Robomaster 
**********
This API abstracts you from coding packets based on DJI Robomaster SDK. Simply include in your python code as one of the import directives.
::

    from rm import Robomaster
   
After you have import Robomaster object, you can code to control Robomaster using making calls to Robomaster's methods in the following workflow.
::

    robot = Robomaster()                #Step 1. Create an Robomaster object

    if robot.connect_via_direct_wifi(): #Step 2. Establish SDK connection using one of Establish SDK connection methods
        robot.move(1,2,3,4)             #Step 3. Execute your command using respective command functions
    else:
        print('error in connecting')
    
    robot.close()                       #Step 4. Close SDK connection


Robomaster Objects
==================
The Robomaster Object has these methods.

Establish SDK connection methods:

* `connect_via_direct_wifi`_
* `connect_via_usb`_
* `connect_via_router`_

Getting Video or Audio Stream methods:

* `videostreamon`_
* `videostreamoff`_
* `getvideoframe`_
* `audiostreamon`_
* `audiostreamoff`_
* `getaudioframe`_

Set Robot Travel mode:

* `set_travel_mode`_
* `query_travel_mode`_

Chassis control:

* `set_chassis_wheel_speed`_
* `move_chassis_by_distance`_
* `move_chassis_by_speed`_

Establish SDK Connection
------------------------
Before any other function call, establish SDK connection using one of these connect methods. Do only once.

.. _connect_via_direct_wifi:

connect_via_direct_wifi(**[** max_connection_attempt **]**)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*connect_via_direct_wifi()* function establishs SDK connection with a Robomaster. Use this function when your host machine is connected to robomaster via direct wifi.
Return True if SDK connection is successful, else return False. When *max_connection_attempt* is absent, 3 connection attempts will be made.

.. _connect_via_usb:

connect_via_usb(**[** max_connection_attempt **]**)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*connect_via_usb()* function establishs SDK connection with a Robomaster. Use this function when your host machine is connected to robomaster via USB.
Return True if SDK connection is successful, else return False. When *max_connection_attempt* is absent, 3 connection attempts will be made.

.. _connect_via_router:

connect_via_router(*address* **[**, max_connection_attempt **]** )
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*connect_via_router()* function establishs SDK connection with a Robomaster. Use this function when your host machine is connected to robomaster via router and robomaster has connected to the same router. Address is the IP address of the robomaster.
Return True if SDK connection is successful, else return False.

::

    r = Robomaster()
    r.connect_via_router('192.168.16.1')

Getting Video or Audio Stream methods
-------------------------------------
Turn video streaming before getting video frames. Do only once. Example of using the video stream.

::

    from PIL import Image as PImage
    import cv2
    import numpy as np
    import time
    import signal
    from rm import Robomaster

    robot = Robomaster
    playvideo = True

    if robot.connect_via_direct_wifi(): 
        if robot.videostreamon(): # Turn on video stream
            while playvideo:
                videoframe = robot.getvideoframe() # Get one frame of video
                cv2.namedWindow("RMLiveview")
                image = PImage.fromarray(videoframe) #turn video frame into image for display
                rimg = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                cv2.imshow("RMLiveview", rimg)
                cv2.waitKey(1)
            robot.videostreamoff()


Example of using the audio stream.

::

    from PIL import Image as PImage
    import pyaudio
    import numpy as np
    import time
    import signal
    from rm import Robomaster

    robot = Robomaster
    playaudio = True

    if robot.connect_via_direct_wifi(): 
        if robot.audiostreamon(): # Turn on audio stream
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16,channels=1,rate=48000,output=True)
            while playaudio:
                a_output = self.robot.getaudioframe()

                if a_output:
                    stream.write(a_output)
                else:
                    print("audio stream empty")
            robot.audiostreamoff()


.. _videostreamon:

videostreamon()
^^^^^^^^^^^^^^^
*videostreamon()* function turns on video streaming from Robomaster. Use this function before getting video frame.
Return True if video stream is turned on successful, else return False. 

.. _videostreamoff:

videostreamoff()
^^^^^^^^^^^^^^^^
*videostreamoff()* function turns off video streaming from Robomaster. Return True if video stream is turned off successful, else return False.

.. _getvideoframe:

getvideoframe()
^^^^^^^^^^^^^^^
*getvideoframe()* function gets a video frame from the stream. Return a h264 decoded video frame. Return None if there is no more video in the stream.

.. _audiostreamon:

audiostreamon()
^^^^^^^^^^^^^^^
*videostreamon()* function turns on audio streaming from Robomaster. Use this function before getting audio frame.
Return True if audio stream is turned on successful, else return False. 


.. _audiostreamoff:

audiostreamoff()
^^^^^^^^^^^^^^^^
*audiostreamoff()* function turns off audio streaming from Robomaster. Return True if audio stream is turned off successful, else return False.

.. _getaudioframe:

getaudioframe()
^^^^^^^^^^^^^^^
*getaudioframe()* function gets a audio frame from the stream. Return a opus decoded video frame. Return None if there is no more audio in the stream.

.. _set_travel_mode:


Set Robot Travel mode:
----------------------

set_travel_mode(**mode**)
^^^^^^^^^^^^^^^^^^^^^^^^^
*set_travel_mode(mode)* functions set the travel mode of the robot. Acceptable value for mode are chassis_lead, gimbal_lead or free. Return ok if it is successful.

.. _query_travel_mode:

query_travel_mode()
^^^^^^^^^^^^^^^^^^^
*query_travel_mode(mode)* function queries the current travel mode of the robot. Return a string containing the travel mode of the robot.

.. _set_chassis_wheel_speed:

Chassis Control
---------------

set_chassis_wheel_speed(**w1,w2,w3,w4**)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*set_chassis_wheel_speed(w1,w2,w3,w4)* function set the rotation speed of the 4 wheels. Upon set, the robot will move until the rotation speed is set otherwise with another chassis command. Acceptable value for w1, w2,w3,w4 ranges from -1000 to 1000. All four w1,w2,w3,w4 must be defined. Return ok if set successful.

.. _move_chassis_by_distance:

move_chassis_by_distance(**x,y,z,vxy,vz**)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
move_chassis_by_distance(x,y,z,vxy,vz)* translate or move the chassis until the defined distance from its current position is reached. 

* x and y are in meters ranges from -5m to 5m. 
* z are in degree to rotate the chassis and acceptable value ranges from -1800 to 1800. 
* vxy is speed in m/s at which to translate x and y distance and acceptable values ranges from 0 to 3.5.
* vz is speed in degree/s at which to rotate the chassis and acceptable values from 0 to 600.
* It is not necessary to define all of the values. The function needs at least value of x or y or z.

.. _move_chassis_by_speed:

move_chassis_by_speed(**x,y,z**)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
move_chassis_by_speed(x,y,z,vxy,vz)* keeps the robot moving at the defined speed until another chassis command is received. 

* x and y are in m/s ranges from -3.5m/s to 3.5m/s. 
* z are in degree/sec to rotate the chassis and acceptable value ranges from -600 (counter-clockwise) to 600 (clockwise) degree/sec. 
* It is not necessary to define all of the values. The function needs at least value of x or y or z.