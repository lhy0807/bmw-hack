import pandas as pd
import pickle

vehicles = []
csv = pd.read_csv('../vehicles.csv')
for _, row in csv.iterrows():
    vehicles.append(
        {
            'VIN': row[0],
            'TrainID': row[1],
            'Cabin': row[2],
            'Seat': row[3],
            'Transit': row[4]
        }
    )

pickle.dump( vehicles, open( "vehicles.pkl", "wb" ) )
print("vehicles transformed")

schedule = []
csv = pd.read_csv('../schedule.csv')
for _, row in csv.iterrows():
    schedule.append(
        {
            row[0]: [
                row[1], row[2], row[3], row[4]
            ]
        }
    )

pickle.dump( schedule, open( "schedule.pkl", "wb" ) )
print("schedule transformed")
