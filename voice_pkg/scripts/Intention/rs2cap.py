import pyrealsense2 as rs
import numpy as np
import cv2

class RealSenseCapture:
    def __init__(self):
        # Configure depth and color streams
        self.pipeline = rs.pipeline()
        config = rs.config()

        # Get device product line for setting a supporting resolution
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        pipeline_profile = config.resolve(pipeline_wrapper)
        device = pipeline_profile.get_device()
        device_product_line = str(device.get_info(rs.camera_info.product_line))

        found_rgb = False
        for s in device.sensors:
            if s.get_info(rs.camera_info.name) == 'RGB Camera':
                found_rgb = True
                break
        if not found_rgb:
            raise ValueError("The device does not have a Depth camera with Color sensor")

        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        # Start streaming
        self.pipeline.start(config)

    def get_frames(self):
        # Wait for a coherent pair of frames: depth and color
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        if not depth_frame or not color_frame:
            return None, None

        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        self.frame_timestamp_ms = color_frame.get_timestamp()

        return depth_image, color_image
    
    def get_depth_at_point(self, start):
        if start is not None:
            # Denormalize the x and y coordinates
            depth_frame = self.get_frames()[0]
            w, h = depth_frame.shape
            x_pixel, y_pixel = int(start.x * w), int(start.y * h)

            # Get the depth value at the specified pixel
            depth = depth_frame[x_pixel, y_pixel]

            return depth
        else:
            return None

    def get(self, cv2_param=None):
        # Get frame timestamp
        return self.frame_timestamp_ms
    
    def isOpened(self):
        # Check if the camera is opened
        return True

    def stop(self):
        # Stop streaming
        self.pipeline.stop()

    def apply_colormap_on_depth(self, depth_image, scale=0.03):
        # Apply colormap on depth image
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=scale), cv2.COLORMAP_JET)
        return depth_colormap

    def show_images(self, color_image, depth_colormap):
        # Show images side by side
        if depth_colormap.shape != color_image.shape:
            resized_color_image = cv2.resize(color_image, dsize=(depth_colormap.shape[1], depth_colormap.shape[0]), interpolation=cv2.INTER_AREA)
            images = np.hstack((resized_color_image, depth_colormap))
        else:
            images = np.hstack((color_image, depth_colormap))
        
        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('RealSense', images)

if __name__ == "__main__":
    cap = RealSenseCapture()
    while cap.isOpened():
        depth_image, color_image = cap.get_frames()
        depth_colormap = cap.apply_colormap_on_depth(depth_image)
        cap.show_images(color_image, depth_colormap)
        if cv2.waitKey(1) & 0xFF == 27:
            cv2.destroyAllWindows()
            break
    cap.stop()
