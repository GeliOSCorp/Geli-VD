"""Geli-VD UI palette. Contrast-first styles for both themes."""
BASE = '''
QWidget {font-family: "Segoe UI", "Inter", Arial; font-size: 12px;}
QMainWindow {border:0;}
QLabel {background:transparent; border:0;}
QLabel#brandIcon {background:transparent;}
QLabel#brandTitle {font-size:24px; font-weight:800; background:transparent;}
QLabel#brandSubtitle {font-size:12px; background:transparent;}
QLabel#brandSignature {font-size:20px; font-weight:800; background:transparent;}
QLabel#section {font-size:12px;font-weight:800;letter-spacing:.4px;background:transparent;}
QLabel#muted {font-size:12px;background:transparent;}
QLabel#videoTitle {font-size:15px;font-weight:700;background:transparent;}
QLabel#infoTitle {font-size:13px;font-weight:700;background:transparent;}
QFrame#hero {border-radius:18px;}
QFrame#card {border-radius:16px;}
QFrame#infoPanel {border-radius:12px;}
QDialog QLabel {line-height:1.4;}
QFrame#separator {border:0;max-height:1px;}
QLineEdit,QComboBox,QTextEdit,QListWidget {border-radius:9px;padding:9px 11px;selection-background-color:#7852eb;}
QLineEdit:focus,QComboBox:focus,QTextEdit:focus,QListWidget:focus {border:1px solid #9275ee;}
QPushButton {border-radius:9px;padding:10px 14px;font-weight:600;min-height:16px;}
QPushButton:disabled {color:#9996a8;}
QPushButton#primary {color:white;font-weight:700;}
QPushButton#platform {text-align:left;}
QCheckBox {spacing:9px;background:transparent;min-height:24px;padding:2px 0;}
QCheckBox::indicator {width:18px;height:18px;border-radius:5px;}
QCheckBox::indicator:checked {image:none;}
QCheckBox:disabled {color:#9290a0;}
QProgressBar {border:0;border-radius:6px;height:13px;text-align:center;font-weight:700;}
QProgressBar::chunk {border-radius:6px;}
QMenuBar {padding:4px 8px;}
QMenuBar::item {padding:7px 12px;border-radius:6px;background:transparent;}
QMenu {padding:6px;}
QMenu::item {padding:8px 16px;border-radius:6px;}
QScrollBar:vertical {width:10px;margin:2px;}
QScrollBar::handle:vertical {border-radius:5px;min-height:30px;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0px;}
QSplitter::handle {width:9px;background:transparent;}
QToolTip {padding:7px;border-radius:5px;}
'''

DARK = BASE + '''
QWidget {background-color:#161521;color:#eeeaf7;}
QMainWindow {background-color:#161521;}
QFrame#hero {background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #35205a,stop:0.50 #27213e,stop:1 #1e2342);border:1px solid #62488e;}
QFrame#card {background:#211e2f;border:1px solid #484055;}
QFrame#infoPanel {background:#29263a;border:1px solid #403950;}
QLabel#brandTitle {color:#faf6ff;}
QLabel#brandSubtitle {color:#d1c5e5;}
QLabel#brandSignature {color:#e2ceff;}
QLabel#section {color:#c9b5ff;}
QLabel#muted {color:#c4bccc;}
QLabel#videoTitle {color:#fff;}
QLabel#infoTitle {color:#e3d5ff;}
QLabel#cover {background:#2c283d;color:#bbb3cf;border:1px solid #494159;border-radius:11px;}
QLineEdit,QComboBox,QTextEdit,QListWidget {background:#292639;color:#f3eefb;border:1px solid #514a65;}
QComboBox QAbstractItemView {background:#282537;color:#f4eefb;selection-background-color:#6750a8;}
QPushButton {background:#353047;color:#f1ecfa;border:1px solid #514863;}
QPushButton:hover {background:#48405e;border-color:#8270a7;}
QPushButton:pressed {background:#574a78;}
QPushButton#primary {background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6844e3,stop:1 #8954e9);border:1px solid #9167ef;}
QPushButton#primary:hover {background:#8757f2;}
QCheckBox {color:#eee8f7;}
QCheckBox::indicator {background:#302b40;border:2px solid #a7a0bc;}
QCheckBox::indicator:hover {border:2px solid #c9b4ff;}
QCheckBox::indicator:checked {background:#7b50ec;border:2px solid #c7b4ff;image:url(:/qt-project.org/styles/commonstyle/images/checkbox_checked.png);}
QProgressBar {background:#343046;color:#fff;}
QProgressBar::chunk {background:#8758f4;}
QMenuBar,QMenu {background:#211c30;color:#eee9f8;}
QMenuBar::item:selected,QMenu::item:selected {background:#45345f;}
QScrollBar::handle:vertical {background:#5c526e;}
QFrame#separator {background:#504661;}
QToolTip {background:#332b48;color:#fff;border:1px solid #6b568d;}
'''

