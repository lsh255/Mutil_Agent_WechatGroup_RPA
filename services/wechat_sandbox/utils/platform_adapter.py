"""
平台适配器抽象层
支持 Windows/Linux 跨平台鼠标和剪贴板操作
"""

import platform
import time
import subprocess
from abc import ABC, abstractmethod
from typing import Optional
from utils.logger import logger


class PlatformAdapter(ABC):
    """平台适配器抽象基类"""
    
    @abstractmethod
    def click_mouse(self, x: int, y: int) -> bool:
        """
        模拟鼠标点击
        
        输入:
            x: 屏幕X坐标
            y: 屏幕Y坐标
        返回:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def double_click(self, x: int, y: int) -> bool:
        """
        模拟鼠标双击
        
        输入:
            x: 屏幕X坐标
            y: 屏幕Y坐标
        返回:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def copy_to_clipboard(self) -> bool:
        """
        执行复制操作（Ctrl+C）
        
        返回:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def get_clipboard(self) -> Optional[str]:
        """
        获取剪贴板内容
        
        返回:
            Optional[str]: 剪贴板文本内容，失败返回None
        """
        pass


class LinuxAdapter(PlatformAdapter):
    """Linux平台适配器（使用 xdotool 和 xclip）"""
    
    def __init__(self):
        """初始化Linux适配器"""
        self._check_dependencies()
        logger.info("LinuxAdapter initialized")
    
    def _check_dependencies(self):
        """检查必要的系统工具是否安装"""
        try:
            subprocess.run(['xdotool', '--version'], capture_output=True, check=True)
            subprocess.run(['xclip', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Linux依赖检查失败: {e}")
            raise RuntimeError("请安装 xdotool 和 xclip: sudo apt install xdotool xclip")
    
    def click_mouse(self, x: int, y: int) -> bool:
        """模拟鼠标点击（Linux版本）"""
        try:
            subprocess.run(['xdotool', 'mousemove', str(x), str(y)], check=True)
            subprocess.run(['xdotool', 'click', '1'], check=True)
            return True
        except Exception as e:
            logger.error(f"模拟鼠标点击失败: {e}")
            return False
    
    def double_click(self, x: int, y: int) -> bool:
        """模拟鼠标双击（Linux版本）"""
        try:
            subprocess.run(['xdotool', 'mousemove', str(x), str(y)], check=True)
            subprocess.run(['xdotool', 'click', '--repeat', '2', '1'], check=True)
            return True
        except Exception as e:
            logger.error(f"模拟鼠标双击失败: {e}")
            return False
    
    def copy_to_clipboard(self) -> bool:
        """执行复制操作（Linux版本）"""
        try:
            subprocess.run(['xdotool', 'key', 'Ctrl+c'], check=True)
            return True
        except Exception as e:
            logger.error(f"执行复制操作失败: {e}")
            return False
    
    def get_clipboard(self) -> Optional[str]:
        """获取剪贴板内容（Linux版本）"""
        try:
            result = subprocess.run(
                ['xclip', '-selection', 'clipboard', '-o'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"获取剪贴板内容失败: {e}")
            return None


class WindowsAdapter(PlatformAdapter):
    """Windows平台适配器（使用 ctypes）"""
    
    def __init__(self):
        """初始化Windows适配器"""
        import ctypes
        from ctypes import wintypes
        
        self.ctypes = ctypes
        self.wintypes = wintypes
        
        user32 = ctypes.windll.user32
        
        # 定义常量
        self.MOUSEEVENTF_MOVE = 0x0001
        self.MOUSEEVENTF_LEFTDOWN = 0x0002
        self.MOUSEEVENTF_LEFTUP = 0x0004
        
        # 定义函数原型
        self.SetCursorPos = user32.SetCursorPos
        self.SetCursorPos.argtypes = [wintypes.INT, wintypes.INT]
        self.SetCursorPos.restype = wintypes.BOOL
        
        self.mouse_event = user32.mouse_event
        self.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.ULONG_PTR]
        self.mouse_event.restype = None
        
        logger.info("WindowsAdapter initialized")
    
    def click_mouse(self, x: int, y: int) -> bool:
        """模拟鼠标点击（Windows版本）"""
        try:
            self.SetCursorPos(x, y)
            time.sleep(0.05)
            self.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            self.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            return True
        except Exception as e:
            logger.error(f"模拟鼠标点击失败: {e}")
            return False
    
    def double_click(self, x: int, y: int) -> bool:
        """模拟鼠标双击（Windows版本）"""
        try:
            self.SetCursorPos(x, y)
            time.sleep(0.05)
            for _ in range(2):
                self.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                self.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                time.sleep(0.05)
            return True
        except Exception as e:
            logger.error(f"模拟鼠标双击失败: {e}")
            return False
    
    def copy_to_clipboard(self) -> bool:
        """执行复制操作（Windows版本）"""
        try:
            import ctypes
            from ctypes import wintypes
            
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            VK_CONTROL = 0x11
            VK_C = 0x43
            KEYEVENTF_KEYDOWN = 0x0000
            KEYEVENTF_KEYUP = 0x0002
            
            # 模拟 Ctrl+C
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYDOWN, 0)
            time.sleep(0.01)
            user32.keybd_event(VK_C, 0, KEYEVENTF_KEYDOWN, 0)
            time.sleep(0.01)
            user32.keybd_event(VK_C, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.01)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            
            return True
        except Exception as e:
            logger.error(f"执行复制操作失败: {e}")
            return False
    
    def get_clipboard(self) -> Optional[str]:
        """获取剪贴板内容（Windows版本）"""
        try:
            import ctypes
            from ctypes import wintypes
            
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            CF_UNICODETEXT = 13
            GMEM_MOVEABLE = 0x0002
            
            user32.OpenClipboard.argtypes = [wintypes.HWND]
            user32.OpenClipboard.restype = wintypes.BOOL
            
            user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
            user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
            
            user32.GetClipboardData.argtypes = [wintypes.UINT]
            user32.GetClipboardData.restype = wintypes.HANDLE
            
            user32.CloseClipboard.argtypes = []
            user32.CloseClipboard.restype = wintypes.BOOL
            
            kernel32.GlobalLock.argtypes = [wintypes.HANDLE]
            kernel32.GlobalLock.restype = wintypes.LPVOID
            
            kernel32.GlobalUnlock.argtypes = [wintypes.HANDLE]
            kernel32.GlobalUnlock.restype = wintypes.BOOL
            
            # 打开剪贴板
            if not user32.OpenClipboard(0):
                logger.warning("无法打开剪贴板")
                return None
            
            # 检查剪贴板是否包含文本
            if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
                user32.CloseClipboard()
                logger.warning("剪贴板中不包含Unicode文本")
                return None
            
            # 获取剪贴板数据
            h_data = user32.GetClipboardData(CF_UNICODETEXT)
            if not h_data:
                user32.CloseClipboard()
                logger.warning("无法获取剪贴板数据")
                return None
            
            # 锁定数据并转换为字符串
            p_data = kernel32.GlobalLock(h_data)
            text = ctypes.c_wchar_p(p_data).value
            
            # 解锁并关闭剪贴板
            kernel32.GlobalUnlock(h_data)
            user32.CloseClipboard()
            
            return text
        except Exception as e:
            logger.error(f"获取剪贴板内容失败: {e}")
            return None


def get_platform_adapter() -> PlatformAdapter:
    """
    工厂方法：根据当前操作系统返回对应的平台适配器
    
    返回:
        PlatformAdapter: 平台适配器实例
        
    异常:
        RuntimeError: 不支持的操作系统
    """
    system = platform.system().lower()
    
    if system == 'linux':
        return LinuxAdapter()
    elif system == 'windows':
        return WindowsAdapter()
    else:
        raise RuntimeError(f"不支持的操作系统: {system}")


# 全局单例
_adapter: Optional[PlatformAdapter] = None


def get_adapter() -> PlatformAdapter:
    """
    获取平台适配器单例
    
    返回:
        PlatformAdapter: 平台适配器实例
    """
    global _adapter
    if _adapter is None:
        _adapter = get_platform_adapter()
    return _adapter
