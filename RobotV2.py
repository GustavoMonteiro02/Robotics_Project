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
from ObjectDetection_20 import *

# Variables
v_continue = 1
v_command = 0
v_turnoff_audio_path = "/flash/turnoff.wav"
v_turnon_audio_path = "/flash/turnon.wav"
v_ssid = "LAPTOP-72BLR83N 5054" 
v_wifi_password = "58jQ/041"
v_video_socket_port = 9090
v_controller_socket_port = 9050
v_alert_socket_port = 9040
v_stream_image_quality = 20
v_controller_socket_ip = "192.168.137.8"
v_command_not_received = 404
v_speed = 50
v_command = v_command_not_received
dc_1 = WeDCMotor(1)
dc_2 = WeDCMotor(2)
dc_3 = WeDCMotor(3)
dc_4 = WeDCMotor(4)
v_object_identifier_model_location = "/sd/20class.kmodel"
v_20ObjectClassifier = 0	#20ObjectClassifier
v_img = 0	#img
v_IdentifierResult = 0	#IdentifierResult
v_cx = 0	#cx
v_cy = 0	#cy
v_alert = ""
last_alert_time = 0
v_front_command = 8
v_back_command = 2
v_left_command = 4
v_right_command = 6
v_stop_command = 5
v_turnoff_command = 0

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
            # Fragmentar e enviar (secure size for UDP is ~1024 bytes)
            FRAG_SIZE = 1024
            img_len = len(raw)
            
            sock_video.sendto(b"##START", (v_video_socket_ip, v_video_socket_port))        
            for i in range(0, img_len, FRAG_SIZE):
                frag = raw[i:i+FRAG_SIZE]
                # Envia fragmento com cabeçalho simples (offset opcional)
                sock_video.sendto(frag, (v_video_socket_ip, v_video_socket_port))
            sock_video.sendto(b"##END", (v_video_socket_ip, v_video_socket_port))    
        except Exception as e:
                print("Erro ao enviar frame:", e)

def receive_command(sock):
    try:
        data, addr = sock.recvfrom(256)
        print("Address Command: ", addr, "data:", data)
        command = data.decode('utf-8').strip()
        print("Input recebido:", command)
        return command
    except Exception:
        return v_command_not_received

def f_Forward(l_FD):
    dc_1.run(l_FD * -1)
    dc_2.run(l_FD)
    dc_3.run(l_FD * -1)
    dc_4.run(l_FD)

def f_Backward(l_BD):
    dc_1.run(l_BD)
    dc_2.run(l_BD * -1)
    dc_3.run(l_BD)
    dc_4.run(l_BD * -1)

def f_TurnLeft(l_TL):
    dc_1.run(l_TL)
    dc_2.run(l_TL)
    dc_3.run(l_TL)
    dc_4.run(l_TL)

def f_TurnRight(l_TR):
    dc_1.run(l_TR * -1)
    dc_2.run(l_TR * -1)
    dc_3.run(l_TR * -1)
    dc_4.run(l_TR * -1)
    
def f_Stop():
    dc_1.run(0)
    dc_2.run(0)
    dc_3.run(0)
    dc_4.run(0)

def is_front_obstacle(v_cx, v_cy):
    return v_cx > 120 and v_cx < 200
    
def is_left_obstacle(v_cx, v_cy):
    return v_cx > 200
    
def is_right_obstacle(v_cx, v_cy):
    return v_cx < 120

def react_to_command(command, v_cx, v_cy):
    print("received command " + str(command))
    v_alert = ""
    # Execute command
    if command == v_front_command:
        print("turning left")            
        if is_front_obstacle(v_cx, v_cy):
            v_alert = obstacle_alert("Front")
        else:
            f_Forward(v_speed)
    elif command == v_back_command:
        f_Backward(v_speed)
    elif command == v_left_command:
        if is_left_obstacle(v_cx, v_cy):
            v_alert = obstacle_alert("Left")        
        else:
            print("turning left")        
            f_TurnLeft(v_speed)
    elif command == v_right_command:
        if is_right_obstacle(v_cx, v_cy):
            print("Right obstacle")
            v_alert = obstacle_alert("Right")
        else:
            print("turning right")
            f_TurnRight(v_speed)
    elif command == v_stop_command or command == v_turnoff_command:
        f_Stop()
    else:
        print("failed")
    return v_alert

def init_camera_lcd():
    # Init camera and LCD
    lcd.init()
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.skip_frames(time=2000)
    sensor.set_auto_gain(True)
    sensor.set_auto_whitebal(True)

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
    
def connect_wifi(ssid, password, nic):
    try:
        nic.connect(ssid, password)
        print("Wi-Fi conectado, IP:", nic.ifconfig()[0])
    except Exception as e:
        print("Failed to connect to wifi: ", e)
        raise e

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
    sock_controller = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_controller.bind(('0.0.0.0', v_controller_socket_port))
    sock_controller.settimeout(0)
    print("Server ready for speed receival")
    
    sock_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_video.settimeout(0)
    print("Server ready for vídeo stream")
    
    sock_alert = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_alert.settimeout(0)
    print("Server ready for alerts stream")
    return sock_video, sock_controller, sock_alert

def get_object_detection(img):
    v_IdentifierResult = v_20ObjectClassifier.object_detection(img)
    if v_IdentifierResult:
        v_cx = v_IdentifierResult[2][0]
        v_cy = v_IdentifierResult[2][1]
        return v_cx, v_cy

def obstacle_alert(direction):
    return "There is an obstacle in the " + direction + " will not move"

def send_alert(alert):
    print(alert)
    try:
        sock_alert.sendto(alert.encode(), (v_controller_socket_ip, v_alert_socket_port))         
    except Exception as e:
            print("Error sending alert:", e)

# Copy audios to internal memory
for nome in ["turnon.wav", "turnoff.wav", "20class.kmodel"]:
    copy_to_flash(nome)
print("Files in internal memory", os.listdir("/flash"))
print("Files in SD", os.listdir("/sd"))


# init
i2s, voice_en = init_audio()
nic = init_wifi()
connect_wifi(v_ssid, v_wifi_password, nic)
sock_video, sock_controller, sock_alert = init_sockets()

init_camera_lcd()
#v_20ObjectClassifier = ObjectDetection_20(v_object_identifier_model_location, "")

play_audio(v_turnon_audio_path)

# Principal Loop 
while v_continue == 1:
    gc.collect()
    
    # Show câmera in LCD
    v_img = sensor.snapshot()
    lcd.display(v_img)

    # compress image
    jpg = v_img.compress(quality = v_stream_image_quality)
    if jpg is None:
        print("Erro: compressão falhou")
        continue

    # Send image
    send_video_stream_image(jpg, v_video_socket_port, v_controller_socket_ip)

    #v_cx, v_cy = get_object_detection(v_img)
    
    v_socket_input = receive_command(sock_controller)
    
    if v_socket_input != v_command_not_received:
        if v_socket_input.startswith("SPEED:"):
            v_speed = int(v_socket_input.split("SPEED:")[1])
        elif v_socket_input.startswith("COMMAND:"):
            v_command = int(v_socket_input.split("COMMAND:")[1])
            
    print ("speed: ", v_speed)
    print ("command: ", v_command)
    
    v_alert = react_to_command(v_command, 150, 0)
    if int(v_command) == v_turnoff_command:
        v_continue = 0

    v_alert = "Cmon"
    current_time = time.time()
    if current_time - last_alert_time >= 1.0 and v_alert != "":
         send_alert(v_alert)
         last_alert_time = current_time
        
play_audio(v_turnoff_audio_path)