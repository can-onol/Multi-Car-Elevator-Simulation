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
        self.b = 0
        self.cp = 0
        self.cd = 0
        self.v = np.zeros(self.n,int)
        self.pp = 0
        self.pd = 0
        
        shaft = self.s.shafts[ns]
        car = shaft.cars[nc]
        dir = shaft.dir
        pos = car.pos
        count = len(car.boarded)+1

        self.b = count
        # Put boarded passenger count at current position
        self.cp = pos
        self.cd = dir
                    
        # Record assigned calls
        for k in range(self.top):
            if car.calls[k,UP]:
                self.v[k] = 1
        for k in range(self.top):
            if car.calls[k,DN]:
                self.v[k+self.top] = 1

        # Record new call
        self.pp = p
        self.pd = d

    def flush(self,wt):
        if self.s.trn:
            self.s.trnf.write("%d " % self.b)
            self.s.trnf.write("%d " % self.cp)
            self.s.trnf.write("%d " % self.cd)
            for j in range(self.n):
                self.s.trnf.write("%d " % self.v[j])
            self.s.trnf.write("%d " % self.pp)
            self.s.trnf.write("%d " % self.pd)
            self.s.trnf.write("  %6.1f\n" % wt)
