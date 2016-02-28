from __future__ import print_function
import matplotlib.pyplot as plt

def process_key(event):
    print(event.key)

fig, ax = plt.subplots(1, 1)
fig.canvas.mpl_connect('key_press_event', process_key)
fig.canvas.mpl_disconnect(fig.canvas.manager.key_press_handler_id)
plt.show()
