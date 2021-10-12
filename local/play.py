import sys
import traceback
import datetime
from pathlib import Path
from threading import Thread
from mutagen.mp3 import MP3

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib  # noqa:F401,F402

from mediaplayer import MediaPlayer

songqueue = []

# Initializes Gstreamer, it's variables, paths
Gst.init(sys.argv)

#DEFAULT_PIPELINE = "playbin uri=https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm"
DEFAULT_PIPELINE = "filesrc name=src ! decodebin ! autoaudiosink"


# Gst.Pipeline https://lazka.github.io/pgi-docs/Gst-1.0/classes/Pipeline.html
# https://lazka.github.io/pgi-docs/Gst-1.0/functions.html#Gst.parse_launch
pipeline = Gst.parse_launch(DEFAULT_PIPELINE)
pipeline_state = Gst.State.NULL

#filesrc.set_property("location", "../../Desktop/music/classical/chopin/chopin_nocturne_0902.mp3")

# https://lazka.github.io/pgi-docs/Gst-1.0/classes/Bus.html
bus = pipeline.get_bus()

# allow bus to emit messages to main thread
bus.add_signal_watch()

# Start pipeline
# pipeline.set_state(Gst.State.PLAYING)

# Init GLib loop to handle Gstreamer Bus Events
loop = GLib.MainLoop()

def change_song(filename):
    global pipeline
    global filesrc
    global bus
    global loop

    # VERY clunky solution!! Do NOT do this even short term!
    set_pipeline_state(Gst.State.NULL)
    pipeline = Gst.parse_launch(DEFAULT_PIPELINE)
    filesrc = pipeline.get_by_name("src")

    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", on_message, loop)

    filesrc.set_property("location", filename)

def set_pipeline_state(state):
    global pipeline
    global pipeline_state

    pipeline.set_state(state)
    pipeline_state = state

def on_message(bus, message, loop):
    global songqueue
    global pipeline_state

    mtype = message.type
    """
        Gstreamer Message Types and how to parse
        https://lazka.github.io/pgi-docs/Gst-1.0/flags.html#Gst.MessageType
    """
    if mtype == Gst.MessageType.EOS:
        if len(songqueue) == 1:
            songqueue.pop(0)
            set_pipeline_state(Gst.State.NULL)
        else:
            songqueue.pop(0)
            oldstate = pipeline_state
            change_song(songqueue[0][0])
            set_pipeline_state(oldstate)

    elif mtype == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(err, debug)
        loop.quit()

    elif mtype == Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        print(err, debug)

    return True

# Add handler to specific signal
# https://lazka.github.io/pgi-docs/GObject-2.0/classes/Object.html#GObject.Object.connect
bus.connect("message", on_message, loop)

# very useful at the moment
def terminal_thread():
    global filesrc
    global pipeline
    global songqueue

    running = True
    while running:
        command = input("> ")
        parts = command.split(" ")

        if parts[0] == "quit":
            running = False
            set_pipeline_state(Gst.State.NULL)
            loop.quit()
        elif parts[0] == "pause":
            if len(songqueue) > 0:
                set_pipeline_state(Gst.State.PAUSED)
            else:
                print("No song to pause.")
        elif parts[0] == "play":
            if len(songqueue) > 0:
                set_pipeline_state(Gst.State.PLAYING)
            else:
                print("No song to play.")
        elif parts[0] == "skip":
            if len(songqueue) == 0:
                print("No song to skip.")
            elif len(songqueue) == 1:
                songqueue.pop(0)
                set_pipeline_state(Gst.State.NULL)
            else:
                songqueue.pop(0)
                oldstate = pipeline_state
                change_song(songqueue[0][0])
                set_pipeline_state(oldstate)
        elif parts[0] == "restart":
            print("This command has not yet been implemented.")
        elif parts[0] == "scrub":
            print("This command has not yet been implemented.")
        elif parts[0] == "add":
            if len(parts) != 2 or parts[1] == '':
                print("Usage: add [path name]")
                continue

            # first check if path even exists
            path = Path(parts[1])
            if not path.exists():
                print("Unable to find file or directory: " + parts[1])
                continue

            if len(songqueue) == 0:
                change_song(parts[1])

            songqueue.append( (parts[1], MP3(parts[1]).info.length) )
        elif parts[0] == "queue":
            if len(songqueue) == 0:
                print("The queue is currently empty.")
            else:
                for i in range(len(songqueue)):
                    songpath = Path(songqueue[i][0])
                    songname = songpath.parent.name + "/" + songpath.stem
                    print(str(i) + ". " + songname + ", (" + str(datetime.timedelta(seconds=songqueue[i][1]))[2:7] + ")")
        elif parts[0] == "status":
            if len(songqueue) == 0:
                print("No song is currently playing.")
            else:
                print("The current song is at " + str(datetime.timedelta(seconds=pipeline.query_position(Gst.Format.TIME)[1] / 1000000000.0)) + " seconds.")
        elif parts[0] == "remove":
            print("This command has not yet been implemented.")
        elif parts[0] == "shuffle":
            print("This command has not yet been implemented.")
        elif parts[0] == "help":
            print("This command has not yet been implemented.")
        else:
            print("Invalid command: " + command)
            print("Enter 'help' for list of available commands.")

thread = Thread(target=terminal_thread)
thread.start()

try:
    loop.run()
except Exception:
    traceback.print_exc()
    loop.quit()

thread.join()
# Stop Pipeline
set_pipeline_state(Gst.State.NULL)