#!/Library/Frameworks/Python.framework/Versions/3.8/bin/python3.8
## !/usr/bin/env python3
# Multi-Car Group Control Simulation in Python
# (c) S.Markon, Linearity Co. Ltd. 2019, 2020, 2021
# v.0.7
#
# Major revision:
#   the simulation object is now copyable, allowing recursion (not working yet!)
#
# Implemented:
#   random passenger generation
#   passenger generation from O/D table (to be supplied externally)
#   unblocking travel by moving idle cars
#   assignment to shafts (by external routines)
#   zoned assignment to cars in shafts
#   generating visual trace of events on a Tkinter canvas (TODO: replace magic numbers)
#
# Not implemented:
#   proper car timings
#   proper assignment
#
#
import random,math
import numpy as np
import sys
from dataclasses import dataclass
from copy import deepcopy
from mcegui import *

from setup import *

# builtins.inputsize = 121
# builtins.netsize = 20


# (Xtrain1,Ytrain1) = load("trnx1.csv",inputsize)
# pipeline1 = load_pipeline('mlp_weights.h5',"standardize.pickle")

def nn_assign(sim,s,p):
        # Cheesy call assignment
        x = max(p.arr,p.dest)
        for i in range(s.ncars):
            if x <= sim.zones[i]:
                break
        c = s.cars[i]
        # xprint("%6.1f assign (%d,%d) to %d" % (s.ncars,p.arr,p.dest,c.id),dbg)
        return c

def nn_algorithm(simulation,p):
    wmin = 9999999
    cmin = 0
    for s in simulation.shafts:
        c = assign(simulation,s,p)
        rec = record(simulation,s.id,c.id,p.arr,p.dir).dump()
        w = pipeline1.predict(rec)
        if w < wmin:
            wmin = w
            cmin = c
    return cmin


dbg = True
trc = False
wtp = True
wts = True
dmp = False
pre = False
sta = False
anim = False

UP = 0
DN = 1
DIR = ("UP","DN")

def xprint(s,x):
    if x:
        print(s)

class simulation:
    def __init__(self,simulator,add=True):
        self.timer = math.inf
        self.state = 'idle'
        self.s = simulator
        if add:
            self.id = simulator.id
            if type(self)==cage:
                self.type = "cage"
            else:
                self.type = "other"
            simulator.id = simulator.id+1
            simulator.sys.append(self)  # self.sys = [] ---> [cage, cage, other, ...]?

    def next(self,st,dt):
        self.state = st
        self.timer = self.s.now + dt


