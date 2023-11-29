import time
import datetime
import serial
import numpy as np
import matplotlib.pyplot as plt
import cv2
import threading
from threading import Lock
from flask import Flask, render_template, session, request, \
    copy_current_request_context, Response
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from flask_serial import Serial

async_mode = None

# World Variable
app = Flask(__name__)
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
ser.reset_input_buffer()
print ('Arduino connected')

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

# CC prop
z1 = 1500
# CCW prop
z2 = 1500
# Var tambah
x = 0
# Midpoint motor
midpoint = 1500
# Video Dashboard
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

@socketio.on('request_data')
def send_data(message):
    if message['data'] == 'mulai':
        data = ser.readline().decode('utf-8').strip()
        depth_now = float(data.split(',')[1])
        kompas_now = float(data.split(',')[2])
        pitch = float(data.split(',')[3])
        roll = float(data.split(',')[4])
        socketio.emit('update', {'kedalaman': depth_now, 'kompas':kompas_now, 'pitch':pitch, 'roll':roll})
        time.sleep(0.2)
    
@socketio.on('stick')
def handle_stick(data):
    print(data)

def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my_response',
                      {'data': 'Server generated event', 'count': count})

@app.route('/')
def index():
    return render_template('index2.html', async_mode=socketio.async_mode)

@app.route('/joy')
def joy():
    return render_template('joygamepad.html', async_mode=socketio.async_mode)

@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})

@socketio.event
def my_broadcast_event(message):
    global z1
    global z2
    global x
    global midpoint

    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)
    print('ini gerak ' + message['data'])
        
    if message['data'] == 'Increase':
        x += 10
        if x > 50:
          x -= 10
        print("Kecepatan tambahan :", x)
    elif message['data'] == 'Decrease':
        x -= 10
        if x < 0:
          x += 10
        print("Kecepatan kurangan :", x)
    
    elif message ['data'] == 'Reset':
        print('Reset')
        midpoint = 1500
        x = 0
        z = 1500
        ser.write(('maju '+str(z)+' '+str(z)+' '+str(z)+' '+str(z)+';').encode())

    elif message['data'] == 'Maju':
        print("kirim maju")
        z1 = midpoint + x
        print('z............', z1)
        ser.write(('maju '+str(z1+10)+' '+str(z1+5)+' 1500 1500;').encode())
        line = ser.readline()
        print(line)

    elif message['data'] =='Mundur':
        print("kirim mundur")
        z2 = midpoint - x
        print('z............', z2)
        ser.write(('maju '+str(z2-3.987)+' '+str(z2)+' 1500 1500;').encode())
        line = ser.readline()
        print(line)
              
    elif message['data'] =='Kiri':
        print("kirim kiri")
        ser.write(('maju 1500 1500 1510 1490;').encode())
        line = ser.readline()
        print(line)
        
    elif message['data'] =='Kanan':
        print("kirim kanan")
        ser.write(('maju 1500 1500 1490 1510;').encode())
        line = ser.readline()
        print(line)
    
    elif message['data'] =='Naik':
        print("kirim naik")
        ser.write(('naik 1520 1520 1520 1520;').encode())
        line = ser.readline()
        print(line)       

    elif message['data'] =='Turun':
        print("kirim turun")
        z2 = midpoint - x
        ser.write(('naik 1480 1480 1480 1480;').encode())
        line = ser.readline()
        print(line)
        
    elif message['data'] == 'Stop':
        print("Stop")
        #ser.write(b'sv;')
        line = ser.readline()
        print(line)
        
    elif message['data'] == 'StopHorizontal':
        print("StopH")
        ser.write(b'sh;')
        line = ser.readline()
        print(line)
        
    elif message['data'] == 'StopVertikal':
        print("StopV")
        ser.write(b'sv;')
        line = ser.readline()
        print(line)

    elif message['data'] == 'StrafeKanan':
        print("StrafeKanan")
        z2 = midpoint - x
        ser.write(('maju 1500 1500 '+str(z2)+' '+str(z2-10)+';').encode())
        line = ser.readline()
        print(line)

    elif message['data'] == 'StrafeKiri':
        print("StrafeKiri")
        z1 = midpoint + x
        ser.write(('maju 1500 1500 '+str(z1)+' '+str(z1+10)+';').encode())
        line = ser.readline()
        print(line)
    
@socketio.event
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})

@socketio.event
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})

@socketio.on('close_room')
def on_close_room(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         to=message['room'])
    close_room(message['room'])

@socketio.event
def my_room_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         to=message['room'])

@socketio.event
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)

@socketio.event
def my_ping():
    emit('my_pong')

@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)

def gather_img():
    while True:
        time.sleep(0.1)
        _, img = cam.read()
        _, frame = cv2.imencode('.jpg', img)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n')

@app.route("/mjpeg")
def mjpeg():
    return Response(gather_img(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0',debug=False)
