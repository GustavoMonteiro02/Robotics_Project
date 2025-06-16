# Imports
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
from Maix import GPIO
from Maix import I2S
import os
import gc

# Variables
v_continua = 1
v_data = 0
v_turnoff_audio_path = "/flash/turnoff.wav"
v_turnon_audio_path = "/flash/turnon.wav"
v_ssid = "LAPTOP-72BLR83N 5054" 
v_wifi_password = "58jQ/041"
v_commands_socket_port = 8080
v_stream_image_quality = 20
v_video_socket_port = 9090
v_video_socket_ip = "192.168.137.83"
v_data_not_received = 404
dc_1 = WeDCMotor(1)
dc_2 = WeDCMotor(2)
dc_3 = WeDCMotor(3)
dc_4 = WeDCMotor(4)

# main functions
def copy_to_flash(nome_arquivo):
    origem = "/sd/" + nome_arquivo
    destino = "/flash/" + nome_arquivo

    try:
        with open(origem, "rb") as f_src:
            dados = f_src.read()
        with open(destino, "wb") as f_dst:
            f_dst.write(dados)
    except Exception as e:
        print("Erro ao copiar:", e)

def play_audio(audio_path):
    voice_en.value(1)
    myAudio = audio.Audio(path=audio_path)
    sample_rate = myAudio.play_process(i2s)[1]
    if sample_rate:
        i2s.set_sample_rate(sample_rate)
    else:
        print("Erro: sample rate inválido")
        return
    myAudio.volume(100)
    while not myAudio.play() == 0:
        pass
    myAudio.finish()

def send_video_stream_image(img, v_video_socket_port, v_video_socket_ip):
    if img:
        try:
            raw = img.to_bytes()
            # Fragmentar e enviar (tamanho seguro para UDP é ~1024 bytes)
            FRAG_SIZE = 1024
            img_len = len(raw)
            
            sock_video.sendto(b"##START", (v_video_socket_ip, v_video_socket_port))        
            for i in range(0, img_len, FRAG_SIZE):
                frag = raw[i:i+FRAG_SIZE]
                # Envia fragmento com cabeçalho simples (offset opcional)
                sock_video.sendto(frag, (v_video_socket_ip, v_video_socket_port))
            print("Imagem enviada em partes")
            sock_video.sendto(b"##END", (v_video_socket_ip, v_video_socket_port))    
        except Exception as e:
                print("Erro ao enviar frame:", e)

def receive_command(sock_cmd):
    try:
        data, addr = sock_cmd.recvfrom(256)
        v_data = int(data.decode('utf-8').strip())
        print("Comando recebido:", v_data)
        sock_cmd.sendto(b"OK", addr)
        return v_data
    except Exception:
        return v_data_not_received

def react_to_command(v_data):
    print("received command " + str(v_data))
    # Execute command
    if v_data == 8:
        dc_1.run(100)
        dc_4.run(100)
    elif v_data == 2:
        dc_1.run(-100)
        dc_4.run(-100)
    elif v_data == 4:
        dc_2.run(50)
        dc_3.run(0)
    elif v_data == 6:
        dc_2.run(0)
        dc_3.run(50)
    elif v_data == 0 or v_data == 5:
        dc_1.run(0)
        dc_2.run(0)
        dc_3.run(0)
        dc_4.run(0)

def init_camera_lcd():
    # Init camera and LCD
    lcd.init()
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.skip_frames(time=2000)

def init_wifi():
    # SPI Wi-Fi
    fm.register(25, fm.fpioa.GPIOHS10, force=True)
    fm.register(8,  fm.fpioa.GPIOHS11, force=True)
    fm.register(9,  fm.fpioa.GPIOHS12, force=True)
    fm.register(28, fm.fpioa.GPIOHS13, force=True)
    fm.register(26, fm.fpioa.GPIOHS14, force=True)
    fm.register(27, fm.fpioa.GPIOHS15, force=True)
    
    nic = network.ESP32_SPI(
        cs=fm.fpioa.GPIOHS10,
        rst=fm.fpioa.GPIOHS11,
        rdy=fm.fpioa.GPIOHS12,
        mosi=fm.fpioa.GPIOHS13,
        miso=fm.fpioa.GPIOHS14,
        sclk=fm.fpioa.GPIOHS15)
    return nic

def init_audio():
    # Audio
    fm.register(32, fm.fpioa.GPIO1)
    voice_en = GPIO(GPIO.GPIO1, GPIO.OUT)
    fm.register(33, fm.fpioa.I2S0_WS)
    fm.register(34, fm.fpioa.I2S0_OUT_D1)
    fm.register(35, fm.fpioa.I2S0_SCLK)
    i2s = I2S(I2S.DEVICE_0)
    i2s.channel_config(i2s.CHANNEL_1, I2S.TRANSMITTER, 
    resolution=I2S.RESOLUTION_16_BIT, cycles=I2S.SCLK_CYCLES_32, 
    align_mode=I2S.RIGHT_JUSTIFYING_MODE)
    return i2s, voice_en

def init_sockets():
    # 📡 Sockets
    sock_cmd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_cmd.bind(('0.0.0.0', v_commands_socket_port))
    sock_cmd.settimeout(0)
    
    sock_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_video.settimeout(0)
    print("Servidor pronto para comandos e envio de vídeo")
    return sock_cmd, sock_video

# Copy audios to internal memory
for nome in ["turnon.wav", "turnoff.wav"]:
    copy_to_flash(nome)
print("Files in internal memory", os.listdir("/flash"))


print("Arquivos no flash:", os.listdir("/flash"))  
print("Memória livre:", gc.mem_free())      

i2s, voice_en = init_audio()
nic = init_wifi()
nic.connect(v_ssid, v_wifi_password)
print("Wi-Fi conectado, IP:", nic.ifconfig()[0])
sock_cmd, sock_video = init_sockets()
init_camera_lcd()

play_audio(v_turnon_audio_path)

# Principal Loop 
while v_continua == 1:

    gc.collect()
    
    # Show câmera in LCD
    img = sensor.snapshot()
    lcd.display(img)
    
    # compress image
    jpg = img.compress(quality = v_stream_image_quality)
    if jpg is None:
        print("Erro: compressão falhou")
        continue

    # Send image
    send_video_stream_image(jpg, v_video_socket_port, v_video_socket_ip)

    v_data = receive_command(sock_cmd)
    
    if v_data != v_data_not_received:
        react_to_command(v_data)
    else: 
        print("no command received")
        
    if v_data == 0:
        v_continua = 0
    
play_audio(v_turnoff_audio_path)