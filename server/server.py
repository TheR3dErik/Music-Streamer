import flask
from flask import request, jsonify
from pathlib import Path
from mutagen.mp3 import MP3
from mediaplayer import MediaPlayer

app = flask.Flask(__name__)
app.config["DEBUG"] = True

songs = []
mp = MediaPlayer()

def init():
    global songs
    songs = load_songs()

def load_songs(songfolder = "../songs"):
    songpath = Path(songfolder)

    songs = []
    allpaths = songpath.rglob("*.mp3")
    id = 0
    for path in allpaths:
        # find length of song with mutagen
        songlen = 0
        try:
            songlen = MP3(str(path)).info.length
        except Exception:
            print("Unable to read mp3 header of file " + str(path) + " successfully.")
            continue

        songname = path.name[:-4]

        song = {
            'id': id,
            'path': str(path),
            'name': songname,
            'length': songlen,
        }
        songs.append(song)
        id += 1
    
    return songs

@app.route('/api/get/all', methods=['GET'])
def songs_all():
    return jsonify(songs)

@app.route('/api/get/id', methods=['GET'])
def song_id():
    code = verify_number_arg(request.args)
    if not code[0]:
        return code[1]
    id = int(code[1])
    
    for song in songs:
        if song['id'] == id:
            return song
    
    # this code should never be reached
    return "Unable to find song by ID of " + str(id)

def verify_number_arg(arg_name):
    if arg_name in request.args:
        try:
            id = float(request.args[arg_name])
            return (True, id)
        except ValueError as e:
            return (False, "ERROR: Invalid " + arg_name + " of " + request.args[arg_name] + " provided.")
    else:
        return (False, "ERROR: No ID field provided. Please specify a song ID.")

@app.route('/api/get/name', methods=['GET'])
def song_name():
    if 'name' in request.args:
        name = request.args['name']
    else:
        return "ERROR: No name field provided. Please specify a song name."
    
    for song in songs:
        if song['name'] == name:
            return song
    
    return "Unable to find song by name of " + name

@app.route('/api/pause', methods=['GET'])
def song_pause():
    mp.pause()

    return "ok"

@app.route('/api/play', methods=['GET'])
def song_play():
    mp.play()

    return "ok"

@app.route('/api/skip', methods=['GET'])
def song_skip():
    mp.skip()

    return "ok"

@app.route('/api/restart', methods=['GET'])
def song_restart():
    mp.restart()

    return "ok"

@app.route('/api/scrub', methods=['GET'])
def song_scrub():
    code = verify_number_arg("num_seconds")
    if not code[0]:
        return code[1]
    num_seconds = code[1]
    return mp.scrub(num_seconds)

@app.route('/api/time', methods=['GET'])
def song_time():
    return mp.get_time()

@app.route('/api/add', methods=['GET'])
def song_add():
    code = verify_number_arg("id")
    if not code[0]:
        return code[1]
    id = int(code[1])
    if id < 0 or id >= len(songs):
        return "ERROR: id of " + str(id) + " is out of bounds. Song list has size of " + str(mp.get_queue_length())
    
    mp.add(songs[id])

    return "ok"

@app.route('/api/queue', methods=['GET'])
def song_queue():
    return jsonify(mp.get_queue())

@app.route('/api/status', methods=['GET'])
def song_status():
    return jsonify(mp.status())

@app.route('/api/remove', methods=['GET'])
def song_remove():
    code = verify_number_arg("index")
    if not code[0]:
        return code[1]
    index = int(code[1])
    return mp.remove(index)

@app.route('/api/shuffle', methods=['GET'])
def song_shuffle():
    mp.shuffle()
    return "ok"

@app.route('/api/clear', methods=['GET'])
def song_clear():
    mp.clear()
    return "ok"

@app.route('/api/swap', methods=['GET'])
def song_swap():
    code1 = verify_number_arg("index1")
    if not code1[0]:
        return code1[1]
    index1 = int(code1[1])

    code2 = verify_number_arg("index2")
    if not code2[0]:
        return code2[1]
    index2 = int(code2[1])

    return mp.swap(index1, index2)

@app.route('/api/move', methods=['GET'])
def song_move():
    codeFrom = verify_number_arg("indexFrom")
    if not codeFrom[0]:
        return codeFrom[1]
    indexFrom = int(codeFrom[1])

    codeTo = verify_number_arg("indexTo")
    if not codeTo[0]:
        return codeTo[1]
    indexTo = int(codeTo[1])

    return mp.move(indexFrom, indexTo)

init()
app.run()