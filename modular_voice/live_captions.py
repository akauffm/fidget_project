"""Live captions from microphone using Moonshine and SileroVAD ONNX models."""

import argparse
import os
import time
from queue import Queue

import numpy as np
from silero_vad import VADIterator, load_silero_vad
from sounddevice import InputStream

from moonshine_onnx import MoonshineOnnxModel, load_tokenizer

import xmlrpc.client

SAMPLING_RATE = 16000
CHUNK_SIZE = 512  # Silero VAD requirement
LOOKBACK_CHUNKS = 5
MAX_LINE_LENGTH = 80
MAX_SPEECH_SECS = 15
MIN_REFRESH_SECS = 0.2

rpc_port = "8050"
rpc = xmlrpc.client.ServerProxy(f"http://localhost:{rpc_port}")


class Transcriber:
    def __init__(self, model_name, rate=16000):
        if rate != 16000:
            raise ValueError("Moonshine supports sampling rate 16000 Hz.")
        self.model = MoonshineOnnxModel(model_name=model_name)
        self.rate = rate
        self.tokenizer = load_tokenizer()
        self.inference_secs = 0
        self.number_inferences = 0
        self.speech_secs = 0
        self.__call__(np.zeros(int(rate), dtype=np.float32))  # Warmup

    def __call__(self, speech):
        self.number_inferences += 1
        self.speech_secs += len(speech) / self.rate
        start = time.time()
        tokens = self.model.generate(speech[np.newaxis, :].astype(np.float32))
        text = self.tokenizer.decode_batch(tokens)[0]
        self.inference_secs += time.time() - start
        return text


def create_input_callback(q):
    def input_callback(data, frames, time, status):
        if status:
            print(status)
        q.put((data.copy().flatten(), status))
    return input_callback


def print_captions(text, cache):
    if len(text) < MAX_LINE_LENGTH:
        for caption in reversed(cache):
            text = caption + " " + text
            if len(text) > MAX_LINE_LENGTH:
                break
    if len(text) > MAX_LINE_LENGTH:
        text = text[-MAX_LINE_LENGTH:]
    else:
        text = " " * (MAX_LINE_LENGTH - len(text)) + text
    print("\r" + (" " * MAX_LINE_LENGTH) + "\r" + text, end="", flush=True)


def soft_reset(vad_iterator):
    vad_iterator.triggered = False
    vad_iterator.temp_end = 0
    vad_iterator.current_sample = 0


def process_audio_loop(q, transcribe, vad_iterator, caption_cache, use_rpc, rpc, lookback_size):
    speech = np.empty(0, dtype=np.float32)
    recording = False
    start_time = time.time()

    def end_recording(speech, do_print=True):
        text = transcribe(speech)
        if do_print:
            print_captions(text, caption_cache)
        caption_cache.append(text)
        if use_rpc and len(text.strip()) > 1:
            if should_speak:
                rpc.speak(text)
            else:
                rpc.setPrompt(text)

    try:
        while True:
            if use_rpc and rpc.getIsSpeaking():
                if recording:
                    end_recording(speech)
                    recording = False
                    soft_reset(vad_iterator)
                # Drain the queue so it doesn't fill up with stale data
                while not q.empty():
                    q.get_nowait()
                time.sleep(0.1)
                continue

            chunk, status = q.get()
            if status:
                print(status)

            speech = np.concatenate((speech, chunk))
            if not recording:
                speech = speech[-lookback_size:]

            speech_dict = vad_iterator(chunk)

            if speech_dict:
                if "start" in speech_dict and not recording:
                    recording = True
                    start_time = time.time()
                elif "end" in speech_dict and recording:
                    recording = False
                    end_recording(speech)
            elif recording:
                if (len(speech) / SAMPLING_RATE) > MAX_SPEECH_SECS:
                    recording = False
                    end_recording(speech)
                    soft_reset(vad_iterator)
                elif (time.time() - start_time) > MIN_REFRESH_SECS:
                    print_captions(transcribe(speech), caption_cache)
                    start_time = time.time()

    except KeyboardInterrupt:
        if recording:
            while not q.empty():
                chunk, _ = q.get()
                speech = np.concatenate((speech, chunk))
            end_recording(speech, do_print=False)
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live captioning demo of Moonshine models")
    parser.add_argument(
        "--model_name",
        default="moonshine/base",
        choices=["moonshine/base", "moonshine/tiny"],
        help="Model to run the demo with"
    )
    parser.add_argument(
        "--use_rpc",
        action='store_true',
        help="Whether to use RPC server"
    )
    parser.add_argument(
        "--speak",
        action='store_true',
        help="Sends the transcript to TTS via RPC"
    )
    args = parser.parse_args()
    use_rpc = args.use_rpc
    should_speak = args.speak
    if should_speak: use_rpc = True
    model_name = args.model_name
    print(f"Loading Moonshine model '{model_name}' ...")
    transcribe = Transcriber(model_name, rate=SAMPLING_RATE)

    vad_model = load_silero_vad(onnx=True)
    vad_iterator = VADIterator(
        model=vad_model,
        sampling_rate=SAMPLING_RATE,
        threshold=0.5,
        min_silence_duration_ms=300,
    )

    caption_cache = []
    lookback_size = LOOKBACK_CHUNKS * CHUNK_SIZE
    q = Queue()

    stream = InputStream(
        samplerate=SAMPLING_RATE,
        channels=1,
        blocksize=CHUNK_SIZE,
        dtype=np.float32,
        callback=create_input_callback(q),
    )

    print("Press Ctrl+C to quit live captions.\n")
    with stream:
        print_captions("Ready...", caption_cache)
        try:
            process_audio_loop(q, transcribe, vad_iterator, caption_cache, use_rpc, rpc, lookback_size)
        except KeyboardInterrupt:
            print(f"""

             model_name :  {model_name}
       MIN_REFRESH_SECS :  {MIN_REFRESH_SECS}s

      number inferences :  {transcribe.number_inferences}
    mean inference time :  {(transcribe.inference_secs / transcribe.number_inferences):.2f}s
  model realtime factor :  {(transcribe.speech_secs / transcribe.inference_secs):0.2f}x
""")
            if caption_cache:
                print(f"Cached captions.\n{' '.join(caption_cache)}")
