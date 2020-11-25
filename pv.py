import os, sys, ctypes
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

#implementing rotation
#add theming maybe
#weird zoom glitch - too fast w/ bar leads to not zooming out properly
#translation for zoom
#Limit ability to pan

class SliderAction(QWidgetAction):
    def __init__(self, parent):
        super(SliderAction, self).__init__(parent)
        # layout = QHBoxLayout()
        self.bar = QSlider(Qt.Horizontal)
        # layout.addWidget(self.bar)
        self.setDefaultWidget(self.bar)

class MoveLabel(QLabel):
    def __init__(self, parent):
        super(MoveLabel, self).__init__()
        self.parent = parent
        self.tvec = QPoint(0, 0)
        self.translations = QPoint(0, 0)
        self.old_scale = self.parent.cur_scale
        self.painter = QPainter()
        self.reallyDoAdd = self.doAdd = True
        # self.mov = QPoint(0, 0)

    def wheelEvent(self, event):
        change = event.angleDelta()

        change = max(change.y() // 10 + self.parent.cur_scale * 99 / 2, 0)

        print("CHANGE: ", change)
        print("SCALE: ", self.parent.cur_scale)
        # self.translations = QPoint(0, 0)
        # self.translations = QPoint(self.width() // 2, self.height() // 2)
        # self.parent.cur_img = self.parent.movedImg
        so = 1 + self.parent.cur_scale
        self.parent.zoom_func(change)
        sn = 1 + self.parent.cur_scale
        pw, ph = self.pixmap().width(), self.pixmap().height()
        ar = pw / ph

        if pw > ph:
            self.translations = QPointF(self.translations.x() * sn/so, self.translations.x() * sn/so * ar**-1)
        else:
            self.translations = QPointF(self.translations.y() * sn/so * ar, self.translations.y() * sn/so)

    def mousePressEvent(self, event):
        # self.translations = QPoint(-event.pos().x(), -event.pos().y())
        self.offset = event.pos()
        # self.translations = QPoint(self.offset.x(), self.offset.y())

    def mouseMoveEvent(self, event):
        x, y = self.translations.x(), self.translations.y()
        # self.mov = event.pos()
        if self.parent.cur_scale > 0:
            parent = self.parent
            p = self.painter

            img = parent.scaleImg(parent.curImg)
            # nuimg = img.toImage()
            # img = self.pixmap()
            baseImg = QImage(img.width(), img.height(), QImage.Format_ARGB32)
            baseImg.fill(0)

            tvec = event.pos() - self.offset
            x += tvec.x()
            y += tvec.y()

            
            p.begin(baseImg)
            # if x >= 0 and y >= 0 and x <= self.width() and y <= self.height():
            # print("BRUSH: ", p.brushOrigin())
            finalt = self.translations + tvec
            # print(self.height(), self.width())
            pw, ph = self.pixmap().width(), self.pixmap().height()
            cutoff = 2/3
            print("CUTOFF:", QPointF(pw, ph) * cutoff)
            if finalt.y() < cutoff * ph and finalt.y() > cutoff * -ph and finalt.x() > cutoff * -pw and finalt.x() < cutoff * pw: 
                p.translate(finalt)
                self.tvec = tvec
                self.doAdd = True
            else:
                self.doAdd = False
                # self.tvec = tvec
                nut = QPoint(0, 0)
                if finalt.y() > cutoff * ph or finalt.y() < cutoff * -ph:
                    nut += QPoint(0, self.tvec.y())
                if finalt.x() < cutoff * -pw or finalt.x() > cutoff * pw:
                    nut += QPoint(self.tvec.x(), 0)

                if nut.x() == 0:
                    nut += QPoint(tvec.x(), 0)
                if nut.y() == 0:
                    nut += QPoint(0, tvec.y())

                self.tvec = nut

                p.translate(self.translations + nut)
            # else:
            #     p.translate(finalt)
            # else:
            #     p.translate(self.translations)
            p.drawPixmap(0, 0, img)
            # p.setBrushOrigin(self.translations + tvec)
            print("FINAL VECTOR:", finalt)
            print("TOTAL:", self.translations)
            p.end()

            final = QPixmap.fromImage(baseImg)
            self.parent.movedImg = final
            self.setPixmap(final)

    def mouseReleaseEvent(self, event):
        if self.doAdd:
            self.reallyDoAdd = True
            
        if self.reallyDoAdd:
            self.translations += self.tvec
        if not self.doAdd:
            self.reallyDoAdd = False
        
        # self.translations = QPoint(self.tvec)

    def mouseDoubleClickEvent(self, event):
        print(self.parent.cur_scale)
        if self.parent.cur_scale > 0:
            self.parent.zoom_func(0)

        elif self.parent.cur_scale == 0:
            self.parent.zoom_func(99)

class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        
        self.setBasic()

        self.passedImage = sys.argv[1]
        self.movedImg = self.curImg = QPixmap(self.passedImage)
        os.chdir(os.path.dirname(self.passedImage))
        self.cur_scale = 0
        self.rotTog = False

        self.neighbors = [os.path.abspath(x) for x in os.listdir(os.path.abspath(os.path.dirname(self.passedImage))) if self.check_valid_img(os.path.abspath(x))]
        # print(self.neighbors)
        self.cur_pos = self.neighbors.index(self.passedImage)

        self.canLeft, self.canRight = self.check_move()

        os.chdir(os.path.abspath(os.path.dirname(self.passedImage)))

        
        self.img = MoveLabel(self)
        self.img.setStyleSheet("max-width:750;max-height:600;min-width:750;min-height:600;")
        print(self.img.size())
        self.img.setAlignment(Qt.AlignCenter)

        header = self.makeHeader()
        buttons = self.makeButtons()
        layout = QVBoxLayout()
        layout.addLayout(header)
        layout.addWidget(self.img, alignment=Qt.AlignCenter)
        layout.addLayout(buttons)

        self.set_image(self.passedImage)

        self.wdg = QWidget(self)
        self.wdg.setLayout(layout)
        self.setCentralWidget(self.wdg)

        self.zoom_func(0)

    def check_valid_img(self, img):
        # print(img)
        return True

    def check_move(self):
        l = r = True
        if self.cur_pos == len(self.neighbors) - 1:
            r = False
        if self.cur_pos == 0:
            l = False

        return l, r

    def check_buttons(self):
        l, r = self.check_move()
        self.LB.setEnabled(l)
        self.RB.setEnabled(r)

    def set_image(self, nuimg):
        self.setWindowTitle("FSC Photo Viewer - " + nuimg.split("\\")[-1])
        text = ""
        # print("BASED")
        try:
            t = QImage(nuimg)
            if not t:
                raise ValueError

            self._img = QPixmap(nuimg)
            self._img = self._img.scaled(self.img.size(), Qt.KeepAspectRatio)
            self.img.setPixmap(self._img)

            self.passedImage = nuimg
            self.curImg = self.movedImg = self._img
            
            self.rotate.setEnabled(True)

        except:
            text = "Could not load file"
            self.rotate.setEnabled(False)

        self.img.setText(text)

    def goLeft(self):
        if self.cur_pos > 0:
            self.set_image(self.neighbors[self.cur_pos - 1])
            self.cur_pos -= 1
        self.check_buttons()

    def goRight(self):
        if self.cur_pos < len(self.neighbors) - 1:
            self.set_image(self.neighbors[self.cur_pos + 1])
            self.cur_pos += 1
        self.check_buttons()

    def _rotate(self):
        # old_s = self.cur_scale
        self.zoom_func(0)
        w, h = self.img.width(), self.img.height()

        baseImg = QImage(h, w, QImage.Format_ARGB32)
        baseImg.fill(0)
        
        p = QPainter(baseImg)
        p.translate(h, 0)
        p.rotate(90)
        print(baseImg.size(), self.img.size())
        p.drawPixmap(0, 0, self.img.pixmap().scaled(self.img.size(), Qt.KeepAspectRatio))
        p.end()

        # self.zoom_func(old_s)

        return baseImg

    def rotateCW(self):
        baseImg = self._rotate()

        if not self.rotTog:
            self.img.setStyleSheet("max-width:600;max-height:750;min-width:600;min-height:750;")
            self.rotTog = True
            self.img.setAlignment(Qt.AlignCenter)
        else:
            self.rotTog = False
            self.img.setStyleSheet("max-width:750;max-height:600;min-width:750;min-height:600;")
            self.img.setAlignment(Qt.AlignCenter)

        self.curImg = QPixmap.fromImage(baseImg)
        self.movedImg = self.curImg

        self.img.setPixmap(self.curImg)

    def makeButtons(self):
        button = QHBoxLayout()
        left, right = QPushButton(), QPushButton()
        left.setObjectName("left")
        right.setObjectName("right")

        left.setEnabled(self.canLeft)
        right.setEnabled(self.canRight)

        left.clicked.connect(self.goLeft)
        right.clicked.connect(self.goRight)

        rot = QPushButton()
        rot.clicked.connect(self.rotateCW)
        rot.setObjectName("rotate")

        button.addWidget(left)
        button.addWidget(right)
        button.addWidget(rot)

        self.LB, self.RB = left, right
        self.rotate = rot

        return button

    def toggle_darkmode(self, dire):
        # self.setStyleSheet("background-color:black;")
        # self.parent.setStyleSheet("background-color:black;")
        # parent = Qt.QCoreApplication.instance()
        parent = QCoreApplication.instance()
        if dire:
            with open("dark.qss", "r") as f:
                nustyle = f.read()
        else:
            with open("design.qss", "r") as f:
                nustyle = f.read()
        parent.setStyleSheet(nustyle)

    def scaleImg(self, oimg, *args):
        scale = None if not args else args[0]
        if not scale:
            scale = self.cur_scale

        _img = oimg
        if scale != 0:
            _img = _img.scaled(self.img.width() + round(self.img.width() * scale), self.img.height() + round(self.img.height() * scale), Qt.KeepAspectRatio)
        else:
            _img = _img.scaled(self.img.size(), Qt.KeepAspectRatio)

        return _img

    def zoom_func(self, bar_full, *args):
        print(bar_full)
        if bar_full > 99:
            bar_full = 99
        if bar_full < 0:
            bar_full = 0
            
        scale = bar_full / 99 * 200 / 100
        print(scale)
        print(self.img.width() + round(self.img.width() * scale), self.img.height() + round(self.img.height() * scale))
        if self.slider.bar.value() != bar_full:
            self.slider.bar.setValue(bar_full)
        
        if bar_full != 0:
            self._img = self.scaleImg(self.movedImg, scale)
        else:
            self._img = self.scaleImg(self.curImg, scale)
            self.movedImg = self.curImg
            self.img.translations = QPoint(0, 0)

        self.img.old_scale = self.cur_scale
        self.cur_scale = scale
        # self._img = self._img.copy(self._img.width() // 4, self._img.height() // 4, self._img.width() // 2, self._img.height() // 2)
        # 
        
        # if bar_full != 0:
        #     base_img = QImage(self._img.width(), self._img.height(), QImage.Format_ARGB32)
        #     p = QPainter(base_img)
        #     p.translate(self.img.mov)
        #     p.drawPixmap(0, 0, self._img)
        #     p.end()

        self.img.setPixmap(self._img)

    def makeHeader(self):
        head = QHBoxLayout()
        info = QPushButton()
        more = QPushButton()
        zoom = QPushButton()

        info.setObjectName("info")
        more.setObjectName("more")
        zoom.setObjectName("zoom")

        # more.setIcon(QIcon("rotate.png"))

        zoom_menu = QMenu(zoom)
        zoom.setMenu(zoom_menu)
        self.slider = slider = SliderAction(zoom_menu)
        zoom_menu.addAction(slider)
        slider.bar.valueChanged.connect(lambda: self.zoom_func(slider.bar.value()))
        
        # more.setPopupMode(QToolButton.InstantPopup)
        # more.setCheckable(True)
        more_menu = QMenu(more)
        dark_mode = QAction("Enable dark mode", more_menu)
        dark_mode.setCheckable(True)
        dark_mode.triggered.connect(lambda: self.toggle_darkmode(dark_mode.isChecked()))

        more_menu.addAction(dark_mode)
        more.setMenu(more_menu)
        # more_bar = QToolBar()
        # more_bar.addWidget(more)
        # more.clicked.connect()

        head.addWidget(info)
        head.addWidget(zoom)
        head.addWidget(more)

        return head

    def setBasic(self):
        height, width = 950, 1000

        self.resize(width, height)
        # self.setMinimumHeight(height) 
        # self.setMaximumHeight(height)
        # self.setMinimumWidth(width) 
        # self.setMaximumWidth(width)

        

def getQSS():
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    with open("design.qss", "r") as f:
        return f.read()

def main():
    sys.argv.append(r"D:\Python Programs\FSC photo viewer\test.png")

    app = QApplication()

    form = Window()
    form.show()

    appid = 'fsc photoviewer v1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

    app.setStyleSheet(getQSS())
    
    app.exec_()

if __name__ == "__main__":
    main()