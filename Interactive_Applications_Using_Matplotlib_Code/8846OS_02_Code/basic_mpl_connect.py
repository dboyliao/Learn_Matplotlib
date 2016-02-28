from __future__ import print_function
import matplotlib.pyplot as plt

def process_key(event):
    print("Key:", event.key)

def process_button(event):
    print("Button:", event.x, event.y, event.xdata, event.ydata, event.button)

fig, ax = plt.subplots(1, 1)
fig.canvas.mpl_connect('key_press_event', process_key)
fig.canvas.mpl_connect('button_press_event', process_button)
plt.show()
