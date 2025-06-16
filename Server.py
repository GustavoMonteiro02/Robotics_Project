from WePort import *
from fpioa_manager import fm
import network
import socket
from WeDCMotor import *
import sensor
import lcd
import image
import time
import audio
from Maix import GPIO, I2S
import os
import gc

# --- Áudio ---
def play_audio(path):
    voice_en.value(1)
    myAudio = audio.Audio(path=path)
    sample_rate = myAudio.play_process(i2s)[1]
    if sample_rate:
        i2s.set_sample_rate(sample_rate)
    else:
        print("Erro no sample rate")
        return
    myAudio.volume(100)
    while not myAudio.play() == 0:
        pass
    myAudio.finish()

# --- Inicialização ---
print("Memória livre:", gc.mem_free())

# Motores
v_data = 0
v_continua = 1
dc_1, dc_2, dc_3, dc_4 = WeDCMotor(1), WeDCMotor(2), WeDCMotor(3), WeDCMotor(4)

# Áudio
v_right_audio_path = "/flash/right.wav"
v_left_audio_path = "/flash/left.wav"
v_front_audio_path = "/flash/front.wav"
v_back_audio_path = "/flash/back.wav"
v_stop_audio_path = "/flash/stop.wav"
v_turnoff_audio_path = "/flash/turnoff.wav"

# GPIO para voz
fm.register(32, fm.fpioa.GPIO1)
voice_en = GPIO(GPIO.GPIO1, GPIO.OUT)
fm.register(33, fm.fpioa.I2S0_WS)
fm.register(34, fm.fpioa.I2S0_OUT_D1)
fm.register(35, fm.fpioa.I2S0_SCLK)
i2s = I2S(I2S.DEVICE_0)
i2s.channel_config(i2s.CHANNEL_1, I2S.TRANSMITTER, resolution=I2S.RESOLUTION_16_BIT, cycles=I2S.SCLK_CYCLES_32, align_mode=I2S.RIGHT_JUSTIFYING_MODE)

# Câmera & LCD
lcd.init()
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)

# SPI Wi-Fi
fm.register(25, fm.fpioa.GPIOHS10, force=True)
fm.register(8,  fm.fpioa.GPIOHS11, force=True)
fm.register(9,  fm.fpioa.GPIOHS12, force=True)
fm.register(28, fm.fpioa.GPIOHS13, force=True)
fm.register(26, fm.fpioa.GPIOHS14, force=True)
fm.register(27, fm.fpioa.GPIOHS15, force=True)

nic = network.ESP32_SPI(cs=fm.fpioa.GPIOHS10, rst=fm.fpioa.GPIOHS11, rdy=fm.fpioa.GPIOHS12,
                        mosi=fm.fpioa.GPIOHS13, miso=fm.fpioa.GPIOHS14, sclk=fm.fpioa.GPIOHS15)
nic.connect("LAPTOP-72BLR83N 5054", "58jQ/041")
print("Wi-Fi conectado, IP:", nic.ifconfig())

# Sockets UDP
sock_cmd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_cmd.bind(('0.0.0.0', 8080))
sock_cmd.settimeout(0)

sock_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_video.settimeout(0)
IP_PC = "192.168.137.83"
PORTA_VIDEO = 9090

# Loop principal
while v_continua:
    gc.collect()
    img = sensor.snapshot()
    lcd.display(img)

    # Envia imagem em pedaços UDP
    jpg = img.compress(quality=20)
    if jpg:
        try:
            sock_video.sendto(b"##START", (IP_PC, PORTA_VIDEO))
            for i in range(0, len(jpg), 1024):
                chunk = jpg[i:i+1024]
                sock_video.sendto(chunk, (IP_PC, PORTA_VIDEO))
            sock_video.sendto(b"##END", (IP_PC, PORTA_VIDEO))
            print("Frame enviado (", len(jpg), "bytes)")
        except Exception as e:
            print("Erro ao enviar frame:", e)

    try:
        data, addr = sock_cmd.recvfrom(256)
        v_data = int(data.decode('utf-8').strip())
        print("Comando recebido:", v_data)
        sock_cmd.sendto(b"OK", addr)

        if v_data == 8:
            play_audio(v_front_audio_path)
            dc_1.run(100); dc_4.run(100)
        elif v_data == 2:
            play_audio(v_back_audio_path)
            dc_1.run(-100); dc_4.run(-100)
        elif v_data == 4:
            play_audio(v_left_audio_path)
            dc_2.run(50); dc_3.run(0)
        elif v_data == 6:
            play_audio(v_right_audio_path)
            dc_2.run(0); dc_3.run(50)
        elif v_data in [0, 5]:
            play_audio(v_stop_audio_path)
            dc_1.run(0); dc_2.run(0); dc_3.run(0); dc_4.run(0)
            if v_data == 0:
                v_continua = 0
                play_audio(v_turnoff_audio_path)
    except:
        pass

sock_cmd.close()
sock_video.close()
nic.disconnect()
