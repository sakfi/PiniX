import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QListWidget, QLabel, QStackedWidget,
                             QPushButton, QGridLayout, QScrollArea, QLineEdit,
                             QInputDialog, QMessageBox, QMenu, QComboBox, QToolButton)
from PyQt6.QtGui import QAction
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
        
        # Video Container
        self.video_container = QWidget()
        self.video_layout = QVBoxLayout(self.video_container)
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.video_container, stretch=1)

        # Controls Container
        self.controls_container = QWidget()
        self.controls_layout = QHBoxLayout(self.controls_container)
        self.controls_layout.setContentsMargins(5, 5, 5, 5)
        
        self.btn_play_pause = QPushButton("Play/Pause")
        self.btn_stop = QPushButton("Stop")
        self.btn_fullscreen = QPushButton("Fullscreen")
        
        self.controls_layout.addWidget(self.btn_play_pause)
        self.controls_layout.addWidget(self.btn_stop)
        self.controls_layout.addWidget(self.btn_fullscreen)
        self.layout.addWidget(self.controls_container)
        
        if MPV_AVAILABLE:
            self.video_container.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors)
            self.video_container.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
            # Create mpv instance taking control of the HWND
            self.player = mpv.MPV(wid=str(int(self.video_container.winId())), vo='gpu', hwdec='auto')
            
            # Connect buttons
            self.btn_play_pause.clicked.connect(self.toggle_play_pause)
            self.btn_stop.clicked.connect(self.stop_playback)
            self.btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        else:
            self.player = None
            lbl = QLabel("MPV Library Not Found\nPlease download mpv lib for Windows and place it in the application folder.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_layout.addWidget(lbl)

    def play(self, url):
        if self.player:
            self.player.play(url)

    def toggle_play_pause(self):
        if self.player:
            self.player.pause = not self.player.pause
            
    def stop_playback(self):
        if self.player:
            self.player.command('stop')
            
    def toggle_fullscreen(self):
        # Fullscreen in embedded mpv on Windows requires resizing the parent QMainWindow
        window = self.window()
        if window.isFullScreen():
            window.showNormal()
        else:
            window.showFullScreen()

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
        self.sidebar.addItem("Favorites")
        self.sidebar.addItem("Settings")
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

        search_layout = QHBoxLayout()
        self.search_bar = QComboBox()
        self.search_bar.setEditable(True)
        self.search_bar.lineEdit().setPlaceholderText("Search channels...")
        search_layout.addWidget(self.search_bar, stretch=1)
        
        self.btn_sort = QToolButton()
        self.btn_sort.setText("Sort ▼")
        self.btn_sort.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        sort_menu = QMenu(self)
        self.action_sort_az = QAction("A-Z", self)
        self.action_sort_za = QAction("Z-A", self)
        self.action_sort_disable = QAction("Default Order", self)
        sort_menu.addActions([self.action_sort_az, self.action_sort_za, self.action_sort_disable])
        self.btn_sort.setMenu(sort_menu)
        search_layout.addWidget(self.btn_sort)
        
        self.page_live_tv_layout.addLayout(search_layout)

        self.channels_list = QListWidget()
        self.page_live_tv_layout.addWidget(self.channels_list)

        self.stack.addWidget(self.page_live_tv)

        #   Page 1: Settings
        self.page_settings = QWidget()
        self.page_settings_layout = QVBoxLayout(self.page_settings)
        
        lbl_settings = QLabel("Provider Settings")
        lbl_settings.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.page_settings_layout.addWidget(lbl_settings)

        self.providers_list = QListWidget()
        self.page_settings_layout.addWidget(self.providers_list)

        btn_layout = QHBoxLayout()
        self.btn_add_provider = QPushButton("Add Provider")
        self.btn_remove_provider = QPushButton("Remove Selected")
        btn_layout.addWidget(self.btn_add_provider)
        btn_layout.addWidget(self.btn_remove_provider)
        self.page_settings_layout.addLayout(btn_layout)

        self.stack.addWidget(self.page_settings)

        # Context menu for favorites
        self.channels_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.channels_list.customContextMenuRequested.connect(self.show_channel_context_menu)

        # Connect signals
        self.sidebar.currentRowChanged.connect(self.on_sidebar_changed)
        self.channels_list.itemDoubleClicked.connect(self.on_channel_selected)
        self.search_bar.currentTextChanged.connect(self.filter_channels)
        self.search_bar.lineEdit().returnPressed.connect(self.save_search_history)
        self.action_sort_az.triggered.connect(lambda: self.sort_channels(Qt.SortOrder.AscendingOrder))
        self.action_sort_za.triggered.connect(lambda: self.sort_channels(Qt.SortOrder.DescendingOrder))
        self.action_sort_disable.triggered.connect(self.disable_sorting)
        self.btn_add_provider.clicked.connect(self.add_provider)
        self.btn_remove_provider.clicked.connect(self.remove_provider)

        # Load Initialization Data
        self.load_search_history()
        self.load_providers()

    def on_sidebar_changed(self, index):
        item = self.sidebar.item(index)
        if not item: return
        text = item.text()
        
        if text == "Live TV":
            self.stack.setCurrentWidget(self.page_live_tv)
            self.load_providers()
        elif text == "Favorites":
            self.stack.setCurrentWidget(self.page_live_tv)
            self.load_favorites_ui()
        elif text == "Settings":
            self.stack.setCurrentWidget(self.page_settings)
            self.refresh_settings_ui()
        else:
            self.stack.setCurrentWidget(self.page_live_tv)

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

    def show_channel_context_menu(self, pos):
        item = self.channels_list.itemAt(pos)
        if item:
            menu = QMenu()
            add_fav_action = menu.addAction("Add to Favorites")
            rem_fav_action = menu.addAction("Remove from Favorites")
            
            action = menu.exec(self.channels_list.mapToGlobal(pos))
            if action == add_fav_action:
                self.add_favorite(item)
            elif action == rem_fav_action:
                self.remove_favorite(item)

    def add_favorite(self, item):
        name = item.text()
        url = item.toolTip()
        fav_str = f"{name}:::{url}"
        
        favorites = self.manager.load_favorites()
        if fav_str not in favorites:
            favorites.append(fav_str)
            self.manager.save_favorites(favorites)
            QMessageBox.information(self, "Favorites", f"Added '{name}' to favorites.")

    def remove_favorite(self, item):
        name = item.text()
        url = item.toolTip()
        fav_str = f"{name}:::{url}"
        
        favorites = self.manager.load_favorites()
        if fav_str in favorites:
            favorites.remove(fav_str)
            self.manager.save_favorites(favorites)
            QMessageBox.information(self, "Favorites", f"Removed '{name}' from favorites.")
            
        if self.sidebar.currentItem() and self.sidebar.currentItem().text() == "Favorites":
            self.load_favorites_ui()

    def load_favorites_ui(self):
        self.channels_list.clear()
        favorites = self.manager.load_favorites()
        for fav in favorites:
            if ":::" in fav:
                name, url = fav.split(":::", 1)
                self.channels_list.addItem(name)
                self.channels_list.item(self.channels_list.count()-1).setToolTip(url)

    def refresh_settings_ui(self):
        self.providers_list.clear()
        providers = self.settings.get_strv("providers")
        for p in providers:
            if ":::" in p:
                name = p.split(":::")[0]
                url = p.split(":::")[2]
                self.providers_list.addItem(f"{name} ({url})")
            else:
                self.providers_list.addItem(p)

    def add_provider(self):
        name, ok1 = QInputDialog.getText(self, "Add Provider", "Provider Name (e.g. My IPTV):")
        if ok1 and name:
            url, ok2 = QInputDialog.getText(self, "Add Provider", "Playlist URL or Local Path:")
            if ok2 and url:
                new_prov = f"{name}:::url:::{url}::::::"
                providers = self.settings.get_strv("providers")
                providers.append(new_prov)
                self.settings.set_strv("providers", providers)
                self.refresh_settings_ui()
                QMessageBox.information(self, "Success", "Provider added! Go back to Live TV to load it.")

    def remove_provider(self):
        selected = self.providers_list.currentRow()
        if selected >= 0:
            providers = self.settings.get_strv("providers")
            if selected < len(providers):
                del providers[selected]
                self.settings.set_strv("providers", providers)
                self.refresh_settings_ui()

    def filter_channels(self, text):
        search_text = text.lower()
        for i in range(self.channels_list.count()):
            item = self.channels_list.item(i)
            # Case-insensitive substring match
            item.setHidden(search_text not in item.text().lower())

    def save_search_history(self):
        text = self.search_bar.currentText().strip()
        if not text: return
        history = self.settings.get_strv("search_history")
        if text in history:
            history.remove(text)
        history.insert(0, text) # Keep newest at the top
        # Limit to 10 items
        history = history[:10]
        self.settings.set_strv("search_history", history)
        
        # Refresh combo box silently
        self.search_bar.blockSignals(True)
        self.search_bar.clear()
        self.search_bar.addItems(history)
        self.search_bar.setCurrentText(text)
        self.search_bar.blockSignals(False)

    def load_search_history(self):
        self.search_bar.blockSignals(True)
        history = self.settings.get_strv("search_history")
        self.search_bar.addItems(history)
        self.search_bar.setCurrentIndex(-1)
        self.search_bar.blockSignals(False)

    def sort_channels(self, order):
        self.channels_list.setSortingEnabled(True)
        self.channels_list.sortItems(order)

    def disable_sorting(self):
        self.channels_list.setSortingEnabled(False)
        # Reload current view to restore original M3U array order
        text = ""
        if self.sidebar.currentItem():
            text = self.sidebar.currentItem().text()
            
        if text == "Favorites":
            self.load_favorites_ui()
        else:
            self.load_providers()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Simple Dark Mode styling
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