LIGHT = BASE + '''
QWidget {background-color:#f6f7fb;color:#28243a;}
QMainWindow {background-color:#f6f7fb;}
QFrame#hero {background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #f8f5ff,stop:0.53 #ede7fc,stop:1 #e1eafe);border:1px solid #c9bafa;}
QFrame#card {background:#fff;border:1px solid #dcd9e8;}
QFrame#infoPanel {background:#f5f3fc;border:1px solid #e3ddef;}
QLabel#brandTitle {color:#392578;}
QLabel#brandSubtitle {color:#60587b;}
QLabel#brandSignature {color:#6340c7;}
QLabel#section {color:#6843c7;}
QLabel#muted {color:#625b75;}
QLabel#videoTitle {color:#262137;}
QLabel#infoTitle {color:#43346b;}
QLabel#cover {background:#f1eff9;color:#756d83;border:1px solid #e0d9ed;border-radius:11px;}
QLineEdit,QComboBox,QTextEdit,QListWidget {background:#fff;color:#29253a;border:1px solid #d7d2e5;}
QComboBox QAbstractItemView {background:#fff;color:#29253a;selection-background-color:#ddd2f5;}
QPushButton {background:#f0edf8;color:#302747;border:1px solid #ddd6ed;}
QPushButton:hover {background:#e6dcfa;border-color:#c9b8ef;}
QPushButton:pressed {background:#d7c8f3;}
QPushButton#primary {background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6446dd,stop:1 #8855e8);border:1px solid #7951e5;}
QPushButton#primary:hover {background:#7b51eb;}
QCheckBox {color:#2d2939;}
QCheckBox::indicator {background:#fff;border:2px solid #9c93b3;}
QCheckBox::indicator:hover {border:2px solid #8c6ce6;}
QCheckBox::indicator:checked {background:#764fe5;border:2px solid #764fe5;image:url(:/qt-project.org/styles/commonstyle/images/checkbox_checked.png);}
QProgressBar {background:#e7e1f1;color:#34294b;}
QProgressBar::chunk {background:#7950ed;}
QMenuBar,QMenu {background:#f4f1fa;color:#282139;}
QMenuBar::item:selected,QMenu::item:selected {background:#e4dcf5;}
QScrollBar::handle:vertical {background:#c6bdd8;}
QFrame#separator {background:#e0d8ee;}
QToolTip {background:#fff;color:#292339;border:1px solid #c8bee3;}
'''

