from flask import Flask, render_template_string, request, Response
import socket
import threading

# ----- CONFIG -----
ROBO_IP = '192.168.137.79'
ROBO_PORT = 8080
STREAM_PORT = 9090

data_lock = threading.Lock()
frame_data = bytearray()

# ----- UDP socket para comandos -----
sock_cmd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ----- UDP socket para vídeo -----
sock_stream = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_stream.bind(('0.0.0.0', STREAM_PORT))
sock_stream.settimeout(0.01)

# ----- Flask App -----
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Controle do Robô</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body { font-family: sans-serif; text-align: center; margin-top: 20px; }
    button { width: 80px; height: 80px; font-size: 24px; margin: 10px; }
    img { max-width: 100%; border: 2px solid #333; margin-bottom: 20px; }
  </style>
</head>
<body>
  <h2>Robô com Câmera</h2>
  <img src="/stream" />
  <form method="POST">
    <div>
      <button name="cmd" value="8">&#8593;</button>
    </div>
    <div>
      <button name="cmd" value="4">&#8592;</button>
      <button name="cmd" value="0">&#x23F9;</button>
      <button name="cmd" value="6">&#8594;</button>
    </div>
    <div>
      <button name="cmd" value="2">&#8595;</button>
    </div>
  </form>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        cmd = request.form["cmd"]
        sock_cmd.sendto(cmd.encode(), (ROBO_IP, ROBO_PORT))
    return render_template_string(HTML)

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
            continue

if __name__ == "__main__":
    threading.Thread(target=video_receiver, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, threaded=True)
