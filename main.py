import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QListWidget, QLabel, QStackedWidget,
                             QPushButton, QGridLayout, QScrollArea)
from PyQt6.QtCore import Qt

from pinix.settings import Settings
from pinix.common import Manager, Provider

try:
    import mpv
    MPV_AVAILABLE = True
except OSError:
    # On Windows, python-mpv requires mpv-2.dll in PATH or current directory.
    MPV_AVAILABLE = False
    print("Warning: mpv library not found. Video playback will be disabled.")
except ImportError:
    MPV_AVAILABLE = False
    print("Warning: python-mpv not installed.")

class PlayerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        if MPV_AVAILABLE:
            self.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors)
            self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
            # Create mpv instance taking control of the HWND
            self.player = mpv.MPV(wid=str(int(self.winId())), vo='gpu', hwdec='auto')
        else:
            self.player = None
            lbl = QLabel("MPV Library Not Found\nPlease download mpv lib for Windows and place it in the application folder.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(lbl)

    def play(self, url):
        if self.player:
            self.player.play(url)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PiniX")
        self.resize(1024, 768)

        self.settings = Settings()
        self.manager = Manager(self.settings)

        # Root central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # 1. Sidebar for Categories
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.addItem("Live TV")
        self.sidebar.addItem("Movies")
        self.sidebar.addItem("Series")
        main_layout.addWidget(self.sidebar)

        # 2. Main Content Stack
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, stretch=1)

        #   Page 0: Player + Channels List (Split View)
        self.page_live_tv = QWidget()
        self.page_live_tv_layout = QVBoxLayout(self.page_live_tv)
        
        self.player_widget = PlayerWidget(self)
        self.player_widget.setMinimumHeight(450)
        self.page_live_tv_layout.addWidget(self.player_widget)

        self.channels_list = QListWidget()
        self.page_live_tv_layout.addWidget(self.channels_list)

        self.stack.addWidget(self.page_live_tv)

        # Connect signals
        self.sidebar.currentRowChanged.connect(self.on_sidebar_changed)
        self.channels_list.itemDoubleClicked.connect(self.on_channel_selected)

        # Load Providers
        self.load_providers()

    def on_sidebar_changed(self, index):
        self.stack.setCurrentIndex(0) # For now always show the main player page

    def load_providers(self):
        providers_list = self.settings.get_strv("providers")
        if providers_list:
            p = providers_list[0]
            if ":::" in p:
                provider = Provider(None, p)
                self.channels_list.addItem(f"Loading {provider.name}...")
                
                # Fetch playlist (blocking for simplicity right now)
                if self.manager.get_playlist(provider):
                    print("Playlist downloaded/cached.")
                    self.manager.check_playlist(provider)
                    self.manager.load_channels(provider)
                    
                    self.channels_list.clear() # clear loading message
                    
                    for channel in provider.channels:
                        # Storing URL in toolTip hack for quick retrieval
                        item = self.channels_list.addItem(channel.name or "Unknown Channel")
                        self.channels_list.item(self.channels_list.count()-1).setToolTip(channel.url)
                        
                else:
                    self.channels_list.clear()
                    self.channels_list.addItem("Failed to download playlist.")

    def on_channel_selected(self, item):
        url = item.toolTip()
        if url:
             print("Playing:", url)
             self.player_widget.play(url)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Simple Dark Mode styling
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
