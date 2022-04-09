from dataclasses import dataclass
import numpy as np
UP = 0
DN = 1
DIR = ("UP","DN")


@dataclass
class record:
    def __init__(self,s,ns,nc,p,d):
        self.s = s
        self.top = s.top
        self.n = self.top*2
        nshafts = self.s.nshafts
        ncars = self.s.ncars
        self.nsnc1 = nshafts*ncars+1
        self.b = np.zeros(self.nsnc1,int)
        self.v = np.zeros((self.nsnc1,3,self.n),int)
        self.p = p
        self.d = d

        self.index = 0
        
        # Data for the assigned car
        self.fill(ns,nc)
        # Data for all cars
        for i in range(nshafts):
            for j in range(ncars):
                self.index = self.index+1
                self.fill(i,j)

    def fill(self,ns,nc):
        shaft = self.s.shafts[ns]
        car = shaft.cars[nc]
        dir = shaft.dir
        pos = car.pos
        count = len(car.boarded)+1

        self.b[self.index] = count
        # Put boarded passenger count at current position
        if dir == UP:
            self.v[self.index,0,pos] = 1
        else:
            self.v[self.index,0,self.top+pos] = 1
                    
        # Record assigned calls
        for k in range(self.top):
            if car.calls[k,UP]:
                self.v[self.index,1,k] = 1
        for k in range(self.top):
            if car.calls[k,DN]:
                self.v[self.index,1,k+self.top] = 1

        # Record new call
        if self.d == UP:
            self.v[self.index,2,self.p] = 1
        else:
            self.v[self.index,2,self.top+self.p] = 1

    def flush(self,wt):
        if self.s.trn:
            for i in range(self.nsnc1):
                self.s.trnf.write("%d " % self.b[i])
                for j in range(3):
                    for k in range(self.n):
                        self.s.trnf.write("%d " % self.v[i,j,k])
                self.s.trnf.write("  %6.1f\n" % wt)
