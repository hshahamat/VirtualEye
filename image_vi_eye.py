from PyQt5 import QtWidgets,QtCore,QtGui
import sys
import numpy as np
import cv2
from scipy.ndimage import morphology
import pyautogui
import math

eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')
        
class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__()
        self.resize(QtWidgets.QApplication.screens()[0].size())
        self.setWindowTitle("Screenshoter")
        self.setMouseTracking(True)


        self.cap = cv2.VideoCapture('eye.mp4')
        self.fnum = 0
        self.speed = 1
        self.pos_idx = 0
        self.is_in_dance = True
        self.size = 50
        
        self.all_eye = []
        
        self.timer1 = QtCore.QTimer(self)
        self.timer1.timeout.connect(self.disp_img)
        self.timer1.start(33)

        
        self.btn_new_eye = QtWidgets.QPushButton("New eye")
        self.btn_new_eye.setFixedSize(90, 30)        
        self.btn_new_eye.clicked.connect(self.on_clk_new_eye)

        self.btn_fill = QtWidgets.QPushButton("Auto fill")
        self.btn_fill.setFixedSize(90, 30)        
        self.btn_fill.clicked.connect(self.on_clk_fill)

        self.btn_clearm = QtWidgets.QPushButton("Clear margins")
        self.btn_clearm.setFixedSize(90, 30)        
        self.btn_clearm.clicked.connect(self.on_clk_clearm)
        
        self.btn_clear = QtWidgets.QPushButton("Clear")
        self.btn_clear.setFixedSize(90, 30)        
        self.btn_clear.clicked.connect(self.on_clk_clear)
        
        self.btn_close = QtWidgets.QPushButton("Close App")
        self.btn_close.setFixedSize(90, 30)
        self.btn_close.clicked.connect(self.close_app)
        
        
        
        self.bk_lbl = QtWidgets.QLabel(self)
        aw = 100
        ah = self.height()
        self.bk_lbl.setGeometry(0, 0, aw, ah)
        self.bk_lbl.setStyleSheet("background-color: yellow")
        
        self.layout = QtWidgets.QVBoxLayout(self)            
        self.layout.setContentsMargins(5, 0, 0, 5)        
        self.layout.addWidget(self.btn_new_eye,0, QtCore.Qt.AlignLeft )
        self.layout.addWidget(self.btn_fill,0, QtCore.Qt.AlignLeft )
        self.layout.addWidget(self.btn_clearm,0, QtCore.Qt.AlignLeft )
        self.layout.addWidget(self.btn_clear,0, QtCore.Qt.AlignLeft )
        self.layout.addWidget(self.btn_close,0, QtCore.Qt.AlignLeft)
        
        self.layout.addStretch(1)
        self.setLayout(self.layout)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint| QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground,True)
    
    
               
            
    def disp_img(self): 
        for eye in self.all_eye:
            if eye.fnum < 70:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, eye.fnum)
                _, frm = self.cap.read()
                eye.fnum += 1
                if eye.fnum > 70:
                    eye.fnum=70
            if eye.fnum == 70:
                p_eye = [eye.x()+eye.width()/2,
                         eye.y()+eye.height()/2]
                pos = pyautogui.position()                
                p_mouse = [pos.x,pos.y]
                mode,level = self.get_mode_and_level(p_eye, p_mouse, eye.width())
                frm = self.get_eye(mode,level)
                
            frame = cv2.resize(frm,(eye.width(),eye.height()))
            rows,cols,ch = frame.shape
            
            gray_ = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            mask = (gray_>4)
            mask = morphology.binary_fill_holes(mask).astype("uint8")*255            
                    
            frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGBA)
            frame[:,:,3] = mask
            bytesPerLine = 4 * cols
            qImg = QtGui.QImage(frame,cols, rows, bytesPerLine,
                                QtGui.QImage.Format_RGBA8888)
            pixmap01 = QtGui.QPixmap.fromImage(qImg)
            eye.img_lbl.setPixmap(pixmap01)
            eye.img_lbl.update()

    def get_eye(self,mode=3,level=3):
        frm_range=[[19,20,21,22],#top-right
                   [101,102,103,103],#bottom-right
                   [179,180,181,181],#right
                   [63,210,211,211],#left
                   [228,229,230,231],#top-left
                   [159,159,158,158],#bottom-left
                   [295,117,177,177],#bottom
                   [264,366,240,240],#top
                   [0,1,2,3]#non
                   ]
        self.cap.set(cv2.CAP_PROP_POS_FRAMES,frm_range[mode][level])    
        ret, frame = self.cap.read()
        return frame
    
    def get_mode_and_level(self, p_eye,p_mouse,siz):
        dist,ang = self.angle_between(p_eye,p_mouse)
        level = int(dist//siz)
        _mode = 8
        if level>3:
            level = 3
        if ang>150 and ang<=210:#left
            _mode = 3
        if ang>100 and ang<=150:#bottom-left
            _mode = 5
        if ang>80 and ang<=100:#bottom
            _mode = 6
        if ang>30 and ang<=80:#bottom-right
            _mode = 1
        if (ang>0 and ang<=30) or (ang>330 and ang<=360):#right
            _mode = 2
        if ang>280 and ang<=330:#top-right
            _mode = 0
        if ang>260 and ang<=280:#top
            _mode = 7
        if ang>210 and ang<=260:#top-left
            _mode = 4            
        if dist<(siz/3):
            _mode = 8
        return _mode,level  

    def on_clk_fill(self):
        self.timer1.stop()
        qaps = QtWidgets.QApplication.primaryScreen()
        preview_screen = qaps.grabWindow(0,0,0,self.width(),self.height())
        bgr_img = self.QScreenToArray(preview_screen)[:,:,:3]
        goz_detect = eye_cascade.detectMultiScale(bgr_img,scaleFactor = 1.1, minNeighbors = 5)
        
        for (ex, ey, ew, eh) in goz_detect:
            cm = 10
            eye = MoveingObject(self,geo=[0, 0, ew-cm, eh-cm])
            eye.move(ex+cm,ey+cm)
            eye.fnum = 0  
            # for i in reversed(range(eye.layout.count())): 
            #     eye.layout.itemAt(i).widget().setParent(None)    
            self.all_eye.append(eye)
        self.timer1.start(33)
            

    def QScreenToArray(self,pixmap):
        channels_count = 4
        image = pixmap.toImage()
        s = image.bits().asstring(pixmap.width() * pixmap.height() * channels_count)
        img = np.frombuffer(s, dtype=np.uint8).reshape((pixmap.height(), pixmap.width(), channels_count))     
        return img
        
    def angle_between(self, P1, P2):
        deltaY = P2[1] - P1[1]
        deltaX = P2[0] - P1[0]
        dist = np.sqrt(deltaY**2+deltaX**2)
        angleInDegrees = math.degrees(math.atan2(deltaY, deltaX))
        if angleInDegrees < 0:
            angleInDegrees += 360
        return dist,angleInDegrees

    def on_clk_clearm(self):
        for eye in self.all_eye:
            eye.opacity = 0
            for i in reversed(range(eye.layout.count())): 
                eye.layout.itemAt(i).widget().setParent(None)
    
    def on_clk_clear(self):
        for eye in self.all_eye:
            eye.setParent(None)
            eye.deleteLater()
        self.all_eye = []
                      
    def on_clk_new_eye(self):
        eye = MoveingObject(self,geo=[0, 0, 60, 60])
        eye.move(200,100)
        eye.fnum = 0        
        self.all_eye.append(eye)

    def close_app(self):
        self.timer1.stop()
        self.cap.release()
        self.close()
       

'''#####################################################'''        
'''#####################################################'''        
class MoveingObject(QtWidgets.QWidget):
    def __init__(self, parent=None,geo=[]):
        super(MoveingObject, self).__init__(parent)
        self.draggable = True
        self.dragging_threshold = 5
        self.borderRadius = 5
        self.opacity = 0.1
        
        self.mousePressPos = None
        self.mouseMovePos = None
        self.parent = parent
        self.setWindowFlags(QtCore.Qt.SubWindow)
        self.setGeometry(*geo)
        
        self.img_lbl = QtWidgets.QLabel(self)
        self.img_lbl.setGeometry(0,0,self.width(),self.height()) 
        
        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)        
        layout.addWidget(
            QtWidgets.QSizeGrip(self), 0,0,
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        
        layout.addWidget(
            QtWidgets.QSizeGrip(self), 0,1,
            QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        
        layout.addWidget(
            QtWidgets.QSizeGrip(self), 1,0,
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        
        layout.addWidget(
            QtWidgets.QSizeGrip(self), 1,1,
            QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.layout = layout
        self.show()

    def paintEvent(self, event):
        window_size = self.size()
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing, True)
        br = QtGui.QBrush(QtGui.QColor(QtCore.Qt.white))  
        qp.setBrush(br)    
        qp.setOpacity(self.opacity)        
        qp.drawRoundedRect(0, 0, window_size.width(), window_size.height(),
                            self.borderRadius, self.borderRadius)
        qp.end()
        self.img_lbl.resize(window_size)
        self.img_lbl.adjustSize()
               
    def mousePressEvent(self, event):
        if self.draggable and event.button() == QtCore.Qt.LeftButton:
            self.setCursor(QtGui.QCursor(QtCore.Qt.ClosedHandCursor))            
            self.mousePressPos = event.globalPos()                # global
            self.mouseMovePos = event.globalPos() - self.pos()    # local
        super(MoveingObject, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.draggable and event.buttons() & QtCore.Qt.LeftButton:          
                
            globalPos = event.globalPos()
            moved = globalPos - self.mousePressPos
            if moved.manhattanLength() > self.dragging_threshold:
                # Move when user drag window more than dragging_threshold
                diff = globalPos - self.mouseMovePos
                self.move(diff)
                self.mouseMovePos = globalPos - self.pos()
        super(MoveingObject, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):        
        if self.mousePressPos is not None:
            self.setCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))            
            if event.button() == QtCore.Qt.LeftButton:
                moved = event.globalPos() - self.mousePressPos
                if moved.manhattanLength() > self.dragging_threshold:
                    # Do not call click event or so on
                    event.ignore()
                self.mousePressPos = None
        super(MoveingObject, self).mouseReleaseEvent(event)
        
        
'''#####################################################'''        
'''#####################################################'''        
root = QtWidgets.QApplication(sys.argv)
app = MainWindow()
app.showMaximized()
sys.exit(root.exec_())