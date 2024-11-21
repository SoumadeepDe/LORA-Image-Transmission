# **LoRa-Based Image Transmission System**

This project showcases an innovative system for transmitting and reconstructing images over a LoRaWAN network. The setup consists of a LoRa node built using a Raspberry Pi Zero 2W, a LoRa pHAT from RAK, and a USB-connected camera. The captured images are processed and transmitted via the LoRa protocol to **The Things Network (TTN)**. A webhook integration pulls the data from TTN into a laptop, where the images are reconstructed and updated dynamically.

---

## **Key Features**
- **Efficient Image Transmission**:
  - The first image is sent entirely after optimization using horizontal pixel run-length encoding.
  - Subsequent transmissions include only pixel differences, minimizing data usage.

- **LoRaWAN Integration**:
  - Uses the LoRa pHAT for long-range, low-power data transmission.
  - Data is routed through TTN for cloud processing.

- **Real-Time Reconstruction**:
  - A Flask server on the laptop receives binary data, reconstructs images, and saves them incrementally (e.g., `reconstructed_image0.png`, `reconstructed_image1.png`).

---

## **System Components**
1. **LoRa Node**:
   - Raspberry Pi Zero 2W: Handles image capture, optimization, and LoRa communication.
   - LoRa pHAT: Provides LoRaWAN connectivity.
   - USB Camera: Captures 128x128 images for transmission.

2. **The Things Network (TTN)**:
   - Acts as the cloud platform for routing image data to the laptop.

3. **Laptop**:
   - Hosts a Flask server for receiving, decoding, and reconstructing images.

---

## **Code Files**
- **`LORA_Node_ImageTransmitCode.py`**: The Python script that runs on the LoRa node. It captures images, processes pixel data, and transmits the data to TTN.
- **`Laptop_ImageReceiveCode.py`**: The Python script that runs on the laptop. It receives image data from TTN, reconstructs the images, and saves them incrementally.

---

## **How It Works**
1. The Raspberry Pi captures an image using the USB camera.
2. The image is resized to 128x128 and optimized by converting pixel data into run-length encoding.
3. The LoRa pHAT sends the binary data to TTN in chunks.
4. TTN forwards the data to the laptop via a webhook powered by **ngrok**.
5. The Flask server processes the incoming data and reconstructs the image in real time.

---

## **Applications**
- Remote monitoring in IoT systems.
- Image transmission over constrained networks.
- Low-power multimedia communication.

---

## **Future Enhancements**
- Improve difference detection algorithms for more efficient updates.
- Extend the system to support higher resolutions.
- Explore encryption techniques for secure data transmission.
