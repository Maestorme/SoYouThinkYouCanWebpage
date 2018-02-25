from sys import byteorder
from array import array
from struct import pack

import pyaudio
import wave
import http.client, urllib.parse, json
import requests, webbrowser
from xml.etree import ElementTree

from pynput.keyboard import Key, Listener
import time

#import pyautogui

THRESHOLD = 500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 16000

webpg_name = ""

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

        if snd_started and num_silent > 30:#was 30
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

    message = """<!doctype html>

<head>
  <meta charset="utf-8">

  <title>%s</title>
  <link rel="stylesheet" href="css/styles.css">
  <link rel="stylesheet" href="css/animate.css">
  
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.4/jquery.min.js"></script>

</head>

<body>

  <div id = 'container'>

    <!--######### HOME DIV ##########-->
    <div id = 'home' class = "animated fadeInDown">

      <h2 style='margin: 0; margin-left: 275px'>PICK A BACKGROUND</h2>
      <div style="text-align: center">
      <img src='img/1.jpg' style='width: 320px; height: 150px'>
      <img src='img/2.jpg' style='width: 320px; height: 150px'>
      <img src='img/3.jpg' style='width: 320px; height: 150px'>
      </div>

      <div style="text-align: center">
      <h2 style="display: inline">1</h2>
      <h2 style="display: inline">2</h2>
      <h2 style="display: inline">3</h2>
      </div>

      <div style="text-align: center">
      <img src='img/4.jpg' style='width: 320px; height: 150px'>
      <img src='img/5.jpg' style='width: 320px; height: 150px'>
      <img src='img/6.jpg' style='width: 320px; height: 150px'>
    </div>
    
    <div style="text-align: center">
      <h2 style="display: inline">4</h2>
      <h2 style="display: inline">5</h2>
      <h2 style="display: inline">6</h2>
    </div>
  </div>

    <!--######### ABOUT DIV ##########-->


    <div id = 'about' class='about'>
      <h2 class = "heading">ABOUT</h2>
      <h2 class = 'heading'>&#8213;</h2>
      
        
     
      <img src="img/me.png" align="middle" id="dp"/> 
      <input type="file" name="pic" accept="image/*">
      <input type="submit" onclick="button_press('image')">
      <p id="missionn-statement">
        Insert Mission Statement Here
      </p>
      <a href='' class='button-link'><div class='post-skills-button'>
        <p>Resume! </p>
      </div></a>

    </div>

  
</div>
<script>
function button_press(inp){
  console.log($('#fields')["0"].value) 
  var arr =  $('#fields')["0"].value.split('\\\\')
  if(inp == 'image'){
    $("#dp").attr("src", arr[2]);
  }
  else{
    $("#resume").attr("src", arr[2]);
  }
  
  
}
</script>
</body>
</html>
""" % webpg_name

    f.write(message)
    f.close()

    webbrowser.open_new_tab(webpg_name + '.htm')




def on_press(key):
    key_press = key
    #print("PRESSED", key_press)
    if key_press == Key.space:
        #print("A HEARD!")
        main()
    if key_press == Key.esc:
        exit()

def play_audio(path):
    chunk = CHUNK_SIZE
    wf = wave.open(path, 'rb')

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
    while data != '' and counter < 200:
        # writing to the stream is what *actually* plays the sound.
        stream.write(data)
        data = wf.readframes(chunk)
        counter += 1
        #print("In loop")
    
    # cleanup stuff.
    stream.close()    
    p.terminate()
    wf.close()
    return

def delete_bg(bg_num):
    template = """<h2 style='margin: 0; margin-left: 275px'>PICK A BACKGROUND</h2>
      <div style="text-align: center">
      <img src='img/1.jpg' style='width: 320px; height: 150px'>
      <img src='img/2.jpg' style='width: 320px; height: 150px'>
      <img src='img/3.jpg' style='width: 320px; height: 150px'>
      </div>

      <div style="text-align: center">
      <h2 style="display: inline">1</h2>
      <h2 style="display: inline">2</h2>
      <h2 style="display: inline">3</h2>
      </div>

      <div style="text-align: center">
      <img src='img/4.jpg' style='width: 320px; height: 150px'>
      <img src='img/5.jpg' style='width: 320px; height: 150px'>
      <img src='img/6.jpg' style='width: 320px; height: 150px'>
    </div>
    
    <div style="text-align: center">
      <h2 style="display: inline">4</h2>
      <h2 style="display: inline">5</h2>
      <h2 style="display: inline">6</h2>
    </div>"""

    f = open(webpg_name + '.htm','r+')
    f.seek(-7,2)
    message = "<script>$('#home').html("+template+")</script>"
    f.write(message)
    f.write('</html>')
    f.close()

def replace_bg(bg_num): 
    global webpg_name
    
    if(bg_num == 'one' or bg_num == 'one one'):
        bg_num = '1'
    elif(bg_num == 'two' or bg_num == 'two two'):
        bg_num = '2'
    elif(bg_num == 'three' or bg_num == 'three three'):
        bg_num = '3'
    elif(bg_num == 'four' or bg_num == 'for' or bg_num == 'four four'):
        bg_num = '4'
    elif(bg_num == 'five' or bg_num == 'five five'):
        bg_num = '5'
    elif(bg_num == 'six' or bg_num == 'sex' or bg_num ==  'six six'):
        bg_num = '6'
    
    print(bg_num) 
    f = open(webpg_name + '.htm','r+')
    f.seek(0,2)
    num = f.tell();
    num -= 9
    f.seek(num)

    url = "./img/"+bg_num+".jpg"
    message = "<script>$('html').css({'background': 'url("+url+") no-repeat center center'});$('#home').empty()</script>"
    f.write(message)
    f.write('</html>')
    f.close()

