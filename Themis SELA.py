import sys
import re
import datetime
import io
import numpy as np
import threading
import difflib
import os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit, QTextEdit,
    QPushButton, QSizePolicy, QMessageBox, QMenu,
    QDialog, QDialogButtonBox, QScrollArea, QCheckBox, QFormLayout
)
from PyQt6.QtGui import QPixmap, QImage, QAction, QKeySequence, QFontDatabase, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QBuffer, QIODeviceBase

import easyocr
from PIL import Image

PALETTE = {
    "background": "#1A243D",      
    "border_gold": "#E6AF42",     
    "text_light": "#F0F0F0",
    "text_dark": "#1A243D",
    "widget_bg": "#5B2D3A",        
    "widget_bg_alt": "#49242F"      
}

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def is_valid_roblox_username(username):
    if not isinstance(username, str): return False
    if not (3 <= len(username) <= 20): return False
    if username.startswith('_') or username.endswith('_'): return False
    if username.count('_') > 1: return False
    if not re.fullmatch(r'[a-zA-Z0-9_]+', username): return False
    return True

class ImageDropArea(QLabel):
    image_received = pyqtSignal(QImage)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("Drop VC Attendee list Screenshot Here\nor Paste from Clipboard (Ctrl+V or Right-Click)")
        self.setWordWrap(True)
        self.setMinimumSize(300, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setObjectName("dropArea")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            image = QImage(event.mimeData().urls()[0].toLocalFile())
            if not image.isNull(): self.image_received.emit(image)
    
    def paste_image(self):
        clipboard = QApplication.clipboard()
        image = clipboard.image()
        if not image.isNull(): self.image_received.emit(image)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        paste_action = QAction("Paste", self)
        paste_action.setEnabled(QApplication.clipboard().mimeData().hasImage())
        paste_action.triggered.connect(self.paste_image)
        menu.addAction(paste_action)
        menu.exec(event.globalPos())

class SuggestionDialog(QDialog):
    def __init__(self, suggestions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm usernames")
        self.setMinimumWidth(450)
        self.checkboxes = []
        layout = QVBoxLayout(self)
        info_label = QLabel("Correct wrong usernames?\nUncheck any you wish to ignore.")
        layout.addWidget(info_label)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        scroll_content = QWidget()
        scroll_content.setObjectName("scrollAreaWidgetContents")
        
        form_layout = QFormLayout(scroll_content)
        for ocr_name, suggested_name, score in suggestions:
            checkbox = QCheckBox(f"{ocr_name}  →  {suggested_name}")
            checkbox.setChecked(True)
            self.checkboxes.append((checkbox, ocr_name, suggested_name))
            form_layout.addRow(checkbox)
        scroll_area.setWidget(scroll_content)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Correct Selected")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_replacements(self):
        replacements = {}
        for checkbox, ocr_name, suggested_name in self.checkboxes:
            if checkbox.isChecked():
                replacements[ocr_name] = suggested_name
        return replacements

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How to Use")
        layout = QVBoxLayout(self)
        help_text = """
        <b>Step 1: Get the Image</b><br>
        - Drag & drop a screenshot file into the drop area.<br>
        - OR, use a snipping tool (Win+Shift+S), then Ctrl+V or right-click to paste.
        <p><b>Step 2: Correct the Names</b><br>
        - The screenshot attendee extraction will appear in the "Attendees" text box.<br>
        - Manually review and correct any mistakes (e.g., 'O' vs '0', 'S' vs '5').
        <p><b>Step 3: Generate the Log</b><br>
        - Fill in the Event, Squad, and Host fields.<br>
        - Click "Generate Log". The app will offer corrections based on `usernames.txt`.
        <p><b>Step 4: Copy the Log</b><br>
        - Click "Copy to Clipboard" to copy the entire generated log.
        <hr>
        <b>How the Username List Works</b><br>
        - The suggestion feature is powered by a `usernames.txt` file.<br><br>
        - <b>Priority:</b> The application will <b>always prioritize and use an external `usernames.txt`</b> file if you place one in the same folder as the `.exe`. This lets you maintain your own custom list.<br><br>
        - <b>Default:</b> If no external file is found, the application uses a <b>built-in default list</b> so the feature works immediately.<br><br>
        - <b>Creation:</b> Newline seperated list of companymen, it is advised you do not create one yourself unless told by command. 
        """
        label = QLabel(help_text)
        label.setWordWrap(True)
        layout.addWidget(label)

class MainWindow(QMainWindow):
    ocr_ready_signal = pyqtSignal()
    ocr_complete_signal = pyqtSignal(list, str) 

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Themis; SELA")
        self.setGeometry(100, 100, 1000, 750)
        icon_path = resource_path('Themis.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.ocr_reader = None
        self.is_ocr_ready = False
        font_path = resource_path('IBMPlexSans-Medium.ttf')
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            self.app_font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        else:
            print("WARNING: Could not load custom font. Using default.")
            self.app_font_family = "Arial" 
        self.setup_ui()
        self.load_master_usernames()
        self.host_input.setFocus()
        self.ocr_ready_signal.connect(self.on_ocr_ready)
        self.ocr_complete_signal.connect(self.on_ocr_complete)
        self.status_label.setText("Initializing EasyOCR... This may take a moment.")
        threading.Thread(target=self.initialize_ocr, daemon=True).start()

    def load_master_usernames(self):
        self.master_usernames = set()
        
        external_path = 'usernames.txt' 
        internal_path = resource_path('usernames.txt')

        try:
            with open(external_path, 'r') as f:
                self.master_usernames = {line.strip() for line in f if line.strip()}
            self.status_label.setText(f"Loaded {len(self.master_usernames)} usernames from external file.")
            return 
        
        except FileNotFoundError:
            pass
        try:
            with open(internal_path, 'r') as f:
                self.master_usernames = {line.strip() for line in f if line.strip()}
            self.status_label.setText(f"Using default username list. Create a usernames.txt to override.")

        except FileNotFoundError:
            self.status_label.setText("No username list found. Suggestion feature disabled.")

    def setup_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("mainWidget")
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15) 
        main_layout.setSpacing(15) 

        form_layout = QVBoxLayout()
        form_layout.setSpacing(10) 
        
        form_layout.addWidget(QLabel("Event:"))
        self.event_input = QComboBox()
        self.event_input.addItems(["Combat Training", "Crate Run", "Rally", "Raid", "Patrol", "Fort Event", "Miscellaneous Event", "Mandatory Event", "PR"])
        self.event_input.view().setAlternatingRowColors(True) 
        form_layout.addWidget(self.event_input)
        
        form_layout.addWidget(QLabel("Squad:"))
        self.squad_input = QComboBox()
        self.squad_input.addItems(["1P", "1A", "1B", "1C","2P", "2A", "2B", "2C", "3P", "3A", "3B", "3C", "HQ"])
        self.squad_input.view().setAlternatingRowColors(True) 
        form_layout.addWidget(self.squad_input)
        
        form_layout.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit()
        form_layout.addWidget(self.host_input)
        
        form_layout.addWidget(QLabel("Day:"))
        self.day_input = QComboBox()
        self.day_input.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        self.day_input.setCurrentIndex(datetime.datetime.today().weekday())
        self.day_input.view().setAlternatingRowColors(True) 
        form_layout.addWidget(self.day_input)
        
        form_layout.addWidget(QLabel("Description (Optional):"))
        self.desc_input = QTextEdit()
        self.desc_input.setMinimumHeight(100) 
        form_layout.addWidget(self.desc_input)
        main_layout.addLayout(form_layout, 1)

        ocr_layout = QVBoxLayout()
        ocr_layout.setSpacing(10) 
        self.drop_area = ImageDropArea()
        self.drop_area.image_received.connect(self.run_ocr_on_image)
        paste_action = QAction("Paste Image", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self.drop_area.paste_image)
        self.addAction(paste_action)
        ocr_layout.addWidget(self.drop_area, 2)
        ocr_layout.addWidget(QLabel("Attendees:"))
        self.attendee_box = QTextEdit()
        self.attendee_box.setPlaceholderText("Extraction results will appear here...")
        ocr_layout.addWidget(self.attendee_box, 3)
        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ocr_layout.addWidget(self.status_label)
        main_layout.addLayout(ocr_layout, 2)
        
        output_layout = QVBoxLayout()
        output_layout.setSpacing(10) 
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        self.log_button = QPushButton("Generate Log")
        button_layout.addWidget(self.log_button)
        self.copy_button = QPushButton("Copy to Clipboard")
        button_layout.addWidget(self.copy_button)
        button_layout.addStretch()
        self.help_button = QPushButton("?")
        self.help_button.setFixedSize(28, 28)
        self.help_button.setObjectName("helpButton")
        self.help_button.clicked.connect(self.show_help_menu)
        button_layout.addWidget(self.help_button)
        output_layout.addLayout(button_layout)
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        output_layout.addWidget(self.output_area)
        main_layout.addLayout(output_layout, 2)

        self.log_button.clicked.connect(self.generate_log_entry)
        self.copy_button.clicked.connect(self.copy_log_to_clipboard)

    def initialize_ocr(self):
        try:
            self.ocr_reader = easyocr.Reader(['en'])
            self.is_ocr_ready = True
            self.ocr_ready_signal.emit()
        except Exception as e:
            self.is_ocr_ready = False
            self.ocr_complete_signal.emit([], f"Failed to initialize EasyOCR: {e}")

    def on_ocr_ready(self):
        self.status_label.setText("Ready. Drop or paste an image.")

    def on_ocr_complete(self, usernames, error_message):
        self.attendee_box.clear()
        if error_message:
            QMessageBox.critical(self, "OCR Error", error_message)
            self.attendee_box.setPlaceholderText("OCR failed. Please try again or enter names manually.")
            self.status_label.setText("OCR failed.")
        elif usernames:
            self.attendee_box.setPlainText("\n".join(usernames))
            self.status_label.setText(f"Successfully extracted {len(usernames)} names.")
        else:
            self.attendee_box.setPlaceholderText("No usernames found. You can enter them manually.")
            self.status_label.setText("No usernames found in the image.")

    def run_ocr_on_image(self, q_image):
        if not self.is_ocr_ready:
            QMessageBox.warning(self, "OCR Not Ready", "The OCR engine is still initializing. Please wait.")
            return
        self.drop_area.setPixmap(QPixmap.fromImage(q_image).scaled(
            self.drop_area.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.attendee_box.setText("Processing OCR...")
        self.status_label.setText("Processing image...")
        QApplication.processEvents()
        buffer = QBuffer()
        buffer.open(QIODeviceBase.OpenModeFlag.ReadWrite)
        q_image.save(buffer, "PNG")
        pil_image = Image.open(io.BytesIO(buffer.data())).convert("RGB")
        numpy_image = np.array(pil_image)
        threading.Thread(target=self._process_in_thread, args=(numpy_image,), daemon=True).start()

    def _process_in_thread(self, image_data):
        try:
            results = self.ocr_reader.readtext(image_data)
            full_text = ' '.join([res[1] for res in results])
            pattern = r'\]\s*([a-zA-Z0-9_]+)'
            usernames = re.findall(pattern, full_text)
            self.ocr_complete_signal.emit(usernames, "")
        except Exception as e:
            self.ocr_complete_signal.emit([], str(e))
            
    def show_help_menu(self):
        menu = QMenu(self)
        how_to_action = QAction("How to Use...", self)
        how_to_action.triggered.connect(lambda: HelpDialog(self).exec())
        menu.addAction(how_to_action)
        about_action = QAction("About...", self)
        about_action.triggered.connect(lambda: QMessageBox.about(self, "About Themis", "Released under Themis; for use in 2C.\nMade by OyundaEmirYT"))
        menu.addAction(about_action)
        menu.exec(self.help_button.mapToGlobal(self.help_button.rect().bottomLeft()))

    def generate_log_entry(self):
        error_messages = []
        host = self.host_input.text().strip()


        if not host:
            error_messages.append("- Host name is missing.")
        elif not is_valid_roblox_username(host):
            error_messages.append(f"- Host username '{host}' is invalid.")

        all_names_from_box = [line.strip() for line in self.attendee_box.toPlainText().split('\n') if line.strip()]
        
        if self.master_usernames:
            suggestions = []
            SIMILARITY_THRESHOLD = 0.8 
            for name in all_names_from_box:
                if name not in self.master_usernames:
                    potential_matches = difflib.get_close_matches(name, self.master_usernames, n=1, cutoff=SIMILARITY_THRESHOLD)
                    if potential_matches:
                        best_match = potential_matches[0]
                        score = difflib.SequenceMatcher(None, name, best_match).ratio()
                        suggestions.append((name, best_match, score))
            if suggestions:
                dialog = SuggestionDialog(suggestions, self)
                if dialog.exec(): 
                    replacements = dialog.get_selected_replacements()
                    all_names_from_box = [replacements.get(name, name) for name in all_names_from_box]
                    self.attendee_box.setPlainText("\n".join(all_names_from_box))
                else: 
                    self.status_label.setText("Log generation cancelled.")
                    return

        invalid_attendees = [name for name in all_names_from_box if not is_valid_roblox_username(name)]
        if invalid_attendees:
            error_list = "\n  - ".join(invalid_attendees)
            error_messages.append(f"- The following attendee usernames are invalid:\n  - {error_list}")

        final_attendees = [name for name in all_names_from_box if name.lower() != host.lower()]
        event_type = self.event_input.currentText()
        num_attendees = len(final_attendees)
        min_required = 1 if event_type == "Crate Run" else 2
        
        if num_attendees < min_required:
            plural_s = "" if min_required == 1 else "s"
            error_messages.append(f"- A '{event_type}' requires at least {min_required} attendee{plural_s} (excluding host). You only have {num_attendees}.")

        if error_messages:
            full_error_message = "Please fix the following issues before generating the log:\n\n" + "\n\n".join(error_messages)
            QMessageBox.warning(self, "Validation Errors", full_error_message)
            return

        if host not in all_names_from_box:
             reply = QMessageBox.question(self, 'Host Not in List',
                                         f"The host '{host}' is not in the VC screenshot. Is this the correct screenshot?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
             if reply == QMessageBox.StandardButton.No:
                 return

        attendees_string = "\n".join(final_attendees) if final_attendees else "N/A"
        log_entry = (f"Event: {self.event_input.currentText()}\n"
                     f"Squad: {self.squad_input.currentText()}\n"
                     f"Host: {host}\n"
                     f"Day: {self.day_input.currentText().lower()}\n"
                     f"Description: {self.desc_input.toPlainText().strip() or 'N/A'}\n"
                     f"Attendees:\n{attendees_string}")
        self.output_area.setPlainText(log_entry.strip())
        self.status_label.setText("Log generated successfully!")

    def copy_log_to_clipboard(self):
        log_text = self.output_area.toPlainText()
        if not log_text:
            QMessageBox.warning(self, "Nothing to Copy", "Please generate a log entry first.")
            return
        QApplication.clipboard().setText(log_text)
        self.status_label.setText("Log copied to clipboard!")


    def get_stylesheet(self):
        arrow_path = resource_path('arrow.png').replace('\\', '/')
        return f"""
            QWidget {{ 
                font-family: '{self.app_font_family}';
                color: {PALETTE['text_light']}; 
                font-size: 14px; 
            }}
            QMainWindow, QDialog {{
                background-color: {PALETTE['background']}; 
            }}
            QComboBox, QLineEdit, QTextEdit {{
                background-color: {PALETTE['widget_bg']};
                border: 1px solid {PALETTE['border_gold']};
                border-radius: 4px; 
                padding: 5px;
            }}
            QTextEdit::placeholderText {{ 
                color: #888; 
            }}
            QPushButton {{
                background-color: {PALETTE['border_gold']}; 
                color: {PALETTE['text_dark']};
                font-size: 14px; 
                font-weight: bold; 
                padding: 8px; 
                border-radius: 5px;
                border: none;
            }}
            QPushButton:hover {{ 
                background-color: #FFD700; 
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 1px;
                border-left-color: {PALETTE['border_gold']};
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-image: url({arrow_path});
                background-position: center;
                background-repeat: no-repeat;
            }}
            QComboBox::down-arrow {{
                width: 0px;
                height: 0px;
            }}
            QComboBox::drop-down:hover {{
                background-color: {PALETTE['widget_bg_alt']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {PALETTE['widget_bg']};
                border: 1px solid {PALETTE['border_gold']};
                outline: 0px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 5px;
                min-height: 25px;
            }}
            QComboBox QAbstractItemView::item:alternate {{
                background-color: {PALETTE['widget_bg_alt']};
            }}
            QComboBox QAbstractItemView::item:selected,
            QComboBox QAbstractItemView::item:hover {{
                background-color: {PALETTE['border_gold']};
                color: {PALETTE['text_dark']};
            }}
            QMenu {{
                background-color: {PALETTE['widget_bg']};
                border: 1px solid {PALETTE['border_gold']};
                padding: 5px;
            }}
            QMenu::item {{
                padding: 5px 15px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background-color: {PALETTE['border_gold']};
                color: {PALETTE['text_dark']};
            }}
            QScrollArea, #scrollAreaWidgetContents {{
                background-color: transparent;
                border: none;
            }}
            QCheckBox {{
                spacing: 10px;
                padding: 5px 0;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid {PALETTE['border_gold']};
                background-color: transparent;
            }}
            QCheckBox::indicator:hover {{
                background-color: {PALETTE['widget_bg_alt']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {PALETTE['border_gold']};
                border: 1px solid {PALETTE['border_gold']};
            }}
            #dropArea {{
                color: {PALETTE['border_gold']}; 
                border: 2px dashed {PALETTE['border_gold']}; 
                border-radius: 10px;
            }}
            #helpButton {{ 
                padding: 4px 8px; 
            }}
            #statusLabel {{
                color: #A0B0D0;
                font-size: 12px;
                padding: 5px;
            }}
        """

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow() 
    stylesheet = window.get_stylesheet()
    app.setStyleSheet(stylesheet)  
    window.show()
    sys.exit(app.exec())