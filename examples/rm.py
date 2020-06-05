import socket
import select
import types
import threading
import time
import queue
import libh264decoder
import numpy as np
import signal
import cv2
import opus_decoder
import sys
from PIL import Image as PImage
import pyaudio

class Robomaster:
    def __init__(self,robot_ip='192.168.2.1',command_port=40923,video_port=40921,audio_port=40922,telem_port=40924,event_port=40925,broadcast=40926,telemetry=True):
        self.robot_ip = robot_ip
        self.command_port = command_port
        self.video_port = video_port
        self.audio_port = audio_port
        self.telem_port = telem_port
        self.broadcast = broadcast
        self.event_port = event_port
        self.command_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.video_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.audio_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.telem_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.event_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.r_socks =[]
        self.w_socks =[]
        self.a_socks =[]
        self.in_video_mode = False
        self.in_audio_mode = False
        self.in_command_mode = False
        self.last_cmd = None
        self.start_cmd_time = -1
        self.timeout = 9.0
        self.cmd_timeout = 15
        self.cmd_start_time = -1
        self.telemetry = telemetry

        self.decoder = libh264decoder.H264Decoder()
        libh264decoder.disable_logging
        self.audiodecoder = opus_decoder.opus_decoder()
        self.decoder_queue = queue.Queue(256)

        self.audio_decoder = opus_decoder.opus_decoder()
        self.audio_decoder_queue = queue.Queue(128)
        self.audioframe = None

        self.last_frame = None                
        self.frame = None
        self.is_freeze = False
        self.videothread = threading.Thread(target=self._receive_video_data)
        self.videothread.daemon = True
        self.audiothread = threading.Thread(target=self._receive_audio_data)
        self.audiothread.daemon = True
        self._cmdseq = 0

        self.socket_closed = False
        self.response =''
        self.connecting = False
        self.connecting_timeout = False
        self.connecting_error = False
        self.in_action = False

        self.telemthread = threading.Thread(target=self._dispatch_telemetry)
        self.telemthread.daemon = True

        self.eventthread = threading.Thread(target=self._dispatch_event)
        self.eventthread.daemon = True
        self.cb_list = []

        self.telemetry_sleep = 0.5

        self.data_queue = {
            self.command_sock : queue.Queue(32),
            self.audio_sock : queue.Queue(32),
            self.video_sock : queue.Queue(32),
            self.telem_sock : queue.Queue(32),
            self.event_sock : queue.Queue(32)
        }
        self.data_timeout = 3

        self.socket_error = False
        self.chassis_x = -1
        self.chassis_y = -1
        self.chassis_pitch = -1
        self.chassis_roll = -1
        self.chassis_yaw = -1
        self.chassis_static = False
        self.chassis_uphill = False
        self.chassis_downhill = False
        self.chassis_onslope = False
        self.chassis_pick_up = False
        self.chassis_slip = False
        self.chassis_impact_x = False
        self.chassis_impact_y = False
        self.chassis_impact_z = False
        self.chassis_roll_over = False
        self.chassis_hill_static = False
        self.people_ai_data = ""
        self.pose_ai_data = ""
        self.marker_ai_data = ""
        self.line_ai_data = ""
        self.robot_ai_data = ""
        self.gimbal_x = -1
        self.gimbal_y = -1


    def __del__(self):
        self.close()

    def close(self):
        self.video_off()
        self.audio_off()
        r = self._blocksend('quit')
        self.socket_closed = True
        self.in_command_mode = False
        self.video_sock.close()
        self.audio_sock.close()
        self.event_sock.close()
        self.command_sock.close()
        if self.telemetry:
            self.telem_sock.close()

    