class simulator:
    """
    Object for controlling the simulation and to provide common functionalities.
    All actors inherit its properties and are registered in "sys".
    At each time the registered actors are scanned for current event.
    Then the "event" method of that actor is called.
    If something happens during executing this, scan is repeated until no more current events.
    Then the timer "now" is stepped, execution continues until reaching the "end" timing.
    """

    def __init__(self,top=10,nshafts=2,ncars=3,seed=1,end=1800,
                     dbg=False,trc=False,wtp=False,wts=False,
                     dmp=False,sta=False,pre=False,dly=1,cap=100,trnf=None):
        self.id = 0
        self.sys = [] # TODO system components of the simulator? shafts, elevator cars, passengers? *******************
        self.now = 0
        self.wt = 0
        self.wtc = 0
        self.st = 0
        self.nt = 0
        self.nn = 0
        self.top = top			# top floor
        self.ncars = ncars		# number of cars per shaft
        self.nshafts = nshafts	# number of shafts
        self.seed = seed		# random seed
        self.end = end           # time limit
        self.dbg = dbg			# generate debug log
        self.trc = trc			# generate graphical trace
        self.wtp = wtp			# print passenger waiting/service times
        self.wts = wts			# passenger waiting/service time statistics
        self.dmp = dmp			# generate visual state dump
        self.sta = sta			# (not used now)
        self.pre = pre			# run cloned simulator at each assigment (not working yet!)
        self.anim = anim
        self.dly = dly
        self.psgs = []           # finished passengers
        self.W = 32
        self.H = 16
        self.D = 2
        self.leftover = 0
        self.trn = None
        self.trnf = None
        self.carCall = np.zeros((self.top, self.nshafts))
        self.extended_hallCall = np.zeros((self.top, self.nshafts))
        self.hallCall = np.zeros((self.top, 2))
        self.hallCall_wt = np.zeros((self.top, 2))


        if trnf:
            self.trnf = open(trnf,"w") # TODO "open" function to write to the file trnf *************************
            self.trn = True
        self.gui = gui(self)
        if dmp or trc:
            self.height = nshafts * 2 * (top + 2) * (ncars + 1)
            self.width = self.end # TODO time limit as width?? ************************
        else:
            self.height = self.H * (top + 2)
            self.width = self.W * (2*nshafts+1)
        #print("W=%d H=%d" % (self.width,self.height))
        self.bldg = [[] for i in range(self.top)] # TODO building floors? ******************** [[],[],[], ..., []]
        self.shafts = [shaft(self,i,ncars) for i in range(nshafts)] # create a shaft list ****************

        n = int(top/math.sqrt(ncars))
        self.zones = [n,]		# assignment floor zones for each car in shaft
        for i in range(1,ncars):
            self.zones.append(int(top*math.sqrt((i+1)/ncars)))
        #print(self.zones)
        self.x = 0
        if seed:
            random.seed(seed)
        if anim:
            for a in self.sys:
                if type(a)==cage:
                    a.init_gpos()

    def run(self):
        """
        Find the next time step; then execute all pending "events" for each
        actor for that time step.
        If any of them causes new events to be scheduled for the same time,
        they will be also executed.
        If previously scheduled events are removed (e.g. a time-out is
        re-scheduled to another time), they are not executed.
        """
        t_next = self.end			# find nearest event time
        for a in self.sys:
            if a.timer < t_next:
                t_next = a.timer
        self.dt = t_next - self.now # time passed from next nearest event and now
        self.now = t_next
        if self.now >= self.end:	# is it before end time?
            #print("Time over") #It is written in the terminal at the end of simulation
            xprint("%6d %6.1f %6.1f %6.1f %6d" % (self.nn,self.wt/self.nt,self.st/self.nt,self.nt/self.nn,self.leftover),self.wts) # Final info.
            if self.trn:
                self.trnf.close()
            if dmp:
                self.gui.tk.update()
            return
        scan = True					# find all events at the same time
        while scan:
            scan = False
            for a in self.sys:
                if a.timer == t_next:
                    a.event()
                    scan = True

    def run_again(self):
        self.run()
        if self.now < self.end:
            self.gui.tk.after(self.dly,self.run_again)
        else:
            self.gui.tk.quit()

    def go(self):					# run simulation until end
        while self.now < self.end:
            self.run()

    def goto(self,p):				# run simulation until passenger p is served
        while self.now < self.end:
            for px in self.psgs:
                if p.id == px.id:
                    return px.wt
            self.run()

    def calculate_extended_matrix(self):
        for i in range(self.nshafts):
            if self.shafts[i].dir == UP:
                self.extended_hallCall[:, i] = self.hallCall_wt[:, 0]
            elif self.shafts[i].dir == DN:
                self.extended_hallCall[:, i] = self.hallCall_wt[:, 1]
            else:
                print("TODO")

        return self.extended_hallCall

class clock(simulation):
    """
    The clock for generating a periodical system status dump.
    More than one clock could be present for different status dumps.
    """
    def __init__(self,s,step=1):
        simulation.__init__(self,s)
        self.step = step
        self.state = 'running'
        self.timer = self.s.now
        #print("clock stars at %f" % self.timer)

    def event(self):
        global anim
        if self.s.dmp:
            self.s.gui.dump()
        elif anim:
            self.s.gui.update()
        #print(self.now)
        self.next('running',self.step)


class traffic(simulation):
    """
    Class for passenger generation.
    More than one "traffic" can be registered.
    """
    def __init__(self,s,rate,OD=None): # OD ?? **************
        simulation.__init__(self,s)
        if not OD:
            self.OD = np.ones(self.s.top)-np.identity(self.s.top)
        else:
            self.OD = OD
        for i in range(self.s.ncars):
            for j in range(self.s.top):
                # print(i,j)
                self.OD[i,j] = 0
                self.OD[j,i] = 0
        # Generate a linear vector "count" corresponding to OD
        # A random number pointing into "count" gives a passenger
        self.range = self.s.top**2
        self.count = np.zeros((self.range,3))
        # print(self.count.shape)
        k = s = 0
        for i in range(self.s.top):
            for j in range(self.s.top):
                s += self.OD[i,j]
                if i==j:
                    self.count[k,0] = -1
                else:
                    self.count[k,0] = s
                self.count[k,1] = i
                self.count[k,2] = j
                k+=1
        # print(self.count[:,0])
        # print(self.OD)
        self.max = s
        self.rate = rate
        self.timer = self.s.now

    def event(self):
        n = random.randint(0,self.max)
        for i in range(self.range):
            if self.count[i,0] >= n:
                fr = int(self.count[i,1])
                to = int(self.count[i,2])
                break
        p = psng(self.s,fr,to)
        c = self.s.algorithm(self.s,p)
        xprint("%6.1f %s" % (self.s.now,p),self.s.dbg)
        p.assign(c)                     # Assing passenger to carrier
        self.timer = self.s.now + random.expovariate(self.rate)


