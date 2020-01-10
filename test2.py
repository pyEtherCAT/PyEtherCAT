# import gevent.monkey
# gevent.monkey.patch_socket()
from pyEtherCAT import MasterEtherCAT
import time
import os
import psutil


#============================================================================#
# C95用の簡易EtherCATパッケージです。
# 本来は細かいパケットに付いて理解を深めた上で仕組みを構築していきますが、
# 説明も実験も追いつかず、ひとまずGPIOで高速にON/OFF出来る部分だけを纏めました。
# 動作は Linux(RaspberryPi含む) にて Python3　で動作します。
# sudo python3 test03.py
#============================================================================#
# ここから簡易ライブラリ
#============================================================================#
def EtherCAT_Init(nic):
    cat = MasterEtherCAT.MasterEtherCAT(nic)  # ネットワークカードのアドレスを記載
    return cat

def EtherCAT_SetUp(cat,ADP):
    cat.EEPROM_SetUp(ADP)  # EEPROMの設定、特に変更不要
    cat.EEPROM_Stasus(enable=0x00, command=0x04)  # EEPROMの設定、特に変更不要
    ADDR = 0x0120  # AL 制御レジスタ
    data = 0x0002  # 2h: 動作前ステートを要求する
    cat.APWR(IDX=0x00, ADP=ADP, ADO=ADDR, DATA=[
             data & 0xFF, (data >> 8) & 0xFF])
    (DATA, WKC) = cat.socket_read()
    #print("[0x{:04x}]= 0x{:04x}".format(ADDR, DATA[0] | DATA[1] << 8))
    ADDR = 0x0120  # AL 制御レジスタ
    data = 0x0002  # 2h: 動作前ステートを要求する
    cat.APWR(IDX=0x00, ADP=ADP, ADO=ADDR, DATA=[
             data & 0xFF, (data >> 8) & 0xFF])
    (DATA, WKC) = cat.socket_read()
    #print("[0x{:04x}]= 0x{:04x}".format(ADDR, DATA[0] | DATA[1] << 8))
    ADDR = 0x0120  # AL 制御レジスタ
    data = 0x0004  # 4h: 安全動作ステートを要求する
    cat.APWR(IDX=0x00, ADP=ADP, ADO=ADDR, DATA=[
             data & 0xFF, (data >> 8) & 0xFF])
    (DATA, WKC) = cat.socket_read()
    #print("[0x{:04x}]= 0x{:04x}".format(ADDR, DATA[0] | DATA[1] << 8))
    ADDR = 0x0120  # AL 制御レジスタ
    data = 0x0008  # 8h: 動作ステートを要求する
    cat.APWR(IDX=0x00, ADP=ADP, ADO=ADDR, DATA=[
             data & 0xFF, (data >> 8) & 0xFF])
    (DATA, WKC) = cat.socket_read()
    #print("[0x{:04x}]= 0x{:04x}".format(ADDR, DATA[0] | DATA[1] << 8))


def EtherCAT_GPIOMode(cat,ADP, data):
    ADDR = 0x0F00  # デジタル I/O 出力データレジスタ
    cat.APWR(IDX=0x00, ADP=ADP, ADO=ADDR, DATA=[data & 0xFF, (data >> 8) & 0xFF])
    (DATA, WKC) = cat.socket_read()
    #print("[0x{:04x}]= 0x{:04x}".format(ADDR, DATA[0] | DATA[1] << 8))

    #ADDR = 0x1000
    #cat.APWR(IDX=0x00, ADP=cat.ADP, ADO=ADDR, DATA=[ (~data & 0xFF), ((~data >> 8) & 0xFF) ])
    #(DATA,WKC) = cat.socket_read()
    #print("[0x{:04x}]= 0x{:04x}".format(ADDR, DATA[0] | DATA[1] << 8))

