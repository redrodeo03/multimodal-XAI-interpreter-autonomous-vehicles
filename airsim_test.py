import airsim
import time

# Connect to the AirSim simulator
client = airsim.CarClient()
client.confirmConnection()

# Set the car in motion
client.enableApiControl(True)
car_controls = airsim.CarControls()
car_controls.throttle = 0.5
car_controls.steering = 0.0
client.setCarControls(car_controls)

# Drive for 3 seconds
print("Driving forward for 3 seconds...")
time.sleep(3)

# Stop the car
car_controls.throttle = 0.0
client.setCarControls(car_controls)

print("Stopping the car.")