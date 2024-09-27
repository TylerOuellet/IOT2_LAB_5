from datetime import datetime
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import config
import json
import time
import ADC0832
import RPi.GPIO as GPIO
import math
trig = 20
echo = 21

#set time
date = datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")
print (f"Timestamp:{date}")
# user specified callback function
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")
# configure the MQTT client
myMQTTClient = AWSIoTMQTTClient(config.CLIENT_ID)
myMQTTClient.configureEndpoint(config.AWS_HOST, config.AWS_PORT)
myMQTTClient.configureCredentials(config.AWS_ROOT_CA, config.AWS_PRIVATE_KEY,config.AWS_CLIENT_CERT)
myMQTTClient.configureConnectDisconnectTimeout(config.CONN_DISCONN_TIMEOUT)
myMQTTClient.configureMQTTOperationTimeout(config.MQTT_OPER_TIMEOUT)
#Connect to MQTT Host
if myMQTTClient.connect():
    print('AWS connection succeeded')
# Subscribe to topic
myMQTTClient.subscribe(config.TOPIC, 1, customCallback)
time.sleep(2)
# Send message to host
collected_data = {
    "temperature" : "INIT",
    "distance" : "INIT"
    }
def send(data):
    payload = json.dumps(collected_data)
    myMQTTClient.publish(config.TOPIC, payload, 1)
def init():
    ADC0832.setup()
    GPIO.setup(trig,GPIO.OUT,initial=GPIO.LOW)
    GPIO.setup(echo,GPIO.IN)

def checkdist():
	GPIO.output(trig, GPIO.HIGH)
	time.sleep(0.000015)
	GPIO.output(trig, GPIO.LOW)
	while not GPIO.input(echo):
		pass
	t1 = time.time()
	while GPIO.input(echo):
		pass
	t2 = time.time()
	return (t2-t1)*340/2

def loop():
    while True:
        res = ADC0832.getADC(0)
        if res == 0:
            collected_data["temperature"] = "N.A"
            continue
        Vr = 3.3 * float(res) / 255
        if Vr == 3.3:
            collected_data["temperature"] = "N.A"
            continue

       
        celciusTemp = float
        kelvenTemp = float

        kelvenTemp = 1/298.15 + 1/3455 * math.log((255 / res) - 1)

        kelvenTemp = 1/kelvenTemp
        celciusTemp = kelvenTemp - 273.15

        #Discard Garbage Values
        if celciusTemp >= 50 or celciusTemp<= -50:
            collected_data["temperature"] = "Discarded Value"
            print("Outlier, Descarded value")
        else:
            celciusTemp = round(celciusTemp,2)
            celciusTemp = str(celciusTemp)
            celciusTemp = celciusTemp
            collected_data["temperature"] = celciusTemp
        
        collected_data["distance"] = checkdist()
        json_data = json.dumps(collected_data)
        send(json_data)
        time.sleep(1)
if __name__ == '__main__':
    init()
    try:
        loop()
    except KeyboardInterrupt: 
        ADC0832.destroy()
        print('The end!')