# return -1 means error in parameter or socket error, return 0 means start sdk mode failed due to robot offline or robot error return 1 means success
    def start_sdk_session(self, robot_ip,reconnect_attempt=3):
        self.socket_error = False
        if robot_ip is None:
            return -1
        else:
            print('Starting SDK session to Robot %s' % self.robot_ip)
            try:
                socket.inet_aton(robot_ip)
                self.robot_ip = robot_ip
                return self._connect(max_connect_attempt=reconnect_attempt)
            except socket.error:
                print("Invalid IP")
                return -1
    
    def quit_sdk_session(self):
        self.close()
    
    def _connect(self,max_connect_attempt=3):
        self.max_connect_attempt = max_connect_attempt
        try:
            rm_command_addr = (self.robot_ip,self.command_port)
            self.command_sock.connect(rm_command_addr)
            self.command_sock.setblocking(False)
            self.command_sock.settimeout(5)
            self.message_q = queue.Queue()
            self.w_socks.append(self.command_sock)
            self.r_socks.append(self.command_sock)
            self.a_socks.append(self.command_sock)
            self.sock_process_thread = threading.Thread(target=self._process_socks)
            self.sock_process_thread.daemon = True
            self.sock_process_thread.start()
            self.connecting_timeout = False
            connect_attempt = 1
            while connect_attempt < self.max_connect_attempt:
                print('Attempt %s.' % str(connect_attempt))

                self._send('command')
                while self.in_command_mode == False and self.connecting_timeout == False and self.connecting_error == False:
                    time.sleep(3)
                
                if self.in_command_mode == False:
                    if self.connecting_timeout:                        
                        self.connecting = False
                    if self.connecting_error:
                        self.connecting = False

                connect_attempt = connect_attempt + 1

                if self.in_command_mode:
                    break

                if connect_attempt > self.max_connect_attempt:
                    return 0

            if self.connecting_error:
                return 0
            if self.in_command_mode:
                return 1
            else:
                return 0
        except socket.error as err:
            print("Robot %s entering command mode failed.(%s)" % (self.robot_ip,err))
            self.command_sock.close()
            self.socket_error = True
            return -1


    #return -1 if no sdk session or socket error, else return result from robot
    def instruct(self,instruction):
        if self.in_command_mode == False:
            return -1

        self._blocksend(instruction)
        if self.socket_error:
            return -1
        
        return self.response

    #non-blocking mode send. Instructions are queued.
    def _send(self, data):
#        self.last_cmd = data.lower()
        try:
            if data.lower() == 'command' and self.in_command_mode == False:
#                print("Connecting to %s" % self.robot_ip)
#                data = data.rstrip() + ' ' + str(self._cmdseq)
                self.message_q.put(data.rstrip())
            else:
                if self.in_command_mode == False:
                    print('Robot %s unable to process as not in command mode except command' % self.robot_ip)
                else:
#                    data = data.rstrip() + ' ' + str(self._cmdseq)                    
                    self.message_q.put(data.rstrip())
            return True
        except queue.Full as err:
            print("Robot %s (send) Queue Full- %s" % (self.robot_ip,err))
            return False

    #block send mode. Returns only when robomaster provide response.
    def _blocksend(self,data):
        while self.in_action:
            time.sleep(0.1)
        
        while self.message_q.empty() == False:
            time.sleep(0.1)

#        d = data.lower()
        self._send(data)

        while self.in_action or self.message_q.empty() == False:
            time.sleep(0.1)

        return self.response

    # return true means successful else failed 
    def video_on(self):
        self._send('stream on')
        i = 0
        while self.in_video_mode == False and i < 5:
            time.sleep(1)
            i = i + 5
        return self.in_video_mode

    def audio_on(self):        
        self._send('audio on')
        i = 0
        while self.in_audio_mode == False and i < 5:
            time.sleep(1)
            i = i + 5
        return self.in_audio_mode

    def video_off(self):
        self._send('stream off')
        i = 0
        while self.in_video_mode == True and i < 5:
            time.sleep(1)
            i = i + 5

    def audio_off(self):
        self._send('audio off')
        i = 0
        while self.in_audio_mode == True and i < 5:
            time.sleep(1)
            i = i + 5

    # return None means the robot is not in video or no data.
    def getvideoframe(self):
        if self.in_video_mode:
            try:
                self.frame = self.decoder_queue.get(timeout=2)
            except queue.Empty:
                if self.socket_closed:
                    print("Robot %s - socket closed" % self.robot_ip)
                print("Robot %s rf- video queue empty" % self.robot_ip)
                return self.last_frame
            else:
                if self.is_freeze:
                    return self.last_frame
                else:
                    self.last_frame = self.frame
                    return self.frame
        else:
            return None

    def video_freeze(self,is_freeze=True):
        self.is_freeze= is_freeze
        if is_freeze:
            self.last_frame = self.frame

    def _get_seq_number_from_response_with_seq(self, response):
        if 'seq' in response:
            try:
                return int(response.split(' ')[-1])
            except ValueError:
                return -2
        else:
            return -1

    def _get_result_from_response_with_seq(self, response):
        if 'seq' in response:
            resp = response.split(' ')
            try:
                s = ' '.join(resp[0:-2])
