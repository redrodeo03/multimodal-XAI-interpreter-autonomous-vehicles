import airsim
import time
import math
import numpy as np
from settings import car_data


# Connect to the AirSim simulator
client = airsim.CarClient()
client.confirmConnection()
client.enableApiControl(True)

# Set initial car controls
car_controls = airsim.CarControls()
car_controls.throttle = 0.5  # Set a constant acceleration
car_controls.steering = 0  # Start with straight steering

# Constants
STEERING_ANGLE = 10  # Degrees
AVOIDANCE_DURATION = 1.5  # Seconds

def print_car_state():
    car_state = client.getCarState()
    s1 = "Car State:"
    print(s1)
    s2 = f"Speed: {car_state.speed:.2f} m/s"
    print(s2)
    s3 = f"Position: x={car_state.kinematics_estimated.position.x_val:.2f}, " + f"y={car_state.kinematics_estimated.position.y_val:.2f}, " + f"z={car_state.kinematics_estimated.position.z_val:.2f}"
    print(s3)
    orientation = car_state.kinematics_estimated.orientation
    pitch, roll, yaw = airsim.to_eularian_angles(orientation)
    s4 = f"Orientation: pitch={math.degrees(pitch):.2f}°, "+ f"roll={math.degrees(roll):.2f}°, "+ f"yaw={math.degrees(yaw):.2f}°"
    print(s4)
    s5 = f"Gear: {car_state.gear}"
    print(s5)
    s6 = f"Collision: {car_state.collision.has_collided}"
    print(s6)
    print("---")
    car_data = s1+s2+s3+s4+s5+s6
    return(car_data)

def detect_parked_car():
    # Simulate detection of parked cars using LIDAR data
    # Returns: -1 for left, 1 for right, 0 for no parked car
    lidar_data = client.getLidarData()
    if lidar_data.point_cloud:
        points = np.array(lidar_data.point_cloud, dtype=np.dtype('f4'))
        points = np.reshape(points, (int(points.shape[0]/3), 3))
        
        # Reduce detection radius here
        DETECTION_RADIUS = 4  # Adjust this value to change the detection radius
        DETECTION_HEIGHT = 3  # Height range for detection
        
        # Filter points within the specified radius and height range
        mask = (np.linalg.norm(points[:, :2], axis=1) < DETECTION_RADIUS) & (np.abs(points[:, 2]) < DETECTION_HEIGHT)
        filtered_points = points[mask]
        
        if filtered_points.shape[0] > 0:
            left_points = filtered_points[filtered_points[:, 1] < 0]
            right_points = filtered_points[filtered_points[:, 1] > 0]
            
            OBSTACLE_THRESHOLD = 2  # Adjust this value to change how close an obstacle needs to be to trigger avoidance
            
            if left_points.shape[0] > 0 and np.min(np.abs(left_points[:, 1])) < OBSTACLE_THRESHOLD:
                return -1
            elif right_points.shape[0] > 0 and np.min(np.abs(right_points[:, 1])) < OBSTACLE_THRESHOLD:
                return 1
    
    return 0

def steer(angle_degrees):
    # Convert degrees to AirSim steering input (-1 to 1)
    return math.sin(math.radians(angle_degrees))

try:
    while True:
        # Detect parked cars
        parked_car_direction = detect_parked_car()
        
        if parked_car_direction != 0:
            # Parked car detected, steer to avoid
            avoidance_angle = STEERING_ANGLE * -parked_car_direction
            car_controls.steering = steer(avoidance_angle)
            client.setCarControls(car_controls)
            print(f"Avoiding parked car: steering {avoidance_angle} degrees")
            car_data = print_car_state()
            time.sleep(AVOIDANCE_DURATION)
            
            # Return to straight path
            car_controls.steering = steer(-avoidance_angle)
            client.setCarControls(car_controls)
            print("Returning to straight path")
            time.sleep(1.5)
            car_controls.steering = 0

        else:
            # No parked car, drive straight
            car_controls.steering = 0
            client.setCarControls(car_controls)
        
        # Small delay to prevent overwhelming the simulator
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Stopping the car...")
    
finally:
    # Stop the car and return control
    client.setCarControls(airsim.CarControls(throttle=0, brake=1))
    car_data=""
    time.sleep(1)
    client.enableApiControl(False)
    print("Control returned to user.")

