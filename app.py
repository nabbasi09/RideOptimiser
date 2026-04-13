import tkinter as tk
from tkinter import ttk, messagebox
import heapq, math, json, os, random
from datetime import datetime
from enum import Enum, auto

AVG_SPEED = 80
BASE_FARE = 50
PER_KM    = 8
PER_MIN   = 1.5
ANIM_MS   = 350
HISTORY_F = "ride_history.json"

BG   = "#0B1A2B"; CARD = "#0F2538"; MID  = "#152D42"
ACC  = "#F97316"; BLUE = "#38BDF8"; TEXT = "#F0F4F8"
DIM  = "#8BA4B8"; GRN  = "#4ADE80"; YEL  = "#FBBF24"; RED = "#F87171"

class Graph:
    def __init__(self): self.nodes={}; self.edges={}
    def add_node(self,n,x,y): self.nodes[n]=(x,y)
    def add_edge(self,u,v,km): self.edges[(u,v)]=km; self.edges[(v,u)]=km
    def neighbors(self,n): return [v for u,v in self.edges if u==n]
    def km(self,u,v): return self.edges.get((u,v),float('inf'))
    def h(self,a,b):
        x1,y1=self.nodes[a]; x2,y2=self.nodes[b]
        return math.hypot(x2-x1,y2-y1)*0.55

def build_graph():
    g=Graph()
    for c,(x,y) in {"Mumbai":(130,430),"Delhi":(340,140),"Bengaluru":(345,550),
        "Kolkata":(620,300),"Chennai":(460,570),"Hyderabad":(390,425),
        "Pune":(185,470),"Ahmedabad":(225,300),"Jaipur":(300,235),
        "Nagpur":(400,350),"Lucknow":(440,200),"Bhopal":(355,295)}.items():
        g.add_node(c,x,y)
    for u,v,d in [
        ("Mumbai","Pune",150),("Mumbai","Ahmedabad",524),("Mumbai","Nagpur",830),
        ("Mumbai","Hyderabad",710),("Mumbai","Bengaluru",981),
        ("Delhi","Jaipur",281),("Delhi","Lucknow",555),("Delhi","Ahmedabad",943),
        ("Delhi","Bhopal",770),("Delhi","Kolkata",1453),
        ("Bengaluru","Chennai",346),("Bengaluru","Hyderabad",570),("Bengaluru","Pune",840),
        ("Kolkata","Hyderabad",1192),("Kolkata","Lucknow",992),("Kolkata","Nagpur",1050),
        ("Hyderabad","Chennai",626),("Hyderabad","Nagpur",497),("Hyderabad","Bhopal",688),
        ("Pune","Hyderabad",560),("Ahmedabad","Jaipur",660),("Ahmedabad","Bhopal",552),
        ("Jaipur","Lucknow",592),("Jaipur","Bhopal",614),
        ("Nagpur","Bhopal",357),("Lucknow","Bhopal",650),("Chennai","Kolkata",1659)]:
        g.add_edge(u,v,d)
    return g

def astar(graph,start,end,speed,avoid=None):
    if start==end: return [start],0.0
    blocked=set(avoid or [])
    def hh(n): return graph.h(n,end)/speed
    heap=[(hh(start),0.0,start,[start])]; best={start:0.0}
    while heap:
        _,g,node,path=heapq.heappop(heap)
        if node==end: return path,g
        if g>best.get(node,float('inf')): continue
        for nei in graph.neighbors(node):
            if nei in blocked and nei!=end: continue
            ng=g+graph.km(node,nei)/speed
            if ng<best.get(nei,float('inf')):
                best[nei]=ng; heapq.heappush(heap,(ng+hh(nei),ng,nei,path+[nei]))
    return [start,end],float('inf')

def dijkstra(graph,start,end):
    if start==end: return [start],0.0
    heap=[(0.0,start,[start])]; seen={}
    while heap:
        cost,node,path=heapq.heappop(heap)
        if node in seen: continue
        seen[node]=cost
        if node==end: return path,cost
        for nei in graph.neighbors(node):
            d=graph.km(node,nei)
            if d<float('inf'): heapq.heappush(heap,(cost+d,nei,path+[nei]))
    return [start,end],float('inf')

