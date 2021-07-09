class Wagon:
    def __init__(self):
        self.slot = {}
        self.pos = ['A1','A2','A3','A4','A5','B1','B2','B3','B4','B5']
        self.slot_height = {'A1':1810, 'A2':1810, 'A3':1810, 'A4':1810, 'A5':1810,
        'B1':1520, 'B2':2260, 'B3':2260, 'B4':2260, 'B5':1510}
        self.slot_length_sum = {'A':24520, 'B':24600}
    
    def check_length_limit(self, level):
        sum = 0
        for p in self.pos:
            if level in p:
                sum += self.slot[p].size['length']
        if sum > self.slot_length_sum[level]:
            raise Exception(f'Exceed length limit of {level}')

    def add_cargo(self, cargo, pos):
        '''
        cargo - A Cargo object
        pos - str like 'A1'
        '''
        if pos in self.pos:
            raise Exception('Position occupied') 

        if cargo.size['height'] > self.slot_height[pos]:
            raise Exception('Heigher than the slot')            

        self.check_length_limit('A')
        self.check_length_limit('B')

        self.slot[pos] = cargo