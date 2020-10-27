import wave

class LavPlayer(object):

	def __init__(self,speechPlayer,sampleRate,filename):
		self.speechPlayer=speechPlayer
		self.wave_file=wave.open(filename, "w")
		self.wave_file.setnchannels(1)
		self.wave_file.setframerate(sampleRate)
		self.wave_file.setsampwidth(2)

	def generateAudio(self):
		print('Generating the wave...')
		while True:
			buf=self.speechPlayer.synthesize(1024)
			if buf:
				self.wave_file.writeframes(buf)
			else:
				self.wave_file.close()
				print("Finished")
				raise SystemExit(0) # Force quit the Python interpreter
