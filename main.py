import sys
from PyQt5.QtWidgets import QApplication
from login import LoginWindow

def main():
    app = QApplication(sys.argv)
    login_window = LoginWindow(app)
    login_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
