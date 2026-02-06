# Venus External

A modern, high-performance external ESP overlay for Roblox, built with Python.

## Features

- **Visuals (ESP)**
  - **Box ESP**: Dynamic 2D boxes around players.
  - **Name Tags**: Display player names.
  - **Health Bars**: Visual health indicator with color gradients.
  - **Snaplines**: Lines to players.
  - **Distance**: Distance indicators in meters.

- **Overlay**
  - **VSync Compatible**: High refresh rate overlay (up to 144Hz+).
  - **Crosshair**: Custom overlay crosshair with FOV circle.
  - **Stream Proof**: (Depending on capture method).

- **Modern UI**
  - Built with `CustomTkinter` for a sleek, dark-themed interface.
  - Draggable, frameless window.
  - Taskbar integration.

## Optimization
Venus uses a smart caching system to minimize memory reads, ensuring zero impact on game performance (FPS) while maintaining buttery smooth overlay updates.

## Installation

1. Install Python 3.10+.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Open Roblox and join a game.
2. Run the application:
   ```bash
   python main.py
   ```
3. Click **"Attach to Roblox"**.
4. Configure visuals in the **Visuals** tab.
5. Click **"Start Overlay"** in the **Settings** tab.

## Disclaimer
This software is for educational purposes only. Use at your own risk.
