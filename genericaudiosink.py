from discord import AudioSink
from discord import AudioFrame
from discord import RTCPPacket
from discord.opus import Decoder as OpusDecoder
import struct
import io
import os

MIN_CMD_LEN = 8


class GenericAudioSink(AudioSink):
    # ---------------------------------------------------------------
    # @Brief: GenericAudioSink implements AudioSink to allow 
    #   recording to a memory buffer.
    # ---------------------------------------------------------------
    __slots__ = (
        "output_dir", "done", "filename", "buffer", "_timestamps","_frame_buffer"
    )

    FRAME_BUFFER_LIMIT = 10

    def __init__(self, output_dir="/data/discord-mic-test-bot/logs/"):
        if not os.path.isdir(output_dir):
            raise ValueError("Invalid output directory")
        self.output_dir = output_dir
        self.filename = ""
        self.buffer = io.BytesIO()
        self.done = False
        self._timestamp = None
        
        # This gives leeway for frames sent out of order
        self._frame_buffer = []

    def __del__(self):
        if not self.done:
            self.cleanup()

    def on_audio(self, frame: AudioFrame) -> None:
        """Takes an audio frame and adds it to a buffer. Once the buffer
        reaches a certain size, all audio frames in the buffer are
        written to file. The buffer allows leeway for packets that
        arrive out of order to be reorganized.

        Parameters
        ----------
        frame: :class:`AudioFrame`
            The frame which will be added to the buffer.
        """
        # append frame to _frame_buffer dict
        if frame.ssrc not in self._frame_buffer:
            self.filename = str(frame.ssrc) + ".pcm"

        self._frame_buffer.append(frame)
        if len(self._frame_buffer) >= self.FRAME_BUFFER_LIMIT:
            self._write_buffer(frame.ssrc)

    def _write_buffer(self, empty=False):
        self._frame_buffer = sorted(self._frame_buffer, key=lambda frame: frame.sequence)
        index = self.FRAME_BUFFER_LIMIT//2 if not empty else self.FRAME_BUFFER_LIMIT
        for frame in self._frame_buffer[:index]:
            self._write_frame(frame)
        self._frame_buffer = self._frame_buffer[index:]

    def _write_frame(self, frame):
        if self._timestamp:
            # write silence
            silence = frame.timestamp - self._timestamp - OpusDecoder.FRAME_SIZE
            if silence > 0: self.buffer.write(b"\x00" * silence * OpusDecoder.CHANNELS)

        self.buffer.write(frame.audio)
        self._timestamp = frame.timestamp

    def cleanup(self) -> None:
        """Writes remaining frames in buffer and closes all files"""
        if self.done: return
        self._write_buffer(empty=True)
        self.done = True

    def write_to_file(self) -> None:
        with open(self.output_dir + "/" + self.filename, "wb") as f:
            f.write(self.buffer.getvalue())

    def get_wav(self, sample_rate=48000, bits_per_sample=16, channels=2) -> io.BytesIO:
        data_size = self.buffer.getbuffer().nbytes
        fmt_chunk_size = 16
        audio_format = 1
        num_channels = channels
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_chunk_size = data_size
        riff_chunk_size = 4 + (8 + fmt_chunk_size) + (8 + data_chunk_size)

        # create new bytes io to return
        wav_buffer = io.BytesIO()

        # Write the RIFF chunk header
        wav_buffer.write(b"RIFF")
        wav_buffer.write(struct.pack("<I", riff_chunk_size))
        wav_buffer.write(b"WAVE")

        # Write the format chunk
        wav_buffer.write(b"fmt ")
        wav_buffer.write(struct.pack("<I", fmt_chunk_size))
        wav_buffer.write(struct.pack("<H", audio_format))
        wav_buffer.write(struct.pack("<H", num_channels))
        wav_buffer.write(struct.pack("<I", sample_rate))
        wav_buffer.write(struct.pack("<I", byte_rate))
        wav_buffer.write(struct.pack("<H", block_align))
        wav_buffer.write(struct.pack("<H", bits_per_sample))

        # Write the data chunk header
        wav_buffer.write(b"data")
        wav_buffer.write(struct.pack("<I", data_chunk_size))

        # Write the audio data
        wav_buffer.write(self.buffer.getvalue())
        wav_buffer.seek(0)

        # Return the new WAV file buffer
        return wav_buffer
    
    def on_rtcp(self, packet: RTCPPacket) -> None:
        """This function receives RTCP Packets, but does nothing with them since
        there is no use for them in this sink.

        Parameters
        ----------
        packet: :class:`RTCPPacket`
            A RTCP Packet received from discord. Can be any of the following:
            :class:`RTCPSenderReportPacket`, :class:`RTCPReceiverReportPacket`,
            :class:`RTCPSourceDescriptionPacket`, :class:`RTCPGoodbyePacket`,
            :class:`RTCPApplicationDefinedPacket`
        """
        pass

