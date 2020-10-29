import re
from ctypes import *
from sys import argv

import ipa
import speechPlayer
from lavPlayer import LavPlayer

AUDIO_OUTPUT_SYNCHRONOUS=2
espeakINITIALIZE_DONT_EXIT = 0x8000
espeakCHARS_WCHAR=3

curPitch=50
curVoice='Adam'
curInflection=0.7
curVolume=1.0
curRate=1.0
lang = "en"

re_textPause=re.compile(r"(?<=[.?!,:;])\s",re.DOTALL|re.UNICODE)

voices={
	'Adam':{
		'cb1_mul':1.3,
		'pa6_mul':1.3,
		'fricationAmplitude_mul':0.85,
	},
		'Benjamin':{
		'cf1_mul':1.01,
		'cf2_mul':1.02,
		#'cf3_mul':0.96,
		'cf4':3770,
		'cf5':4100,
		'cf6':5000,
		'cfNP_mul':0.9,
		'cb1_mul':1.3,
		'fricationAmplitude_mul':0.7,
		'pa6_mul':1.3,
	},
	'Caleb':{
		'aspirationAmplitude':1,
		'voiceAmplitude':0,
	},
	'David':{
		'voicePitch_mul':0.75,
		'endVoicePitch_mul':0.75,
		'cf1_mul':0.75,
		'cf2_mul':0.85,
		'cf3_mul':0.85,
	},
}

def applyVoiceToFrame(frame,voiceName):
	v=voices[voiceName]
	for paramName in (x[0] for x in frame._fields_):
		absVal=v.get(paramName)
		if absVal is not None:
			setattr(frame,paramName,absVal)
		mulVal=v.get('%s_mul'%paramName)
		if mulVal is not None:
			setattr(frame,paramName,getattr(frame,paramName)*mulVal)

def encodeEspeakString(text):
	return text.encode('utf8')

class espeak_VOICE(Structure):
	_fields_=[
		('name',c_char_p),
		('languages',c_char_p),
		('identifier',c_char_p),
		('gender',c_byte),
		('age',c_byte),
		('variant',c_byte),
		('xx1',c_byte),
		('score',c_int),
		('spare',c_void_p),
	]

	def __eq__(self, other):
		return isinstance(other, type(self)) and addressof(self) == addressof(other)

	# As __eq__ was defined on this class, we must provide __hash__ to remain hashable.
	# The default hash implementation is fine for  our purposes.
	def __hash__(self):
		return super().__hash__()

player=speechPlayer.SpeechPlayer(22050)
lavPlayer=LavPlayer(player,22050,'test.wav')

espeakDLL = cdll.LoadLibrary("libespeak-ng.so")
espeakDLL.espeak_Initialize(
            AUDIO_OUTPUT_SYNCHRONOUS, 300,
            None,
            # #10607: ensure espeak does not exit NVDA's process on errors such as the espeak path being invalid.
            espeakINITIALIZE_DONT_EXIT
    )

# Set Voice
v=espeak_VOICE()
lang=lang.replace('_','-')
v.languages=encodeEspeakString(lang)
try:
    espeakDLL.espeak_SetVoiceByProperties(byref(v))
except:
    v.languages=encodeEspeakString("en")
    espeakDLL.espeak_SetVoiceByProperties(byref(v))

textList=re_textPause.split(argv[1])
lastIndex=len(textList)-1
for index,chunk in enumerate(textList):
    if not chunk: continue
    chunk=chunk.strip()
    if not chunk: continue
    clauseType=chunk[-1]
    if clauseType in ('.','!'):
        endPause=150
    elif clauseType=='?':
        endPause=150
    elif clauseType==',':
        endPause=120
    else:
        endPause=100
        clauseType=None
    endPause/=curRate
    textBuf=create_unicode_buffer(chunk)
    textPtr=c_void_p(addressof(textBuf))
    chunks=[]
    while textPtr:
        phonemeBuf=espeakDLL.espeak_TextToPhonemes(byref(textPtr),espeakCHARS_WCHAR,0x36182)
        if not phonemeBuf: continue
        chunks.append(string_at(phonemeBuf))
    chunk=b"".join(chunks).decode('utf8') 
    chunk=chunk.replace('ə͡l','ʊ͡l')
    chunk=chunk.replace('a͡ɪ','ɑ͡ɪ')
    chunk=chunk.replace('e͡ɪ','e͡i')
    chunk=chunk.replace('ə͡ʊ','o͡u')
    chunk=chunk.strip()
    if not chunk: continue
    pitch=curPitch#+pitchOffset
    basePitch=25+(21.25*(pitch/12.5))
    for args in ipa.generateFramesAndTiming(chunk,speed=curRate,basePitch=basePitch,inflection=curInflection,clauseType=clauseType):
        frame=args[0]
        if frame:
            applyVoiceToFrame(frame,curVoice)
            frame.preFormantGain*=curVolume
            player.queueFrame(*args)
    player.queueFrame(None,endPause,max(10.0,10.0/curRate))
lavPlayer.generateAudio()

espeakDLL.espeak_Terminate()
