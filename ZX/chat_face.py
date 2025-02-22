from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from qfluentwidgets import SearchLineEdit, TextBrowser, ToolButton, FluentIcon, InfoBar, InfoBarPosition
from custom_button import GradientButton
from modle import AIChat
from markdown import markdown
import os

class AIResponseThread(QThread):
    """AI响应工作线程"""
    response_ready = pyqtSignal()
    
    def __init__(self, ai_chat):
        super().__init__()
        self.ai_chat = ai_chat
        self.text = ""
        
    def set_text(self, text):
        """设置要处理的文本"""
        self.text = text
        
    def run(self):
        """线程运行函数"""
        if self.text:
            self.ai_chat.set_user_text(self.text)
            self.ai_chat.get_response()
            self.response_ready.emit()

class ChatInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('ChatInterface')
        
        # 创建布局
        self.vBoxLayout = QVBoxLayout(self)
        self.hBoxLayout = QHBoxLayout()
        self.buttonLayout = QHBoxLayout()
        
        # 创建组件
        self.chatBrowser = TextBrowser(self)
        self.chatBrowser.setReadOnly(True)  # 设置为只读
        self.chatBrowser.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # 保存原始的insertHtml方法
        self._original_insert_html = self.chatBrowser.insertHtml
        
        # 重写insertHtml方法
        def new_insert_html(html):
            cursor = self.chatBrowser.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.chatBrowser.setTextCursor(cursor)
            self._original_insert_html(html)
        
        # 绑定新的方法
        self.chatBrowser.insertHtml = new_insert_html
        self.chatBrowser.setMouseTracking(False)  # 禁用鼠标跟踪
        self.chatBrowser.setCursor(Qt.CursorShape.ArrowCursor)  # 设置鼠标指针为箭头形状
        self.chatBrowser.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByKeyboard | 
                                               Qt.TextInteractionFlag.TextSelectableByMouse)  # 允许选择文本但禁止光标移动
        
        self.inputEdit = SearchLineEdit(self, show_search_button=False)
        self.sendButton = GradientButton('发送', self)
        self.saveButton = ToolButton(FluentIcon.SAVE, self)
        self.saveButton.setToolTip('保存对话记录')
        self.saveButton.clicked.connect(self.onSaveButtonClicked)
        
        # 设置组件属性
        self.chatBrowser.setMinimumHeight(400)
        self.inputEdit.setMinimumWidth(300)
        self.inputEdit.setPlaceholderText('请输入消息...')
        self.sendButton.setFixedSize(66, 31)
        
        # 组装布局
        self.hBoxLayout.addWidget(self.inputEdit)
        self.hBoxLayout.addWidget(self.sendButton)
        
        self.vBoxLayout.addWidget(self.chatBrowser)
        self.buttonLayout.addWidget(self.saveButton)
        self.buttonLayout.addStretch()
        self.vBoxLayout.addLayout(self.buttonLayout)
        self.vBoxLayout.addLayout(self.hBoxLayout)
        
        # 设置布局间距和边距
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setContentsMargins(10, 10, 10, 10)
        self.hBoxLayout.setSpacing(10)
        self.buttonLayout.setContentsMargins(0, 0, 0, 10)
        
        # 创建AI聊天实例和工作线程
        self.ai_chat = AIChat()
        self.response_thread = AIResponseThread(self.ai_chat)
        
        # 连接信号
        self.sendButton.clicked.connect(self.onSendButtonClicked)
        self.inputEdit.returnPressed.connect(self.onSendButtonClicked)
        
        # 连接AI聊天信号
        self.ai_chat.water_txt.connect(self.onStreamResponse)
        self.ai_chat.push_content.connect(self.onReasoningContent)
        self.ai_chat.error_occurred.connect(self.onError)
        
        # 连接线程信号
        self.response_thread.response_ready.connect(self.onResponseReady)
        
    def onSaveButtonClicked(self):
        """加载聊天记录按钮点击事件"""
        # 选择要加载的聊天记录文件
        chat_file_path = QFileDialog.getOpenFileName(
            self,
            "选择聊天记录文件",
            "",
            "JSON 文件 (*.json)"
        )[0]
        
        if not chat_file_path:
            return
            
        # 加载聊天记录
        if self.ai_chat.load_chat_history(chat_file_path):
            # 更新界面显示历史对话
            self.chatBrowser.clear()
            for message in self.ai_chat.chat_history:
                if message['role'] == 'user':
                    self.chatBrowser.insertHtml(f"<br><strong>🧑‍💻 You：</strong><br>{markdown(message['content'])}<br>")
                else:
                    self.chatBrowser.insertHtml(f"<br><strong>🤖 AI：</strong><br>{markdown(message['content'])}<br>")
            
            InfoBar.success(
                title='成功',
                content=f'已加载聊天记录',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            # 更新当前聊天文件路径
            self.chat_file_path = chat_file_path
        else:
            InfoBar.error(
                title='错误',
                content='加载聊天记录失败',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
        
    def onStreamResponse(self, content: str):
        """处理流式响应"""
        if not hasattr(self, '_first_response'):
            self._first_response = True
            self.chatBrowser.insertHtml("<br><strong>🤖 AI：</strong><br><br>")
        html_content = markdown(content)  # 将 Markdown 转换为 HTML
        self.chatBrowser.insertHtml(html_content)  # 移除额外的换行符
        self.chatBrowser.verticalScrollBar().setValue(
            self.chatBrowser.verticalScrollBar().maximum()
        )
    
    def onReasoningContent(self, reasoning: str):
        """处理推理内容"""
        if not hasattr(self, '_first_reasoning'):
            self._first_reasoning = True
            self.chatBrowser.insertHtml("> 💭 思考过程：<br><br>")
        html_content = markdown(reasoning)  # 将 Markdown 转换为 HTML
        self.chatBrowser.insertHtml(html_content)
        self.chatBrowser.verticalScrollBar().setValue(
            self.chatBrowser.verticalScrollBar().maximum()
        )
    
    def onError(self, error: str):
        """处理错误信息"""
        error_html = f"<br><br><strong>❌ 错误：</strong>{error}<br>"
        self.chatBrowser.insertHtml(error_html)
        self.chatBrowser.verticalScrollBar().setValue(
            self.chatBrowser.verticalScrollBar().maximum()
        )
        self.enableInput()

    def onResponseReady(self):
        """响应完成时启用输入"""
        self.enableInput()
        
    def enableInput(self):
        """启用输入控件"""
        self.inputEdit.setEnabled(True)
        self.sendButton.setEnabled(True)
        
    def disableInput(self):
        """禁用输入控件"""
        self.inputEdit.setEnabled(False)
        self.sendButton.setEnabled(False)

    def onSendButtonClicked(self):
        """发送按钮点击事件"""
        text = self.inputEdit.text().strip()
        if text:
            # 如果是首次对话，弹出保存对话框
            if not hasattr(self, 'chat_file_path'):
                chat_file_path = QFileDialog.getSaveFileName(
                    self,
                    "选择保存对话记录的文件",
                    "",
                    "JSON 文件 (*.json)"
                )[0]
                
                if not chat_file_path:
                    return
                    
                if not chat_file_path.endswith('.json'):
                    chat_file_path += '.json'
                
                self.chat_file_path = chat_file_path
                # 初始化空的对话历史文件
                self.ai_chat.chat_history = []
                self.ai_chat.reasoning_history = []
                self.ai_chat.save_chat_history(self.chat_file_path)
                # 创建推理历史文件
                reasoning_file_path = chat_file_path.replace('.json', '_reasoning.json')
                self.reasoning_file_path = reasoning_file_path
                self.ai_chat.save_reasoning_history(self.reasoning_file_path)
            
            # 重置对话状态
            if hasattr(self, '_first_response'):
                delattr(self, '_first_response')
            if hasattr(self, '_first_reasoning'):
                delattr(self, '_first_reasoning')
            
            # 显示用户输入（使用HTML格式）
            user_html = f"<br><strong>🧑‍💻 You：</strong><br>{markdown(text)}<br>"
            self.chatBrowser.insertHtml(user_html)
            self.chatBrowser.verticalScrollBar().setValue(
                self.chatBrowser.verticalScrollBar().maximum()
            )
            
            # 禁用输入，等待响应
            self.disableInput()
            
            # 在工作线程中处理响应
            self.response_thread.set_text(text)
            self.response_thread.start()
            
            # 清空输入框
            self.inputEdit.clear()
            
            # 保存当前对话记录
            self.ai_chat.save_chat_history(self.chat_file_path)

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = ChatInterface()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())