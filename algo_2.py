import csv
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
    def __init__(self, vin, t, code, plant, uuid, dda=None) -> None:
        self.vin = vin
        self.t = t
        self.code = code
        self.plant = plant
        self.dda = dda
        self.length, self.height = vehicle[code]
        self.uuid = uuid

btime = datetime.datetime.strptime('2021-08-01 00:00:00', '%Y-%m-%d %H:%M:%S')
dda_to_int = {'CD':0, 'XA':1, 'ZZ':2}
int_to_dda = ['CD', 'XA', 'ZZ']
int_to_seat = ['A1', 'A2', 'A3', 'A4', 'A5', 'B1', 'B2', 'B3', 'B4', 'B5']
cars = []
cars_dda = [[], [], []]
ts = []
car_loading_table = []
with open('schedule.csv') as csvf:
    reader = csv.reader(csvf, delimiter=',')
    tmp = True
    uuid = 0
    for row in reader:
        if tmp:
            tmp = False
            continue
        vin, t, code, plant, dda = row
        t = (datetime.datetime.strptime(t, '%Y-%m-%d %H:%M:%S') - btime).total_seconds()
        ts.append(t)
        cars.append((t, Car(vin, t, code, plant, uuid, dda)))
        cars_dda[dda_to_int[dda]].append(Car(vin, t, code, plant, uuid)) 
        car_loading_table.append([vin, "WAIT", "None", "None", "None"])
        uuid += 1
     
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
        if code in ['G08', 'F52', 'F49', 'F39']:
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
            elif self.loads[9] is None:
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

full_wagon_tx = [[], [], []]
not_full_wagon_tx = [[], [], []]
head_wagon_tx = [0, 0, 0]
departed_wagon_tx_dda = [[], [], []]
departed_wagon_tx = []
full_wagon_dd = [[], [], []]
not_full_wagon_dd = [[], [], []]
head_wagon_dd = [0, 0, 0]
departed_wagon_dd_dda = [[], [], []]
departed_wagon_dd = []
transit_schedule = list(range(0, total_length, 240))
buffer = []
trunk_tx_dd = []
trunk_ind = 1
cars_transit_table = []
i = 0
while True:
    if i>= len(cars):
        break
    t, curr_car = cars[i]
    d = dda_to_int[curr_car.dda]
    if curr_car.plant == "TX":
        skipped = False
        if len(transit_schedule) != 0:
            if len(buffer)<=6 and i>=transit_schedule[0]:
                if curr_car.code in ['F52', 'F49', 'F39','G20']:
                    buffer.append(curr_car)
                    skipped = True
                if len(buffer)==6:
                    trunk_time = buffer[-1].t
                    trunk_time_str = btime + datetime.timedelta(seconds=trunk_time)
                    trunk_time_str = trunk_time_str.strftime('%Y-%m-%d %H:%M:%S')
                    trunk_tx_dd.append(("TK{}".format(trunk_ind), "TX", "DD", trunk_time_str))
                    for j in range(6):
                        t_car = buffer[j]
                        new_car_time = trunk_time+7200
                        new_car = Car(t_car.vin, new_car_time, t_car.code, "DD", t_car.uuid, t_car.dda)
                        inserted = False
                        for k in range(i,len(cars)):
                            if new_car_time > cars[k][0]:
                                cars.insert(k+1, (new_car_time, new_car))
                                inserted = True
                                break
                        if not inserted:
                            cars.append((new_car_time, new_car))
                        #cars.append((trunk_time+7200, Car(t_car.vin, trunk_time+7200, t_car.code, "DD", t_car.uuid, t_car.dda)))
                        cars_transit_table.append((buffer[j].uuid, "TK{}".format(trunk_ind)))
                    #cars = sorted(cars, key=lambda x: x[0])
                    trunk_ind += 1
                    buffer = []
                    transit_schedule.pop(0)
        if not skipped:
            if len(not_full_wagon_tx[d]) == 0:
                not_full_wagon_tx[d].append(Wagon())
                not_full_wagon_tx[d][-1].insert_TX(curr_car)
            else:
                for j in range(len(not_full_wagon_tx[d])):
                    ret = not_full_wagon_tx[d][j].insert_TX(curr_car)
                    if ret is not None:
                        if not_full_wagon_tx[d][j].full():
                            full_wagon_tx[d].append(not_full_wagon_tx[d].pop(j))
                        break
                if ret is None:
                    not_full_wagon_tx[d].append(Wagon())
                    not_full_wagon_tx[d][-1].insert_TX(curr_car)   
    if curr_car.plant == "DD":
        if len(not_full_wagon_dd[d]) == 0:
            not_full_wagon_dd[d].append(Wagon())
            not_full_wagon_dd[d][-1].insert_DD(curr_car)
        else:
            for j in range(len(not_full_wagon_dd[d])):
                ret = not_full_wagon_dd[d][j].insert_DD(curr_car)
                if ret is not None:
                    if not_full_wagon_dd[d][j].full():
                        full_wagon_dd[d].append(not_full_wagon_dd[d].pop(j))
                    break
            if ret is None:
                not_full_wagon_dd[d].append(Wagon())
                not_full_wagon_dd[d][-1].insert_DD(curr_car)    
    # Train departure check
    if len(full_wagon_dd[d]) - head_wagon_dd[d] + len(full_wagon_tx[d]) - head_wagon_tx[d] >= 29:
        departed_wagon_dd_dda[d].append((head_wagon_dd[d], len(full_wagon_dd[d]))) # [head, tail)
        departed_wagon_tx_dda[d].append((head_wagon_tx[d], len(full_wagon_tx[d])))
        departed_wagon_dd.append((d, head_wagon_dd[d], len(full_wagon_dd[d])))
        departed_wagon_tx.append((d, head_wagon_tx[d], len(full_wagon_tx[d])))
        head_wagon_dd[d] = len(full_wagon_dd[d])
        head_wagon_tx[d] = len(full_wagon_tx[d])
    i += 1

