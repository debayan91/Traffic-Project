# Advanced Traffic Control System for Urban Road Network
> An AI-Powered Solution for Smart City Traffic Optimization

![GitHub stars](https://img.shields.io/github/stars/debayan91/Traffic?style=for-the-badge&logo=github)
![GitHub forks](https://img.shields.io/github/forks/debayan91/Traffic?style=for-the-badge&logo=github)
![License](https://img.shields.io/github/license/debayan91/Traffic?style=for-the-badge)
![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg?style=for-the-badge&logo=python)

<br>

<p align="center">
  <!-- ======================================================================================================= -->
  <!-- IMPORTANT: Replace the link below with the path to the demo GIF you uploaded to your repository! -->
  <!-- Example: <img src="assets/demo.gif" alt="System Demo" width="800"/> -->
  <!-- ======================================================================================================= -->
  <img src="path/to/your/demo.gif" alt="System Demo" width="800"/>
  <br/>
  <em>Full system simulation demonstrating dynamic signal timing based on real-time traffic density.</em>
</p>

---

## 📋 Table of Contents

- [About The Project](#-about-the-project)
- [Key Features](#-key-features)
- [How It Works: The Core Logic](#-how-it-works-the-core-logic)
- [Tech Stack](#-tech-stack)
- [Hardware Requirements](#-hardware-requirements)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation & Setup](#installation--setup)
- [Usage](#️-usage)
- [Achieved Sustainable Development Goals (SDGs)](#-achieved-sustainable-development-goals-sdgs)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 🚀 About The Project

This project presents a software-based, AI-driven system designed to replace traditional, fixed-timer traffic lights with an intelligent, adaptive control mechanism. By analyzing real-time video feeds from intersections, the system dynamically adjusts signal timings to optimize traffic flow, reduce congestion, and prioritize emergency vehicles.

The solution integrates state-of-the-art object detection models (YOLO) with physical hardware control (Arduino), creating a scalable and efficient system that directly aligns with modern Smart City initiatives.

---

## ✨ Key Features

- **Real-Time Video Processing:** Analyzes live video streams from four directions simultaneously.
- **AI-Based Vehicle Detection:** Utilizes the YOLO (You Only Look Once) model to accurately detect and classify various vehicle types (cars, buses, trucks, ambulances).
- **Weighted Prioritization System:** Assigns different weights to vehicle types, giving higher priority to emergency vehicles and public transport.
- **Dynamic Green Light Timing:** Calculates green light duration based on the real-time traffic density and vehicle weights in each lane.
- **Hardware Integration:** Interfaces with an Arduino Mega to control physical traffic light LEDs for a real-world simulation.
- **Visual Dashboard:** A Pygame-based GUI provides a comprehensive view of all video feeds, traffic counts, lane weights, and current signal statuses.

---

## 🧠 How It Works: The Core Logic

The system's intelligence is built on a continuous, four-step adaptive control loop:

1.  **Real-Time Video Analysis**
    The system processes four independent video feeds, one for each lane. Using a pre-trained **YOLO** model, it identifies and classifies all vehicles within each feed, providing a constant stream of data on traffic composition and volume.

2.  **Weighted Vehicle Prioritization**
    Each detected vehicle is assigned a "weight" based on its type to determine its priority. For example, an ambulance is given a high weight (e.g., 10) to ensure immediate passage, while a bus has a higher weight than a car. This ensures that emergency services and high-occupancy vehicles are prioritized.

3.  **Dynamic Green Light Calculation**
    The total "weight" for each lane is calculated by summing the weights of all its waiting vehicles. The green light duration is then made directly proportional to this total weight, ensuring that lanes with heavier traffic or high-priority vehicles are cleared effectively. The system enforces a minimum and maximum green time to maintain flow.

4.  **Intelligent Lane Switching & Optimization**
    After an initial calibration period, the system grants the green light to the lane with the highest traffic weight. To optimize performance, video processing is focused on the active (green) lane. When its cycle ends, the system intelligently selects the next green light recipient by identifying which of the waiting (red light) lanes has accumulated the highest traffic weight.

---

## 🛠️ Tech Stack

- **Python:** Core programming language.
- **OpenCV:** For real-time video capture and image processing.
- **Ultralytics YOLOv8:** For state-of-the-art object detection.
- **PyTorch:** The backend framework for the YOLO model.
- **Pygame:** For creating the visualization dashboard and GUI.
- **PySerial:** For communication between the Python script and the Arduino.
- **Arduino (C++):** For controlling the physical LED hardware.
- **NumPy:** For efficient numerical operations.

---

## 🔩 Hardware Requirements

To build the physical simulation of the traffic intersection, you will need:
-   1 x Arduino Mega 2560
-   12 x 220-ohm resistors
-   4 x Red LEDs
-   4 x Yellow LEDs
-   4 x Green LEDs
-   26 x Male-to-Male Jumper Cables
-   1 x Standard 400-hole Breadboard

---

## ⚙️ Getting Started

Follow these instructions to get a local copy up and running.

### Prerequisites

- [Python 3.9+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installation/) (Python package installer)
- [Git](https://git-scm.com/downloads)
- [Arduino IDE](https://www.arduino.cc/en/software)

### Installation & Setup

1.  **Clone the Repository**
    ```
    git clone https://github.com/debayan91/Traffic.git
    cd Traffic
    ```

2.  **Create a Virtual Environment**
    It's highly recommended to use a virtual environment to manage dependencies.
    ```
    # For Windows
    python -m venv venv
    venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    A `requirements.txt` file is included. Install all necessary packages with:
    ```
    pip install -r requirements.txt
    ```

4.  **Set up the Arduino**
    - Connect the Arduino Mega to your computer.
    - Open the Arduino IDE.
    - Open the `.ino` sketch file located in the `/Arduino` folder of this project.
    - Select the correct board (Arduino Mega) and port from the `Tools` menu.
    - Click `Upload` to flash the sketch to the Arduino.

5.  **Assemble the Hardware**
    - Follow a circuit diagram to connect the LEDs and resistors to the Arduino. A diagram can be found in the `/docs` folder.

---

## ▶️ Usage

Once the setup is complete, you can run the main application.

- Ensure your Arduino is connected to the computer and the correct COM port is specified in the script.
- Run the main Python script from the root directory:
  ```
  python main.py
  ```
- The Pygame window will launch, displaying the video feeds, traffic data, and a simulation of the traffic lights.

---

## 🌍 Achieved Sustainable Development Goals (SDGs)

This project contributes to several UN SDGs by creating a more efficient and sustainable urban transportation infrastructure.

-   **SDG 3: Good Health and Well-being**
    > Less traffic congestion means lower emissions, reducing respiratory diseases linked to air pollution.

-   **SDG 9: Industry, Innovation, and Infrastructure**
    > The project enhances urban transport systems by using AI-driven automation, making cities smarter and more resilient.

-   **SDG 11: Sustainable Cities and Communities**
    > By optimizing traffic flow, the project enhances urban mobility and creates safer, more efficient, and sustainable transport systems.

-   **SDG 13: Climate Action**
    > Reducing congestion leads to lower vehicle emissions and better fuel efficiency, contributing to climate action.

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## ✉️ Contact

Debayan Dutta - [GitHub Profile](https://github.com/debayan91)

Project Link: [https://github.com/debayan91/Traffic](https://github.com/debayan91/Traffic)
```