@dataclass
class psng(simulation):
    """
    Passenger class
    Arrive -> Assign -> Wait -> Board -> Travel -> Leave
    """
    def __init__(self,s,arr,dest):
        simulation.__init__(self,s)
        self.arr = arr  # current floor of the passenger
        self.dest = dest # destination floor of the passenger
        self.carrier = None # the elevator car the passenger will get on
        if arr < dest:
            self.dir = UP
        else:
            self.dir = DN
        self.t_arr = self.s.now
        self.state = 'arrived'

    def __repr__(self):
        if self.carrier:
            return f"psng(id:{self.id}, arr:{self.arr}, dest:{self.dest}, carrier:{self.carrier.id}, st:{self.state})"
        else:
            return f"psng(id:{self.id}, arr:{self.arr}, dest:{self.dest}, st:{self.state})"


    def assign(self,c):
        self.s.nn = self.s.nn + 1       # ??
        self.carrier = c
        #### modificiation
        self.s.hallCall[self.arr, self.carrier.shaft.dir] = 1
        #### modification end
        self.s.bldg[self.arr].append(self) # [ [], [], [psng1, psng2, ... (add passenger to current_floor)], ...,[]]
        c.calls[self.arr,self.dir] = 1  # psng's arrived floor. It's different from other call matrices
        ''' [up down]
            [1  0   ]  arrived passenger 
            [0  0   ]
            [0  1   ]
        '''
        if c.state == "idle":
            if c.pos == self.arr:
                c.next("open",0)
            else:
                c.next("close",0)
        if self.state != 'assigned':
            if self.s.trn:
                self.rec = record(self.s,c.shaft.id,c.id,self.arr,self.dir) #
            self.state = 'assigned'

        # Recursive simulation
        if self.s.pre:
            xprint("%6.1f wtx calculation starts" % self.s.now,self.s.dbg)
            saved=random.getstate()
            sim2=deepcopy(self.s)
            sim2.pre=False
            #sim2.dbg=False
            #random.seed(self.s.seed)
            wtx=sim2.goto(self)
            self.wtx=wtx
            random.setstate(saved)
            xprint("%6.1f wtx=%6.1f" % (self.s.now,self.wtx),self.s.dbg)

    def board(self):
        self.t_board = self.s.now
        wt = self.t_board - self.t_arr
        self.wt = wt
        #### modification
        self.s.hallCall_wt[self.arr, self.carrier.shaft.dir] = self.wt
        #### modification end
        self.carrier.board(self)
        xprint("wt=%6.1f %6.1f %s" % (self.wt,self.s.now,self),self.s.dbg) # print to console when boarded
        if self.s.trn and self.state != 'boarded':
            self.rec.flush(wt)
        self.state = 'boarded'

    def leave(self):
        self.t_leave = self.s.now
        st = self.t_leave-self.t_arr
        wtc = self.t_leave-self.t_board
        self.wtc = wtc
        self.carrier.leave(self)
        self.state = 'finished'
        xprint("%6.1f PSG %6.1f %6.1f" % (self.s.now,self.wt,st),self.s.wtp) # print to console when arrived to destination
        self.st = st
        self.s.wt = self.s.wt + self.wt
        self.s.wtc = self.s.wtc + self.wtc
        self.s.st = self.s.st + self.st
        self.s.nt = self.s.nt + 1
        self.s.psgs.append(self)
        xprint("ASD %6.1f %s" % (self.s.now,self),self.s.dbg)