train_time_table = []
tr_ind = 1
for i in range(len(departed_wagon_tx)):
    tr_ind_str = "TR{}".format(tr_ind)
    d, h_tx, t_tx = departed_wagon_tx[i]
    d, h_dd, t_dd = departed_wagon_dd[i]
    wagon_t_tx = btime + datetime.timedelta(seconds=full_wagon_tx[d][t_tx-1].latest_time()+14400)
    wagon_t_tx_str = wagon_t_tx.strftime('%Y-%m-%d %H:%M:%S')
    wagon_t_dd = btime + datetime.timedelta(seconds=full_wagon_dd[d][t_dd-1].latest_time()+14400)
    wagon_t_dd_str = wagon_t_dd.strftime('%Y-%m-%d %H:%M:%S')
    train_time_table.append((tr_ind_str, t_tx - h_tx, t_dd - h_dd, int_to_dda[d], wagon_t_tx_str, wagon_t_dd_str))
    tr_ind += 1         
    for i_tx in range(h_tx, t_tx):
        for p in range(10): # Position
            curr_car = full_wagon_tx[d][i_tx].loads[p]
            uuid = curr_car.uuid
            car_loading_table[uuid][1] = tr_ind_str
            car_loading_table[uuid][2] = "T{}".format(i_tx - h_tx + 1)
            car_loading_table[uuid][3] = int_to_seat[p]
    for i_dd in range(h_dd, t_dd):
        for p in range(10): # Position
            curr_car = full_wagon_dd[d][i_dd].loads[p]
            uuid = curr_car.uuid
            car_loading_table[uuid][1] = tr_ind_str
            car_loading_table[uuid][2] = "D{}".format(i_dd - h_dd + 1)
            car_loading_table[uuid][3] = int_to_seat[p]
            
non_departed_wagon_tx = [[], [], []]
non_departed_wagon_dd = [[], [], []]
init_dict = {'F52':0, 'G20':0, 'G28':0, 'G38':0, 'F49':0, 'F39':0, 'G08':0}
non_departed_wagon_code_tx = [dict(init_dict), dict(init_dict), dict(init_dict)]
non_departed_wagon_code_tx_total = dict(init_dict)
non_departed_wagon_code_dd = [dict(init_dict), dict(init_dict), dict(init_dict)]
non_departed_wagon_code_dd_total = dict(init_dict)
for d in range(3):
    tail = departed_wagon_tx_dda[d][-1][1]
    non_departed_wagon_tx[d] += full_wagon_tx[d][tail:]
    non_departed_wagon_tx[d] += not_full_wagon_tx[d]
    tail = departed_wagon_dd_dda[d][-1][1]
    non_departed_wagon_dd[d] += full_wagon_dd[d][tail:]
    non_departed_wagon_dd[d] += not_full_wagon_dd[d]
for d in range(3):
    for i in range(len(non_departed_wagon_tx[d])):
        for p in range(10):
            curr_car = non_departed_wagon_tx[d][i].loads[p]
            if curr_car is not None:
                non_departed_wagon_code_tx[d][curr_car.code] += 1
                non_departed_wagon_code_tx_total[curr_car.code] += 1
    for i in range(len(non_departed_wagon_dd[d])):
        for p in range(10):
            curr_car = non_departed_wagon_dd[d][i].loads[p]
            if curr_car is not None:
                non_departed_wagon_code_dd[d][curr_car.code] += 1 
                non_departed_wagon_code_dd_total[curr_car.code] += 1  
for i in range(len(cars_transit_table)):
    car_loading_table[cars_transit_table[i][0]][-1] = cars_transit_table[i][1]
with open('trains.csv', 'w') as csvf:
    writer = csv.writer(csvf, delimiter=',')
    writer.writerow(('TrainID', 'TX_Wagon', 'DD_Wagon', 'DDA', 'TX_Time', 'DD_Time'))
    for item in train_time_table:
        writer.writerow(item)
with open('trunks.csv', 'w') as csvf:
    writer = csv.writer(csvf, delimiter=',')
    writer.writerow(('TrunkID', 'From', 'To', 'Time'))
    for item in trunk_tx_dd:
        writer.writerow(item)
with open('vehicles.csv', 'w') as csvf:
    writer = csv.writer(csvf, delimiter=',')
    writer.writerow(('VIN', 'TrainID', 'Cabin', 'Seat', 'Transit'))
    for item in car_loading_table:
        writer.writerow(item)
           