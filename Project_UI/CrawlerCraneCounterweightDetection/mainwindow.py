# This Python file uses the following encoding: utf-8
# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py

# Sudo apt-get install libxkbcommon-x11-0
# sudo apt install libegl1-mesa
import sys
from PySide6.QtWidgets import QApplication, QWidget,QFileDialog,QButtonGroup
from PySide6.QtCore import QDir,Qt
from PySide6.QtGui import QPixmap
from ui_form import Ui_MainWindow
from Stream_Inference import Stream_Inference
import os
from datetime import datetime

class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.stream_import.clicked.connect(self.stream_import)
        #页面切换按钮组
        self.PageSwitchButtonGroup = QButtonGroup()
        self.PageSwitchButtonGroup.addButton(self.ui.home)
        self.PageSwitchButtonGroup.addButton(self.ui.config)
        self.PageSwitchButtonGroup.buttonClicked.connect(self.page_switch)

        # 添加日志文本地址
        self.log_dir = "logs/" + datetime.now().strftime("%Y_%m_%d") + '.txt'

        #流、权重文件浏览
        self.stream_path=""
        self.ui.open_stream_file.clicked.connect(lambda:self.open_file(self.ui.stream_file_list,0))
        self.ui.open_weight_file.clicked.connect(lambda:self.open_file(self.ui.weight_file_list,1))
        self.ui.open_weight_file_2.clicked.connect(lambda:self.open_file(self.ui.weight_file_list_2,1))

        #设备选择
        self.deviceButtonGroup = QButtonGroup()
        self.deviceButtonGroup.addButton(self.ui.GPU)
        self.deviceButtonGroup.addButton(self.ui.CPU)
        self.deviceButtonGroup_2 = QButtonGroup()
        self.deviceButtonGroup_2.addButton(self.ui.GPU_2)
        self.deviceButtonGroup_2.addButton(self.ui.CPU_2)

        #检测标注显示
        self.ui.box.clicked.connect(self.show_box)
        self.ui.Label.clicked.connect(self.show_label)
        self.stream_inference_thread=""

        #默认配重检测推理参数
        self.weight_path="../../utils/models/best.pt"
        self.imgsz=640
        self.conf=0.1
        self.device="cuda:0"

        #默认字符检测推理参数
        self.weight_sr = "../../utils/ESPCN_x2.pb"
        self.weight_character = "../../CounterweightCharacterRecognition/detect/train/weights/best.pt"
        self.imgsz_2=640
        self.conf_2=0.5
        self.device_2="cuda:0"

        #置信度滑动条
        self.ui.conf.valueChanged.connect(lambda:self.sliderChanged(self.ui.conf.value(),0))
        self.ui.conf_2.valueChanged.connect(lambda:self.sliderChanged(self.ui.conf_2.value(),1))

        # 从文件中加载历史数据
        self.load_stream_path()
        self.ui.stream_file_list.currentIndexChanged.connect(self.save_stream_path)

        #按钮状态切换
        self.ui.weight_file_list.currentIndexChanged.connect(lambda:self.button_mode_switch(self.ui.weight_file_list.currentText(),self.deviceButtonGroup))
        self.ui.weight_file_list_2.currentIndexChanged.connect(lambda:self.button_mode_switch(self.ui.weight_file_list_2.currentText(),self.deviceButtonGroup_2))
        self.button_mode_switch(self.ui.weight_file_list.currentText(),self.deviceButtonGroup)
        self.button_mode_switch(self.ui.weight_file_list_2.currentText(),self.deviceButtonGroup_2)
        self.stream_import()

    def save_stream_path(self):
        # 断开 currentIndexChanged 信号的连接
        self.ui.stream_file_list.currentIndexChanged.disconnect(self.save_stream_path)
        # 将当前选择的文本添加到列表的首位
        current_text = self.ui.stream_file_list.currentText()
        current_index = self.ui.stream_file_list.currentIndex()
        self.ui.stream_file_list.removeItem(current_index)
        self.ui.stream_file_list.insertItem(0, current_text)
        self.ui.stream_file_list.setCurrentIndex(0)
        # 保存当前 ComboBox 中的所有文本到文件
        with open("config/stream_path.txt", "w", encoding="utf-8") as file:
            for i in range(self.ui.stream_file_list.count()):
                file.write(self.ui.stream_file_list.itemText(i) + "\n")
        # 重新连接 currentIndexChanged 信号
        self.ui.stream_file_list.currentIndexChanged.connect(self.save_stream_path)

    def load_stream_path(self):
        # 从文件中加载历史数据到 ComboBox
        try:
            with open("config\stream_path.txt", "r", encoding="utf-8") as file:
                lines = file.readlines()
                for line in lines:
                    self.ui.stream_file_list.addItem(line.strip())
        except FileNotFoundError:
            pass

    def show_box(self):
        self.stream_inference_thread.box = (lambda x: True if x.isChecked() else False)(self.ui.box)

    def show_label(self):
        self.stream_inference_thread.label = (lambda x: True if x.isChecked() else False)(self.ui.Label)

    def sliderChanged(self, value , type):
        if type==0:
            formatted_str = "{:.2f}".format(value/100)
            self.ui.conf_value.setText(formatted_str)
        else:
            formatted_str = "{:.2f}".format(value/100)
            self.ui.conf_value_2.setText(formatted_str)
    def is_unique(self,current_item, combo_box):
        for index in range(combo_box.count()):
            if combo_box.itemText(index) == current_item:
                return False,index
        return True , 0

    def open_file(self,combobox,type):
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Open File")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setViewMode(QFileDialog.Detail)
        if type==0:
            file_dialog.setNameFilter("Video Files (*.mp4 *.avi *.mov)")
            if file_dialog.exec():
                selected_files = file_dialog.selectedFiles()
                if len(selected_files) == 1:
                    flag,index = self.is_unique(selected_files[0], combobox)
                    if flag:
                        if combobox.count()>=self.ui.stream_file_list.maxCount():
                            combobox.removeItem(combobox.maxCount()-1)
                        combobox.addItem(selected_files[0])
                        combobox.setCurrentIndex(combobox.count()-1)
                    else:
                        combobox.setCurrentIndex(index)
                else:
                    return
        elif type ==1:
            file_dialog.setNameFilter("Weight Files (*.pt *.engine *.onnx)")
            if file_dialog.exec():
                selected_files = file_dialog.selectedFiles()
                if len(selected_files) == 1:
                    if self.is_unique(selected_files[0], combobox):
                        combobox.addItem(selected_files[0])
                    combobox.setCurrentText(selected_files[0])
                    file_extension = os.path.splitext(selected_files[0])[-1]
                    if combobox == self.ui.open_weight_file:
                        self.button_mode_switch(selected_files[0],self.deviceButtonGroup)
                    else:
                        self.button_mode_switch(selected_files[0],self.deviceButtonGroup_2)
                else:
                    return

    def button_mode_switch(self,file,buttongroup):
        file_extension = os.path.splitext(file)[-1]
        if file_extension==".engine":
            for button in buttongroup.buttons():
                button.setCheckable(False)
        else:
            for button in buttongroup.buttons():
                button.setCheckable(True)

    def stream_import(self):
        self.stream_path = str(self.ui.stream_file_list.currentText())
        flag,index = self.is_unique(self.stream_path,self.ui.stream_file_list)
        if flag:
            if self.ui.stream_file_list.count()>=self.ui.stream_file_list.maxCount():
                self.ui.stream_file_list.removeItem(self.ui.stream_file_list.maxCount()-1)
            self.ui.stream_file_list.addItem(self.ui.stream_file_list.currentText())
            self.ui.stream_file_list.setCurrentIndex(self.ui.stream_file_list.count()-1)
        self.stream_path = int(self.stream_path) if str.isdigit(self.stream_path) else self.stream_path #获取本地相机代号

        #配重检测推理参数
        # self.weight_path = str(self.ui.weight_file_list.currentText())
        self.imgsz = int(self.ui.imgsz.text())
        self.device = "CPU" if self.ui.CPU.isChecked() else "cuda:0"
        self.conf = self.ui.conf.value()*0.01
        #字符检测推理参数
        # self.weight_character = str(self.ui.weight_file_list_2.currentText())
        self.imgsz_2= int(self.ui.imgsz_2.text())
        self.device_2 = "CPU" if self.ui.CPU_2.isChecked() else "cuda:0"
        self.conf_2 = self.ui.conf_2.value()*0.01
        #创建线程
        self.stream_inference_thread = Stream_Inference(self.stream_path,self.weight_path,self.imgsz,self.conf,self.device,self.weight_sr, self.weight_character,self.imgsz_2,self.conf_2,self.device_2)
        self.stream_inference_thread.processed_image.connect(self.display_processed_image)
        self.stream_inference_thread.result_info.connect(self.display_results)
        self.stream_inference_thread.start()
        self.ui.stackedWidget.setCurrentIndex(1)

    def page_switch(self,botton):
        if botton==self.ui.home:
            if self.ui.stackedWidget.currentIndex()==1:
                return
            else:
                self.stream_import()
        else:
            self.stream_inference_thread.stop()
            self.ui.stackedWidget.setCurrentIndex(0)

    def stream_reload(self):
        self.stream_inference_thread.stop()
        self.ui.stackedWidget.setCurrentIndex(0)

    def display_processed_image(self, image):
        pixmap = QPixmap.fromImage(image)
        pixmap = pixmap.scaled(self.ui.annotated_image.size())
        self.ui.annotated_image.setPixmap(pixmap)

    def display_results(self,num_weight,total_mass,total_mass_L,total_mass_R,warming_info):
        self.ui.num_weight.setText(str(num_weight))
        self.ui.total_mass.setText(str(int(total_mass)))
        self.ui.total_mass_L.setText(str(int(total_mass_L)))
        self.ui.total_mass_R.setText(str(int(total_mass_R)))
        self.ui.warming_info.setText(warming_info)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
