# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 13:42:47 2021

@author: rltjr
"""

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow
from threading import Thread
from time import sleep

# SL GUI Form
form_SL = uic.loadUiType("gui/form_SL.ui")[0]

# SL GUI Class
class SLClass(QMainWindow, form_SL) :
    def __init__(self,listen,data) :
        super().__init__()
        self.data = data      # Shared Data
        self.listen = listen  # Listening Data
        self.class_value = {} # Involving the All of the Class which i made
        self.setupUi(self)
        self.SL_Start.clicked.connect(self.Start)
        self.SL_Stop.clicked.connect(self.End)
    def Move(self,position):
        sleep(0.01)
        if self.data["stop"] == True:
                return
        Now_position = self.listen['stepper']['X'] % self.data['Microstep']
        Move_position = position*(self.data['Microstep']/4)-Now_position
        if Move_position < 0 :
            Move_position = Move_position + self.data['Microstep']
        self.class_value['SERVER_tcp'].send('stepper%'+'m'+str(int(Move_position)))
        self.data["STATE"].append("Move to "+str(position+1))
        while True:
            if self.data["stop"]:
                break
            if (self.listen['stepper']['X'] % self.data['Microstep']) == position*(self.data['Microstep']/4):
                self.data["STATE"].append("Position "+str(position+1))
                break
            sleep(0.1)
        sleep(0.1)
    def Sweep(self,mode,N_sweep=0):
        if self.data["stop"]:
                return
        if mode == 1: # ON
            self.class_value['SERVER_tcp'].send('stepper%'+'r'+str(N_sweep))
            while True:
                if self.data["stop"] == True:
                    break
                if self.listen['stepper']['stop'] == False:
                    break
                sleep(0.01)
        elif mode == 0: # OFF
            self.class_value['SERVER_tcp'].send('stepper%Stop')
            sleep(0.1)
            while True:
                if self.data["stop"] == True:
                    break
                if self.listen['stepper']['stop'] == True:
                    break
                else:   # if stoping do not work
                    self.class_value['SERVER_tcp'].send('stepper%Stop')
                    sleep(0.1)
                sleep(0.01)
    def Laser_Shot(self,mode):
        if self.data["stop"] == True:
                return
        if mode == 1:
            while True:
                self.data["LASER"] = ""
                self.class_value['LASER_tcp'].send("shot")
                sleep(0.5)
                if self.listen['laser']["state"] == 1:
                    self.data["STATE"].append("LASER Start")
                    sleep(0.5)
                    break
                else:
                    print("Checking the LASER Starting")
            while True:
                if self.data["stop"] == True:
                    break
                if self.listen['laser']["state"] == 0:
                    self.data["STATE"].append("LASER End")
                    break
                sleep(0.1)
        elif mode ==0:
            self.class_value['LASER_tcp'].send("stop")
    def Laser_Setting(self,mode,value):
        if self.data["stop"] == True:
                return
        if mode == 'count':
            while True:
                self.data["LASER"] = ""
                self.class_value['LASER_tcp'].send("c"+str(value))
                sleep(0.2)
                if self.listen['laser']["count"] == str(value):
                    self.data["STATE"].append("LASER count: "+str(value))
                    break
                else:
                    print("Checking the LASER Count Setting")
        elif mode == 'reprate':
            while True:
                self.data["LASER"] = ""
                self.class_value['LASER_tcp'].send("r"+str(value))
                sleep(0.2)
                if self.listen['laser']["reprate"] == str(value):
                    self.data["STATE"].append("LASER reprate: "+str(value))
                    break
                else:
                    print("Checking the LASER reprate Setting")
        elif mode == 'mode':
            self.class_value['LASER_tcp'].send("m"+str(value))
            self.data["STATE"].append("LASER mode: "+str(value))
        sleep(0.05)
    def repeat(self):
        count = 1
        for i in range(self.Repeat.value()):
            if self.data["stop"] == True:
                    break
            self.Repeat_str.setText(str(count))
            self.data["STATE"].append("-Periodic "+str(count)+" Start-")
            count = count + 1
            self.Move(self.T1_position.value()-1)
            if self.T1_sweep_On.isChecked():
                self.Sweep(True,self.T1_sweep.value())
            self.Laser_Setting('count',self.T1_shot.value())
            self.Laser_Setting('reprate',self.T1_reprate.value())
            self.Laser_Shot(True)
            self.Sweep(False)
            self.Move(self.T2_position.value()-1)
            if self.T1_sweep_On.isChecked():
                self.Sweep(True,self.T2_sweep.value())
            self.Laser_Setting('count',self.T2_shot.value())
            self.Laser_Setting('reprate',self.T2_reprate.value())
            self.Laser_Shot(True)
            self.data["STATE"].append("-Periodic "+str(count-1)+" End-")
            self.Sweep(False)
        count = count + 1
        self.End(True)
    def Start(self):
        self.data["stop"] = False
        self.th_s = Thread(target=self.repeat)
        self.th_s.start()
    def End(self,mode=0):
        self.data["stop"] = True
        if mode ==0:
            self.class_value['SERVER_tcp'].send('stepper%Stop')
            self.class_value['LASER_tcp'].send("stop")
        self.class_value['window'].stepper_control_box.setEnabled(True)
        self.class_value['window'].stepper_box.setEnabled(True)
        self.class_value['window'].laser_control_box.setEnabled(True)
        self.class_value['window'].temp_control_box.setEnabled(True)