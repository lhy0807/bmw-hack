from django.shortcuts import render
import pickle
import imageio
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import cv2
import io
import base64
matplotlib.use('TkAgg')

vehicles = pickle.load( open( "vehicles.pkl", "rb" ) )
print("vehicles loaded")
schedule = pickle.load( open( "schedule.pkl", "rb" ) )
print("schedule loaded")
trains = pickle.load( open( "trains.pkl", "rb" ) )
print("trains loaded")

def index(request):
    todays_train = []
    past_10_days_train_num = {}
    for t in trains:
        d1 = t[4]
        d1_date = int(d1.split(' ')[0].split('-')[2])
        d2 = t[5]
        d2_date = int(d2.split(' ')[0].split('-')[2])
        if (d1_date == 15) or (d2_date == 15):
            todays_train.append({
                'TrainID': t[0],
                'TX_Wagon': t[1],
                'DD_Wagon': t[2],
                'DDA': t[3],
                'TX_Time': t[4],
                'DD_Time': t[5]
            })
        if d1_date >= 5 and d1_date < 15:
            if d1_date not in past_10_days_train_num:
                past_10_days_train_num[d1_date] = 1
            else:
                past_10_days_train_num[d1_date] += 1

        elif d2_date >= 5 and d2_date < 15:
            if d2_date not in past_10_days_train_num:
                past_10_days_train_num[d2_date] = 1
            else:
                past_10_days_train_num[d2_date] += 1
    
    return render(request, 'dash/index.html', {'trains':todays_train, 'trains_10':past_10_days_train_num})

def car(request):
    return render(request, 'dash/car.html', {'vehicles':vehicles})

def model(request, vin):
    data = {}
    img_src = ""
    data['VIN'] = vin
    data['ETA'] = schedule[vin][0]
    data['Code'] = schedule[vin][1]
    data['Plant'] = schedule[vin][2]
    data['DDA'] = schedule[vin][3]
    img_src = 'dash/' + schedule[vin][1].lower() + '.png'
    
    # find train id
    train = {}
    TrainID = ""
    Cabin = ""
    Seat = ""
    Transit = ""
    for i in vehicles:
        if i['VIN'] == data['VIN']:
            train = i
            TrainID = i['TrainID']
            Cabin = i['Cabin']
            Seat = i['Seat']
            Transit = i['Transit']

    return render(request, 'dash/model.html', {'data':data, 'img_src':img_src, 'train':train})

def train(request, TrainID, Cabin, Seat):
    # find VIN
    VIN = {}
    for i in vehicles:
        if i['TrainID'] == TrainID and i['Cabin'] == Cabin:
            VIN[i['Seat']] =  i['VIN']
    DDA = ""
    models = {}
    for i in VIN.keys():
        models[i] = schedule[VIN[i]][1]
        DDA = schedule[VIN[i]][-1]
    
    wagon = imageio.imread('../wagon.png')
    h = 60
    w = 150
    h_off = 30
    w_off = 50
    pic = wagon.copy()
    for idx, i in enumerate(['A1','A2','A3','A4','A5']):
        model = models[i]
        bmw = imageio.imread(f'../{model.lower()}.jpg')
        res = cv2.resize(bmw, dsize=(w, h), interpolation=cv2.INTER_CUBIC)
        pic[h_off+h:h_off+h*2, w*idx+w_off:w*(idx+1)+w_off, :] = res

        if i == Seat:
            pic = cv2.rectangle(pic, (h_off+h, w*idx+w_off), (h_off+h*2, w*(idx+1)+w_off), color, thickness)

    for idx, i in enumerate(['B1','B2','B3','B4','B5']):
        model = models[i]
        bmw = imageio.imread(f'../{model.lower()}.jpg')
        res = cv2.resize(bmw, dsize=(w, h), interpolation=cv2.INTER_CUBIC)
        pic[h_off:h_off+h, w*idx+w_off:w*(idx+1)+w_off, :] = res
    
    fig, ax = plt.subplots(1, 1)
    plt.imshow(pic)
    plt.axis('off')
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=1200)
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    #close figure
    plt.close(fig)
    return render(request, 'dash/train.html',
    {'img':data,'TrainID':TrainID, 'Cabin':Cabin, 'Seat':Seat, 'DDA':DDA})