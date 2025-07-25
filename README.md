<img width="2048" height="1433" alt="Themis" src="https://github.com/user-attachments/assets/0cc5172d-b16b-453e-b9c3-70c062d30870" />

# Themis; SELA - Event Log Aid

Themis; SELA is a desktop application designed to streamline the process of logging event attendance. It uses Optical Character Recognition (OCR) to extract usernames from a screenshot of a voice channel, and then formats them into a standardized log entry.

## Features
- **Purpose-built for 2C** 
- **OCR-Powered Username Extraction:** Automatically extracts usernames from screenshots.
- **Drag-and-Drop & Paste Support:** Easily import screenshots by dragging the file or pasting from the clipboard.
- **Username Correction:** Suggests corrections for misspelled usernames based on a master list.
- **Customizable Log Format:** Generates a clean, formatted log entry ready to be copied.
- **Simple User Interface:** Intuitive and easy-to-use interface built with PyQt6.

## How to Use

1.  **Run the Application:** Launch the `Themis SELA.exe` executable.
2.  **Provide a Screenshot:**
    -   Drag and drop a screenshot of the voice channel participants onto the designated area.
    -   Alternatively, copy a screenshot to your clipboard and paste it using `Ctrl+V` or the right-click context menu.
3.  **Verify Attendees:** The extracted usernames will appear in the "Attendees" text box. Review the list and manually correct any errors.
4.  **Fill in Event Details:**
    -   Select the event type, squad, and day of the week.
    -   Enter the host's username.
    -   Optionally, add a description for the event.
5.  **Generate the Log:** Click the "Generate Log" button.
    -   If the application finds potential misspellings in the attendee list, it will prompt you with suggestions. You can accept or reject these corrections.
6.  **Copy the Log:** Click the "Copy to Clipboard" button to copy the formatted log entry.

## `usernames.txt`

`usernames.txt` is used to to power the username correction feature.

-   **External List:** To use your own list of usernames, create a file named `usernames.txt` and place it in the same directory as the executable. The application will prioritize this file.
-   **Default List:** If no external `usernames.txt` is found, the application will fall back to a default, built-in list.
-   **Format:** The `usernames.txt` file should be a simple text file with one username per line.

## Running from Source

To run the application from source, you first need to set up the environment and install the dependencies.

### First-Time Setup (PowerShell Script)
The recommended way to get started is to use the `install_dependencies.ps1` script. This will ensure Python and all required libraries are installed correctly.

1.  **Open PowerShell:** Navigate to the project directory in your terminal.
2.  **Run the Setup Script:** Execute the following command:
    ```powershell
    .\install_dependencies.ps1
    ```
3.  **Follow the Prompts:** The script will guide you through the installation process.

### Launching the Application
Once the setup is complete, you can launch the application using the `launch.ps1` script.

-   **Using PowerShell:**
    ```powershell
    .\launch.ps1
    ```
This will start the application directly, without re-running the dependency checks.

### Manual Method
If you prefer to manage the dependencies and launch process yourself, follow these steps:

1.  **Install Python:** Ensure you have Python 3 installed and accessible from your command line.
2.  **Install Dependencies:** Open a terminal and run the following command to install the required libraries:
    ```bash
    pip install PyQt6 easyocr Pillow numpy
    ```
3.  **Run the Application:** Once the dependencies are installed, run the main script:
    ```bash
    python "Themis SELA.py"
    ```

## Building from Source

You can build the executable in two ways:

### Using the PowerShell Script (Recommended)
The `install_dependencies.ps1` script also provides an option to build the executable. After running the script, select option `2` from the menu to start the build process.

### Manual Build

If you prefer to build manually, you will need Python and the following libraries:

-   `PyQt6`
-   `easyocr`
-   `Pillow`
-   `numpy`
-   `PyInstaller`

Once you have the dependencies installed, you can build the executable by running the following command in the project directory:

```bash
pyinstaller "Themis_SELA.spec"
```

## File Size
The standalone executable is large (around 240MB zipped, 750MB unzipped) because it bundles the `easyocr` library and its language models. This is necessary to ensure the application works out-of-the-box on any system without requiring the user to install Python or download additional dependencies. The models themselves are a significant portion of the size, but they are essential for the OCR functionality to work offline.


