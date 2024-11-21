from flask import Flask, request, jsonify
from PIL import Image
import os
import struct
import base64

app = Flask(__name__)

# Directory to save the reconstructed images
SAVE_DIR = "received_image_data"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# File to store the reconstructed image
IMAGE_FILE_TEMPLATE = os.path.join(SAVE_DIR, "reconstructed_image{}.png")

# Initialize reconstructed image
image_width = 128
image_height = 128
reconstructed_image = Image.new("RGB", (image_width, image_height), (255, 255, 255))

# Track total chunks for the first full image
total_chunks = 0
processed_chunks = 0
image_count = 0


def process_chunk(chunk_data):
    """
    Process a single chunk of raw binary data to update the image in real-time.
    """
    global reconstructed_image, image_count

    segment_size = struct.calcsize(">HHHBHB")
    for i in range(0, len(chunk_data), segment_size):
        try:
            x1, x2, y, r, g, b = struct.unpack(">HHHBHB", chunk_data[i:i + segment_size])

            # Validate pixel coordinates
            if not (0 <= x1 <= x2 < image_width and 0 <= y < image_height):
                print(f"Invalid pixel data: x1={x1}, x2={x2}, y={y}")
                continue

            color = (r, g, b)

            # Update the pixel data in the image
            for x in range(x1, x2 + 1):
                reconstructed_image.putpixel((x, y), color)
        except Exception as e:
            print(f"Error processing segment: {e}")

    # Save the updated image
    image_filename = IMAGE_FILE_TEMPLATE.format(image_count)
    reconstructed_image.save(image_filename)
    print(f"Image saved as {image_filename}")


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle incoming data chunks via POST requests.
    """
    global total_chunks, processed_chunks, reconstructed_image, image_count

    try:
        # Parse incoming JSON payload
        data = request.get_json()
        if "uplink_message" not in data or "frm_payload" not in data["uplink_message"]:
            return jsonify({"status": "error", "message": "Invalid payload structure"}), 400

        # Decode Base64 payload
        encoded_payload = data["uplink_message"]["frm_payload"]
        chunk_data = base64.b64decode(encoded_payload)

        # Handle the first chunk with metadata
        if processed_chunks == 0:
            total_chunks = int.from_bytes(chunk_data[:2], byteorder='big')  # First 2 bytes for metadata
            chunk_data = chunk_data[2:]  # Strip metadata from the first chunk
            print(f"Total chunks expected: {total_chunks}")

        # Process the chunk
        process_chunk(chunk_data)
        processed_chunks += 1
        print(f"Chunk {processed_chunks}/{total_chunks} processed.")

        # Reset counters after the first image is fully processed
        if processed_chunks == total_chunks:
            print(f"Image {image_count} fully received and reconstructed.")
            total_chunks = 0
            processed_chunks = 0
            image_count += 1  # Increment image count for the next image

        return jsonify({"status": "success", "message": "Chunk processed"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/get_image', methods=['GET'])
def get_image():
    """
    Endpoint to retrieve the current image file path.
    """
    try:
        if image_count > 0:
            latest_image_path = IMAGE_FILE_TEMPLATE.format(image_count - 1)
            return jsonify({"status": "success", "image_path": latest_image_path}), 200
        else:
            return jsonify({"status": "error", "message": "No images reconstructed yet"}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000)
