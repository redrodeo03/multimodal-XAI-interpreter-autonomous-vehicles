import airsim
import cv2
import numpy as np
import os
import time

# Connect to the AirSim simulator
client = airsim.CarClient()
client.confirmConnection()

# Set up video writer for the top-down view
output_dir = "airsim_recordings"
os.makedirs(output_dir, exist_ok=True)

timestamp = time.strftime("%Y%m%d-%H%M%S")
top_down_video_path = os.path.join(output_dir, f"top_down_{timestamp}.avi")

fps = 10.0

top_down_writer = None

def create_video_writer(frame):
    global top_down_writer
    height, width, _ = frame.shape
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    top_down_writer = cv2.VideoWriter(top_down_video_path, fourcc, fps, (width, height))

def get_image():
    responses = client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)])
    response = responses[0]
    img1d = np.fromstring(response.image_data_uint8, dtype=np.uint8)
    img_rgb = img1d.reshape(response.height, response.width, 3)
    return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

try:
    while True:
        # Capture image
        image = get_image()
        
        if top_down_writer is None:
            create_video_writer(image)
        
        # Write frame to video file
        top_down_writer.write(image)
        
        # Display the image (optional)
        cv2.imshow("AirSim View", image)
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("Recording stopped by user")
except Exception as e:
    print(f"An error occurred: {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    # Release video writer and close window
    if top_down_writer is not None:
        top_down_writer.release()
    cv2.destroyAllWindows()
    
    print(f"Video saved to {top_down_video_path}")