#                print(s)
                s = s.rstrip()
                return s
            except Exception as e:
                return str('')
        else:
            return str('')
                        
    def _process_going_into_command(self, result):    

        r = result

        if self._get_seq_number_from_response_with_seq(result) > -1:
            r = self._get_result_from_response_with_seq(result)

        if self.in_command_mode == False:
            if r.lower() == 'ok':
                try:
                    event_sock_addr = (self.robot_ip,self.event_port)
                    self.event_sock.connect_ex(event_sock_addr)
                    self.event_sock.setblocking(False)
                    self.event_sock.settimeout(10)
                    self.eventthread.start()
                    self.r_socks.append(self.event_sock)
                    self.a_socks.append(self.event_sock)
                    print('Robot %s connected to event port' % self.robot_ip)
                except socket.error as err:
                    self.event_sock.close()
                    print("Robot %s timeout at connecting to event port - %s" % (self.robot_ip,err))
                try:
                    if self.telemetry:
                        telem_address = ('0.0.0.0', self.telem_port)
                        self.telem_sock.bind(telem_address)
                        self.telemthread.start()
                        self.r_socks.append(self.telem_sock)
                        self.a_socks.append(self.telem_sock)
                        print('Robot %s started telemetry receiver' % self.robot_ip)
                    print('SDK Connection to Robot %s successful' % self.robot_ip)
                except socket.error as err:
                    self.telem_sock.close()
#                    self.socket_error = True
                    print("Robot %s error at binding to telemetry port - %s" % (self.robot_ip,err))
                self.in_command_mode = True
                self.connecting = False
            else:
                if r.lower() == 'error':
                    print('Robot %s command mode failed' % self.robot_ip)
                    self.connecting_error = True
                else:
                    self.connecting_error = True
                    print('Robot %s encountered unexpected data when going into command mode - %s' % (self.robot_ip, r))
        else:
            self.connecting_error = True
            print('Robot %s is not going into command mode' % self.robot_ip)

    def _dispatch_telemetry(self):
            while self.socket_closed == False:
                sleep = 0.1
                try:
                    d = self.data_queue[self.telem_sock].get()
                    data = d.decode('UTF-8')
                except queue.Empty:
                    sleep = self.telemetry_sleep
                else:
                    if 'chassis' in data:
                        self._parse_chassis_data(data)
                    if 'gimbal' in data:
                        self._parse_gimbal_data(data)
                    if 'AI' in data:
                        self._parse_ai_data(data)

                if self.data_queue[self.telem_sock].empty():
                    time.sleep(sleep)

    def _parse_chassis_data(self,data):
        streams = data.split(';')
        for ss in streams:
            ss = ss.lstrip()
            ss = ss.rstrip()
            tokens = ss.split(" ")
            if 'push' in ss:
                i = 3
            else:
                i = 1
            if 'position' in ss:
                try:
                    self.chassis_x = float(tokens[i])
                    self.chassis_y = float(tokens[i+1])
                except ValueError:
                    print('Error in parsing position telemetry')
            if 'attitude' in ss:
                try:
                    self.chassis_pitch = float(tokens[i])
                    self.chassis_roll = float(tokens[i+1])
                    self.chassis_yaw = float(tokens[i+2])
                except ValueError:
                    print('Error in parsing attitude telemetry')
            if 'status' in ss:
