import random,math
UP = 0
DN = 1
DIR = ("UP","DN")


def assign(sim,s,p):
        # Cheesy call assignment
        x = max(p.arr,p.dest)
        for i in range(s.ncars):
            if x <= sim.zones[i]:
                break
        c = s.cars[i]
        #xprint("%6.1f assign (%d,%d) to %d" % (s.now,p.arr,p.dest,c.id),dbg)
        return c

def dist(sim,c,p):
    d = 0
    if c.shaft.dir == UP:
        if p.dir == UP:
            if p.arr >= c.pos:
                d = p.arr - c.pos
            else:
                d = 2*sim.top - (c.pos - p.arr)
        else: # p: DOWN
            d = 2*sim.top - c.pos - p.arr
    else: # c: DOWN
        if p.dir == DN:
            if p.arr <= c.pos:
                d = c.pos - p.arr
            else:
                d = 2*sim.top - (p.arr - c.pos)
        else: # UP
            d = c.pos + p.arr
    return d

def algorithm(simulation,p):
    wmin = 999
    cmin = 0
    for s in simulation.shafts: 
        c = assign(simulation,s,p)
        w = dist(simulation,c,p)
        if w < wmin:
            wmin = w
            cmin = c
    return cmin