class cage(simulation):
    """
    Multi-car elevator cage
    Responds to calls according to current shaft direction.
    Runs until collecting all hall calls and discharging boarded passengers.
    """
    def __init__(self,s,shaft,
                 pos=0,
                 t_run=2.3,
                 t_open=2.4,
                 t_leave=0.8,
                 t_board=0.8,
                 t_close=3.4,
                 cap=100):
        simulation.__init__(self,s)
        self.shaft = shaft
        self.pos = pos # position of the cage
        self.id = pos
        self.sid = None  # id of the cage inside the cage (cage 1, cage 2, ...)
        self.lastpos = pos
        self.home = pos # the position of the cage when idle
        self.t_run=t_run        # Time required to pa 1 floor level
        self.t_open=t_open      # Time taken to open doors
        self.t_leave=t_leave    # Time required for passengers to leave # time taken for passenger to leave
        self.t_board=t_board    # Time required for passengers to board
        self.t_close=t_close    # Time taken to close doors
        self.cap=cap            # PAX capacity
        self.blocked_cage = None
        self.blocks_at = -1     # The floor of next blocking cage.
        self.boarded = []       # List of passengers who have boarded.
        self.calls = np.zeros((self.s.top,2)) # 2 here is the directions for UP and DN, the destination floors of the passengers are stored
        # self.calls_wt = np.zeros((self.s.top, 2))
        # List of floors (up and down separately) Write a 1 at the location where a call is made from

    def init_gpos(self):
        self.gpos = self.s.gui.gpos(self.shaft.id,self.pos) # GUI related. GUI position?


    def __repr__(self): # Produce string representing car information.
        return f"cage(id:{self.id}, pos:{self.pos}, dir:{DIR[self.shaft.dir]}, st:{self.state}, shaftID:{self.shaft.id}, " \
               f"\ncallRequests:{self.calls}, " \
               f"\nwth:{self.s.hallCall_wt}, " \
               f"\nwtc:{self.s.carCall})," \
               f"\nwtB:{self.s.calculate_extended_matrix()})"


    def board(self,p): #board the passenger p
        self.boarded.append(p)
        if p in self.s.bldg[p.arr]:
            self.s.bldg[p.arr].remove(p) # Remove passenger from waiting floor.
        self.calls[p.dest,self.shaft.dir] = 1 # Add destination to the call list of this car.
        # self.calls_wt[p.arr,self.shaft.dir] = p.wt

    def leave(self,p): # deboard the passenger p
        self.boarded.remove(p)
        self.calls[p.dest,self.shaft.dir] = 0
        self.s.carCall[p.dest, self.shaft.id] = p.wtc

    def event(self):

        """
        State transition graph of an elevator:
        IDLE -> {OPEN, CLOSE}
        OPEN -> {OPEN, BOARD}
        BOARD -> {BOARD, CLOSE}
        CLOSE -> {CLOSE, RUN, IDLE}
        RUN -> {RUN, OPEN}
        """
        if self.state == 'idle':
            if self.here():
                # Passengers waiting at this landing
                self.next('open',self.t_open)
            elif self.called() != -1:
                # Passengers arrived somewhere else
                self.next('close',self.t_run)
            else:
                # Nothing to do
                self.timer = math.inf

        # ************IMPORTANT********************************
        elif self.state == 'open':
            self.trace() # GUI Related.
            self.calls[self.pos,self.shaft.dir] = 0 # Call at this floor is removed from call list.
            if self.blocked_cage != None and self.pos == self.blocks_at: # TODO: Check what the block below means:
                # Yielded to neighbor cage
                xprint("%6.1f %s yielded at %d" % (self.s.now,self,self.blocks_at),self.s.dbg) # there is a blocking elevator car
                # Wake up that cage
                self.blocked_cage.timer = self.s.now
                self.blocked_cage = None
                self.blocks_at = -1
            self.state = 'board'
            for p in self.boarded: # Disembark passengers for this floor.
                # A passenger is leaving
                if p.dest == self.pos:
                    p.leave()
                    self.next('open',self.t_leave)
        elif self.state == 'board':
            self.next('close',self.t_close)
            for p in self.s.bldg[self.pos]:
                # A passenger is boarding
                if p.carrier == self and p.dir == self.shaft.dir: # if the floor of the passenger (that are assigned to this car) and car is the same and their direction is the same
                    if len(self.boarded) < self.cap: # if there are still capacity
                        p.board()
                        self.next('board',self.t_board)
                    else:
                        self.s.leftover = self.s.leftover+1     #TODO: Perhaps better to restore this passenger back to the pool?
        # **************************************************************************************************************
        elif self.state == 'close':
            #print(self.calls)
            if self.called() != -1:
                xprint("%6.1f %s  called at %d" % (self.s.now,self,self.called()),self.s.dbg)
                self.check_blocking()   # This is actually a waiting loop. This car stops until the blocking car has cleared all the space until target floor.
            else:
                self.next('idle',math.inf)
                self.shaft.turn()
        elif self.state == 'run':
            #if (self.pos == 0 and self.shaft.dir == DN) or (self.pos == self.top-1 and self.shaft.dir == UP):
            #    self.next('idle',math.inf)
            #    self.shaft.turn()
            if self.here() or self.called() == -1: # open when there is a passenger in this floor or there is no call
                self.next('open',self.t_open)
            else:
                if self.shaft.dir == UP:
                    self.pos += 1           # No need to check for max or min floor because:
                else:                       # Either there is a call and it will be between 0-max
                    self.pos -= 1           # Or there is no call and the elevator will stop.
                self.trace()
                self.next('run',self.t_run)
        xprint("%6.1f %s" % (self.s.now,self),self.s.dbg)   # In case of any event produce debug data.


    # def otherPos(self):
    #     if self.shaft.dir == UP and self.over != None:
    #         print('upper car position:', self.over.pos)


    def here(self):
        return self.calls[self.pos,self.shaft.dir] != 0     # return true if there is a call in the current floor and direction **********

    def check_blocking(self):
        # If the neighbor car is blocking us, tell it move please
        x = self.blocked()      # Floor that the blocking car must move to, to remove blocking.
        #print("blocked returns ",x)
        if x != -1:
            #print("unblocking ",x)
            self.unblock(x)
            # # if the position of the blocking car is more than 2 units away, move the elevator car
            # if((self.shaft.dir == UP and self.pos < self.over.pos - 4) or (self.shaft.dir == DN and self.pos > self.under.pos + 4)):
            #     if(self.shaft.dir == UP):
            #         print("Debug blocking: ", "this car pos: ", self.pos,"over car pos: ", self.over.pos, "shaft: ", self.shaft.id)
            #     else:
            #         print("Debug blocking ","this car pos: ", self.pos,"under car pos: ", self.under.pos, "shaft: ", self.shaft.id)
            #     self.next("run", self.t_run)
            # else:
            self.next('close',math.inf)
        else:
            self.next('run',self.t_run)


    def higher(self):
        # Do we have a call above?
        for i in range(self.pos+1,self.s.top):
            if self.calls[i,UP] != 0:
                return i
        for i in range(self.s.top-1,self.pos,-1):
            if self.calls[i,DN] != 0:
                return i
        return -1

    def lower(self):
        # Do we have a call below?
        for i in range(self.pos-1,0,-1):
            if self.calls[i,DN] != 0:
                return i
        for i in range(0,self.pos):
            if self.calls[i,UP] != 0:
                return i
        return -1

    def called(self):
        # Are we called away from this floor?
        if self.shaft.dir == UP:
            return self.higher()
        else:
            return self.lower()

    def blocked(self):      # TODO: Change the check for not 'cl' but the current pos of this car + some safety distance.
        # Are we blocked from going to the closest call?
        cl = self.called()       # The destination floor of this car.
        #print("Blocked: cl=", cl)
        if cl != -1:
            if self.shaft.dir == UP and self.over != None and self.over.pos <= cl:  # If there is a cabin above and its posn is lower than our destination.
                return cl+1
            elif self.shaft.dir == DN and self.under != None and self.under.pos >= cl: # Vice versa.
                return cl-1
        #print("Blocked: False")
        return -1

    def unblock(self,x):
        # Tell blocking car to go
        if self.shaft.dir == UP:
            y = self.over
        else:
            y = self.under

        xprint("%6.1f %s unblocks %s for %d" % (self.s.now,self,y,x),self.s.dbg)
        y.blocked_cage = self           #This cabin is the one which is blocked by the blocking cabin:y
        y.blocks_at = x                 # Misleading variable name. Blocking cabin destination.
        y.calls[x,self.shaft.dir] = 2   # Add the detination as the floor to move to, with type '2' (direct move.) TODO: Check meaning of '2'
        if y.state == 'idle':
            y.next('close',0)

    def trace(self):        # GUI related.
        if self.s.trc:
            st = self.s.now
            base = (self.s.top*5+10)*self.s.nshafts
            for s in self.s.shafts:
                i = 0
                for c in s.cars:
                    self.s.gui.cv.create_oval(st,base-c.pos*5,st+4,base-c.pos*5+4,fill=self.s.gui.colors[i],outline=self.s.gui.colors[i])
                    i += 1
                base -= self.s.top*5+10