#                print(ss)
                try:
                    self.chassis_static = True if tokens[i] == "1" else False
                    self.chassis_uphill = True if tokens[i+1] == "1" else False
                    self.chassis_downhill = True if tokens[i+2] == "1" else False
                    self.chassis_pick_up = True if tokens[i+3] == "1" else False
                    self.chassis_onslope = True if tokens[i+4] == "1" else False
                    self.chassis_slip = True if tokens[i+5] == "1" else False
                    self.chassis_impact_x = True if tokens[i+6] == "1" else False
                    self.chassis_impact_y = True if tokens[i+7] == "1" else False
                    self.chassis_impact_z = True if tokens[i+8] == "1" else False
                    self.chassis_roll_over = True if tokens[i+9] == "1" else False
                    self.chassis_hill_static = True if tokens[i+10] == "1" else False
                except ValueError:
                    print('Error in parsing attitude telemetry')
    
    def _parse_gimbal_data(self,data):
        streams = data.split(";")
        for ss in streams:
            tokens = ss.split(" ")
            if 'attitude' in ss:
                try:
                    self.gimbal_x = float(tokens[3])
                    self.gimbal_y = float(tokens[4])
                except ValueError:
                    print('Error in parsing gimbal telemetry')

    def _parse_ai_data(self,data):
        if ";" in data:
            streams = data.split(";")
            for ss in streams:
                self._put_ai_data(ss)
        else:
            self._put_ai_data(data)

    def _put_ai_data(self,data):
        dd = data.split(" ")
        s = ' '.join(dd[3:])
        if 'people' in data:
            self.people_ai_data = s
        if 'pose' in data:
            self.pose_ai_data = s
        if 'marker' in data:
            self.marker_ai_data = s
        if 'line' in data:
            self.line_ai_data = s
        if 'robot' in data:
            self.robot_ai_data = s


    def _dispatch_event(self):
        while self.socket_closed == False:
            sleep = 0.1
            try:
                d = self.data_queue[self.event_sock].get()
                data = d.decode('UTF-8')
            except queue.Empty:
                sleep = self.telemetry_sleep
            else:
                for pcb in self.cb_list:
                    pcb(data)

            if self.data_queue[self.telem_sock].empty():
                time.sleep(sleep)

    def inform(self, who):
        if who:
            if who not in self.cb_list:
                self.cb_list.append(who)

    def stop_inform(self, who):
        if who:
            if who in self.cb_list:
                self.cb_list.remove(who)

    def _process_video_mode(self, result):
        if result.lower() == 'ok':
            try:
                rm_video_addr = (self.robot_ip, self.video_port)
                result = self.video_sock.connect_ex(rm_video_addr)
                self.video_sock.setblocking(False)
                self.video_sock.settimeout(10)
                self.r_socks.append(self.video_sock)
                self.a_socks.append(self.video_sock)
                self.videothread.start()
                self.in_video_mode = True
                print('Robot %s - in video mode. %s' % (self.robot_ip, self.video_port))
            except socket.error as err:
                self.in_video_mode = False
                print('Robot %s - failed to enter video mode due to timeout. (%s)' % (self.robot_ip, err))
        else: 
            print('Robot %s - failed to enter video mode. (%s)' % (self.robot_ip, result))
    
    def _process_audio_mode(self, result):
        if result.lower() == 'ok':
            rm_audio_addr = (self.robot_ip, self.audio_port)
            self.audio_sock.connect_ex(rm_audio_addr)
            self.audio_sock.setblocking(False)
            self.audio_sock.settimeout(10)
            self.r_socks.append(self.audio_sock)
            self.a_socks.append(self.audio_sock)
            self.audiothread.start()
            self.in_audio_mode = True
            print('Robot %s - in audio mode.' % self.robot_ip)
        else: 
            print('Robot %s - failed to enter audio mode. (%s)' % (self.robot_ip, result))

    def _receive_video_data(self):
        print('Robot %s start receiving video' % self.robot_ip)
        self.video_packet_data = b''
        print('')
        while self.socket_closed == False and self.in_video_mode == True:
            try:
                data = self.data_queue[self.video_sock].get(timeout=2)
            except queue.Empty:
                print("Robot %s - video data stream queue no data" %(self.robot_ip))
            else:                
                self.video_packet_data += data            
                if len(data) != 1460:
                    for frame in self._h264_decode(self.video_packet_data):
                        try:
                            self.decoder_queue.put(frame,timeout=2)
#                            print('xx')
                        except queue.Full:
                            if self.socket_closed == True:
                                break
                            print("Robot %s - video queue full" % self.robot_ip)
                            continue
