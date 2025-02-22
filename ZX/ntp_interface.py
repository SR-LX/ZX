import sys
import json
from PyQt6.QtCore import Qt, QTimer, QRandomGenerator, pyqtSignal, QMetaObject, Q_ARG
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication, QLineEdit, QFileDialog
from PyQt6.QtGui import QPainter, QColor
from qfluentwidgets import (CardWidget, MessageBox, LineEdit, isDarkTheme, InfoBar, InfoBarPosition,
                          MessageBoxBase, SubtitleLabel, CaptionLabel)
from custom_button import GradientButton
import ntplib
import threading
from datetime import datetime
import pyqtgraph as pg
import numpy as np
import time
import requests
import pytz

# 将 URLInputDialog 移到类外部
class URLInputDialog(MessageBoxBase):
    """ URL input dialog """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel('输入目标网址', self)
        self.urlLineEdit = LineEdit(self)

        self.urlLineEdit.setPlaceholderText('例如: www.example.com')
        self.urlLineEdit.setClearButtonEnabled(True)

        self.warningLabel = CaptionLabel("URL 格式无效")
        self.warningLabel.setTextColor("#cf1010", QColor(255, 28, 32))

        # 添加组件到布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.urlLineEdit)
        self.viewLayout.addWidget(self.warningLabel)
        self.warningLabel.hide()

        # 设置按钮文本
        self.yesButton.setText('确定')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(350)

    def validate(self):
        """ 重写验证方法 """
        url = self.urlLineEdit.text().strip()
        if not url:
            self.warningLabel.setText("请输入URL")
            self.warningLabel.show()
            self.urlLineEdit.setError(True)
            return False
        return True

