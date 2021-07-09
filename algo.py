import csv
from typing import List
import numpy as np
import datetime

a_limit = 24520
b_limit = 24600
vehicle = dict()
with open('vehicle.csv') as csvf:
    reader = csv.reader(csvf, delimiter=',')
    header = True
    for row in reader:
        if header:
            header = False
            continue
        _, code, length, _, height = row
        vehicle[code] = (int(length), int(height))

class Car:
    def __init__(self, vin, t, code, plant, dda=None) -> None:
        self.vin = vin
        self.t = t
        self.code = code
        self.plant = plant
        self.dda = dda
        self.length, self.height = vehicle[code]

btime = datetime.datetime.strptime('2021-08-01 00:00:00', '%Y-%m-%d %H:%M:%S')
dda_to_int = {'CD':0, 'XA':1, 'ZZ':2}
int_to_dda = ['CD', 'XA', 'ZZ']
int_to_seat = ['A1', 'A2', 'A3', 'A4', 'A5', 'B1', 'B2', 'B3', 'B4', 'B5']
cars = []
cars_dda = [[], [], []]
ts = []
with open('schedule.csv') as csvf:
    reader = csv.reader(csvf, delimiter=',')
    for row in reader:
        vin, t, code, plant, dda = row
        t = (datetime.datetime.strptime(t, '%Y-%m-%d %H:%M:%S') - btime).total_seconds()
        ts.append(t)
        cars.append(Car(vin, t, code, plant, dda))
        cars_dda[dda_to_int[dda]].append(Car(vin, t, code, plant)) 
     
total_length = len(ts)            
class Wagon:
    def __init__(self) -> None:
        self.idx = None
        self.loads = [None for _ in range(10)] # In order A1-A5 B1-B5, 5 for B1, 9 for B5
        self.al = self.bl = 0
        
    def full(self) -> bool:
        return all(self.loads)
    
    def empty(self) -> bool:
        return not any(self.loads)
    
    def available_seats(self) -> list:
        l = []
        for i in range(10):
            if self.loads[i] is None:
                l.append(i)
        return l

    def insert_DD(self, car): # 2xG38+3xG08 in A, 3xG38+2xG08 in B
        code = car.code
        loc = None
        G38locs = [0,1,5,6,9]
        G08locs = [2,3,4,7,8]
        if self.full():
            return loc
        if code in ['G38']:
            for x in G38locs:
                if self.loads[x] is None:
                    loc = x
                    break
        if code in ['G08']:
            for x in G08locs:
                if self.loads[x] is None:
                    loc = x
                    break
        if loc is not None:
            if loc in range(0,5):
                valid = (car.length <= a_limit - self.al)
            else:
                valid = (car.length <= b_limit - self.bl)
            if valid:
                self.loads[loc] = car
                if loc in range(0,5):
                    self.al += car.length
                else:
                    self.bl += car.length
            else:
                loc = None
        return loc        
                    
    def insert_TX(self, car): 
        code = car.code
        loc = None
        if self.full():
            return loc
        if code in ['F52', 'G20', 'G28', 'G38']:
            if self.loads[5] is None:
                loc = 5
            if self.loads[9] is None:
                loc = 9
            else:
                for i in range(10):
                    if self.loads[i] is None:
                        loc = i
                        break
        else:
            for i in range(10):
                if self.loads[i] is None and i not in [5,9]:
                    loc = i
                    break
        if loc is not None:
            if loc in range(0,5):
                valid = (car.length <= a_limit - self.al)
            else:
                valid = (car.length <= b_limit - self.bl)
            if valid:
                self.loads[loc] = car
                if loc in range(0,5):
                    self.al += car.length
                else:
                    self.bl += car.length
            else:
                loc = None
        return loc
    
    def latest_time(self):
        assert not self.empty()
        t = 0
        for i in range(10):
            if self.loads[i] is not None:
                if self.loads[i].t > t:
                    t = self.loads[i].t
        return t
         
