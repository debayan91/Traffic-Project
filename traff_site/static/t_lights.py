from tkinter import *
import random

lights = Tk()
lights.title("Traffic Lights")
lights.geometry("1000x400+200+200")
lights.resizable(False,False)
lights.config(bg="#4ea6a1")

canvas=Canvas(lights,height=400,width=1000,bg="White")
canvas.pack()

t1=canvas.create_rectangle(100,50,200,350,fill="Black")
t2=canvas.create_rectangle(300,50,400,350,fill="Black")
t3=canvas.create_rectangle(500,50,600,350,fill="Black")
t4=canvas.create_rectangle(700,50,800,350,fill="Black")

g1=canvas.create_oval(100,50,200,150,fill="green")
y1=canvas.create_oval(100,150,200,250,fill="yellow")
r1=canvas.create_oval(100,250,200,350,fill="red")

g2=canvas.create_oval(300,50,400,150,fill="green")
y2=canvas.create_oval(300,150,400,250,fill="yellow")
r2=canvas.create_oval(300,250,400,350,fill="red")

g3=canvas.create_oval(500,50,600,150,fill="green")
y3=canvas.create_oval(500,150,600,250,fill="yellow")
r3=canvas.create_oval(500,250,600,350,fill="red")

g4=canvas.create_oval(700,50,800,150,fill="green")
y4=canvas.create_oval(700,150,800,250,fill="yellow")
r4=canvas.create_oval(700,250,800,350,fill="red")

canvas.itemconfig(r1,fill="darkgray")
canvas.itemconfig(y1,fill="darkgray")

canvas.itemconfig(g2,fill="darkgray")
canvas.itemconfig(y2,fill="darkgray")

canvas.itemconfig(g3,fill="darkgray")
canvas.itemconfig(y3,fill="darkgray")

canvas.itemconfig(g4,fill="darkgray")
canvas.itemconfig(y4,fill="darkgray")

times=[15,18,20,12]
greens=[g1,g2,g3,g4]
reds=[r1,r2,r3,r4]
yellows=[y1,y2,y3,y4]
lanes=[2,0,0,0]
curr_green=0
while True:
    Label(lights, text=f"Timer : {times[0]}", bg="black", fg="white").place(x=125, y=360)
    Label(lights, text=f"Timer : {times[1]}", bg="black", fg="white").place(x=325, y=360)
    Label(lights, text=f"Timer : {times[2]}", bg="black", fg="white").place(x=525, y=360)
    Label(lights, text=f"Timer : {times[3]}", bg="black", fg="white").place(x=725, y=360)
    lights.update()
    lights.after(times[curr_green]*100)
    canvas.itemconfig(greens[curr_green],fill="darkgray")
    canvas.itemconfig(yellows[curr_green],fill="yellow")
    lights.update()
    lights.after(int(times[curr_green]*100/5))
    canvas.itemconfig(yellows[curr_green],fill="darkgray")
    maxind=times.index(max(times))
    canvas.itemconfig(greens[maxind],fill="green")
    canvas.itemconfig(reds[maxind],fill="darkgray")
    curr_green=maxind
    for i in range(0,4):
        if(i!=maxind):
            canvas.itemconfig(reds[i],fill="red")
    for i in range(0,4):
        times[i]=random.randint(10,30)
    lights.update()

        


lights.mainloop()