def get_route(graph,start,end,pref,traffic,avoid=None):
    if start==end: return [start],0,0
    speed=AVG_SPEED/traffic
    _,km=dijkstra(graph,start,end)
    if pref in("Fastest","Avoid tolls"):
        path,hours=astar(graph,start,end,speed,avoid)
    elif pref=="Eco-friendly":
        path,_=dijkstra(graph,start,end); hours=km/(speed*0.9)
    else:
        path,_=dijkstra(graph,start,end); hours=km/speed
    return path,round(km),round(hours*60)

def calc_fare(km,eta,surge,pax):
    return int((BASE_FARE+km*PER_KM+eta*PER_MIN)*surge*(1+(pax-1)*0.15))

class St(Enum): IDLE=auto(); TO_PU=auto(); TO_DO=auto()

class Driver:
    def __init__(self,name,city,color):
        self.name=name; self.city=city; self.color=color
        self.state=St.IDLE; self.rating=4.8; self.trips=0; self.earned=0
        self.path=[]; self.pidx=0; self.pu=self.do=None
    @property
    def available(self): return self.state==St.IDLE
    @property
    def status(self):
        return {St.IDLE:"🟢 Available",St.TO_PU:f"🟡 → {self.pu}",
                St.TO_DO:f"🔵 → {self.do}"}[self.state]

class Surge:
    def __init__(self): self.active=0; self.rush=False
    @property
    def mult(self):
        m=2.0 if self.active>=6 else 1.6 if self.active>=4 else 1.3 if self.active>=2 else 1.0
        return round(min(m*(1.25 if self.rush else 1.0),2.5),2)
    @property
    def label(self):
        m=self.mult
        if m>=2.0: return f"🔴 Surge ×{m}",RED
        elif m>=1.5: return f"🟠 High ×{m}","#FFA500"
        elif m>1.0: return f"🟡 Moderate ×{m}",YEL
        return "🟢 Normal ×1.0",GRN

