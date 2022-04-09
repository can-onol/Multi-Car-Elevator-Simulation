import random,math

def assign(simulation,s,p):
        # Cheesy call assignment
        x = max(p.arr,p.dest)
        for i in range(s.ncars):
            if x <= simulation.zones[i]:
                break
        c = s.cars[i]
        #xprint("%6.1f assign (%d,%d) to %d" % (s.now,p.arr,p.dest,c.id),dbg)
        return c


def algorithm(simulation,p):
    s = simulation.shafts[random.randint(0,simulation.nshafts-1)]
    c = assign(simulation,s,p)
    return c
