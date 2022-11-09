from aiogram import types
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import texttospeech as tts

from bot import config

tts_client = tts.TextToSpeechClient(credentials=config.google)

voice = tts.VoiceSelectionParams()
voice.ssml_gender = 'MALE'

audio_config = tts.AudioConfig()
audio_config.audio_encoding = 'OGG_OPUS'

text = tts.SynthesisInput()

request = tts.SynthesizeSpeechRequest()
request.audio_config = audio_config


async def gen(answer: str, locale: str):
    text.text = answer

    if locale == 'ru':
        locale = 'ru-RU'
    else:
        locale = 'en-GB'

    voice.name = f'{locale}-Standard-B'
    voice.language_code = locale

    request.voice = voice
    request.input = text

    try:
        return types.BufferedInputFile(
            tts_client.synthesize_speech(request=request).audio_content,
            'bp1lh-voice'
        )
    except GoogleAPICallError:
        return
