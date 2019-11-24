from socket import *
import time
import threading
import json
import pickle
import math
import change_node as change_node
import time
import numpy as np
from multiprocessing import Process
import eventlet#导入eventlet这个模块
eventlet.monkey_patch()#超时退出

BUFSIZ = 1024

class node:

    def __init__(self, idx):

        self.port_basis = 9000
        self.my_port = self.port_basis+idx

        self.if_start_up = True
        self.master = True
        self.timeslot = None
        self.master_ID = None
        self.F = None
        self.timeslot_available = np.arange(1,8)
        # 读取拓扑，获取每个点的坐标
        self.x_list, self.y_list, self.node_num = self.get_topology()


        # 存储已经收到的报文，src——address
        self.received_src = []
        # 记录id，第几次路由
        self.idx=0

        recv_socket = socket(AF_INET, SOCK_DGRAM)
        recv_socket.bind(('127.0.0.1', self.my_port))
        self.recv_socket = recv_socket

    # 向某个节点发送报文信息
    def send(self, msg, to_port):
        self.recv_socket.sendto(msg.encode('utf-8'), ('127.0.0.1', to_port))
        # print("---Send:","----Port:",str(to_port), msg)

    def broadcast(self, msg):
        # 查看拓扑
        self.x_list, self.y_list, self.node_num = self.get_topology()

        # 本节点的index
        index = self.my_port-self.port_basis-1

        for i in range(self.node_num):
            if i!=index:
                # 广播，距离N=5以内的节点均可以广播到
                if math.sqrt(math.pow((self.x_list[i]-self.x_list[index]),2)+math.pow((self.y_list[i]-self.y_list[index]),2))<5:
                    self.send(msg, i+self.port_basis+1)

    def get_topology(self):
        # 从文件读取拓扑
        pkl_file = open('ylist.pkl', 'rb')
        y_list = pickle.load(pkl_file)
        pkl_file.close()

        pkl_file = open('xlist.pkl', 'rb')
        x_list = pickle.load(pkl_file)
        pkl_file.close()
        # 端口数目
        node_num = len(x_list)
        # 根据端口数目设置所有端口
        self.allport = []
        for i in range(node_num):
            port_temp = i + 1 + self.port_basis
            self.allport.append(port_temp)
        return x_list, y_list, node_num

    def fast_send(self):
        print("Start Fast Sending .--------------")
        F = np.random.randint(low=10, high=1000)
        with eventlet.Timeout(20, False):  # 设置超时时间为20秒
            while True:
                time.sleep(0.2)
                print("fast_sending...")
                msg = write_json(des_address="", src_address=self.my_port, content="", master_ID=self.my_port, F=F,
                               flag="FAST_SEND")
                self.broadcast(msg)
    def broadcast_HELLO(self):
        print("Start broadcast HELLO in period")
        while True:
            time.sleep(1)
            msg = write_json(des_address="", src_address=self.my_port, content="", master_ID=self.master_ID, F=self.F,
                             flag="HELLO")
            print("broadcasting HELLO")
            self.broadcast(msg)

    def run(self):
        p_fast_send = Process(target=self.fast_send)
        p_HELLO = Process(target=self.broadcast_HELLO)
        while True:
            # 如果刚开机
            if self.if_start_up:
                self.if_start_up = False
                print("开机，开始持续5s的监听")
                # 扫频慢收。5秒没有响应，则开始快发
                self.recv_socket.settimeout(5)
                try:
                    while True:
                        data, address = self.recv_socket.recvfrom(BUFSIZ)
                        des_address, src_address, content, master_ID, F, flag = parse_json(data.decode('utf-8'))
                        print(flag)
                        # 如果收到了”快发“或者心跳信息，申请入网
                        if flag == "FAST_SEND" or flag == "HELLO":
                            print("Receive %s from address %d" % (flag, src_address))
                            # 向master申请入网
                            msg = write_json(des_address=master_ID, src_address=self.my_port,
                                             content="", master_ID="", F=F, flag="APPLY")
                            print("APPLY to master:", master_ID)
                            self.broadcast(msg)
                            # 等待确认消息
                            while True:
                                data, address = self.recv_socket.recvfrom(BUFSIZ)
                                des_address, src_address, content, master_ID, F, flag = parse_json(
                                    data.decode('utf-8'))
                                if flag == "ACK" and des_address == self.my_port:
                                    print("Receive ACK from %d, connected to this master" % src_address)
                                    self.master = False
                                    self.timeslot = content
                                    self.master_ID = master_ID
                                    self.F = F
                                    print("%d连接至子网，时隙%d：，中心节点%d：，频率%d："%(self.my_port, self.timeslot,
                                                                         self.master_ID, self.F))
                                    break
                            recv_response = True
                            self.recv_socket.settimeout(None)
                            break
                except timeout:
                    print("没有监听到周围节点")
                    recv_response = False
                # 快发
                if not recv_response:
                    print("没有监听到周围节点，开始持续20s的快发")
                    self.recv_socket.settimeout(20)
                    # 开启新进程，开始快发
                    p_fast_send.start()
                    # 20s没有人响应，则关机
                    try:
                        while True:
                            data, address = self.recv_socket.recvfrom(BUFSIZ)
                            des_address, src_address, content, master_ID, F, flag = parse_json(data.decode('utf-8'))
                            # 收到申请
                            if flag == "APPLY" and des_address == self.my_port:
                                print("Receive APPLY from ", src_address)
                                p_fast_send.terminate()
                                # 发送ACK，分配时隙，自己作为master
                                self.master = True
                                # 分配自己的时隙
                                self.timeslot = self.timeslot_available[0]
                                # 更新可用时隙
                                self.timeslot_available = np.delete(self.timeslot_available, 0)
                                self.master_ID = self.my_port
                                self.F = F
                                # 分配申请入网节点的时隙
                                content = self.timeslot_available[0]
                                self.timeslot_available = np.delete(self.timeslot_available, 0)

                                to_port = src_address
                                msg = write_json(des_address=to_port, src_address=self.my_port,
                                                 content=content, master_ID=self.my_port, F=F, flag="ACK")
                                print("Send ACK back")
                                self.broadcast(msg)
                                self.recv_socket.settimeout(None)
                                break
                    except timeout:
                        print("20秒内没有收到申请入网消息，关机")
                        p_fast_send.terminate()
                        self.recv_socket.close()
                        return 0

            # 开始广播HELLO心跳信息
            if not p_HELLO.is_alive():
                print("开始定时广播")
                p_HELLO.start()
            # 正常运行模式，持续扫频慢收监听
            data, address = self.recv_socket.recvfrom(BUFSIZ)
            des_address, src_address, content, master_ID, F, flag = parse_json(data.decode('utf-8'))
            # 中心节点在运行过程中收到刚开机节点的入网申请
            if self.master:
                # 收到申请入网消息
                if flag == "APPLY" and des_address == self.my_port:
                    if self.timeslot_available.size > 0:
                        to_port = src_address
                        # 分配时隙
                        content = self.timeslot_available[0]
                        self.timeslot_available = np.delete(self.timeslot_available, 0)
                        msg = write_json(des_address=to_port, src_address=self.my_port,
                                         content=content, master_ID=self.my_port, F=self.F, flag="ACK")
                        print("send back ACK to:", to_port)
                        self.broadcast(msg)

            # 如果收到了
            # if flag is "HELLO" and F is not self.F:
        self.recv_socket.close()

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)

# 打包报文数据，形成json格式报文
def write_json(des_address, src_address, content, master_ID, F, flag):
    python2json = {}
    # route_list = [1, 2, 3]
    python2json["content"] = content
    python2json["src_address"] = src_address
    python2json["des_address"] = des_address
    python2json["flag"] = flag
    python2json["master_ID"] = master_ID
    python2json["F"] = F
    json_str = json.dumps(python2json, cls=NpEncoder)
    return json_str

def parse_json(json_str):
    json2python = json.loads(json_str)
    return json2python['des_address'], json2python['src_address'], json2python['content'],\
           json2python['master_ID'], json2python['F'], json2python['flag']

c = node(4)
c.run()