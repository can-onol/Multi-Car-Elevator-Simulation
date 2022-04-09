from tkinter import *


class gui:        
    def __init__(self,simulator):
        self.tk = Tk()
        self.colors = ("red","salmon","orange","yellow","green","cyan","blue","purple","magenta")
        self.s = simulator
        self.W = 32
        self.H = 16
        self.D = 2
        self.x = 0
        if self.s.dmp or self.s.trc:
            self.height = self.s.nshafts * 2 * (self.s.top + 2) * (self.s.ncars + 1)
            self.width = self.s.end
        else:
            self.height = self.H * (self.s.top + 2)
            self.width = self.W * (2*self.s.nshafts+1)
        self.cv=Canvas(self.tk,width=self.width,height=self.height)
        self.cv.pack()
        if self.s.anim:
            self.frame()
            for a in self.s.sys:
                if a.type=="cage":
                    a.init_gpos()
 
    def frame(self):
        dW = self.W
        dw = self.W/3
        dH = self.H
        self.cv.create_rectangle(0,0,self.width,self.height,outline="black")
        for i in range(self.s.top+1):
            p = (i+1)*dH
            x = 0
            for j in range(self.s.nshafts+1):
                #self.cv.create_rectangle(x,dH,x+dW,self.height-dH,outline="black",fill="grey")
                self.cv.create_line(x,p,x+dw,p)
                x = x+dw
                self.cv.create_rectangle(x,dH,x+dW,self.height-dH,outline="black")
                x = x+dW

    def gpos(self,i,j):
        """
        Create the cage marks on the GUI
        """
        dW = self.W
        dw = self.W/3
        dH = self.H
        x = dw+i*(dw+dW)
        y = self.height - dH*(2+j)
        dd = self.D
        p = self.cv.create_rectangle(x+dd,y+dd,x+dW-dd,y+dH-dd,fill=self.colors[j])
        return p
            

    def update(self):
        """
        For each clock tick, update the cage positions
        """
        for a in self.s.sys:
            if a.type=="cage":
                if a.lastpos != a.pos:
                    #print("move %d from %d to %d" % (a.id,a.lastpos,a.pos))
                    self.cv.move(a.gpos,0,self.H*(a.lastpos-a.pos))
                    a.lastpos = a.pos
        self.tk.update()                

    def dump(self):
        """
        For each clock tick, dump the full system status on a Tkinter screen.
        Currently passengers are shown only with their calls, not with their
        status (waiting, riding). We should show O/D matrices for a full dump.
        """
        global screen,clock
        self.x = self.x+1
        self.y = self.height-2
        
        for a in self.s.sys:
            if a.type=="cage":
                for i in range(a.s.top):
                    if a.pos == i:
                        self.cv.create_rectangle(self.x,self.y,self.x+1,self.y+1,outline="black")
                    self.y = self.y-1
                if (self.s.now%10)==0 and (self.s.now%100)!=0:
                    self.cv.create_rectangle(self.x,self.y,self.x+1,self.y+1,outline="gray")
                self.y = self.y-1
                for i in range(a.s.top):
                    if a.calls[i,0]==1:
                        self.cv.create_rectangle(self.x,self.y,self.x+1,self.y+1,outline="blue")
                    self.y = self.y-1
                if (self.s.now%10)==0 and (self.s.now%100)!=0:
                    self.cv.create_rectangle(self.x,self.y,self.x+1,self.y+1,outline="gray")
                for i in range(a.s.top):
                    if a.calls[i,1]==1:
                        self.cv.create_rectangle(self.x,self.y,self.x+1,self.y+1,outline="red")
                    self.y = self.y-1
                self.cv.create_rectangle(self.x,self.y,self.x+2,self.y+2,outline="green")
        self.tk.update()                

        
