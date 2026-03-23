import sys
import os
import subprocess
import socket
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout,
    QLabel, QPushButton
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer


TARGET_SCRIPT = "Allappui.py"


# 🔹 Check internet
def is_internet_available():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except:
        return False


# 🔹 Worker thread for git pull
class UpdateWorker(QThread):
    finished = Signal(bool)

    def run(self):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
            process = subprocess.Popen(
                ["git", "pull"],
                cwd=os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
    
            process.communicate()
            self.finished.emit(True)
    
        except:
            self.finished.emit(False)


class UpdateDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Updater")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()

        self.label = QLabel("Checking...")
        self.label.setAlignment(Qt.AlignCenter)

        self.button = QPushButton("")
        self.button.setVisible(False)

        layout.addWidget(self.label)
        layout.addWidget(self.button)

        self.setLayout(layout)

        self.center_window()
        self.start_update()

    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 300) // 2
        y = (screen.height() - 150) // 2
        self.move(x, y)

    def start_update(self):
        if not is_internet_available():
            self.label.setText("No Internet Connection")
            self.button.setText("Retry")
            self.button.setVisible(True)
            self.button.clicked.connect(self.retry)
            return

        self.label.setText("Updating...")
        self.button.setVisible(False)

        self.worker = UpdateWorker()
        self.worker.finished.connect(self.update_done)
        self.worker.start()

    def retry(self):
        self.button.setVisible(False)
        self.start_update()

    def update_done(self, success):
        self.label.setText("Update Complete")

        self.button.setText("Launch")
        self.button.setVisible(True)
        self.button.clicked.connect(self.launch_app)

        # 🔥 Auto launch after 3 sec
        QTimer.singleShot(3000, self.launch_app)

    def launch_app(self):
        script_path = os.path.join(os.getcwd(), TARGET_SCRIPT)

        if os.path.exists(script_path):
            subprocess.Popen([sys.executable, script_path])

        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = UpdateDialog()
    dialog.show()
    sys.exit(app.exec())