# Geli-VD 1.8.7: campos protagonistas, navegación de cuentas y progreso legible.
BASE_186 = """
QLabel#dialogTitle {font-size:23px;font-weight:800;background:transparent;}
QLabel#accountTitle {font-size:20px;font-weight:800;background:transparent;}
QLabel#accountStatus {font-size:12px;font-weight:700;border-radius:9px;padding:10px 12px;}
QListWidget#accountNav {padding:8px;border-radius:12px;outline:0;}
QListWidget#accountNav::item {padding:12px 11px;margin:3px 2px;border-radius:9px;}
QFrame#linkCard {border-radius:13px;}
QLineEdit#heroUrl {font-size:13px;font-weight:500;border-radius:9px;padding:10px 13px;}
QPushButton#pasteAction {font-weight:700;padding:11px 14px;}
QProgressBar#downloadProgress {font-size:12px;font-weight:800;text-align:center;border-radius:7px;}
QProgressBar#downloadProgress::chunk {border-radius:7px;}
"""
DARK += BASE_186 + """
QFrame#linkCard {background:#242036;border:1px solid #655392;}
QLineEdit#heroUrl {background:#302941;border:2px solid #8a65d6;color:#ffffff;}
QLineEdit#heroUrl:focus {border:2px solid #bb96ff;}
QFrame#accountCard {background:#231f32;border:1px solid #4d4266;border-radius:14px;}
QLabel#dialogTitle,QLabel#accountTitle {color:#f7f1ff;}
QLabel#accountStatus {background:#342b49;color:#e1d2ff;}
QLabel#accountStatus[connected="true"] {background:#1d453c;color:#b2f5d1;}
QListWidget#accountNav {background:#231f32;border:1px solid #514568;}
QListWidget#accountNav::item {color:#f5efff;}
QListWidget#accountNav::item:selected {background:#513b79;color:#ffffff;}
QListWidget#accountNav::item:hover {background:#3b3154;}
QProgressBar#downloadProgress {background:#4a3b67;color:#ffffff;}
QProgressBar#downloadProgress::chunk {background:#8652f3;}
"""
LIGHT += BASE_186 + """
QFrame#linkCard {background:#f0ebff;border:1px solid #c9b4f5;}
QLineEdit#heroUrl {background:white;border:2px solid #a58aef;color:#242035;}
QLineEdit#heroUrl:focus {border:2px solid #7445e5;}
QFrame#accountCard {background:#ffffff;border:1px solid #dfd6f0;border-radius:14px;}
QLabel#dialogTitle,QLabel#accountTitle {color:#33205f;}
QLabel#accountStatus {background:#f1ecfb;color:#635182;}
QLabel#accountStatus[connected="true"] {background:#e4f7eb;color:#175e3b;}
QListWidget#accountNav {background:#f9f7fe;border:1px solid #dfd8ef;}
QListWidget#accountNav::item {color:#362a57;}
QListWidget#accountNav::item:selected {background:#e7dcff;color:#4522a3;}
QListWidget#accountNav::item:hover {background:#eee8fa;}
QProgressBar#downloadProgress {background:#69568a;color:#ffffff;}
QProgressBar#downloadProgress::chunk {background:#7947e4;}
"""

# 1.8.7 REV2 — punto de entrada visual principal.
HERO_REV2 = """
QLabel#heroHeading {font-size:16px;font-weight:800;background:transparent;}
QLabel#heroHelp {font-size:12px;background:transparent;}
QLineEdit#heroUrl {font-size:14px;font-weight:600;padding:13px 16px;border-radius:11px;}
QPushButton#pasteAction {font-size:13px;font-weight:750;padding:13px 15px;}
QFrame#linkCard {border-radius:17px;}
"""
DARK += HERO_REV2 + """
QFrame#linkCard {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #302245,stop:1 #252036);border:2px solid #8050c9;}
QLabel#heroHeading {color:#ffffff;}
QLabel#heroHelp {color:#cec2e8;}
QLineEdit#heroUrl {background:#1d1a2c;color:#ffffff;border:2px solid #a67df8;selection-background-color:#8054ed;}
QLineEdit#heroUrl:focus {border:2px solid #cfadff;}
QPushButton#pasteAction {background:#50416a;color:#ffffff;border:1px solid #8974ae;}
QPushButton#pasteAction:hover {background:#665180;}
"""
LIGHT += HERO_REV2 + """
QFrame#linkCard {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #e9e1ff,stop:1 #f5f2ff);border:2px solid #a588ed;}
QLabel#heroHeading {color:#3d2076;}
QLabel#heroHelp {color:#68568d;}
QLineEdit#heroUrl {background:#ffffff;color:#292039;border:2px solid #9973e7;selection-background-color:#8054ed;}
QLineEdit#heroUrl:focus {border:2px solid #6740ce;}
QPushButton#pasteAction {background:#e8ddff;color:#3d2380;border:1px solid #bfa8ef;}
QPushButton#pasteAction:hover {background:#dac6ff;}
"""
