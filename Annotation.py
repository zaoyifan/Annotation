# coding: utf-8
import os
import numpy
import cv2
import tkinter
# from tkinter import ttk
# from tkinter import colorchooser
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showerror
# import xml.etree.ElementTree as ET

scalar = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

class Annotation:
    # 标注类
    def __init__(self, imageFolder, classToWrite, zoomRatio):
        self.classToWrite = classToWrite
        self.zoomRatio = zoomRatio
        # self.outputformat = outputformat
        self.imageFolder = imageFolder
        if not os.path.exists(self.imageFolder):
            raise Exception("Path {} does not exist!".format(self.imageFolder))
            
        # 读取标注日志，若无标注日志，则重新生成
        self.annotationCache = os.path.join(self.imageFolder, r'AnnotationCache.txt')
        self.imageList = []
        if not os.path.exists(self.annotationCache):
            self.imageList = self.getImageList()
            self.curFile = 0
            with open(self.annotationCache, 'w') as f:
                f.writelines(str(self.curFile) + '\n')
                for i in range(0, len(self.imageList)):
                    f.writelines(self.imageList[i] + '\n')
        else:
            with open(self.annotationCache, 'r') as f:
                self.curFile = int(f.readline().replace('\n', ''))
                for line in f.readlines():
                    self.imageList.append(line.replace('\n', ''))

        self.height = 0
        self.width = 0
        self.bboxList = []
        self.curImg = None
        self.curXY = [0, 0]
        self.initBboxXY = [0, 0]
        self.curBboxXY = [0, 0]
        self.isDrawFinished = True

    def getImageList(self):
        # 获取待标注图像列表
        imageList = []
        fileList = os.listdir(self.imageFolder)
        for i in range(0, len(fileList)):
            filePath = os.path.join(self.imageFolder, fileList[i])
            if os.path.isfile(filePath):
                file_path = os.path.split(filePath)
                lists = file_path[1].split('.')
                file_ext = lists[-1]
                img_ext = ['bmp', 'jpeg', 'gif', 'psd', 'png', 'jpg', 'tif']
                if file_ext.lower() in img_ext:
                    imageList.append(filePath)
        imageList.sort()
        return imageList

    def read_txt(self, filePathName):
        # 读取标签
        file_path = os.path.splitext(filePathName)
        txtPathName = file_path[0] + '.txt'
        if not os.path.exists(txtPathName):
            file_to_read = open(txtPathName, 'w')
            file_to_read.close()
        with open(txtPathName, 'r') as file_to_read:
            while True:
                lines = file_to_read.readline()
                if not lines:
                    break
                data = lines.split()
                classNum, x1, y1, x2, y2 = [int(x) for x in data]
                dataToRead = [classNum, round(self.zoomRatio * x1), round(self.zoomRatio * y1), round(self.zoomRatio * x2), round(self.zoomRatio * y2)]
                dataToRead = [int(x) for x in dataToRead]
                self.bboxList.append(dataToRead)

    def save_txt(self, filePathName):
        # 保存标签
        file_path = os.path.splitext(filePathName)
        txtPathName = file_path[0] + '.txt'
        with open(txtPathName, 'w') as file:
            for i in range(0, len(self.bboxList)):
                classNum, x1, y1, x2, y2 = self.bboxList[i]
                x1, y1, x2, y2 = round(x1/self.zoomRatio), round(y1/self.zoomRatio), round(x2/self.zoomRatio), round(y2/self.zoomRatio)
                lineToWrite = str(classNum)+' '+str(x1)+' '+str(y1)+' '+str(x2)+' '+str(y2)+'\n'
                file.writelines(lineToWrite)

    # def read_xml(self, filePathName):
    #     file_path = os.path.splitext(filePathName)
    #     xmlPathName = file_path[0] + '.xml'
    #     tree = ET.parse(xmlPathName)
    #     root = tree.getroot()

    # def save_xml(self, filePathName):
    #     file_path = os.path.splitext(filePathName)
    #     xmlPathName = file_path[0] + '.xml'

    # 创建回调函数
    def draw_rectangle(self, event, x, y, flags, param):
        # 当按下左键是返回起始位置坐标
        global x1, y1
        self.curXY = [x, y]
        if event == cv2.EVENT_LBUTTONDOWN:
            x1, y1 = x, y
            self.initBboxXY = [x, y]
        # 当鼠标左键按下并移动是绘制图形，event可以查看移动，flag查看是否按下
        elif event == cv2.EVENT_MOUSEMOVE and flags == cv2.EVENT_FLAG_LBUTTON:
            self.isDrawFinished = False
            self.curBboxXY = [x, y]
        elif event == cv2.EVENT_LBUTTONUP:
            self.isDrawFinished = True
            x1, y1, x2, y2 = self.getTLAndBR(x1, y1, x, y)
            self.bboxList.append([self.classToWrite, x1, y1, x2, y2])
            print(len(self.bboxList))

    def getTLAndBR(self, x_1, y_1, x_2, y_2):
        if x_1 <= x_2:
            if y_1 <= y_2:
                x1, y1, x2, y2 = x_1, y_1, x_2, y_2
            elif y_1 > y_2:
                x1, y1, x2, y2 = x_1, y_2, x_2, y_1
        elif x_1 > x_2:
            if y_1 <= y_2:
                x1, y1, x2, y2 = x_2, y_1, x_1, y_2
            elif y_1 > y_2:
                x1, y1, x2, y2 = x_2, y_2, x_1, y_1
        if x1 < 0:
            x1 = 0
        if y1 < 0:
            y1 = 0
        if x2 >= round(self.width * self.zoomRatio):
            x2 = round(self.width * self.zoomRatio) - 1
        if y2 >= round(self.height * self.zoomRatio):
            y2 = round(self.height * self.zoomRatio) - 1
        return x1, y1, x2, y2

    def run(self):
        cv2.namedWindow('Annotation')
        while self.curFile < len(self.imageList):
            self.bboxList.clear()
            img = cv2.imdecode(numpy.fromfile(self.imageList[self.curFile], dtype=numpy.uint8), cv2.IMREAD_COLOR)
            self.height, self.width, _ = img.shape
            offset_x = round((screen_width - self.width * self.zoomRatio) / 2)
            offset_y = round((screen_height - self.height * self.zoomRatio) / 2)
            cv2.moveWindow('Annotation', offset_x, offset_y)

            self.read_txt(self.imageList[self.curFile])
            print(str(self.curFile + 1) + '/' + str(len(self.imageList)))
            print(len(self.bboxList))

            # 绑定鼠标事件
            cv2.setMouseCallback('Annotation', self.draw_rectangle)
            while True:
                self.curImg = cv2.resize(img, (round(self.width * self.zoomRatio), round(self.height * self.zoomRatio)))

                for j in range(0, len(self.bboxList)):
                    class_num, x_1, y_1, x_2, y_2 = self.bboxList[j]
                    self.curImg = cv2.rectangle(self.curImg, (x_1, y_1), (x_2, y_2), scalar[class_num-1], 2)
                    cv2.putText(self.curImg, str(class_num), (x_1, y_1), cv2.FONT_HERSHEY_COMPLEX, 0.8, scalar[class_num-1], 1)
                if not self.isDrawFinished:
                    cv2.rectangle(self.curImg, (self.initBboxXY[0], self.initBboxXY[1]),
                                  (self.curBboxXY[0], self.curBboxXY[1]), (255, 255, 255), 1)

                cv2.line(self.curImg, (self.curXY[0], 0), (self.curXY[0], round(self.height * self.zoomRatio)), (255, 255, 255), 1)
                cv2.line(self.curImg, (0, self.curXY[1]), (round(self.width * self.zoomRatio), self.curXY[1]), (255, 255, 255), 1)

                cv2.putText(self.curImg, str(self.curFile + 1) + '/' + str(len(self.imageList)) + '-' + str(len(self.bboxList)), (10, 30), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)

                cv2.imshow("Annotation", self.curImg)

                key_pressed = cv2.waitKey(1)
                a_pressed = [ord('a'), ord('A')]
                d_pressed = [ord('d'), ord('D')]
                w_pressed = [ord('w'), ord('W')]
                undo_pressed = [27]
                if key_pressed in d_pressed:
                    self.save_txt(self.imageList[self.curFile])
                    self.curFile = self.curFile + 1
                    with open(self.annotationCache, 'r') as f:
                        lines = f.readlines()
                    lines[0] = str(self.curFile)+'\n'
                    with open(self.annotationCache, 'w') as f:
                        f.writelines(lines)
                    break
                elif key_pressed in a_pressed:
                    self.save_txt(self.imageList[self.curFile])
                    self.curFile = self.curFile - 1
                    if self.curFile < 0:
                        self.curFile = 0
                    with open(self.annotationCache, 'r') as f:
                        lines = f.readlines()
                    lines[0] = str(self.curFile) + '\n'
                    with open(self.annotationCache, 'w') as f:
                        f.writelines(lines)
                    break
                elif key_pressed in w_pressed:
                    if len(self.bboxList):
                        self.bboxList.pop()
                        print(len(self.bboxList))
                    else:
                        continue
                elif key_pressed in undo_pressed:
                    return


