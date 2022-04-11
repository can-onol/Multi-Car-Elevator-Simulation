from dataclasses import dataclass
import numpy as np
import pandas as pd

UP = 0
DN = 1
DIR = ("UP","DN")
numShaft=4
numCar=1
positions = np.zeros((numCar, numShaft))

@dataclass
class record:
    def __init__(self,s,ns,nc,p,d):
        self.s = s
        self.top = s.top
        self.n = self.top*2
        self.nshaft = s.nshafts
        self.ncars = s.ncars
        self.b = 0

        self.v = np.zeros((3,self.n),int)
        self.sh = np.zeros(self.nshaft)
        self.ca = np.zeros(self.ncars)

        # self.ca = np.zeros(len(self.shaft.car), int)

        self.ns = ns
        self.dir = d

        shaft = self.s.shafts[ns]
        self.shaftId = shaft.id
        # Onehot encoding of shaft
        self.sh[self.shaftId] = 1

        car = shaft.cars[nc]
        self.carId = car.id
        # Onehot encoding of car
        self.ca[self.carId] = 1

        positions[car.id, shaft.id] = car.pos
        # print(positions)

        self.carCap = car.cap
        dir = shaft.dir
        pos = car.pos
        count = len(car.boarded)+1

        self.b = count
        # Put boarded passenger count at current position
        if dir == UP:
            self.v[0,pos] = 1
        else:
            self.v[0,self.top+pos] = 1

        # Record assigned calls
        for k in range(self.top):
            if car.calls[k,UP]:
                self.v[1,k] = 1
        for k in range(self.top):
            if car.calls[k,DN]:
                self.v[1,k+self.top] = 1

        # Record new call
        if d == UP:
            self.v[2,p] = 1
        else:
            self.v[2,self.top+p] = 1
            
    def dump(self):
        res = np.zeros(self.n*3+1,int)
        res[0] = self.b
        k = 1
        for i in range(3):
            for j in range(self.n):
                res[k] = self.v[i,j]
                k = k+1
        return [res]

    def flush(self,wt):
        if self.s.trn:
            self.s.trnf.write("%d\t%d\t%d\t%d\t" % (self.b, self.dir, self.carId, self.shaftId))
            for i in range(len(self.ca)):
                self.s.trnf.write("%d " % self.ca[i])
            self.s.trnf.write("\t")
            for i in range(len(self.sh)):
                self.s.trnf.write("%d " % self.sh[i])
            self.s.trnf.write("\t")
            for i in range(numCar):
                for j in range(numShaft):
                    self.s.trnf.write("%d " % positions[i,j])
                self.s.trnf.write("\t")
            for i in range(3):
                for j in range(self.n):
                    self.s.trnf.write(" %d" % self.v[i, j])
                self.s.trnf.write("\t")  # TODO: Kontrol edilecek.
            self.s.trnf.write("  %6.1f\n" % wt)
