import pandas as pd

schedule = pd.read_csv('schedule.csv')
CD = schedule[(schedule['DDA'] == 'CD')]

for idx, row in CD.iterrows():
    cargo = Cargo(row)
    wagon.add_cargo(cargo)
    