class shaft(simulation):
    """
    Shaft with "ncars" cages
    Manages direction:
    runs its cages in UP direction until all become idle.
    then runs them in DOWN direction until all return to their home floor.
    """
    def __init__(self,s,id,ncars,cap=100):
        simulation.__init__(self,s,False)
        self.id = id
        self.dir = UP   # direction of the cars in a shaft is always the same TODO: is this a must?
        self.cars = []
        self.ncars = ncars
        for i in range(ncars):
            c = cage(s,pos=i,shaft=self,cap=cap)
            c.sid = i       # what is sid                 Shaft ID of this car which one in this shaft?
            c.over = None
            c.under = None
            if i>0:
                self.cars[-1].over = c
                c.under = self.cars[-1]
            self.cars.append(c)

    def turn(self):
        if self.dir == UP:
            # Turn to "DOWN" when all cars are idle
            allhome = True
            allIdle = True
            for c in self.cars:
                if c.pos != c.home:
                    allhome = False
                if c.state != "idle":
                    allIdle = False
            if allhome:
                return
            if allIdle:     # All cars have serviced the passengers in this direction.
                # execute shaft direction flip
                self.dir = DN
                xprint("%6.1f %d TURN: %s" % (self.s.now,self.id,DIR[self.dir]),self.s.dbg)
                for c in self.cars:
                    c.calls[c.home,1-self.dir] = 2  #TODO: Check what '2' is.     # This makes sure that each car has a destination of homing floor.
                    if c.here():
                        c.next('open',0)
                    else:
                        c.next('close',0)
        else:
            # Turn to "UP" when all cars are back home
            for c in self.cars:     # IMPORTANT: Before direction change to UP, all cars must go to ground floor.
                if c.pos != c.home:
                    return
            # execute shaft direction flip1):
            self.dir = UP
            xprint("%6.1f TURN: %s" % (self.s.now,DIR[self.dir]),self.s.dbg)
            for c in self.cars:
                c.next('close',0)

