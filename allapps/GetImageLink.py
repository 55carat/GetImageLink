import sys
import os
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QComboBox, QPushButton, 
                               QLineEdit, QFileDialog, QSystemTrayIcon, QStyle, QMessageBox, QSizePolicy, QSpacerItem, QSpinBox)
from PySide6.QtCore import Qt

# Import the core logic from the existing Instant_Fill script
from Instant_Fill import ChromeBrowserController, ChromeLaunchThread, ExcelProcessThread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Website Launcher")
        self.resize(700, 300)
        
        # Center on screen
        try:
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - 700) // 2
            y = (screen.height() - 300) // 2
            self.move(x, y)
        except Exception:
            pass
            
        self.controller = ChromeBrowserController(port=9222)
        
        # System Tray Icon for Notifications
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray_icon.show()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Add a stretch at the top to push content down
        main_layout.addSpacerItem(QSpacerItem(20, 100, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Dummy font creation since label removed
        font = self.font()
        font.setPointSize(16)

        # --- Region Selection ---
        region_layout = QHBoxLayout()
        region_layout.setAlignment(Qt.AlignCenter)
        region_label = QLabel("Select Amazon Region:")
        region_label.setFont(font)
        
        self.regions = {
            "Amazon US (.com)": "www.amazon.com",
            "Amazon India (.in)": "www.amazon.in",
            "Amazon UK (.co.uk)": "www.amazon.co.uk",
            "Amazon Canada (.ca)": "www.amazon.ca",
            "Amazon Mexico (.com.mx)": "www.amazon.com.mx",
            "Amazon Brazil (.com.br)": "www.amazon.com.br",
            "Amazon Germany (.de)": "www.amazon.de",
            "Amazon France (.fr)": "www.amazon.fr",
            "Amazon Italy (.it)": "www.amazon.it",
            "Amazon Spain (.es)": "www.amazon.es",
            "Amazon Japan (.co.jp)": "www.amazon.co.jp",
            "Amazon Australia (.com.au)": "www.amazon.com.au",
            "Amazon UAE (.ae)": "www.amazon.ae",
            "Amazon Saudi Arabia (.sa)": "www.amazon.sa",
            "Amazon Singapore (.sg)": "www.amazon.sg",
        }
        
        self.region_combo = QComboBox()
        self.region_combo.addItems(list(self.regions.keys()))
        self.region_combo.setFont(font)
        self.region_combo.setMinimumWidth(300)
        self.region_combo.setMinimumHeight(40)
        
        region_layout.addWidget(region_label)
        region_layout.addWidget(self.region_combo)

        # Add tab count next to region dropdown
        tabs_label = QLabel("Tabs:")
        tabs_label.setFont(font)
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setFont(font)
        self.concurrent_spin.setMinimum(1)
        self.concurrent_spin.setMaximum(50)
        self.concurrent_spin.setValue(5)
        self.concurrent_spin.setMinimumHeight(40)
        self.concurrent_spin.setMinimumWidth(120)

        region_layout.addWidget(tabs_label)
        region_layout.addWidget(self.concurrent_spin)

        main_layout.addLayout(region_layout)

        # --- File Selection ---
        self.excel_widget = QWidget()
        excel_layout = QVBoxLayout(self.excel_widget)
        excel_layout.setAlignment(Qt.AlignCenter)
        
        file_selection_layout = QHBoxLayout()
        file_selection_layout.setContentsMargins(0, 0, 0, 0)
        
        self.browse_btn = QPushButton("Browse Excel")
        self.browse_btn.setFont(font)
        self.browse_btn.setMinimumHeight(40)
        self.browse_btn.clicked.connect(self.on_browse)
        
        self.excel_path_input = QLineEdit()
        self.excel_path_input.setFont(font)
        self.excel_path_input.setPlaceholderText("Select Excel File First...")
        self.excel_path_input.setReadOnly(True)
        self.excel_path_input.setMinimumWidth(500)
        self.excel_path_input.setMinimumHeight(40)
        
        file_selection_layout.addWidget(self.browse_btn)
        file_selection_layout.addWidget(self.excel_path_input)
        
        excel_layout.addLayout(file_selection_layout)
        main_layout.addWidget(self.excel_widget)
        
        # --- App Control ---
        control_layout = QHBoxLayout()
        control_layout.setAlignment(Qt.AlignCenter)
        
        self.launch_btn = QPushButton("Launch Chrome && Process")
        self.launch_btn.setFont(font)
        self.launch_btn.setMinimumHeight(40)
        self.launch_btn.setEnabled(False) # Disabled until file is selected
        self.launch_btn.clicked.connect(self.on_launch)
        
        self.stop_btn = QPushButton("Stop App")
        self.stop_btn.setFont(font)
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setStyleSheet("background-color: #ff4c4c; color: white;")
        self.stop_btn.clicked.connect(self.on_stop)
        
        control_layout.addWidget(self.launch_btn)
        control_layout.addWidget(self.stop_btn)
        
        main_layout.addLayout(control_layout)
        
        
        
        self.status_label = QLabel("")
        self.status_label.setFont(font)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setMinimumHeight(50)
        main_layout.addWidget(self.status_label)
        
        # Add a stretch at the bottom
        main_layout.addSpacerItem(QSpacerItem(20, 100, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def show_coming_soon(self):
        QMessageBox.information(self, "Coming Soon", "This feature is coming soon.")
        
    def on_stop(self):
        self.stop_btn.setEnabled(False)
        self.stop_btn.setText("Stopping...")
        if hasattr(self, "process_thread") and self.process_thread.isRunning():
            self.process_thread.stop_requested = True
            # The app will quit when the thread emits finished_signal, see below.
        else:
            self._quit_app()

    def _quit_app(self, *args):
        # Disconnect Playwright safely and kill the app
        if getattr(self, "controller", None):
            self.controller.disconnect()
        QApplication.quit()

    def on_launch(self):
        self.launch_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.thread = ChromeLaunchThread(self.controller)
        self.thread.status_signal.connect(self.update_status)
        self.thread.notification_signal.connect(self.show_notification)
        self.thread.finished_signal.connect(self.on_launch_finished)
        self.thread.start()
            
    def update_status(self, text):
        self.status_label.setText(text)
        
    def show_notification(self, title, message):
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 5000)
        
    def on_launch_finished(self, success, is_running):
        if success:
            excel_path = self.excel_path_input.text()
            domain = self.regions.get(self.region_combo.currentText())
            if excel_path:
                self.process_thread = ExcelProcessThread(self.controller, excel_path, domain, batch_size=self.concurrent_spin.value())
                self.process_thread.status_signal.connect(self.update_status)
                self.process_thread.notification_signal.connect(self.show_notification)
                self.process_thread.retry_save_signal.connect(self.show_save_error_dialog, type=Qt.BlockingQueuedConnection)
                self.process_thread.finished_signal.connect(self.on_process_finished)
                self.process_thread.start()
            else:
                self.launch_btn.setEnabled(True)
                self.browse_btn.setEnabled(True)
        else:
            self.launch_btn.setEnabled(True)
            self.browse_btn.setEnabled(True)
            
    def on_browse(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls *.xlsm)")
        if file_path:
            self.excel_path_input.setText(file_path)
            self.launch_btn.setEnabled(True)

    def show_save_error_dialog(self):
        QMessageBox.warning(self, "Excel File Open", "The Excel sheet is currently open.\nPlease close the file in Excel and click OK to save changes.", QMessageBox.Ok)

    def on_process_finished(self, success):
        self.launch_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        if getattr(self, "process_thread", None) and getattr(self.process_thread, "stop_requested", False):
            self._quit_app()
        elif success:
            self.show_notification("Process Complete", "Finished processing all valid rows in the Excel file.")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        import playwright
    except ImportError:
        print("Playwright not found!")
        print("Please install it using: pip install playwright")
        print("Then run: playwright install chromium")
        sys.exit(1)
    
    main()