#                            self.frame = frame
                    self.video_packet_data = b''
                #except socket.error as err:
               # print('Robot %s - video error. (%s)' % (self.robot_ip, err))


    def _h264_decode(self, packet_data):
        res_frame_list = []
        frames = self.decoder.decode(packet_data)
        for framedata in frames:
            (frame, w, h, ls) = framedata
            if frame is not None:
#                print 'frame size %i bytes, w %i, h %i, linesize %i' % (len(frame), w, h, ls)
                frame = np.fromstring(frame, dtype=np.ubyte, count=len(frame), sep='')
#                frame = np.frombuffer(frame, dtype=np.ubyte, count=len(frame))
                frame = (frame.reshape((h, int(ls / 3), 3)))
                frame = frame[:, :w, :]
                res_frame_list.append(frame)
        return res_frame_list

    def _receive_audio_data(self):
        self.audio_packet_data = b''
        print('')
#        while True:
        while self.socket_closed == False and self.in_audio_mode == True:
#            try:
#                data = self.video_sock.recv(4096)
            try:
                data = self.data_queue[self.audio_sock].get(timeout=None)
#                print('')
            except queue.Empty:
                print("Robot %s - audio data stream queue no data" %(self.robot_ip))
            else:                
                self.audio_packet_data += data

                if len(self.audio_packet_data) != 0:
                    output = self.audio_decoder.decode(self.audio_packet_data)
#                    print('')
                    if output:
                        try:
                            self.audio_decoder_queue.put(output, timeout=2)
                        except queue.Full:
                            if self.socket_closed == True:
                                break
                            print("Robot %s - audio queue full" % self.robot_ip)
                            continue
                    self.audio_packet_data = b''

    #return None means no audio or robot not in audio mode else return byte array.
    def getaudioframe(self):
        if self.in_audio_mode:
            try:
                self.audioframe = self.audio_decoder_queue.get(timeout=2)
            except queue.Empty:
                if self.socket_closed:
                    print("Robot %s - socket closed" % self.robot_ip)
#                print("Robot %s - audio queue empty.(readaudioframe)" % self.robot_ip)
                return None
            else:
                return self.audioframe
        else:
            return None
#            print("Robot %s is not in audio mode.")                    


    def _process_socks(self):
        data =[]
#        while True:
        while self.socket_closed == False:
            try:
                readable, writable, exceptional = select.select(self.r_socks,self.w_socks,self.a_socks)
            except Exception:
                readable = []
                writable = []
                exceptional = []

            for r in readable:
                if r is self.command_sock:
#                    print("command port")
                    decode_error = False
                    try:
                        cdata,address = self.command_sock.recvfrom(4096)
                        d_full = cdata.decode('UTF-8')
#                        print("received from %s- %s : %s" % (address,self.last_cmd,cdata))
                        seq_num = self._get_seq_number_from_response_with_seq(d_full)
                        d = d_full
                        if seq_num > -1:
                            d = self._get_result_from_response_with_seq(d_full)

                    except socket.error as err:
                        print('Robot %s - recevie data failed. (%s)' % (self.robot_ip, err))
                        self.socket_error = True
                    except UnicodeDecodeError as err:
                        decode_error = True

                    if decode_error == False:
                        if self.in_command_mode == False:
                            self._process_going_into_command(d)
                        if self.last_cmd == 'stream on':
                            self._process_video_mode(d)
                        if self.last_cmd == 'audio on':
                            self._process_audio_mode(d)
                        self.response = d
                    self.in_action = False
                    self.last_cmd = None
                else:
                    if r is self.video_sock:
#                        print('v')
                        vdata,address = self.video_sock.recvfrom(4096)
                        if self.data_queue[self.video_sock].full():
                            self.data_queue[self.video_sock].get()
                        self.data_queue[self.video_sock].put(vdata)
                    else:
                        if r is self.audio_sock:
#                            print('a')            
                            adata,address = self.audio_sock.recvfrom(4096)
                            if self.data_queue[self.audio_sock].full():
                                self.data_queue[self.audio_sock].get()
                            self.data_queue[self.audio_sock].put(adata)
                        else:
                            if r is self.event_sock:
                                edata,address = self.event_sock.recvfrom(4096)
                                if self.data_queue[self.event_sock].full():
                                    self.data_queue[self.event_sock].get()
                                self.data_queue[self.event_sock].put(edata)
                            else:
                                if r is self.telem_sock and self.telemetry:
                                    tdata,address = self.telem_sock.recvfrom(4096)
                                    self.data_queue[self.telem_sock].put(tdata)
                                  
        
            for w in writable:
                try:
                    if self.message_q.empty() == False and w is self.command_sock:
#                        if (self.response != '' and self.last_cmd is None) or self.in_command_mode == False:
                        if self.in_action == False or self.in_command_mode == False:
                            msg_to_send = self.message_q.get_nowait()
                            self._cmdseq = (self._cmdseq + 1) % 100 
                            msg_to_send_with_seq = msg_to_send + ' seq ' + str(self._cmdseq) + ';'
                            self.command_sock.send(msg_to_send_with_seq.encode('UTF-8'))
                            print('Robot %s send %s' % (self.robot_ip, msg_to_send_with_seq))
                            self.last_cmd = msg_to_send
                            self.response = ''
                            self.cmd_start_time = time.time()
                            self.in_action = True
                            if self.last_cmd == 'command' and self.in_command_mode == False:
                                self.connecting = True
                        else:
#                            if self.response == '' and self.in_command_mode and self.last_cmd:
                            if self.in_action and self.in_command_mode:
                                if (time.time() - self.cmd_start_time) > self.cmd_timeout:
                                    print("Robot %s response to last command (%s) timeout. Proceed with next command." % (self.robot_ip, self.last_cmd))
                                    msg_to_send = self.message_q.get_nowait()
                                    self._cmdseq = (self._cmdseq + 1) % 100 
                                    msg_to_send_with_seq = msg_to_send + ' seq ' + str(self._cmdseq)
                                    self.command_sock.send(msg_to_send_with_seq.encode('UTF-8'))
                                    print('Robot %s send %s' % (self.robot_ip, msg_to_send_with_seq))
                                    self.last_cmd = msg_to_send
                                    self.response = ''
                                    self.cmd_start_time = time.time()
                                    self.in_action = True
                    else:
                        if self.message_q.empty() and w is self.command_sock and self.connecting:
                            if(time.time() - self.cmd_start_time) > self.cmd_timeout:
                                self.connecting_timeout = True

                except socket.error as err:
                    print('Robot %s - send command (%s) failed. (%s)' % (self.robot_ip, msg_to_send, err))
                    self.socket_error = True
                   
            for e in exceptional:
                print ("handling exceptional")
                if e is self.command_sock:
                    self.w_socks.remove(e)
                    self.r_socks.remove(e)
                    self.a_socks.remove(e)
                    e.close()
                    print("error in command port.")
                    
                if e is self.video_sock:
                    self.r_socks.remove(e)
                    self.a_socks.remove(e)
                    e.close()
                    print("error in video port")

                if e is self.audio_sock:
                    self.r_socks.remove(e)
                    self.a_socks.remove(e)
                    e.close()
                    print("error in audio port")



def testattitudepush(data):
    print(data)

def testpositionpush(data):
    print('position')
    print(data)

def teststatuspush(data):
    print('status')
    print(data)

if __name__ == '__main__':
    try:

        r = Robomaster()

        if r.start_sdk_session('192.168.2.1') == 1: # connect function returns true when connected. otherwise
            r.instruct('chassis push attitude on status on position on')
            time.sleep(1)
            print(r.instruct('sound event applause on'))
            r.inform(testattitudepush)
            print(r.instruct('armor event hit on'))
            print(r.instruct('sensor_adapter event io_level on'))
            print(r.instruct('gimbal push attitude on'))
            time.sleep(1)
            r.instruct('gimbal moveto p 20 y 50 vp 100 vy 100')
            time.sleep(2)
            print(r.gimbal_x)
            print(r.gimbal_y)
            print(r.instruct('chassis position ?'))
            time.sleep(1)
            print(r.instruct('chassis wheel w1 0 w2 0 w3 0 w4 0'))
            time.sleep(1)
            i = 0
            while i < 100:
                i = i + 1
                time.sleep(0.1)

            print(r.instruct('chassis wheel w9 20 w2 20 w3 30 w5 40'))
            time.sleep(1)

        else:
            print('false')
        
#        r.av_off()
        r.quit_sdk_session()

    except KeyboardInterrupt:
        sys.exit(0)
