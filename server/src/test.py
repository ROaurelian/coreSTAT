import serial
import time

# Replace 'COM3' with your Arduino's serial port
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)  # Wait for the connection to initialize

# Example data to send
data_to_send = [0x01, 0x55, 0x33, 0xA8]

# Send data
ser.write(bytearray(data_to_send))

# Wait for response and read it
received_data = ser.readline().decode().strip()
print("Received:", received_data)

ser.close()
