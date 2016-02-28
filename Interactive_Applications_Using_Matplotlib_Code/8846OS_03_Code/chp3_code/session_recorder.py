from contextlib import contextmanager
from matplotlib.animation import TimedAnimation, MencoderWriter
from matplotlib import rcParams

class SessionAnimation(TimedAnimation):
    def new_frame_seq(self):
        return iter([])

class SessionWriter(MencoderWriter):
    def finish(self):
        pass

@contextmanager
def record_session(filename, interval=100, codec=None, bitrate=None, fig=None):
    if codec is None:
        codec = rcParams['animation.codec']
    if bitrate is None:
        bitrate = rcParams['animation.bitrate']
    if fig is None:
        fig = plt.gcf()
    
    anim = SessionAnimation(fig, interval=interval, repeat=False)
    # writer expects frame rate (not interval) in seconds (not milliseconds)
    writer = SessionWriter(1000.0 / interval, codec, bitrate)

    grabby = lambda *x: writer.grab_frame()
    anim.event_source.add_callback(grabby)
    try:
        anim.save(filename, writer=writer)
        yield fig
    finally:
        writer.cleanup()

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    with record_session('session.mp4') as fig:
        ax = fig.add_subplot(1, 1, 1)
        ax.plot([1, 2, 3, 4, 5])
        plt.show()