class NTPMonitorCard(CardWidget):
    # 添加信号
    update_plot_signal = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_ntp()
        self.setup_graph()
        self.init_timer()
        self.is_monitoring = False
        self.monitoring_thread = None
        self.save_path = None
        self.monitoring_data = []
        
        # 连接信号到槽函数
        self.update_plot_signal.connect(self.update_plot)

    def update_plot(self, delay):
        """在主线程中更新图表"""
        self.data_x.append(len(self.data_x))
        self.data_y.append(delay)
        if len(self.data_x) > 100:
            self.data_x = self.data_x[-100:]
            self.data_y = self.data_y[-100:]
        self.plot.setData(self.data_x, self.data_y)

    def monitor_network(self):
        delays = []
        while self.is_monitoring:
            try:
                start_time = time.time()
                response = requests.get(self.target_url, timeout=5)
                end_time = time.time()
                delay = (end_time - start_time) * 1000  # 转换为毫秒
                
                if response.status_code == 200:
                    delays.append(delay)
                    
                    # 记录数据
                    record = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                        'delay': delay,
                        'status': response.status_code,
                        'success': True
                    }
                    self.monitoring_data.append(record)
                    
                    # 使用信号更新UI和图表
                    self.update_plot_signal.emit(delay)
                    
                    # 计算平均延迟
                    if delays:
                        avg_delay = sum(delays[-100:]) / len(delays[-100:])
                        # 使用QMetaObject.invokeMethod安全地更新UI
                        QMetaObject.invokeMethod(self.delayLabel, "setText",
                                                Qt.ConnectionType.QueuedConnection,
                                                Q_ARG(str, f'当前延迟: {delay:.2f}ms'))
                        QMetaObject.invokeMethod(self.avgDelayLabel, "setText",
                                                Qt.ConnectionType.QueuedConnection,
                                                Q_ARG(str, f'平均延迟: {avg_delay:.2f}ms'))
                else:
                    record = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                        'status': response.status_code,
                        'success': False,
                        'error': f'HTTP {response.status_code}'
                    }
                    self.monitoring_data.append(record)
                    QMetaObject.invokeMethod(self.delayLabel, "setText",
                                            Qt.ConnectionType.QueuedConnection,
                                            Q_ARG(str, f'请求失败: HTTP {response.status_code}'))
                
                time.sleep(1)  # 添加延时避免请求过于频繁
                
            except Exception as e:
                record = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                    'success': False,
                    'error': str(e)
                }
                self.monitoring_data.append(record)
                QMetaObject.invokeMethod(self.delayLabel, "setText",
                                        Qt.ConnectionType.QueuedConnection,
                                        Q_ARG(str, f'监测错误: {str(e)}'))
                time.sleep(1)

    def show_url_dialog(self):
        """显示URL输入对话框"""
        dialog = URLInputDialog(self)
        if dialog.exec():
            return dialog.urlLineEdit.text().strip()
        return None

    def init_timer(self):
        """初始化定时器"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(10)  # 每10毫秒更新一次时间

    def setup_ui(self):
        self.vBoxLayout = QVBoxLayout(self)
        
        # 时间显示部分
        self.timeLabel = QLabel(self)
        self.timeLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timeLabel.setStyleSheet('font-size: 24px; font-weight: bold;')

        # 网络测试部分
        self.urlLayout = QHBoxLayout()
        self.startButton = GradientButton('开始监测', self)
        self.startButton.clicked.connect(self.toggle_monitoring)
        self.urlLayout.addWidget(self.startButton)

        # 延迟显示标签
        self.delayLabel = QLabel('当前延迟: --', self)
        self.delayLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avgDelayLabel = QLabel('平均延迟: --', self)
        self.avgDelayLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 图表
        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setBackground('transparent')
        self.graphWidget.setMinimumHeight(200)
        self.graphWidget.showGrid(x=True, y=True)

        # 添加组件到布局
        self.vBoxLayout.addWidget(self.timeLabel)
        self.vBoxLayout.addLayout(self.urlLayout)
        self.vBoxLayout.addWidget(self.delayLabel)
        self.vBoxLayout.addWidget(self.avgDelayLabel)
        self.vBoxLayout.addWidget(self.graphWidget)

    def setup_ntp(self):
        self.ntp_client = ntplib.NTPClient()
        self.ntp_server = 'time.kriss.re.kr'  # 韩国NTP服务器
        self.time_offset = 0
        self.last_sync = 0

    def sync_ntp(self):
        try:
            response = self.ntp_client.request(self.ntp_server, version=3, timeout=5)
            self.time_offset = response.offset
            self.last_sync = time.time()
            return True
        except Exception as e:
            print(f"NTP同步失败: {str(e)}")
            return False

    def update_time(self):
        # 每60秒重新同步一次NTP
        if time.time() - self.last_sync > 60:
            self.sync_ntp()
    
        current_time = time.time() + self.time_offset
        # 使用韩国时区
        korea_tz = pytz.timezone('Asia/Seoul')
        local_time = datetime.fromtimestamp(current_time, tz=pytz.UTC).astimezone(korea_tz)
        self.timeLabel.setText(local_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])

    def toggle_monitoring(self):
        if not self.is_monitoring:
            # 先选择保存路径
            self.save_path = QFileDialog.getSaveFileName(
                self,
                "选择保存位置",
                "",
                "JSON 文件 (*.json)"
            )[0]
            
            if not self.save_path:  # 如果用户取消选择文件
                return
                
            if not self.save_path.endswith('.json'):
                self.save_path += '.json'
            
            # 然后显示URL输入对话框
            url = self.show_url_dialog()
            if url:
                self.target_url = url
                self.is_monitoring = True
                self.startButton.setText('停止监测')
                self.monitoring_data = []  # 清空之前的数据
                self.monitoring_thread = threading.Thread(target=self.monitor_network, daemon=True)
                self.monitoring_thread.start()
                InfoBar.success(
                    title='成功',
                    content=f'开始监测 {url}',
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
        else:
            self.is_monitoring = False
            self.startButton.setText('开始监测')
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=1)
            # 保存数据
            self.save_monitoring_data()

    def save_monitoring_data(self, is_second_round=False):
        if not self.monitoring_data or not self.save_path:
            return
            
        # 只在第二轮对话时保存数据
        if not is_second_round:
            return
            
        data = {
            'target_url': self.target_url,
            'start_time': self.monitoring_data[0]['timestamp'],
            'end_time': self.monitoring_data[-1]['timestamp'],
            'ntp_server': self.ntp_server,
            'records': self.monitoring_data
        }
        
        try:
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            InfoBar.success(
                title='成功',
                content=f'数据已保存至 {self.save_path}',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=f'保存数据失败: {str(e)}',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )

    def setup_graph(self):
        """初始化图表"""
        self.data_x = []
        self.data_y = []
        pen = pg.mkPen(color=(66, 166, 255), width=2)
        # 移除重复创建的graphWidget
        self.plot = self.graphWidget.plot(pen=pen)
        self.graphWidget.setTitle('网络延迟监测')
        self.graphWidget.setLabel('left', '延迟 (ms)')
        self.graphWidget.setLabel('bottom', '时间点')

class NTPInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.monitor = NTPMonitorCard(self)
        self.vBoxLayout.addWidget(self.monitor)
        self.setObjectName('NTP-Interface')