class App:
    def __init__(self,root):
        self.root=root
        root.title("RideOptimiser – Indian Cities")
        root.geometry("1600x950"); root.configure(bg=BG); root.minsize(1300,750)
        self.graph=build_graph(); self.cities=sorted(self.graph.nodes)
        self.drivers=[Driver("Arjun Singh","Mumbai","#E74C3C"),
                      Driver("Priya Sharma","Delhi","#3498DB"),
                      Driver("Ravi Kumar","Bengaluru","#F39C12"),
                      Driver("Neha Patel","Ahmedabad","#9B59B6")]
        self.surge=Surge(); self.queue=[]; self.history=[]
        self.cur_driver=None; self.cur_booking=None; self.route_path=[]
        self.v_pu=tk.StringVar(value="Delhi"); self.v_do=tk.StringVar(value="Mumbai")
        self.v_pref=tk.StringVar(value="Fastest"); self.v_pax=tk.IntVar(value=1)
        self.v_rush=tk.BooleanVar(value=False); self.v_avoid=tk.StringVar(value="None")
        self._build_ui(); self._load_history(); self._refresh()

    def _card(self,parent,title,expand=False):
        f=tk.Frame(parent,bg=CARD,highlightthickness=1,highlightbackground=MID)
        f.pack(fill=tk.BOTH if expand else tk.X,expand=expand,pady=(0,6))
        tk.Label(f,text=title,bg=CARD,fg=ACC,font=("Segoe UI",11,"bold")).pack(anchor="w",padx=12,pady=(10,4))
        return f

    def _lbl(self,parent,text):
        tk.Label(parent,text=text,bg=CARD,fg=DIM,font=("Segoe UI",9,"bold")).pack(anchor="w",padx=12,pady=(6,1))

    def _btn(self,parent,text,cmd,bg=BLUE,fg="white",bold=False,padx=14):
        b=tk.Button(parent,text=text,command=cmd,bg=bg,fg=fg,relief="flat",
                  font=("Segoe UI",10,"bold" if bold else "normal"),
                  padx=padx,pady=8,cursor="hand2",
                  activebackground=bg,activeforeground=fg,
                  highlightthickness=0,bd=0)
        b.pack(side=tk.LEFT,padx=(0,8),pady=4)

    def _build_ui(self):
        bar=tk.Frame(self.root,bg=CARD,height=50); bar.pack(fill=tk.X); bar.pack_propagate(False)
        tk.Label(bar,text="🚖  RideOptimiser",bg=CARD,fg=ACC,font=("Segoe UI",15,"bold")).pack(side=tk.LEFT,padx=18)
        tk.Label(bar,text="Indian Cities · A* Routing · Smart Surge",bg=CARD,fg=DIM,font=("Segoe UI",10)).pack(side=tk.LEFT)
        self.lbl_q=tk.Label(bar,text="",bg=CARD,fg=DIM,font=("Segoe UI",9)); self.lbl_q.pack(side=tk.RIGHT,padx=18)

        body=tk.Frame(self.root,bg=BG); body.pack(fill=tk.BOTH,expand=True)

        # LEFT
        left=tk.Frame(body,bg=BG,width=295); left.pack(side=tk.LEFT,fill=tk.Y,padx=(8,4),pady=8); left.pack_propagate(False)
        rc=self._card(left,"🚖  Ride Details")
        self._lbl(rc,"Pickup")
        pu=ttk.Combobox(rc,textvariable=self.v_pu,values=self.cities,state="readonly",font=("Segoe UI",10))
        pu.pack(fill=tk.X,padx=12,pady=2); pu.bind("<<ComboboxSelected>>",lambda _:self._refresh())
        self._lbl(rc,"Dropoff")
        do=ttk.Combobox(rc,textvariable=self.v_do,values=self.cities,state="readonly",font=("Segoe UI",10))
        do.pack(fill=tk.X,padx=12,pady=2); do.bind("<<ComboboxSelected>>",lambda _:self._refresh())
        self._lbl(rc,"Passengers")
        pf=tk.Frame(rc,bg=CARD); pf.pack(anchor="w",padx=12,pady=2)
        for n in(1,2,3,4): ttk.Radiobutton(pf,text=str(n),variable=self.v_pax,value=n,command=self._refresh).pack(side=tk.LEFT,padx=4)
        self._lbl(rc,"Route Preference")
        for pr,ic in [("Fastest","🚀"),("Eco-friendly","🌿"),("Avoid tolls","🚧")]:
            ttk.Radiobutton(rc,text=f"{ic} {pr}",variable=self.v_pref,value=pr,command=self._refresh).pack(anchor="w",padx=14,pady=1)
        self._lbl(rc,"Avoid City")
        av=ttk.Combobox(rc,textvariable=self.v_avoid,values=["None"]+self.cities,state="readonly",font=("Segoe UI",10))
        av.pack(fill=tk.X,padx=12,pady=2); av.bind("<<ComboboxSelected>>",lambda _:self._refresh())
        bf=tk.Frame(rc,bg=CARD); bf.pack(fill=tk.X,padx=12,pady=10)
        self._btn(bf,"📍Check Route",self._check,bg="#1E6091",fg="black")
        self._btn(bf,"🚀  Book Ride",self._book,bg=ACC,fg="black")

        ef=self._card(left,"⏱️  ETA & Fare")
        self.lbl_eta=tk.Label(ef,text="-- min",bg=CARD,fg=BLUE,font=("Segoe UI",26,"bold")); self.lbl_eta.pack(anchor="w",padx=12,pady=(2,0))
        self.lbl_fare=tk.Label(ef,text="₹ --",bg=CARD,fg=GRN,font=("Segoe UI",18,"bold")); self.lbl_fare.pack(anchor="w",padx=12)
        self.lbl_km=tk.Label(ef,text="",bg=CARD,fg=DIM,font=("Segoe UI",9)); self.lbl_km.pack(anchor="w",padx=12,pady=(0,8))

        tc=self._card(left,"🚦  Traffic")
        self.lbl_surge=tk.Label(tc,text="🟢 Normal ×1.0",bg=CARD,fg=GRN,font=("Segoe UI",10,"bold")); self.lbl_surge.pack(anchor="w",padx=12,pady=(2,4))
        ttk.Checkbutton(tc,text="Rush Hour (+25% travel time)",variable=self.v_rush,command=self._toggle_rush).pack(anchor="w",padx=12,pady=(0,8))

        hc=self._card(left,"📜  Ride History",expand=True)
        self.hist_lb=tk.Listbox(hc,bg="#07111D",fg=TEXT,font=("Courier",8),relief="flat",selectbackground=MID,highlightthickness=0)
        self.hist_lb.pack(fill=tk.BOTH,expand=True,padx=8,pady=(0,8))

        # CENTER map
        center=tk.Frame(body,bg=CARD,highlightthickness=1,highlightbackground=MID)
        center.pack(side=tk.LEFT,fill=tk.BOTH,expand=True,pady=8)
        tk.Label(center,text="🗺️  Live Map   (scroll=zoom · right-drag=pan)",bg=CARD,fg=ACC,font=("Segoe UI",11,"bold")).pack(anchor="w",padx=12,pady=6)
        self.canvas=tk.Canvas(center,bg="#07111D",highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH,expand=True,padx=8,pady=(0,8))
        self._sc=1.0; self._ox=0.0; self._oy=0.0; self._px=self._py=0
        self.canvas.bind("<MouseWheel>",self._zoom); self.canvas.bind("<Button-4>",self._zoom); self.canvas.bind("<Button-5>",self._zoom)
        self.canvas.bind("<ButtonPress-3>",self._ps); self.canvas.bind("<B3-Motion>",self._pm)
        self.canvas.bind("<ButtonPress-2>",self._ps); self.canvas.bind("<B2-Motion>",self._pm)

        # RIGHT
        right=tk.Frame(body,bg=BG,width=335); right.pack(side=tk.RIGHT,fill=tk.Y,padx=(4,8),pady=8); right.pack_propagate(False)
        self.drv_card=self._card(right,"🚗  Drivers")
        lc=self._card(right,"📟  Event Log",expand=True)
        inn=tk.Frame(lc,bg=CARD); inn.pack(fill=tk.BOTH,expand=True,padx=8)
        self.log=tk.Text(inn,bg="#07111D",fg=DIM,font=("Courier",8),relief="flat",state=tk.DISABLED,wrap=tk.WORD)
        sb=tk.Scrollbar(inn,command=self.log.yview,bg=MID,troughcolor=CARD,highlightthickness=0)
        self.log.configure(yscrollcommand=sb.set); self.log.pack(side=tk.LEFT,fill=tk.BOTH,expand=True); sb.pack(side=tk.RIGHT,fill=tk.Y)
        tk.Button(lc,text="Clear Log",command=self._clear_log,bg=MID,fg=DIM,font=("Segoe UI",8),relief="flat").pack(pady=6)

        ac=self._card(right,"⭐  Actions")
        rf=tk.Frame(ac,bg=CARD); rf.pack(fill=tk.X,padx=12,pady=4)
        tk.Label(rf,text="Rate ride:",bg=CARD,fg=DIM,font=("Segoe UI",9)).pack(side=tk.LEFT)
        self.v_rating=tk.IntVar(value=0)
        for i in range(1,6): ttk.Radiobutton(rf,text=str(i),variable=self.v_rating,value=i,command=self._rate).pack(side=tk.LEFT,padx=2)
        bf2=tk.Frame(ac,bg=CARD); bf2.pack(fill=tk.X,padx=12,pady=(0,10))
        self._btn(bf2,"📞 Call Driver",self._call,fg="black")
        self._btn(bf2,"❌ Cancel Ride",self._cancel,fg=RED)

    def _w2s(self,x,y): return x*self._sc+self._ox, y*self._sc+self._oy
    def _zoom(self,e):
        f=1.1 if(e.delta>0 or e.num==4) else 0.9
        self._sc*=f; self._ox=e.x-(e.x-self._ox)*f; self._oy=e.y-(e.y-self._oy)*f; self._draw_map()
    def _ps(self,e): self._px,self._py=e.x,e.y
    def _pm(self,e):
        self._ox+=e.x-self._px; self._oy+=e.y-self._py; self._px,self._py=e.x,e.y; self._draw_map()

    def _draw_map(self):
        c=self.canvas; c.delete("all"); g=self.graph
        pu,do=self.v_pu.get(),self.v_do.get()
        drawn=set()
        for(u,v),km in g.edges.items():
            if(v,u) in drawn: continue
            drawn.add((u,v))
            x1,y1=self._w2s(*g.nodes[u]); x2,y2=self._w2s(*g.nodes[v])
            c.create_line(x1,y1,x2,y2,fill="#1E3A52",width=1.5)
            c.create_text((x1+x2)/2,(y1+y2)/2-8,text=str(km),fill="#2A4060",font=("Segoe UI",7))
        if len(self.route_path)>=2:
            pts=[]
            for city in self.route_path: pts.extend(self._w2s(*g.nodes[city]))
            c.create_line(pts,fill=BLUE,width=4)
        R=12
        for city,(wx,wy) in g.nodes.items():
            sx,sy=self._w2s(wx,wy); sel=city in(pu,do)
            c.create_oval(sx-R-2,sy-R-2,sx+R+2,sy+R+2,fill=ACC if sel else BLUE,outline="")
            c.create_oval(sx-R,sy-R,sx+R,sy+R,fill=ACC if sel else "#1E4A6E",outline=ACC if sel else BLUE,width=2)
            c.create_text(sx,sy,text=city[0],fill="white",font=("Segoe UI",9,"bold"))
            c.create_text(sx,sy+R+9,text=city,fill=ACC if sel else DIM,font=("Segoe UI",8,"bold" if sel else "normal"))
        for label,city,col in[("P",pu,GRN),("D",do,RED)]:
            if city in g.nodes:
                sx,sy=self._w2s(*g.nodes[city])
                c.create_oval(sx+R-1,sy-R-10,sx+R+15,sy-R+4,fill=col,outline="")
                c.create_text(sx+R+7,sy-R-3,text=label,fill="white",font=("Segoe UI",7,"bold"))
        DR=9
        for d in self.drivers:
            if d.city not in g.nodes: continue
            sx,sy=self._w2s(*(g.nodes[d.city][0]+5,g.nodes[d.city][1]-5))
            c.create_oval(sx-DR,sy-DR,sx+DR,sy+DR,fill=d.color,outline="white",width=1.5)
            c.create_text(sx,sy,text=d.name[0],fill="white",font=("Segoe UI",7,"bold"))
            c.create_text(sx,sy-DR-7,text=d.name.split()[0],fill=d.color,font=("Segoe UI",7))

    def _refresh(self):
        pu,do=self.v_pu.get(),self.v_do.get()
        tf=1.8 if self.v_rush.get() else 1.0
        av=[self.v_avoid.get()] if self.v_avoid.get()!="None" else None
        self.route_path,km,eta=get_route(self.graph,pu,do,self.v_pref.get(),tf,av)
        fare=calc_fare(km,eta,self.surge.mult,self.v_pax.get())
        if pu==do:
            self.lbl_eta.config(text="0 min"); self.lbl_fare.config(text="₹ 50"); self.lbl_km.config(text="Same city")
        else:
            self.lbl_eta.config(text=f"{eta} min"); self.lbl_fare.config(text=f"₹ {fare:,}")
            via=" → ".join(self.route_path[1:-1]) if len(self.route_path)>2 else "direct"
            self.lbl_km.config(text=f"{km} km  |  via {via}")
        lbl,col=self.surge.label; self.lbl_surge.config(text=lbl,fg=col)
        self.lbl_q.config(text=f"Queue: {len(self.queue)}  |  Active: {sum(1 for d in self.drivers if not d.available)}")
        self._draw_map(); self._refresh_drivers()

    def _refresh_drivers(self):
        for w in self.drv_card.winfo_children()[1:]: w.destroy()
        tf=1.8 if self.v_rush.get() else 1.0; pu=self.v_pu.get()
        for d in self.drivers:
            row=tk.Frame(self.drv_card,bg=MID if not d.available else CARD)
            row.pack(fill=tk.X,padx=8,pady=2)
            tk.Label(row,text="●",bg=row["bg"],fg=d.color,font=("Segoe UI",14)).pack(side=tk.LEFT,padx=(6,4),pady=4)
            info=tk.Frame(row,bg=row["bg"]); info.pack(side=tk.LEFT,fill=tk.X,expand=True,pady=4)
            tk.Label(info,text=d.name,bg=row["bg"],fg=TEXT,font=("Segoe UI",9,"bold")).pack(anchor="w")
            tk.Label(info,text=d.status,bg=row["bg"],fg=DIM,font=("Segoe UI",8)).pack(anchor="w")
            right=tk.Frame(row,bg=row["bg"]); right.pack(side=tk.RIGHT,padx=6,pady=4)
            if d.available and pu in self.graph.nodes:
                _,_,eta=get_route(self.graph,d.city,pu,"Fastest",tf)
                tk.Label(right,text=f"{eta} min",bg=row["bg"],fg=YEL,font=("Segoe UI",9,"bold")).pack(anchor="e")
            tk.Label(right,text=f"⭐{d.rating:.1f}  {d.trips}▲",bg=row["bg"],fg=DIM,font=("Segoe UI",8)).pack(anchor="e")

    def _toggle_rush(self):
        self.surge.rush=self.v_rush.get(); self._refresh()
        self._log(f"Rush Hour {'ON' if self.v_rush.get() else 'OFF'}","warn")

    def _check(self):
        pu,do=self.v_pu.get(),self.v_do.get()
        if pu==do: messagebox.showinfo("Route","Same city."); return
        tf=1.8 if self.v_rush.get() else 1.0
        av=[self.v_avoid.get()] if self.v_avoid.get()!="None" else None
        path,km,eta=get_route(self.graph,pu,do,self.v_pref.get(),tf,av)
        algo="A*" if self.v_pref.get() in("Fastest","Avoid tolls") else "Dijkstra"
        messagebox.showinfo("Route Info",
            f"Algorithm : {algo}\nRoute     : {' → '.join(path)}\n"
            f"Distance  : {km} km\nETA       : {eta} min  ({eta/60:.1f} hrs)\n"
            f"Traffic   : {'Rush Hour ×1.8' if tf>1 else 'Normal'}")
        self._log(f"Route: {pu}→{do}  {km} km  {eta} min  [{algo}]")

    def _book(self):
        pu,do=self.v_pu.get(),self.v_do.get()
        if pu==do: messagebox.showerror("Error","Same city."); return
        avail=[d for d in self.drivers if d.available]
        if not avail:
            self.queue.append((pu,do,self.v_pref.get(),self.v_pax.get()))
            self._log(f"All busy — queued ({len(self.queue)} waiting)","warn")
            self._refresh(); return
        tf=1.8 if self.v_rush.get() else 1.0
        _,km,eta=get_route(self.graph,pu,do,self.v_pref.get(),tf)
        fare=calc_fare(km,eta,self.surge.mult,self.v_pax.get())
        best=min(avail,key=lambda d:get_route(self.graph,d.city,pu,"Fastest",tf)[2])
        best.pu=pu; best.do=do; best.state=St.TO_PU
        self.cur_driver=best; self.cur_booking=(pu,do,fare)
        self.surge.active+=1
        self._log(f"Booked: {pu}→{do}  ₹{fare:,} ({self.v_pax.get()} pax)  → {best.name}  ETA {eta} min  ×{self.surge.mult}","book")
        self._animate(best,pu,do,fare)

    def _animate(self,driver,pu,do,fare):
        tf=1.8 if self.v_rush.get() else 1.0
        av=[self.v_avoid.get()] if self.v_avoid.get()!="None" else None
        path1,_,_=get_route(self.graph,driver.city,pu,"Fastest",tf,av)
        if len(path1)<=1: self._begin_do(driver,pu,do,fare,tf,av); return
        driver.path=path1; driver.pidx=0
        self._step(driver,pu,do,fare,tf,av,True)

    def _step(self,driver,pu,do,fare,tf,av,to_pu):
        if driver.pidx>=len(driver.path)-1:
            if to_pu:
                driver.city=pu; self._log(f"{driver.name} arrived at {pu}.","ok")
                self._begin_do(driver,pu,do,fare,tf,av)
            else:
                driver.city=do; driver.state=St.IDLE; driver.trips+=1; driver.earned+=fare
                self.surge.active=max(0,self.surge.active-1)
                self._log(f"{driver.name} completed → {do}.  ₹{fare:,} earned.","ok")
                self._add_history(pu,do,fare,driver.name)
                self._try_queue(); self._refresh()
            return
        driver.pidx+=1; driver.city=driver.path[driver.pidx]
        self._refresh()
        self.root.after(ANIM_MS,lambda:self._step(driver,pu,do,fare,tf,av,to_pu))

    def _begin_do(self,driver,pu,do,fare,tf,av):
        driver.state=St.TO_DO
        path2,_,_=get_route(self.graph,pu,do,"Fastest",tf,av)
        driver.path=path2; driver.pidx=0
        self._step(driver,pu,do,fare,tf,av,False)

    def _try_queue(self):
        if not self.queue: return
        pu,do,pref,pax=self.queue.pop(0)
        self.v_pu.set(pu); self.v_do.set(do); self.v_pref.set(pref); self.v_pax.set(pax)
        self._log(f"Dispatching queued {pu}→{do}…","info")
        self.root.after(600,self._book)

    def _call(self):
        d=self.cur_driver
        if d and not d.available:
            messagebox.showinfo("Call Driver",f"📞 Calling {d.name}…\nAt: {d.city}\n{d.status}"); self._log(f"Called {d.name}.")
        else: messagebox.showinfo("Call Driver","No active driver. Book first.")

    def _cancel(self):
        d=self.cur_driver
        if d and not d.available:
            d.state=St.IDLE; d.path=[]; d.pidx=0
            self.surge.active=max(0,self.surge.active-1)
            self._log("Ride cancelled.","warn"); self.cur_driver=self.cur_booking=None; self._refresh()
        else: messagebox.showinfo("Cancel","No active ride.")

    def _rate(self):
        r=self.v_rating.get()
        if r and self.cur_driver:
            d=self.cur_driver
            d.rating=round((d.rating*max(d.trips,1)+r)/(max(d.trips,1)+1),1)
            self._log(f"You rated {d.name}: {r}⭐","ok"); self._log(f"{d.name} rated you: {random.randint(3,5)}⭐")
            self._refresh_drivers()

    COLORS={"info":DIM,"ok":GRN,"warn":YEL,"book":BLUE,"error":RED}
    def _log(self,msg,typ="info"):
        ts=datetime.now().strftime("[%H:%M:%S]"); col=self.COLORS.get(typ,DIM)
        self.log.configure(state=tk.NORMAL)
        tag=f"t{id(msg)}{datetime.now().microsecond}"
        self.log.insert(tk.END,f"{ts} {msg}\n",tag); self.log.tag_config(tag,foreground=col)
        self.log.configure(state=tk.DISABLED); self.log.see(tk.END)

    def _clear_log(self):
        self.log.configure(state=tk.NORMAL); self.log.delete("1.0",tk.END); self.log.configure(state=tk.DISABLED)

    def _add_history(self,pu,do,fare,driver):
        ts=datetime.now().strftime("%H:%M")
        self.history.append({"time":ts,"pickup":pu,"dropoff":do,"fare":fare,"driver":driver})
        self.hist_lb.insert(0,f"{ts}  {pu[:3]}→{do[:3]}  ₹{fare:,}  {driver.split()[0]}")
        if self.hist_lb.size()>30: self.hist_lb.delete(tk.END)
        try:
            with open(HISTORY_F,"w") as f: json.dump(self.history[-100:],f,indent=2)
        except: pass

    def _load_history(self):
        if not os.path.exists(HISTORY_F): return
        try:
            with open(HISTORY_F) as f: self.history=json.load(f)
            for e in self.history[-15:]:
                self.hist_lb.insert(0,f"{e['time']}  {e['pickup'][:3]}→{e['dropoff'][:3]}  ₹{e['fare']:,}  {e['driver'].split()[0]}")
            self._log(f"Loaded {len(self.history)} past rides.","info")
        except: pass

if __name__=="__main__":
    root=tk.Tk(); App(root); root.mainloop()