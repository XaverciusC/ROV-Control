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

app = Flask(__name__)
# app.config['SERIAL_TIMEOUT'] = 0.2
# app.config['SERIAL_PORT'] = 'COM2'
# app.config['SERIAL_BAUDRATE'] = 115200
# app.config['SERIAL_BYTESIZE'] = 8
# app.config['SERIAL_PARITY'] = 'N'
# app.config['SERIAL_STOPBITS'] = 1
m = True
n = 1
z1 = 1500
z2 = 1500
x = 0
midpoint = 1500
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
fourcc = cv2.VideoWriter_fourcc(*'H264')
out = None

def startrecord():
    global fourcc
    global out
    global n
    global m
    global cam
    out = cv2.VideoWriter('vid_4.h264',fourcc, 10.0, (640,480))
    while m:
        ret, frame = cam.read()
        if ret == True:

            out.write(frame)
            print('recordnya jalan')

        else:
            print('recordnya stop')
            break
      
def stoprecord():
    global m
    global out
    m = False

    out.release()
    print('recordnya stop harusnya')
    

# ser = Serial(app)
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

#def my_loop():
#    with open("datadep.txt", "a") as file:
#        while True:
#            data = ser.readline().decode('utf-8').strip()
#            timestamp = time.time()
#            dt_object = datetime.datetime.fromtimestamp(timestamp)
            
            #print(data)
            #depth = float(depth_data)
#            if data.startswith('A') :
                #timeupdt = float(formated_time)
#                formated_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')
#                depth_now = float(data.split(',')[1])
#                xaxis = float(data.split(',')[2])
#                yaxis = float(data.split(',')[3])
#                zaxis = float(data.split(',')[4])
#                headingDegrees = float(data.split(',')[5])
                #print('masuk', formated_time, depth_now, xaxis, yaxis, zaxis, headingDegrees)
#                file.write(f'{formated_time}, {depth_now}, {xaxis}, {yaxis}, {zaxis}, {headingDegrees}' + "\n")
#                file.flush()
#            time.sleep(0.1) 
#            pass

# create a new thread to run the loop
#thread1 = threading.Thread(target=my_loop)
#thread1.start()

ser.reset_input_buffer()
print ('Arduino connected')

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

#///////////////////////////////////////////////#
@socketio.on('request_data')
def send_data(message):
    if message['data'] == 'mulai':
        with open("2523(19).txt", "a") as file:
            data = ser.readline().decode('utf-8').strip()
            timestamp = time.time()
            dt_object = datetime.datetime.fromtimestamp(timestamp)
            if data.startswith('A'):
                formated_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')
                depth_now = float(data.split(',')[1])
                kompas_now = float(data.split(',')[2])
                pitch = float(data.split(',')[3])
                roll = float(data.split(',')[4])
                x_axis = float(data.split(',')[5])
                y_axis = float(data.split(',')[6])
                z_axis = float(data.split(',')[7])
                x_axisgy = float(data.split(',')[8])
                y_axisgy = float(data.split(',')[9])
                z_axisgy = float(data.split(',')[10])
                file.write(f'{formated_time}, {depth_now}, {kompas_now} , {pitch} , {roll} , {x_axis} , {y_axis} , {z_axis} , {x_axisgy} , {y_axisgy} , {z_axisgy}'  + "\n")
                file.flush()
                socketio.emit('update', {'kedalaman': depth_now, 'kompas':kompas_now})
                time.sleep(0.2)

#///////////////////////////////////////////////#

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
    return render_template('index.html', async_mode=socketio.async_mode)


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
    global cam
    global out
    global m
    global n
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
    
    #elif message['data'] == 'Rekam' or ['data'] == 'StopRek':
    elif message['data'] == 'Rekam':
        print("Rekam")
        n += 1
        startrecord()

    elif message['data'] == 'StopRek':
        print("StopRekam")
        stoprecord()
    

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


# setup camera and resolution

#fourcc = cv2.VideoWriter_fourcc(*'H264')
#out = cv2.VideoWriter('Hasil_2.h264', fourcc, 20.0, (640,480))

#while(cam.isOpened()):
    #ret, frame = cam.read()
    #if ret == True:
        #out.write(frame)
        
        #cv2.imshow('frame',frame)
        #if cv2.waitKey(1) & 0xFF == ord('q'):
            #break
    #else:
        #break

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
