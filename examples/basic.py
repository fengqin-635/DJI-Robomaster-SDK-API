import time
from rm import Robomaster
import threading
import socket
import os
import sys
import socket

def testattitudepush(data):
    print(data)

def main(mode='host'):
    robot_ip = '192.168.2.1'
    robot = Robomaster()
    if mode == 'network':
        robot_ip = robotlistener()
        if robot_ip == '':
            print('no robot connected to network')
            robot_ip = '192.168.2.1'
    
    if robot.start_sdk_session(robot_ip) == 1:
        robot.instruct('chassis push attitude on status on position on')
        time.sleep(1)
        print(robot.instruct('sound event applause on'))
        robot.inform(testattitudepush)
        print(robot.instruct('armor event hit on'))
        print(robot.instruct('sensor_adapter event io_level on'))
        print(robot.instruct('gimbal push attitude on'))
        time.sleep(1)
        robot.instruct('gimbal moveto p 20 y 50 vp 100 vy 100')
        time.sleep(2)
        print(robot.gimbal_x)
        print(robot.gimbal_y)
        print(robot.instruct('chassis position ?'))
        time.sleep(1)
        print(robot.instruct('chassis wheel w1 0 w2 0 w3 0 w4 0'))
        time.sleep(1)
        i = 0
        while i < 100:
            i = i + 1
            time.sleep(0.1) #loop for you to clap to test event callback

        print(robot_ip.instruct('chassis wheel w9 20 w2 20 w3 30 w5 40'))
        time.sleep(1)
        robot.quit_sdk_session()
    else:
        print('connection failed')


def robotlistener():
    try:
        broad_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        broad_address = ('0.0.0.0', 40926)
        broad_sock.bind(broad_address)

        found_robot_ip = ''
        i = 0
        print('waiting for broadcast')

        while found_robot_ip == '' and i < 10:
            data, address = broad_sock.recvfrom(4096)
            d = data.decode('UTF-8')
            print("Received broadcast from %s - %s " % (address, d))
            if 'robot ip' in d:
                s = d.split()
                if len(s) >= 3:
                    found_robot_ip = s[2]
                    try:
                        socket.inet_aton(found_robot_ip)
                        print('Found robot - %s' % found_robot_ip)
                    except socket.error:
                        found_robot_ip =''
                        print('invalid ip address.')
                else:
                    print('not robot ip broadcast')
            else:
                print('not robot ip broadcast')
                
            i = i + 1
            time.sleep(0.5)
            print('scan %s' % str(i))
        
        return found_robot_ip
    except socket.error as err:
        print("Unable to listen for robots - %s" % err)
        sys.exit(0)

if __name__ == "__main__":
    try:
        main('host') # main('network') if you wish to try using router mode
    except KeyboardInterrupt:
        e.close()
        sys.exit(0)