from sys import byteorder
from array import array
from struct import pack

import pyaudio
import wave
import http.client, urllib.parse, json
import requests, webbrowser

from pynput.keyboard import Key, Listener
#import pyautogui

THRESHOLD = 500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 16000

def is_silent(snd_data):
    "Returns 'True' if below the 'silent' threshold"
    return max(snd_data) < THRESHOLD

def normalize(snd_data):
    "Average the volume out"
    MAXIMUM = 16384
    times = float(MAXIMUM)/max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i*times))
    return r

def trim(snd_data):
    "Trim the blank spots at the start and end"
    def _trim(snd_data):
        snd_started = False
        r = array('h')

        for i in snd_data:
            if not snd_started and abs(i)>THRESHOLD:
                snd_started = True
                r.append(i)

            elif snd_started:
                r.append(i)
        return r

    # Trim to the left
    snd_data = _trim(snd_data)

    # Trim to the right
    snd_data.reverse()
    snd_data = _trim(snd_data)
    snd_data.reverse()
    return snd_data

def add_silence(snd_data, seconds):
    "Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
    r = array('h', [0 for i in range(int(seconds*RATE))])
    r.extend(snd_data)
    r.extend([0 for i in range(int(seconds*RATE))])
    return r

def record():
    """
    Record a word or words from the microphone and 
    return the data as an array of signed shorts.

    Normalizes the audio, trims silence from the 
    start and end, and pads with 0.5 seconds of 
    blank sound to make sure VLC et al can play 
    it without getting chopped off.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
        input=True, output=True,
        frames_per_buffer=CHUNK_SIZE)

    num_silent = 0
    snd_started = False

    r = array('h')

    while 1:
        # little endian, signed short
        snd_data = array('h', stream.read(CHUNK_SIZE))
        if byteorder == 'big':
            snd_data.byteswap()
        r.extend(snd_data)

        silent = is_silent(snd_data)

        if silent and snd_started:
            num_silent += 1
        elif not silent and not snd_started:
            snd_started = True

        if snd_started and num_silent > 30:
            break

    sample_width = p.get_sample_size(FORMAT)
    
    #print(sample_width)
    stream.stop_stream()
    stream.close()
    p.terminate()

    r = normalize(r)
    r = trim(r)
    r = add_silence(r, 0.5)
    return sample_width, r

def record_to_file(path):
    "Records from the microphone and outputs the resulting data to 'path'"
    sample_width, data = record()
    data = pack('<' + ('h'*len(data)), *data)

    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()





def new_html(webpg_name):
    f = open(webpg_name + '.htm','w')

    message = """<html>
    <head><title>%s</title></head>
    <body><p>Hello World!</p></body>
    </html>""" % webpg_name

    f.write(message)
    f.close()

    webbrowser.open_new_tab('helloworld.html')




def on_press(key):
    key_press = key
    #print("PRESSED", key_press)
    if key_press == Key.space:
        #print("A HEARD!")
        main()
    if key_press == Key.esc:
        exit()

def play_beep():
    chunk = CHUNK_SIZE
    wf = wave.open('beep.wav', 'rb')

    # create an audio object
    p = pyaudio.PyAudio()

    # open stream based on the wave object which has been input.
    stream = p.open(format =
                    p.get_format_from_width(wf.getsampwidth()),
                    channels = wf.getnchannels(),
                    rate = wf.getframerate(),
                    output = True)

    # read data (based on the chunk size)
    data = wf.readframes(chunk)
    counter = 0

    # play stream (looping from beginning of file to the end)
    while data != '' or counter > 100:
        # writing to the stream is what *actually* plays the sound.
        stream.write(data)
        data = wf.readframes(chunk)
        counter += 1

    # cleanup stuff.
    #stream.close()    
    #p.terminate()
    print("Done")

def main():
    #play_beep()
    print("please speak a word into the microphone")
    record_to_file('demo2.wav')
    print("done - result written to demo.wav")
    ##play_beep()

    apiKey = "fccfe347ad474720b3f796bb2dbb59b9"

    url = '/speech/recognition/interactive/cognitiveservices/v1?language=en-us&format=detailed'
    headers = {'Ocp-Apim-Subscription-Key': apiKey, 'Content-type': 'audio/wav; codec=audio/pcm; samplerate=16000'}

    f = open('demo2.wav', "rb")
    data = f.read()
    f.close()
    conn = http.client.HTTPSConnection("speech.platform.bing.com")


    conn.request("POST", url, data, headers)
    

    response = conn.getresponse()
    #print(response.read())
    print(response.status, response.reason)  
    json_data = json.loads(response.read())
    print(json.dumps(json_data, indent=4))
    if json_data["RecognitionStatus"] != "Success":
        main()
    converted = json_data["NBest"][0]['Lexical']
    new_data = "https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/82a89dc2-4a08-4e07-9fc5-d78be0a2df05?subscription-key=29647c98e81f4307b5dd2e5e369c9aed&spellCheck=true&bing-spell-check-subscription-key=6e38fbc3d86e4723aae5c6920126f288&verbose=true&timezoneOffset=0&q="+converted
    r = requests.get(new_data)
    #print(r.json())
    checking = r.json()["topScoringIntent"]["intent"]
    
    #print(checking);

    if(checking == "CreateWebpge"):
        webpg_name = 'my_html'
        new_html(webpg_name)


    with Listener(on_press=on_press) as listener:
        listener.join()

main()