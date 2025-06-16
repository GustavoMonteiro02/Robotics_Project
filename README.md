# Robotics_Project

### **Intelligent Remote Control System** using https://pt.weeemake.com/product/ai-machine-learning-starter-kit-ai-education.html

#### **Project Overview**
The main goal of this project is to develop an intelligent remote control system for a mobile robot with real-time video transmission, integrating various embedded programming, network communication, motor control, audio, and web interface technologies. The system consists of two main components: the embedded code running on the robot (using MaixPy) and a web application (developed in Python/Flask) that enables remote control.

### **Specific Objectives**
#### **Remote Control via Web Interface**
- Allow the user to control the robot’s movement (forward, backward, left, right, and stop) using buttons on a web page accessible via a browser.
- Commands are transmitted via UDP from the web server to the robot.

#### **Real-Time Video Transmission**
- Capture images using the built-in camera on the robot.
- Compress and fragment JPEG frames.
- Send images via UDP to the Flask server.
- Reconstruct frames on the server and display real-time video in the web interface.

#### **Integration with DC Motors**
- Use the WeDCMotor library to control the robot’s four motors.
- Interpret received numerical commands (e.g., 8 for forward, 2 for backward, etc.) and convert them into motor actions.

#### **Audio Playback**
- Play activation and deactivation sound messages (e.g., "turnon.wav" and "turnoff.wav") using the device’s audio interface.
- Provide auditory feedback to the user indicating the robot’s status.

#### **Network Management and Connectivity**
- Establish Wi-Fi connection using an ESP32 module via SPI.
- Enable bidirectional communication between the robot and the local server.

#### **Optimization of Embedded Resources**
- Implement garbage collection mechanisms to free up memory.
- Copy audio files from the SD card to flash storage to ensure availability and efficiency.

#### **Robustness and Modularity**
- Organize the code modularly, facilitating future expansion, such as computer vision or AI-based control.
- Implement basic error management to handle compression or network failures.

This is a fascinating and well-structured project! Do you need help refining any aspects of the implementation, debugging, or expanding functionality? I'd love to assist. 🚀