def replace_title(full_name):
    global webpg_name
    

    f = open(webpg_name + '.htm','r+')
    f.seek(0,2)
    num = f.tell();
    num -= 7
    f.seek(num)
    inner = '<h3 id="title">'+full_name+'</h3>'
    
    message = "<script>$('title').html('"+full_name+"');$('#home').append('"+inner+"')</script>"
    f.write(message)
    f.write('</html>')
    f.close()

def tts(text):
    apiKey2 = "fccfe347ad474720b3f796bb2dbb59b9"

    params = ""
    headers = {"Ocp-Apim-Subscription-Key": apiKey2}

    #AccessTokenUri = "https://api.cognitive.microsoft.com/sts/v1.0/issueToken";
    AccessTokenHost = "api.cognitive.microsoft.com"
    path = "/sts/v1.0/issueToken"

    # Connect to server to get the Access Token
    #print ("Connect to server to get the Access Token")
    conn = http.client.HTTPSConnection(AccessTokenHost)
    conn.request("POST", path, params, headers)
    response = conn.getresponse()
    #print(response.status, response.reason)

    data = response.read()
    conn.close()

    accesstoken = data.decode("UTF-8")
    #print ("Access Token: " + accesstoken)

    body = ElementTree.Element('speak', version='1.0')
    body.set('{http://www.w3.org/XML/1998/namespace}lang', 'en-us')
    voice = ElementTree.SubElement(body, 'voice')
    voice.set('{http://www.w3.org/XML/1998/namespace}lang', 'en-US')
    voice.set('{http://www.w3.org/XML/1998/namespace}gender', 'Female')
    voice.set('name', 'Microsoft Server Speech Text to Speech Voice (en-US, ZiraRUS)')
    voice.text = text

    headers = {"Content-type": "application/ssml+xml", 
                "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm", 
                "Authorization": "Bearer " + accesstoken, 
                "X-Search-AppId": "07D3234E49CE426DAA29772419F436CA", 
                "X-Search-ClientID": "1ECFAE91408841A480F00935DC390960", 
                "User-Agent": "TTSForPython"}
                
    #Connect to server to synthesize the wave
    #print ("\nConnect to server to synthesize the wave")
    conn = http.client.HTTPSConnection("speech.platform.bing.com")
    conn.request("POST", "/synthesize", ElementTree.tostring(body), headers)
    response = conn.getresponse()
    #print(response.status, response.reason)

    data = response.read()
    f = open('tts.wav','wb')
    f.write(data)
    f.close()
    conn.close()

    play_audio('tts.wav')
    
    #print("The synthesized wave length: %d" %(len(data)))

def stt(convtype):
    play_audio("beep.wav")
    print("Please speak into the microphone:")
    record_to_file('demo2.wav')
    print("Done. Result written.")
    play_audio("beep.wav")

    apiKey = "fccfe347ad474720b3f796bb2dbb59b9"

    url = '/speech/recognition/'+convtype+'/cognitiveservices/v1?language=en-us&format=detailed'

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
        
        conn.close()
        time.sleep(2)
        main()
    else:

        converted = json_data["NBest"][0]['Lexical']
    
    return converted
    
   
    
def main():
    global webpg_name
    converted = stt('interactive')

    new_data = "https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/82a89dc2-4a08-4e07-9fc5-d78be0a2df05?subscription-key=8527651763554d578c96a14a4b03c64e&verbose=true&timezoneOffset=0&q="+converted
    
    r = requests.get(new_data)
    
    print(r.json())
    
    checking = r.json()["topScoringIntent"]["intent"]
    
    print(checking);

    if(checking == "CreateWebpage"):
        if(len(r.json()["entities"])>0):
            webpg_name = r.json()["entities"][0]["entity"]
        else:
            tts('What should I call it?')

            '''json_data = stt()

            converted = json_data["NBest"][0]['Lexical']'''
            converted = stt('interactive')
            print(converted)
            webpg_name = converted
        new_html(webpg_name)
        tts(webpg_name+' has been created')

    elif checking == "Background":
        if(len(r.json()["entities"])>2):
            bg_num = r.json()["entities"][2]["resolution"]["value"]
        else:
            tts('Which picture do I set it to?')
            bg_num = stt('interactive')
            print(bg_num)
            
        replace_bg(bg_num)
        
    elif checking == "Title":
        if(len(r.json()["entities"])>3):
            f_name = r.json()["entities"][2]["entity"]
            l_name = r.json()["entities"][3]["entity"]
            full_name = f_name+' '+l_name
        else:
            tts('Can you repeat the title?')
            full_name = stt('interactive')
            print(full_name)

        replace_title(full_name)

    elif checking == "remove_factors":
        pass

    with Listener(on_press=on_press) as listener:
        listener.join()



main()