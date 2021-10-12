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

        #self.pipeline = Gst.parse_launch("filesrc name=src ! decodebin ! autoaudiosink")
        self.pipeline = Gst.parse_launch("filesrc name=src ! decodebin ! audio/x-raw, rate=16000, channels=1, format=S16LE ! audiomixer blocksize=320 ! udpsink host=localhost port=10000")
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
    
    def get_queue(self):
        return self.songqueue

    def set_pipeline_state(self, state):
        self.pipeline.set_state(state)
        self.pipeline_state = state

    def run_loop(self):
        self.loop.run()
    
    def change_song(self, filename):
        # VERY clunky solution!! Do NOT do this even short term!
        self.set_pipeline_state(Gst.State.NULL)
        #self.pipeline = Gst.parse_launch("filesrc name=src ! decodebin ! autoaudiosink")
        self.pipeline = Gst.parse_launch("filesrc name=src ! decodebin ! audioconvert ! audioresample ! audio/x-raw,format=S16LE,channels=2,rate=44100 ! udpsink host=127.0.0.1 port=10000")
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

    def play(self):
        if len(self.songqueue) > 0:
            self.set_pipeline_state(Gst.State.PLAYING)
    
    def skip(self):
        if len(self.songqueue) == 1:
            self.songqueue.pop(0)
            self.set_pipeline_state(Gst.State.NULL)
        else:
            self.songqueue.pop(0)
            oldstate = self.pipeline_state
            self.change_song(self.songqueue[0]['path'])
            self.set_pipeline_state(oldstate)
    
    def restart(self):
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 0)

    def scrub(self, num_seconds):
        current_time = self.pipeline.query_position(Gst.Format.TIME)[1]
        offset = int(num_seconds * 1000000000)
        new_time = current_time + offset
        if new_time < 0:
            new_time = 0
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, new_time)
        return new_time / 1000000000.0
    
    def get_time(self):
        current_time = self.pipeline.query_position(Gst.Format.TIME)[1]
        return current_time / 1000000000.0
    
    def add(self, song, queue_pos=-1):
        # first check if path even exists

        if queue_pos > len(self.songqueue):
            queue_pos = len(self.songqueue)
        elif queue_pos == -1:
            queue_pos = len(self.songqueue)

        if queue_pos == 0:
            self.change_song(song['path'])

        self.songqueue = self.songqueue[0:queue_pos] + [song] + self.songqueue[queue_pos:]
    
    def status(self):
        if len(self.songqueue) == 0:
            return ("none", 0)
        else:
            current_time = self.pipeline.query_position(Gst.Format.TIME)[1] / 1000000000.0

            return ("playing" if self.pipeline_state == Gst.State.PLAYING else "paused", current_time)
    
    def remove(self, queue_pos):
        if (queue_pos >= 0 and queue_pos < len(self.songqueue)):
            self.songqueue.pop(queue_pos)

            if (queue_pos == 0):
                self.change_song(self.songqueue[0]['path'])
            
            return "ok"
        else:
            return "not ok"

    def shuffle(self):
        self.set_pipeline_state(Gst.State.NULL)
        shuffle(self.songqueue)
        self.change_song(self.songqueue[0]['path'])
    
    def clear(self):
        self.set_pipeline_state(Gst.State.NULL)
        self.songqueue.clear()
    
    def swap(self, index1, index2):
        if index1 < 0 or index1 >= len(self.songqueue):
            return "not ok"

        if index2 < 0 or index2 >= len(self.songqueue):
            return "not ok"

        self.songqueue[index1], self.songqueue[index2] = self.songqueue[index2], self.songqueue[index1]
        if index1 == 0 or index2 == 0:
            self.change_song(self.songqueue[0]['path'])
        
        return "ok"
    
    def move(self, indexFrom, indexTo):
        if indexFrom < 0 or indexFrom >= len(self.songqueue):
            return "not ok"

        if indexTo < 0 or indexTo > len(self.songqueue):
            return "not ok"

        song = self.songqueue[indexFrom]
        self.songqueue.insert(indexTo, song)
        if indexTo < indexFrom:
            self.songqueue.pop(indexFrom+1)
        else:
            self.songqueue.pop(indexFrom)
        if indexFrom == 0 or indexTo == 0:
            self.change_song(self.songqueue[0]['path'])
        
        return "ok"