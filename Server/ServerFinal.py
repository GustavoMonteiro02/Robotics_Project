import time
from flask import Flask, render_template_string, request, Response, make_response

import socket
import threading

# ----- CONFIG -----
ROBO_IP = '192.168.137.18'
STREAM_PORT = 9090
ROBO_PORT = 9050

data_lock = threading.Lock()
frame_data = bytearray()

# ----- UDP sockets -----
sock_cmd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_speed = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock_stream = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_stream.bind(('0.0.0.0', STREAM_PORT))
sock_stream.settimeout(0.2)

# ----- Flask App -----
app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <title>Controle do Robô</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {
      --primary-color: #0ea5e9;
      --bg-color: #1e293b;
      --surface-color: #334155;
      --text-color: #e2e8f0;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: 'Segoe UI', sans-serif;
      background-color: var(--bg-color);
      color: var(--text-color);
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 20px;
    }

    h2 {
      font-size: 28px;
      margin-bottom: 20px;
      color: #ffffff;
    }

    .camera {
      border: 4px solid var(--surface-color);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
      margin-bottom: 30px;
    }

    img {
      width: 100%;
      max-width: 480px;
      display: block;
    }

    .dpad {
      display: grid;
      grid-template-columns: repeat(3, 80px);
      grid-template-rows: repeat(3, 80px);
      gap: 10px;
      justify-content: center;
      margin-top: 20px;
    }

    .dpad button {
      background-color: var(--surface-color);
      color: white;
      border: 2px solid #475569;
      border-radius: 12px;
      font-size: 28px;
      cursor: pointer;
      transition: background-color 0.2s, transform 0.1s;
    }

    .dpad button:hover {
      background-color: var(--primary-color);
    }

    .dpad button:active {
      transform: scale(0.95);
    }

    .speed-control {
      margin-top: 40px;
      text-align: center;
    }

    .speed-control input[type=range] {
      width: 300px;
      margin: 10px 0;
    }

    .send-speed {
      background-color: var(--primary-color);
      color: white;
      padding: 10px 20px;
      font-size: 16px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      margin-top: 10px;
      transition: background 0.2s, transform 0.1s;
    }

    .send-speed:hover {
      background-color: #0284c7;
    }

    .send-speed:active {
      transform: scale(0.96);
    }

    @media (max-width: 600px) {
      .dpad {
        grid-template-columns: repeat(3, 60px);
        grid-template-rows: repeat(3, 60px);
      }

      .dpad button {
        font-size: 22px;
      }

      .speed-control input[type=range] {
        width: 80%;
      }

      .send-speed {
        width: 90%;
      }
    }
  </style>
</head>
<body>

  <h2>Robot's Cam</h2>

  <div class="camera">
    <img src="/stream" alt="Robot's Cam">
  </div>

  <!-- Controle direcional -->
  <!-- Controle direcional com diagonais -->
<div class="dpad">
  <button onclick="sendCmd(7)">&#8598;</button> <!-- up-left -->
  <button onclick="sendCmd(8)">&#8593;</button> <!-- up -->
  <button onclick="sendCmd(9)">&#8599;</button> <!-- up-right -->

  <button onclick="sendCmd(4)">&#8592;</button> <!-- left -->
  <button onclick="sendCmd(5)">&#x23F9;</button> <!-- stop -->
  <button onclick="sendCmd(6)">&#8594;</button> <!-- right -->

  <button onclick="sendCmd(1)">&#8601;</button> <!-- down-left -->
  <button onclick="sendCmd(2)">&#8595;</button> <!-- down -->
  <button onclick="sendCmd(3)">&#8600;</button> <!-- down-right -->
</div>

<div style="margin-top:10px;">
  <button onclick="sendCmd(0)">TURN OFF</button>
</div>


  <!-- Controle de velocidade -->
  <div class="speed-control">
    <label for="speed"><strong>Speed:</strong></label><br>
    <input type="range" id="speed" min="10" max="200" value="100"
           oninput="document.getElementById('speedValue').innerText = this.value">
    <span id="speedValue">100</span><br>
    <button class="send-speed" onclick="sendSpeed()">Change Speed</button>
  </div>

  <script>
    function sendCmd(cmd) {
      fetch('/send_cmd', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'cmd=' + cmd
      }).then(() => console.log('Comando enviado:', cmd));
    }

    function sendSpeed() {
  const value = document.getElementById('speed').value;
  fetch('/set_speed', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'speed=' + value
  }).then(() => console.log('Velocidade enviada:', value));
}


  </script>
</body>
</html>
'''

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)

@app.route("/send_cmd", methods=["POST"])
def send_cmd():
    cmd = request.form.get("cmd")
    print(f"➡️  Comando POST recebido: {cmd}")
    if cmd:
        try:
            sock_speed.sendto(("COMMAND:"+cmd).encode(), (ROBO_IP, ROBO_PORT))
            print(f"✅ Comando {cmd} enviado via UDP para {ROBO_IP}:{ROBO_PORT}")
        except Exception as e:
            print(f"❌ Erro ao enviar comando: {e}")
            return "Erro", 500
    return "OK", 200

@app.route("/set_speed", methods=["POST"])
def set_speed():
    speed = request.form.get("speed", "50")
    print(f"➡️  Velocidade recebida: {speed}")
    try:
        sock_speed.sendto(("SPEED:"+speed).encode(), (ROBO_IP, ROBO_PORT))
        print(f"✅ Velocidade {speed} enviada via UDP para {ROBO_IP}:{ROBO_PORT}")
    except Exception as e:
        print(f"❌ Erro ao enviar velocidade: {e}")
        return "Erro", 500
    return "OK", 200


@app.route("/stream")
def stream():
    def gen():
        global frame_data
        while True:
            with data_lock:
                if frame_data:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

def video_receiver():
    global frame_data
    buffer = bytearray()
    while True:
        try:
            packet, _ = sock_stream.recvfrom(1024)
            if packet.startswith(b'##START'):
                buffer = bytearray()
            elif packet.startswith(b'##END'):
                with data_lock:
                    frame_data = buffer
            else:
                buffer.extend(packet)
        except socket.timeout:
            print("⏳ Timeout esperando pacote de vídeo...")
            continue


if __name__ == "__main__":
    print("🚀 Flask servidor iniciado em http://0.0.0.0:5000")
    threading.Thread(target=video_receiver, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, threaded=True)
