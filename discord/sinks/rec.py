import wave
import queue
from .core import Filters, Sink, default_filters
import pydub
import os
import time 
from google.cloud import speech

#os.environ["GOOGLE_APPLICATION_CREDENTIALS"]


class RecSink(Sink):
    """A special sink added for live transcription.
    .. versionadded:: 2.0
    """

    def __init__(self, *, filters=None):
        if filters is None:
            filters = default_filters
        self.filters = filters
        Filters.__init__(self, **self.filters)
        self.encoding = "wav"
        self.vc = None
        self.audio_data = {}
        self.seg = queue.Queue()
        self.result = ""
    '''Formats combined chunks from proc_audiochunk into format that google API accepts, to use different service,
       Change the seg values at the end of this method.'''
    def format_audio(self, audio):
        bytes = self.seg.get()
        width = self.vc.decoder.SAMPLE_SIZE // self.vc.decoder.CHANNELS
        framer = self.vc.decoder.SAMPLING_RATE
        channeln = self.vc.decoder.CHANNELS
        seg = pydub.AudioSegment(
            data = bytes.getvalue(),
            sample_width = width,
            frame_rate = framer,
            channels = channeln,
        )
        
        seg = seg.split_to_mono()
        seg = seg[0]
        seg = seg.set_frame_rate(16000)
        #seg.export("testymctester.wav", format="wav") #uncomment to output as .wav
        seg = seg.raw_data
        #self.result = self.transcribe(seg)


        client = speech.SpeechClient()
        # In practice, stream should be a generator yielding chunks of audio data.
        stream = [seg]
        requests = (
            speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in stream
        )

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_automatic_punctuation=True,
        )

        streaming_config = speech.StreamingRecognitionConfig(config=config)

        # streaming_recognize returns a generator.
        responses = client.streaming_recognize(
            config=streaming_config,
            requests=requests,
        )

        for response in responses:
            for result in response.results:
                alternatives = result.alternatives
        
            self.result = result.alternatives[0].transcript
            f = open("transcription.txt", "w")
            f.write(self.result)
            f.close()
        
    def get_result(self):
        return self.result
