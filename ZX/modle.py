from openai import OpenAI
from PyQt6.QtCore import QObject, pyqtSignal
import json
from datetime import datetime

class AIChat(QObject):
    # 定义信号
    complete_txt = pyqtSignal(str)      # 完整响应
    water_txt = pyqtSignal(str)        # 流式响应片段
    error_occurred = pyqtSignal(str)   # 错误信息
    push_content = pyqtSignal(str)     # 推理过程

    def __init__(self):
        super().__init__()
        self.client = OpenAI(
            base_url="https://ai-gateway.vei.volces.com/v1",
            api_key="sk-b2d745f1f1a64f79b35663ec04c56a7cso93ys03hn8pb2h6"  # 请替换为真实API密钥
        )
        self.USTEXT = ""  # 用户输入文本
        self._response_buffer = []     # 响应内容缓冲区
        self._reasoning_buffer = []    # 推理内容缓冲区
        self._has_reasoning = False    # 是否包含推理标记
        self.chat_history = []         # 对话历史记录
        self.reasoning_history = []    # 推理历史记录
        self.reasoning_file_path = None  # 初始化推理历史文件路径为None
        # 移除不必要的初始化调用
        self.load_reasoning_history(self.reasoning_file_path)  # 加载已有的推理历史

    def set_user_text(self, text: str):
        """设置用户输入文本"""
        self.USTEXT = text.strip()

    def get_response(self):
        """发起AI对话请求并处理响应"""
        if not self.USTEXT:
            self.error_occurred.emit("输入内容不能为空")
            return ""

        try:
            # 发起流式请求
            messages = [
                {"role": "system", "content": "你是一个乐于助人的AI助手。"}
            ]
            
            # 添加历史对话记录
            if self.chat_history:
                messages.extend([
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in self.chat_history
                ])
            
            # 添加当前用户输入
            messages.append({"role": "user", "content": self.USTEXT})
            
            stream = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=2000,
                timeout=30  # 增加超时设置
            )

            # 初始化状态
            self._response_buffer = []
            self._has_reasoning = False
            is_first_content = True

            # 处理数据流
            for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                # 处理推理内容
                if self._process_reasoning(delta):
                    continue

                # 处理普通文本内容
                content = getattr(delta, 'content', '')
                if content:
                    self._process_content(content, is_first_content)
                    is_first_content = False

            # 最终处理
            self._finalize_processing()
            return self._get_full_response()

        except Exception as e:
            error_msg = f"请求失败: {str(e)}"
            self.error_occurred.emit(error_msg)
            return error_msg

    def _process_reasoning(self, delta) -> bool:
        """处理推理内容，返回是否包含推理数据"""
        if hasattr(delta, 'reasoning_content'):
            reasoning = delta.reasoning_content
            self.push_content.emit(reasoning)
            self._has_reasoning = True
            self._reasoning_buffer.append(reasoning)
            return True
        return False

    def _process_content(self, content: str, is_first: bool):
        """处理文本内容片段"""
        # 添加首次内容前缀
        if is_first:
            self.water_txt.emit("\n\n## AI说： \n")
            # 记录用户输入到对话历史
            self.chat_history.append({
                'role': 'user',
                'content': self.USTEXT,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # 发送片段并缓存
        self.water_txt.emit(content)
        self._response_buffer.append(content)

    def _finalize_processing(self):
        """最终处理逻辑"""
        # 处理推理内容
        if self._has_reasoning:
            full_reasoning = ''.join(self._reasoning_buffer)
            self.reasoning_history.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'content': full_reasoning
            })
        else:
            reasoning = "🤔 本次回答没有经过深度思考"
            self.push_content.emit(reasoning)
            self.reasoning_history.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'content': reasoning
            })

        # 发送完整响应并记录到对话历史
        full_response = ''.join(self._response_buffer)
        self.complete_txt.emit(full_response)
        self.chat_history.append({
            'role': 'assistant',
            'content': full_response,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        # 清空缓冲区
        self._reasoning_buffer = []

        # 保存推理历史到当前使用的文件
        if self.reasoning_file_path:
            self.save_reasoning_history(self.reasoning_file_path)
    def save_chat_history(self, file_path: str):
        """保存对话历史到JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'chat_history': self.chat_history,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.error_occurred.emit(f"保存对话历史失败: {str(e)}")
            return False

    def save_reasoning_history(self, file_path: str):
        """保存推理历史到JSON文件"""
        # 确保文件路径有效
        if not file_path or not isinstance(file_path, str):
            self.error_occurred.emit("推理历史文件路径未设置或无效")
            return False
            
        try:
            # 更新当前实例的推理历史文件路径
            self.reasoning_file_path = file_path
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'reasoning_history': self.reasoning_history,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.error_occurred.emit(f"保存推理历史失败: {str(e)}")
            return False

    def load_chat_history(self, file_path: str):
        """从JSON文件加载对话历史"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'chat_history' in data:
                    self.chat_history = data['chat_history']
            return True
        except Exception as e:
            self.error_occurred.emit(f"加载对话历史失败: {str(e)}")
            return False

    def load_reasoning_history(self, file_path: str):
        """从JSON文件加载推理历史"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'reasoning_history' in data:
                    self.reasoning_history = data['reasoning_history']
            return True
        except Exception as e:
            self.error_occurred.emit(f"加载推理历史失败: {str(e)}")
            return False

    def _get_full_response(self) -> str:
        """获取完整响应内容"""
        return ''.join(self._response_buffer)