def SelectFolder():
    # 选择数据路径
    pathvalue.set(askdirectory())


# def ChooseColor():
#     # 选择标注颜色
#     colorinfo = colorchooser.askcolor()
#     if None in colorinfo:
#         return
#     colorlabel.configure(bg=colorinfo[1])
#     global color
#     color = (int(colorinfo[0][0]), int(colorinfo[0][1]), int(colorinfo[0][2]))


def StartAnnotation():
    # 判断类别编号是否为非负整数
    classToWrite = classvalue.get()
    if not classToWrite.isdigit():
        showerror('Class Number Error', 'Please enter a non-negative integer!')
        return
    else:
        classToWrite = int(classToWrite)

    # 判断缩放倍数是否为正数
    zoomRatio = float(zoomvalue.get())
    if zoomRatio <= 0:
        showerror('Zoom Factor Error', 'Please enter a positive number!')
        return

    # 判断数据路径是否存在
    imageFolder = pathvalue.get()
    if not os.path.isdir(imageFolder) or not os.path.exists(imageFolder):
        showerror('Folder Error', 'Please enter an existing folder!')
        return
    
    # 输出格式
    # outputformat = formatvalue.get()

    # 开始标注
    DetectionAnnotation = Annotation(imageFolder, classToWrite, zoomRatio)
    window.destroy()
    DetectionAnnotation.run()