def EtherCAT_CHIP_ID(cat,ADP):
    ADDR = 0x0E00
    cat.APRD(IDX=0x00, ADP=ADP, ADO=ADDR, DATA=[0x00,0x00,0x00,0x00])
    (DATA,WKC) = cat.socket_read()
    print("[0x{:04x}]= 0x{:04x}".format(ADDR, DATA[2] | DATA[3] << 8))

def EtherCAT_GPIO_Out(cat,ADP, data):
    ADDR = 0x0F10
    cat.APWR(IDX=0x00, ADP=ADP, ADO=ADDR, DATA=[data & 0xFF, (data >> 8) & 0xFF])
    (DATA,WKC) = cat.socket_read()
    #print("{:x} : [0x{:04x}]= 0x{:04x}".format(ADP,ADDR, DATA[0] | DATA[1] << 8))
def EtherCAT_GPIO_In(cat):
    ADDR = 0x0F18
    cat.APRD(IDX=0x00, ADP=ADP, ADO=ADDR, DATA=[0x00,0x00])
    (DATA,WKC) = cat.socket_read()
    #print("[0x{:04x}]= 0x{:04x}".format(ADDR, DATA[0] | DATA[1] << 8))


#============================================================================#
# ここまで　簡易ライブラリ
#============================================================================#

def RUN1(lock):
    ADP = 0x0000 - 0
    #-- EtherCATのステートマシンを実行に移す処理
    lock.acquire()
    EtherCAT_SetUp(cat,ADP)         # EtherCATスレーブの初期設定
    EtherCAT_GPIOMode(cat,ADP, 0xFFFF)         # EtherCATスレーブのGPIO方向設定　1:出力
    lock.release()
    while 1:
        lock.acquire()
        EtherCAT_GPIO_Out(cat,ADP,0xFFFF)
        lock.release()
        #time.sleep(1)
        lock.acquire()
        EtherCAT_GPIO_Out(cat,ADP,0x0000)
        lock.release()
        #time.sleep(1)

def RUN2(lock):
    #-- EtherCATのステートマシンを実行に移す処理
    ADP = 0x0000 - 1  # 例　これは2台目　繋がってなければ必要ない
    lock.acquire()
    EtherCAT_SetUp(cat,ADP)         # EtherCATスレーブの初期設定
    EtherCAT_GPIOMode(cat,ADP, 0xFFFF)         # EtherCATスレーブのGPIO方向設定　0:入力 1:出力
    lock.release()

    while 1:
        for i in range(16):
            lock.acquire()
            EtherCAT_GPIO_Out(cat,ADP,0x0001<<i)
            lock.release()
            #time.sleep(0.0001)
        for i in range(16):
            lock.acquire()
            EtherCAT_GPIO_Out(cat,ADP,0x8000>>i)
            lock.release()
            #time.sleep(0.0001)
    # -- 1台目のLEDをシフトする
    TIME = 0.1

def RUN3(lock):
    #-- EtherCATのステートマシンを実行に移す処理
    ADP = 0x0000 - 2  # 例　これは2台目　繋がってなければ必要ない
    lock.acquire()
    EtherCAT_SetUp(cat,ADP)         # EtherCATスレーブの初期設定
    EtherCAT_GPIOMode(cat,ADP, 0xFFFF)         # EtherCATスレーブのGPIO方向設定　0:入力 1:出力
    lock.release()

    while 1:
        for i in range(0xFFFF):
            lock.acquire()
            EtherCAT_GPIO_Out(cat,ADP,i)
            lock.release()
        # -- 1台目のLEDをシフトする

import threading
if __name__ == "__main__":
    cat = EtherCAT_Init("eth0")    # EtherCATのネットワーク初期設定
    lock = threading.Lock()
    thread_1 = threading.Thread(target=RUN1,args=(lock,))
    thread_1.setDaemon(True)
    thread_1.start()
    thread_2 = threading.Thread(target=RUN2,args=(lock,))
    thread_2.setDaemon(True)
    thread_2.start()
    thread_3 = threading.Thread(target=RUN3,args=(lock,))
    thread_3.setDaemon(True)
    thread_3.start()
    while 1 : pass