total_wagon_tx = []
total_wagon_dd = []
for d in range(3):      
    wagon_tx = []
    lawtx = -1
    wagon_dd = []
    lawdd = -1
    for i in range(len(cars_dda[d])):
        if cars_dda[d][i].plant == "TX":
            if len(wagon_tx) == (lawtx+1):
                wagon_tx.append(Wagon())
                wagon_tx[-1].insert_TX(cars_dda[d][i])
            else:
                for j in range(lawtx+1, len(wagon_tx)):
                    ret = wagon_tx[j].insert_TX(cars_dda[d][i])
                    if ret is not None:
                        if wagon_tx[j].full():
                            lawtx += 1
                        break
                if ret is None:
                    wagon_dd.append(Wagon())
                    wagon_dd[-1].insert_TX(cars_dda[d][i]) 
        if cars_dda[d][i].plant == "DD":
            if len(wagon_dd) == (lawdd+1):
                wagon_dd.append(Wagon())
                wagon_dd[-1].insert_DD(cars_dda[d][i])
            else:
                for j in range(lawdd+1, len(wagon_dd)):
                    ret = wagon_dd[j].insert_DD(cars_dda[d][i])
                    if ret is not None:
                        if wagon_dd[j].full():
                            lawdd += 1
                        break
                if ret is None:
                    wagon_dd.append(Wagon())
                    wagon_dd[-1].insert_DD(cars_dda[d][i]) 
    total_wagon_dd.append(wagon_dd)
    total_wagon_tx.append(wagon_tx)               

total_sorted_wagon_tx = []
total_sorted_wagon_dd = []
for d in range(3):
    tx = []
    dd = []
    for item in total_wagon_tx[d]:
        if item.full():
            tx.append((item.latest_time(), item))
    sorted_tx = sorted(tx, key=lambda x: x[0])
    total_sorted_wagon_tx.append(sorted_tx)
    for item in total_wagon_dd[d]:
        if item.full():
            dd.append((item.latest_time(), item))
    sorted_dd = sorted(dd, key=lambda x: x[0])
    total_sorted_wagon_dd.append(sorted_dd)

train_time_table = []
car_loading_table = []
tr_ind = 0
for d in range(3):
    wagon_tx = total_sorted_wagon_tx[d]
    wagon_dd = total_sorted_wagon_dd[d]
    h_tx = t_tx = h_dd = t_dd = 0
    while(True):
        if (t_tx >= len(wagon_tx)) or (t_dd >= len(wagon_dd)):
            for i in range(h_tx, t_tx):
                for p in range(10):
                    curr_car = wagon_tx[i][1].loads[p]
                    if curr_car is not None:
                        car_loading_table.append((curr_car.vin, "WAIT", "None", "None", "None"))
            for i in range(h_dd, t_dd):
                for p in range(10):
                    curr_car = wagon_dd[i][1].loads[p]
                    if curr_car is not None:
                        car_loading_table.append((curr_car.vin, "WAIT", "None", "None", "None"))                        
            break
        if wagon_tx[t_tx][0] < wagon_dd[t_dd][0]:
            t_tx += 1
        else:
            t_dd += 1
        if t_tx - h_tx + t_dd - h_dd == 29:
            tr_ind_str = "TR{}".format(tr_ind)
            for i in range(h_tx, t_tx):
                for p in range(10):
                    curr_car = wagon_tx[i][1].loads[p]
                    car_loading_table.append((curr_car.vin, tr_ind_str, "T{}".format(i), int_to_seat[p], "None"))
            for i in range(h_dd, t_dd):
                for p in range(10):
                    curr_car = wagon_dd[i][1].loads[p]
                    car_loading_table.append((curr_car.vin, tr_ind_str, "D{}".format(i), int_to_seat[p], "None"))
            tr_ind_str = "TR{}".format(tr_ind)
            wagon_t_tx = btime + datetime.timedelta(seconds=wagon_tx[t_tx][0])
            wagon_t_tx_str = wagon_t_tx.strftime('%Y-%m-%d %H:%M:%S')
            wagon_t_dd = btime + datetime.timedelta(seconds=wagon_dd[t_dd][0])
            wagon_t_dd_str = wagon_t_dd.strftime('%Y-%m-%d %H:%M:%S')
            train_time_table.append((tr_ind_str, t_tx - h_tx, t_dd - h_dd, int_to_dda[d], wagon_t_tx_str, wagon_t_dd_str))
            h_tx = t_tx
            h_dd = t_dd
            tr_ind += 1
        
with open('trains.csv', 'w') as csvf:
    writer = csv.writer(csvf, delimiter=',')
    writer.writerow(('TrainID', 'TX_Wagon', 'DD_Wagon', 'DDA', 'TX_Time', 'DD_Time'))
    for item in train_time_table:
        writer.writerow(item)
with open('trunks.csv', 'w') as csvf:
    writer = csv.writer(csvf, delimiter=',')
    writer.writerow(('TrunkID', 'From', 'To', 'Time'))
with open('vehicles.csv', 'w') as csvf:
    writer = csv.writer(csvf, delimiter=',')
    writer.writerow(('VIN', 'TrainID', 'Cabin', 'Seat', 'Transit'))
    for item in car_loading_table:
        writer.writerow(item)
print("Bravo!")