if __name__ == "__main__":
    import argparse

    # Construct the argument parser
    parser = argparse.ArgumentParser()

    # Add the arguments to the parser
    parser.add_argument('--dbg', action='store_true',default=dbg)
    parser.add_argument('--trc', action='store_true',default=trc)
    parser.add_argument('--wtp', action='store_true',default=wtp)
    parser.add_argument('--wts', action='store_true',default=wts)
    parser.add_argument('--dmp', action='store_true',default=dmp)
    parser.add_argument('--sta', action='store_true',default=sta)
    parser.add_argument('--pre', action='store_true',default=pre)
    parser.add_argument('--end', action='store', default=1800)
    parser.add_argument('--rate', action='store', default=0.02)
    parser.add_argument('--top', action='store', default=20)
    parser.add_argument('--nshaft', action='store', default=2)
    parser.add_argument('--ncar', action='store', default=3)
    parser.add_argument('--out', action='store',default=None)
    parser.add_argument('--alg', action='store', default="simple")
    parser.add_argument('--rec', action='store', default="rec0")
    parser.add_argument('--anim', action='store_true', default=anim)
    parser.add_argument('--dly', action='store', default=1)
    parser.add_argument('--cap', action='store', default=1)
    parser.add_argument('--trnf', action='store', default=None)
    args = vars(parser.parse_args())
    dbg = args['dbg']
    trc = args['trc']
    wtp = args['wtp']
    wts = args['wts']
    dmp = args['dmp']
    sta = args['sta']
    pre = args['pre']
    end = int(args['end'])
    rate = float(args['rate'])
    top = int(args['top'])
    nshaft = int(args['nshaft'])
    ncar = int(args['ncar'])
    outfile = args['out']
    alg = args['alg']
    rec = args['rec']
    anim = args['anim']
    dly = int(args['dly'])
    cap = int(args['cap'])
    trnf = args['trnf']

    if alg == "nn":
        algorithm = nn_algorithm
        assign = nn_assign
    else:
        exec("from "+alg+" import algorithm")

    exec("from "+rec+" import record")
    seed=1
    sim = simulator(top,nshaft,ncar,seed,end,dbg,trc,wtp,wts,dmp,sta,pre,dly,cap,trnf)
    sim.algorithm = algorithm
    t1=traffic(sim,rate)
    cl=clock(sim,1)
    #if dmp:
    #    simulator.run(end=end)
    #else:
    #    while simulator.now < end:
    #       simulator.run()
    if anim:
        sim.gui.frame()
        sim.run_again()
        sim.gui.tk.mainloop()
    else:
        sim.go()

    if not anim and (dmp or trc):
        if outfile:
            sim.gui.cv.postscript(file=outfile, colormode='color')
        sim.gui.tk.mainloop()

