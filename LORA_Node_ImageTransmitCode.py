#!/usr/bin/env python3
import logging
from PIL import Image, ImageChops
import struct
from rak811.rak811_v3 import Rak811
from timeit import default_timer as timer
import subprocess
import os

logging.basicConfig(level=logging.INFO)

# Initialize the LoRa module
lora = Rak811()

# LoRa setup
print('Setup')
lora.set_config('lora:work_mode:0')  # Set LoRa mode
lora.set_config('lora:join_mode:0')  # OTAA join mode
lora.set_config('lora:region:US915')  # US915 frequency region

# Join the LoRa network
print('Joining')
lora.join()
print("Joined successfully")


# Capture an image using the webcam
def capture_image(image_path):
    try:
        subprocess.run(['fswebcam', '-r', '128x128', '--jpeg', '85', image_path], check=True)
        print(f"Image captured and saved to {image_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error capturing image: {e}")
        raise


# Convert image to optimized pixel data
def image_to_optimized_pixel_data(image):
    width, height = image.size
    optimized_data = []

    for y in range(height):
        start_x = 0
        current_color = None

        for x in range(width):
            r, g, b = image.getpixel((x, y))
            color = (r, g, b)

            if color != current_color:
                if current_color is not None:
                    optimized_data.append((start_x, x - 1, y, *current_color))
                start_x = x
                current_color = color

        if current_color is not None:
            optimized_data.append((start_x, width - 1, y, *current_color))

    return optimized_data


# Encode pixel data into binary format
def encode_binary(data):
    binary_data = b""
    for segment in data:
        x1, x2, y, r, g, b = segment
        binary_data += struct.pack(">HHHBHB", x1, x2, y, r, g, b)
    return binary_data


# Find differences between two images
def find_image_differences(image1, image2):
    diff = ImageChops.difference(image1, image2).convert("RGB")
    width, height = diff.size
    changed_pixels = []

    for y in range(height):
        for x in range(width):
            if diff.getpixel((x, y)) != (0, 0, 0):  # Non-zero pixel indicates a difference
                r, g, b = image2.getpixel((x, y))
                changed_pixels.append((x, x, y, r, g, b))

    return changed_pixels


# Main execution
current_image_path = '/home/nsu/Documents/LoRA_ImageSend/current_image.jpeg'
previous_image_path = '/home/nsu/Documents/LoRA_ImageSend/previous_image.jpeg'
chunk_size = 10  # Number of segments per chunk

try:
    # Infinite loop for continuous image transmission
    while True:
        # Capture the current image
        capture_image(current_image_path)
        current_image = Image.open(current_image_path).resize((128, 128)).convert("RGB")

        # Check if a previous image exists
        if os.path.exists(previous_image_path):
            previous_image = Image.open(previous_image_path).resize((128, 128)).convert("RGB")
            differences = find_image_differences(previous_image, current_image)
        else:
            differences = image_to_optimized_pixel_data(current_image)  # Send full image if no previous image

        total_chunks = (len(differences) + chunk_size - 1) // chunk_size

        start_time = timer()
        for i in range(0, len(differences), chunk_size):
            chunk = differences[i:i + chunk_size]
            binary_chunk = encode_binary(chunk)

            if i == 0:
                # Add metadata (total_chunks) to the first chunk
                metadata = total_chunks.to_bytes(2, byteorder='big')
                binary_chunk = metadata + binary_chunk

            try:
                lora.send(binary_chunk)
                percentage_done = ((i // chunk_size) + 1) / total_chunks * 100
                print(f"Chunk sent ({percentage_done:.2f}% done)")
            except Exception as e:
                logging.error(f"Failed to send chunk: {e}")
                break

        end_time = timer()
        print(f"Image transmission completed in {end_time - start_time:.2f} seconds")

        # Save the current image as the previous image for the next iteration
        current_image.save(previous_image_path)

except KeyboardInterrupt:
    print("Stopping image transmission...")

finally:
    lora.close()