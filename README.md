# A Python Module for interfacing with DJI Robomaster in Cleartext SDK mode

This Python module handles the networking interfaces to control DJI Robomaster EP in SDK mode and handling of telemetry and event data from DJI Robomaster EP. This library must use in conjuction with [Robomaster EP Cleartext SDK](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/sdk_intro.html). Please refer to Robomaster EP Cleartext SDK for the commands to control Robomaster EP and to request telemetry data from Robomaster EP. 

Before using these codes, please ensure your machine has the necessary software and environment as prescribed in [Preparation Steps in Robomaster EP Cleartext SDK](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/sdk_intro.html#id1).

## Robomaster Class

This rm module provides the interfacing via a Robomaster Class. 

    rm.Robomaster(robot_ip='192.168.2.1', command_port=40923, video_port=40921, audio_port=40922, telem_port=40924, event_port=40925, broadcast=40926)

Constructor class for a Robomaster Object. All parameters are optional if the interfacing ports remain default to the Robomaster Cleartext SDK. 

## Robomaster Object's Methods

A Robomaster Object provides the following public methods:

    Robomaster.start_sdk_session(self, robot_ip, reconnect_attempt=3)

> start_sdk_session enters the Robomaster into cleartext SDK mode by sending "command" to Robomaster as specified by the robot_ip. This is first method to use and need not send "command" again. The robot_ip must be in IP address format (e.g. 192.168.2.1) and refers to [Access Method in Robomaster Cleartext SDK](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/connection.html) for the IP address to use. Returns 1 if successful. Return 0 or -1 if fails and -1 for parameter error while 0 for Robomaster EP rejects.  

    Robomaster.quit_sdk_session(self)

> quit_sdk_session exits the Robomaster from cleartext SDK mode.

    Robomaster.instruct(self, instruction)

> instruct send instruction to Robomaster. This is to be used after Robomaster enters SDK mode. Please refer to [clear text agreement](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/api.html) for the format of instruction. NOTE: Do not need to put ; and seq number in your instructions as instruct will append ; and seq number to your instruction. instruct() returns when there is response from Robomaster. Returns result from Robomaster or -1 if there is no SDK session or socket error.

    Robomaster.video_on(self)

> video_on instructs Robomaster to stream video out. Returns true if successful.


    Robomaster.audio_on(self)

> video_on instructs Robomaster to stream audio out. Returns true if successful.


    Robomaster.getvideoframe(self)

> getvideoframe returns a numpy array containing a frame of h264 decoded video with a resolution of 1280*720 and a refresh rate of 30 FPS.

    Robomaster.getaudioframe(self)

> getaudioframe returns a frame of opus decoded audio data that is at sampling rate of 48000 bps, a frame size of 960 bit, and a single channel.

    Robomaster.inform(self, who)

> inform registers a function passed by the who parameter. Robomaster objects calls the registered function when Robomaster reports one of the following events. Robomaster object calls the function by providing the event data provided by Robomaster robot. Robomaster robot reports event only when there is corresponding command to turn on the respective event detection. Please refer to [clear text agreement](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/api.html) for the format of event data.

Event | Event Detection and Event Data Format
------|--------------------------------
Armor Hit | [3.2.6.3 and 3.2.6.4](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id32)
Sound | [3.2.7.1 and 3.2.7.2](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id38) 
Sensor Adaptor | [3.2.10.4 and 3.2.10.5](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id38)

    Robomaster.stop_inform(self, who)

> stop_information deregister the function to call when there is a event detected.

## Robomaster Object's Variables

Robomaster Object has the following public variables. These public variables are meant to provide telemetry data of the Robomaster robot when the respective telemetry data push are turned on via SDK command.

Variable | Telemetry Push | Sections on SDK Command on command and data format
---------|----------------|---------------
Robomaster.chassis_x (float) | chassis position x from position of power on | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16) 
Robomaster.chassis_y (float) | chassis position y from position of power on | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16) 
Robomaster.chassis_pitch (float) | chassis attitude pitch | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16)
Robomaster.chassis_roll (float) | chassis attitude roll | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16)
Robomaster.chassis_yaw (float) | chassis attitude yaw | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16)
Robomaster.gimbal_x (float) | gimbal position x | [3.2.4.8 and 3.2.4.9](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id26) 
Robomaster.gimbal_y (float) | gimbal position y| [3.2.4.8 and 3.2.4.9](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id26) 
Robomaster.chassis_static (Boolean) | chassis moving? | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16)
Robomaster.chassis_uphill (Boolean) | chassis facing uphill? | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16)
Robomaster.chassis_downhill (Boolean) | chassis facing downhill? | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16)
Robomaster.chassis_onslope (Boolean) | chassis on slope? | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16)
Robomaster.chassis_pick_up (Boolean) | chassis being picked up? | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16)
Robomaster.chassis_slip (Boolean) | chassis slipping? free movement | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16)
Robomaster.chassis_impact_x (Boolean) | chassis impact on x? | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16)
Robomaster.chassis_impact_y (Boolean) | chassis impact on y? | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16)
Robomaster.chassis_impact_z (Boolean) | chassis impact on z? | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16)
Robomaster.chassis_roll_over (Boolean) | chassis rolled over? | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16)
Robomaster.chassis_hill_static (Boolean) | chassis on hill and static? | [3.2.3.8](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id16)
Robomaster.people_ai_data (string) | position data of detected people | [3.2.15.2 and 3.2.15.3](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id67)
Robomaster.pose_ai_data (string) | data of detected gesture | [3.2.15.2 and 3.2.15.3](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id67)
Robomaster.marker_ai_data (string) | data of detected marker | [3.2.15.2 and 3.2.15.3](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id67)
Robomaster.line_ai_data (string) | data of detected line | [3.2.15.2 and 3.2.15.3](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id67)
Robomaster.robot_ai_data (string) | data of detected robot | [3.2.15.2 and 3.2.15.3](https://robomaster-dev.readthedocs.io/zh_CN/latest/sdk/protocol_api.html#id67)

## Codes Examples

File Name | Objective
----------|----------
basic.py| Show basic use of Robomaster with callback examples
RobotVideoClient.py| Show video and audio streaming of Robomaster 


(c)2020, 65Drones Pte Ltd
