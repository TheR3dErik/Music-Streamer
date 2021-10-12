from threading import Thread
import traceback
from mediaplayer import MediaPlayer

mp = MediaPlayer()

def command_thread():
    global mp

    running = True
    while running:
        command = input("> ")

        if command == "":
            continue

        parts = command.split(" ")

        if parts[0] == "quit":
            mp.quit()
            running = False
        elif parts[0] == "pause":
            mp.pause()
        elif parts[0] == "play":
            mp.play()
        elif parts[0] == "skip":
            mp.skip()
        elif parts[0] == "restart":
            mp.restart()
        elif parts[0] == "scrub":
            if len(parts) == 2:
                num_seconds = -1
                try:
                    num_seconds = float(parts[1])
                except Exception:
                    print("Unable to read " + parts[1] + " as number of seconds to scrub. Ignoring request.")
                    continue

                mp.scrub(num_seconds)
            else:
                print("Usage: scrub [number of seconds]")
        elif parts[0] == "add":
            if len(parts) == 2:
                mp.add(parts[1])
            elif len(parts) == 3:
                pos = -1
                try:
                    pos = int(parts[2])
                except Exception:
                    print("Unable to read " + parts[2] + " as index in queue. Attemping to add song to the end instead.")
                
                mp.add(parts[1], pos)
            else:
                print("Usage: add [path name] [optional index in queue]")
        elif parts[0] == "queue":
            mp.queue()
        elif parts[0] == "status":
            mp.status()
        elif parts[0] == "remove":
            if len(parts) == 2:
                queue_pos = -1
                try:
                    queue_pos = int(parts[1])
                except Exception:
                    print("Unable to read " + parts[1] + " as index in queue. Ignoring request.")
                    continue

                mp.remove(queue_pos)
            else:
                print("Usage: remove [index in queue]")
        elif parts[0] == "shuffle":
            mp.shuffle()
        elif parts[0] == "clear":
            mp.clear()
        elif parts[0] == "swap":
            if len(parts) == 3:
                index1 = -1
                try:
                    index1 = int(parts[1])
                except Exception:
                    print("Unable to read " + parts[1] + " as first index. Ignoring request.")
                    continue

                index2 = -1
                try:
                    index2 = int(parts[2])
                except Exception:
                    print("Unable to read " + parts[2] + " as second index. Ignoring request.")
                    continue

                mp.swap(index1, index2)
            else:
                print("Usage: swap [first index] [second index]")
        elif parts[0] == "help":
            print("This command has not yet been implemented.")
        else:
            print("Invalid command: " + command)
            print("Enter 'help' for list of available commands.")


thread = Thread(target=command_thread)
thread.start()

try:
    mp.run_loop()
except Exception:
    traceback.print_exc()
    mp.quit()

thread.join()
mp.quit()