# 创建窗口
window = tkinter.Tk()
window.withdraw()

# 目标类别编号
classlabel = tkinter.Label(window, text='Class Number', font=('Times New Roman', 10))
classlabel.grid(row=0, column=0, pady=5, padx=5)
classvalue = tkinter.StringVar()
classentry = tkinter.Entry(window, textvariable=classvalue, width=24, font=('Times New Roman', 10), justify='center')
classentry.grid(row=0, column=1, pady=5, padx=5)

# 缩放倍数
zoomlabel = tkinter.Label(window, text='Zoom Factor', font=('Times New Roman', 10))
zoomlabel.grid(row=1, column=0, pady=5, padx=5)
zoomvalue = tkinter.StringVar()
zoomentry = tkinter.Entry(window, textvariable=zoomvalue, width=24, font=('Times New Roman', 10), justify='center')
zoomentry.grid(row=1, column=1, pady=5, padx=5)

# 输出格式
# formatlabel = tkinter.Label(window, text='Output Format', font=('Times New Roman', 10))
# formatlabel.grid(row=2, column=0, pady=5, padx=5)
# formatvalue = tkinter.StringVar()
# formatcombobox = ttk.Combobox(window, textvariable=formatvalue, width=21, font=('Times New Roman', 10), justify='center')
# formatcombobox['values'] = ['XML', 'TXT']
# formatcombobox.current(0)
# formatcombobox.grid(row=2, column=1, pady=5, padx=5)

# 标注颜色
# colorbutton = tkinter.Button(window, text='Choose Color', font=('Times New Roman', 10), command=ChooseColor)
# colorbutton.grid(row=3, column=0, pady=5, padx=5)
# color = None
# colorlabel = tkinter.Label(window, bg='#FFFFFF', width=20, font=('Times New Roman', 10), justify='center')
# colorlabel.grid(row=3, column=1, pady=5, padx=5)

# 数据路径
pathbutton = tkinter.Button(window, text='Select Folder', width=11, font=('Times New Roman', 10), command=SelectFolder)
pathbutton.grid(row=2, column=0, pady=5, padx=5)
pathvalue = tkinter.StringVar()
pathentry = tkinter.Entry(window, textvariable=pathvalue, width=24, font=('Times New Roman', 10), justify='center')
pathentry.grid(row=2, column=1, pady=5, padx=5)

# 开始标注
startbutton = tkinter.Button(window, text='Click Me To Start Annotation', font=('Times New Roman', 10), command=StartAnnotation)
startbutton.grid(row=3, column=0, columnspan=2, pady=5, padx=5)

# 设置窗口属性
window.update()
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
window_width = window.winfo_width()
window_height = window.winfo_height()
offset_x = round((screen_width - window_width) / 2)
offset_y = round((screen_height - window_height) / 2)
window.geometry('+%d+%d'%(offset_x, offset_y))
window.resizable(width=False, height=False)
window.title('Annotation')
window.deiconify()

window.mainloop()
