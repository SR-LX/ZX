from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import SearchLineEdit, TextBrowser
from custom_button import GradientButton

class ChatInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('ChatInterface')
        
        # 创建布局
        self.vBoxLayout = QVBoxLayout(self)
        self.hBoxLayout = QHBoxLayout()
        
        # 创建组件
        self.chatBrowser = TextBrowser(self)
        self.inputEdit = SearchLineEdit(self, show_search_button=False)
        self.sendButton = GradientButton('发送', self)
        
        # 设置组件属性
        self.chatBrowser.setMinimumHeight(400)
        self.inputEdit.setMinimumWidth(300)
        self.inputEdit.setPlaceholderText('请输入消息...')
        self.sendButton.setFixedSize(66, 31)
        
        # 组装布局
        self.hBoxLayout.addWidget(self.inputEdit)
        self.hBoxLayout.addWidget(self.sendButton)
        
        self.vBoxLayout.addWidget(self.chatBrowser)
        self.vBoxLayout.addLayout(self.hBoxLayout)
        
        # 设置布局间距和边距
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setContentsMargins(10, 10, 10, 10)
        self.hBoxLayout.setSpacing(10)
        
        # 连接信号
        self.sendButton.clicked.connect(self.onSendButtonClicked)
        self.inputEdit.returnPressed.connect(self.onSendButtonClicked)
        
    def onSendButtonClicked(self):
        """发送按钮点击事件"""
        text = self.inputEdit.text().strip()
        if text:
            self.chatBrowser.append(f"You: {text}")
            # 这里可以添加调用API的代码
            self.inputEdit.clear()

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = ChatInterface()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())