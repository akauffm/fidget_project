from xmlrpc.server import SimpleXMLRPCServer

server = SimpleXMLRPCServer(("localhost", 8050), allow_none=True)

prompt = " "
temperature = 0
paused = False
isSpeaking = False
textToSpeak = ""

def setPrompt(p):
  global prompt
  if (p == prompt):
    return "Prompt unchanged"
  else:
    prompt = p
    print(prompt)
    return "Prompt changed"

def getPrompt():
  return prompt

def pauseStream():
  global paused
  paused = True

def unpauseStream():
  global paused
  paused = False

def getPause():
  global paused
  return paused

def setTemperature(t):
  global temperature
  temperature = t
  print(temperature)
  return "Temperature changed"

def getTemperature():
  return temperature

def setIsSpeaking(f):
  global isSpeaking
  isSpeaking = f

def getIsSpeaking():
  return isSpeaking

def speak(text):
  global textToSpeak
  textToSpeak = text

def getSpeech():
  return textToSpeak

server.register_function(setPrompt, "setPrompt")
server.register_function(getPrompt, "getPrompt")
server.register_function(setTemperature, "setTemperature")
server.register_function(getTemperature, "getTemperature")
server.register_function(pauseStream, "pauseStream")
server.register_function(unpauseStream, "unpauseStream")
server.register_function(getPause, "getPause")
server.register_function(setIsSpeaking, "setIsSpeaking")
server.register_function(getIsSpeaking, "getIsSpeaking")
server.register_function(speak, "speak")
server.register_function(getSpeech, "getSpeech")

server.serve_forever()