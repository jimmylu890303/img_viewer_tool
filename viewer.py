import sys
from PyQt5.QtCore import QRect, QRectF, QSize, Qt,QPoint,QPointF
from PyQt5.QtGui import QPainter, QPixmap, QWheelEvent,QImage
from PyQt5.QtWidgets import (QApplication, QGraphicsItem, QGraphicsPixmapItem,
                             QGraphicsScene, QGraphicsView)
import numpy  as np
import os
import cv2
from PyQt5.QtGui import QPen

class ImageViewer(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.opacity = 0.5
        self.graphicsScene = QGraphicsScene()
        self.enableMask = True
        self.isPress = False
        self.radius = 10  
        self.mouse_x = 0
        self.mouse_y = 0
    
    def loadInitImg(self,root_folder_path):
        self.root_folder_path = root_folder_path
        img_path = os.path.join(root_folder_path,'patch')
        mask_path = os.path.join(root_folder_path,'mask')
        self.imgs = [os.path.join(img_path,img) for img in os.listdir(img_path)]
        self.masks = [os.path.join(mask_path,img) for img in os.listdir(mask_path)]
        self.totalImgs = len(self.imgs)
        self.idx = 0     
        self.load_img()
    def load_img(self):
        self.pixmap = QPixmap(self.imgs[self.idx])
        self.pixmapItem = QGraphicsPixmapItem(self.pixmap)
        self.mask = cv2.imread(self.masks[self.idx])
        mask_qimage = self.deal_mask(self.mask)
        self.mask_pixmap = QPixmap.fromImage(mask_qimage)
        self.mask_pixmapItem = QGraphicsPixmapItem(self.mask_pixmap)
        self.mask_pixmapItem.setOpacity(self.opacity)
        self.__initWidget()
    def __initWidget(self):
        """ 初始化 Image viewer """
        self.resize(1600, 1200)
        # 隱藏滾動條
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 縮放的錨點
        self.setTransformationAnchor(self.AnchorUnderMouse)
        # 平滑缩放
        self.pixmapItem.setTransformationMode(Qt.SmoothTransformation)
        self.setRenderHints(QPainter.Antialiasing |
                            QPainter.SmoothPixmapTransform)
        # 設置圖片
        self.graphicsScene.addItem(self.pixmapItem)
        self.graphicsScene.addItem(self.mask_pixmapItem)
        self.setScene(self.graphicsScene)
        self.fitInView(self.pixmapItem, Qt.KeepAspectRatio)
  
    def deal_mask(self,mask):
        gray_image = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        if len(gray_image[gray_image > 125]) == 0:
            gray_image = gray_image * 255


        alpha_channel = np.zeros_like(gray_image, dtype=np.uint8)
        alpha_channel[gray_image > 125] = 255
        mask[gray_image > 120] = [0,255,0]
        # Add alpha channel
        rgba_image = cv2.merge((mask[:, :, 0], mask[:, :, 1], mask[:, :, 2], alpha_channel))
        # Convert PIL Image to QImage
        height, width, channels = rgba_image.shape
        bytes_per_line = channels * width
        qimage = QImage(rgba_image.data, width, height, bytes_per_line, QImage.Format_RGBA8888)
        return qimage
    
    def create_circle_mask(self,mask, center):
        cv2.circle(mask, center, self.radius, (0, 0, 0), -1)

    def removeArea(self, x, y):
        self.create_circle_mask(self.mask, (x, y))
        mask_qimage = self.deal_mask(self.mask)
        self.mask_pixmap = QPixmap.fromImage(mask_qimage)
        self.mask_pixmapItem.setPixmap(self.mask_pixmap)
        self.mask_pixmapItem.setOpacity(self.opacity)

    def enable_mask(self):
        self.enableMask = not self.enableMask
        self.mask_pixmapItem.setVisible(self.enableMask)
    def mousePressEvent(self,e):
        super().mousePressEvent(e)
        self.isPress = True
    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.isPress = False
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self.isPress:
            scenePos = self.mapToScene(event.pos()).toPoint()
            x = int(scenePos.x())
            y = int(scenePos.y())
            self.mouse_x = event.pos().x()
            self.mouse_y = event.pos().y()
            self.removeArea(x, y)
    def next_img(self):
        if self.idx < self.totalImgs-1: 
            self.idx +=1
            self.load_img()
    def prev_img(self):
        if self.idx > 0:
            self.idx -=1
            self.load_img()
    def change_eraser(self,val):
        self.radius = val
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        pen = QPen(Qt.red)
        painter.setPen(pen)
        painter.drawEllipse(QPoint(self.mouse_x, self.mouse_y), 2*self.radius, 2*self.radius)
    def save_mask(self):
        gray_image = cv2.cvtColor(self.mask, cv2.COLOR_BGR2GRAY)
        mask = self.mask.copy()
        mask[gray_image > 120] = [255,255,255]
        mask = cv2.cvtColor(mask,cv2.COLOR_BGR2GRAY)
        save_path = os.path.join(self.root_folder_path,'save')
        save_file_path = os.path.join(save_path,self.imgs[self.idx].split("\\")[-1])
        cv2.imwrite(save_file_path,mask)
