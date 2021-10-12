import sys
import datetime
from pathlib import Path
from random import shuffle

from mutagen.mp3 import MP3

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

class MediaPlayer:
    def __init__(self):
        Gst.init(sys.argv)

        self.pipeline = Gst.parse_launch("filesrc name=src ! decodebin ! autoaudiosink")
        self.pipeline_state = Gst.State.NULL

        self.loop = GLib.MainLoop()

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message, self.loop)

        self.songqueue = []
    
    def on_message(self, bus, message, loop):
        mtype = message.type
        """
            Gstreamer Message Types and how to parse
            https://lazka.github.io/pgi-docs/Gst-1.0/flags.html#Gst.MessageType
        """
        if mtype == Gst.MessageType.EOS:
            self.skip()

        elif mtype == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(err, debug)
            loop.quit()

        elif mtype == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            print(err, debug)

        return True
    
    def get_queue_length(self):
        return len(self.songqueue)

    def set_pipeline_state(self, state):
        self.pipeline.set_state(state)
        self.pipeline_state = state

    def run_loop(self):
        self.loop.run()
    
    def change_song(self, filename):
        # VERY clunky solution!! Do NOT do this even short term!
        self.set_pipeline_state(Gst.State.NULL)
        self.pipeline = Gst.parse_launch("filesrc name=src ! decodebin ! autoaudiosink")
        filesrc = self.pipeline.get_by_name("src")

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message, self.loop)

        filesrc.set_property("location", filename)
    
    def quit(self):
        self.set_pipeline_state(Gst.State.NULL)
        self.loop.quit()
    
    def pause(self):
        if len(self.songqueue) > 0:
            self.set_pipeline_state(Gst.State.PAUSED)
        else:
            print("No song to pause.")

    def play(self):
        if len(self.songqueue) > 0:
            self.set_pipeline_state(Gst.State.PLAYING)
        else:
            print("No song to play.")
    
    def skip(self):
        if len(self.songqueue) == 0:
            print("No song to skip")
        elif len(self.songqueue) == 1:
            self.songqueue.pop(0)
            self.set_pipeline_state(Gst.State.NULL)
        else:
            self.songqueue.pop(0)
            oldstate = self.pipeline_state
            self.change_song(self.songqueue[0][0])
            self.set_pipeline_state(oldstate)
    
    def restart(self):
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 0)

    def scrub(self, num_seconds):
        current_time = self.pipeline.query_position(Gst.Format.TIME)[1]
        offset = int(num_seconds * 1000000000)
        new_time = current_time + offset
        if new_time < 0:
            print("Attempting to scrub to time before start of song. Restarting instead.")
            new_time = 0
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, new_time)
        print("The time has been set to " + str(datetime.timedelta(seconds=(new_time)/1000000000.0))[2:7] + " (" + str(int(new_time/1000000000.0)) + " seconds)")
    
    def add(self, path_name, queue_pos=-1):
        # first check if path even exists
        path = Path(path_name)
        if not path.exists():
            print("Unable to find file or directory: " + path_name)
            return
        
        songstoadd = []
        if path.is_file():
            loaded_mp3 = True
            # find length of song with mutagen
            songlen = 0
            try:
                songlen = MP3(path_name).info.length
            except Exception:
                print("Unable to read mp3 header of file " + path_name + " successfully.")
                loaded_mp3 = False

            if loaded_mp3:
                songstoadd.append( (path_name, songlen) )
        else:
            allpaths = path.rglob("*.mp3")
            for song in allpaths:
                # find length of song with mutagen
                songlen = 0
                try:
                    songlen = MP3(str(song)).info.length
                except Exception:
                    print("Unable to read mp3 header of file " + str(song) + " successfully.")
                    continue

                songstoadd.append( (str(song), songlen) )
        
        # all the "songs" got weeded out if this is true
        if (len(songstoadd) == 0):
            return

        if queue_pos > len(self.songqueue):
            print("Requested queue position of " + int(queue_pos) + " is greater " +
            + "than the current length of the queue. Adding to end instead.")
            queue_pos = len(self.songqueue)
        elif queue_pos == -1:
            queue_pos = len(self.songqueue)

        if queue_pos == 0:
            self.change_song(songstoadd[0][0])

        #self.songqueue.insert(queue_pos, (path_name, songlen))
        self.songqueue = self.songqueue[0:queue_pos] + songstoadd + self.songqueue[queue_pos:]
    
    def queue(self):
        if len(self.songqueue) == 0:
            print("The queue is currently empty.")
        else:
            for i in range(len(self.songqueue)):
                songpath = Path(self.songqueue[i][0])
                songname = songpath.parent.name + "/" + songpath.stem
                print(str(i) + ". " + songname + ", (" + str(datetime.timedelta(seconds=self.songqueue[i][1]))[2:7] + ")")
    
    def status(self):
        if len(self.songqueue) == 0:
            print("No song is currently playing.")
        else:
            current_time = self.pipeline.query_position(Gst.Format.TIME)[1] / 1000000000.0

            print("The player is currently " + ("playing." if self.pipeline_state == Gst.State.PLAYING else "paused."))
            print("The time is at " + str(datetime.timedelta(seconds=current_time))[2:7] + " (" + str(int(current_time)) + " seconds)")
    
    def remove(self, queue_pos):
        if (queue_pos < 0 or queue_pos >= len(self.songqueue)):
            print("Out of bounds index " + str(queue_pos) + " passed for removal.")
        else:
            self.songqueue.pop(queue_pos)

            if (queue_pos == 0):
                self.change_song(self.songqueue[0][0])

    def shuffle(self):
        self.set_pipeline_state(Gst.State.NULL)
        shuffle(self.songqueue)
        self.change_song(self.songqueue[0][0])
    
    def clear(self):
        self.set_pipeline_state(Gst.State.NULL)
        self.songqueue.clear()
    
    def swap(self, index1, index2):
        if index1 < 0 or index1 >= len(self.songqueue):
            print("First index of " + str(index1) + " is out of range.")
            return

        if index2 < 0 or index2 >= len(self.songqueue):
            print("Second index of " + str(index2) + " is out of range.")
            return

        self.songqueue[index1], self.songqueue[index2] = self.songqueue[index2], self.songqueue[index1]
        if index1 == 0 or index2 == 0:
            self.change_song(self.songqueue[0][0])
