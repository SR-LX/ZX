import requests
import time
import statistics
from typing import List, Tuple
from datetime import datetime
import ntplib
import threading
from queue import Queue
import os  # 添加在文件开头的导入部分

class NTPTimeSync:
    def __init__(self, ntp_server: str = 'ntp.aliyun.com', display_time: bool = False):
        self.ntp_server = ntp_server
        self.time_offset = 0.0
        self.running = True
        self.time_queue = Queue()
        self.lock = threading.Lock()
        self.display_time = display_time
        self.sync_thread = threading.Thread(target=self._sync_ntp_time_loop)
        self.sync_thread.daemon = True
        self.sync_thread.start()
        
        if display_time:
            self.display_thread = threading.Thread(target=self._display_time_loop)
            self.display_thread.daemon = True
            self.display_thread.start()

    def _sync_ntp_time_loop(self) -> None:
        """持续运行的NTP时间同步循环"""
        while self.running:
            try:
                ntp_client = ntplib.NTPClient()
                response = ntp_client.request(self.ntp_server, version=3, timeout=5)
                with self.lock:
                    self.time_offset = response.offset
                    self.time_queue.put(self.time_offset)
                if not self.display_time:  # 只在非显示模式下打印同步信息
                    print(f'\nNTP服务器同步成功 - 时间偏移: {self.time_offset*1000:.2f}ms')
            except Exception as e:
                if not self.display_time:  # 只在非显示模式下打印错误信息
                    print(f'\nNTP服务器同步失败: {str(e)}')
                with self.lock:
                    self.time_offset = 0.0
            time.sleep(30)  # 提高同步频率到30秒一次

    # 在文件开头添加导入
    import pytz
    
    # 在 _display_time_loop 方法中修改
    def _display_time_loop(self) -> None:
        """显示NTP服务器时间的循环"""
        korea_tz = pytz.timezone('Asia/Seoul')
        while self.running:
            try:
                with self.lock:
                    current_time = self.get_current_time()
                # 使用韩国时区
                local_time = datetime.fromtimestamp(current_time/1000, tz=pytz.UTC).astimezone(korea_tz)
                print(f"\r{self.ntp_server} 当前时间: {local_time.strftime('%Y-%m-%d %H:%M:%S')} (韩国时间)", end='', flush=True)
                time.sleep(0.5)
            except Exception as e:
                print(f"\r时间显示错误: {str(e)}", end='', flush=True)
                time.sleep(1)

    def get_current_time(self) -> float:
        """获取当前校正后的时间戳（毫秒）"""
        with self.lock:
            return (time.time() + self.time_offset) * 1000

    def stop(self) -> None:
        """停止NTP同步线程"""
        self.running = False
        if self.sync_thread.is_alive():
            self.sync_thread.join()
        if hasattr(self, 'display_thread') and self.display_thread.is_alive():
            self.display_thread.join()

class WebPing:
    def __init__(self, url: str, count: int = 4, timeout: float = 5.0):
        """初始化WebPing对象

        Args:
            url (str): 目标网页URL
            count (int, optional): 测试次数. 默认为4次
            timeout (float, optional): 超时时间(秒). 默认为5秒
        """
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        self.url = url
        self.count = count
        self.timeout = timeout
        self.results: List[Tuple[float, float, bool]] = []  # (发送时间, 接收时间, 成功状态)
        self.ntp_sync = NTPTimeSync()

    def get_current_time(self) -> float:
        """获取当前校正后的时间戳（毫秒）"""
        return self.ntp_sync.get_current_time()

    def ping(self) -> None:
        """执行ping测试"""
        print(f'\n\n正在 Ping {self.url} 进行 {self.count} 次测试:')  # 添加一个额外的换行
        print('=' * 60)

        for i in range(self.count):
            start_time = self.get_current_time()
            try:
                response = requests.get(self.url, timeout=self.timeout)
                end_time = self.get_current_time()
                success = response.status_code == 200
                self.results.append((start_time, end_time, success))
                
                send_delay = 0
                recv_delay = 0
                if success:
                    total_time = end_time - start_time
                    send_delay = total_time / 2
                    recv_delay = total_time / 2
                
                status = '成功' if success else f'失败 (状态码: {response.status_code})'
                print(f'\n请求 {i+1}: {status}')  # 添加换行
                if success:
                    print(f'发送延迟: {send_delay:.2f}ms')
                    print(f'接收延迟: {recv_delay:.2f}ms')
                print(f'发送时间: {datetime.fromtimestamp(start_time/1000).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]}')
                print(f'接收时间: {datetime.fromtimestamp(end_time/1000).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]}')
                
            except requests.exceptions.Timeout:
                print(f'\n请求 {i+1}: 超时 - 超过 {self.timeout}秒')  # 添加换行
                self.results.append((start_time, start_time + self.timeout * 1000, False))
                
            except requests.exceptions.RequestException as e:
                print(f'\n请求 {i+1}: 错误 - {str(e)}')  # 添加换行
                self.results.append((start_time, start_time, False))
                
            time.sleep(1)

    def show_statistics(self) -> None:
        """显示测试统计结果"""
        if not self.results:
            print('\n没有可用的测试结果')
            return

        print('\n测试统计:')
        print('=' * 60)
        
        # 计算成功请求的统计数据
        success_results = [(end - start) for start, end, s in self.results if s]
        success_count = len(success_results)
        
        if success_count > 0:
            avg_time = statistics.mean(success_results)
            min_time = min(success_results)
            max_time = max(success_results)
            if len(success_results) > 1:
                std_dev = statistics.stdev(success_results)
            else:
                std_dev = 0
                
            print(f'成功请求数: {success_count}/{self.count} ({success_count/self.count*100:.1f}%)')
            print(f'平均单向延迟: {avg_time/2:.2f}ms')
            print(f'最小单向延迟: {min_time/2:.2f}ms')
            print(f'最大单向延迟: {max_time/2:.2f}ms')
            print(f'标准偏差: {std_dev/2:.2f}ms')
        else:
            print('所有请求均失败')
            
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'ntp_sync'):
            self.ntp_sync.stop()

def main():
    # 启用 Windows 终端的 ANSI 支持
    if os.name == 'nt':
        os.system('')  # 启用 ANSI 支持
    
    # 创建韩国NTP时间显示实例
    print("\033[2J\033[H")  # 清屏并将光标移到开头
    print("NTP 时间同步显示区域:")
    print("=" * 60)
    print("\n" * 2)  # 为 NTP 显示预留空间
    korea_ntp = NTPTimeSync('time.kriss.re.kr', display_time=True)
    
    try:
        # 将光标移动到预留空间之后
        print("\033[6;1H")  # 移动到第6行开始显示用户交互
        url = input('请输入要测试的网址: ')
        count = int(input('请输入测试次数 (默认4次): ') or '4')
        timeout = float(input('请输入超时时间 (默认5秒): ') or '5')
        
        print(f'\n开始测试 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        pinger = WebPing(url, count, timeout)
        pinger.ping()
        pinger.show_statistics()
    finally:
        korea_ntp.stop()

if __name__ == '__main__':
    main()