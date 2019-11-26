import shlex
import subprocess
import matplotlib.pyplot as plt

import threading
from multiprocessing import Process

import pickle

def get_topology():
    # 从文件读取拓扑
    pkl_file = open(config.y, 'rb')
    y_list = pickle.load(pkl_file)
    pkl_file.close()

    pkl_file = open(config.x, 'rb')
    x_list = pickle.load(pkl_file)
    pkl_file.close()
    # 端口数目
    node_num = len(x_list)
    # 根据端口数目设置所有端口

    return x_list, y_list, node_num

if __name__ == '__main__':
    x_list = None
    seq = ""
    # shell_cmd = 'python3 simulate_batch.py --example=1'
    shell_cmd = 'python3 simulate_batch.py --num=20'
    cmd = shlex.split(shell_cmd)
    p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    flag = "Receive APPLY from"
    lines = []
    rep_lines=set([])
    while p.poll() is None:
        line = p.stdout.readline().decode()
        line = line.strip()
        if line:
            if 'HELLO' in line:
                if line not in rep_lines:
                    rep_lines.add(line)
                    print(line)
            else:
                print(line)
            if 'SEQ:' in line:
                seq = line
            if 'Topology generated' in line:
                if x_list is None:
                    import config
                    print(config.x)
                    x_list, y_list, node_num = get_topology()
            if flag in line:
                idx = line.find(flag)
                master = int(line[idx - 5:idx - 1])
                children = int(line[idx + 19:idx + 23])
                if (master, children) not in lines:
                    lines.append((master, children))
                    master = master - 9001
                    children = children - 9001

                    plt.scatter(x_list[master], y_list[master], marker="s", s=80, c="b")
                    plt.scatter(x_list[children], y_list[children], marker="o", c="r")
                    plt.plot([x_list[master], x_list[children]], [y_list[master], y_list[children]], c="b")
                    plt.text(x_list[master] + 0.05, y_list[master] + 0.05, str(master + 1))
                    plt.text(x_list[children] + 0.05, y_list[children] + 0.05, str(children + 1))
                    plt.title(str(seq))
                    plt.xlim((0,10))
                    plt.ylim((0,0.5))
                    plt.pause(0.01)  # 暂停一秒


    if p.returncode == 0:
        print('Subprogram success')
    else:
        print('Subprogram failed')