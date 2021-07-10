from django.shortcuts import render
import pickle

vehicles = pickle.load( open( "vehicles.pkl", "rb" ) )
print("vehicles loaded")
schedule = pickle.load( open( "schedule.pkl", "rb" ) )
print("schedule loaded")

def index(request):
    return render(request, 'dash/index.html')

def car(request):
    return render(request, 'dash/car.html', {'vehicles':vehicles})

def model(request, vin):
    data = {}
    img_src = ""
    for i in schedule:
        if vin in i:
            data['VIN'] = vin
            data['ETA'] = i[vin][0]
            data['Code'] = i[vin][1]
            data['Plant'] = i[vin][2]
            data['DDA'] = i[vin][3]
            img_src = 'dash/' + i[vin][1].lower() + '.png'
            break
    
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