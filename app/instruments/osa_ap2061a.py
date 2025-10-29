"""光谱分析仪 AP2061A 控制类"""
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import PyApex
from PyApex.Errors import ApexError


class OSA_AP2061A:
    """便捷的 PyApex AP2XXX OSA 接口封装"""

    _CHANNEL_ALIASES: Dict[str, str] = {
        "sum": "1+2",
        "total": "1+2",
        "0": "1+2",
        "both": "1&2",
        "1&2": "1&2",
        "dual": "1&2",
        "1": "1",
        "ch1": "1",
        "channel1": "1",
        "2": "2",
        "ch2": "2",
        "channel2": "2",
    }

    def __init__(
        self,
        ip: str,
        port: int = 5900,
        simulation: bool = False,
        timeout: Optional[float] = 30.0,
    ) -> None:
        """
        初始化 OSA 连接
        
        Args:
            ip: 仪器 IP 地址
            port: 控制端口
            simulation: 是否使用模拟模式
            timeout: 超时时间(秒)
        """
        self._ip = ip
        self._port = port
        self._ap2xxx = PyApex.AP2XXX(ip, PortNumber=port, Simulation=simulation)
        
        if not self._ap2xxx.IsConnected():
            raise ConnectionError(f"无法连接到 AP2061A ({ip}:{port})")
            
        if timeout is not None:
            try:
                self._ap2xxx.SetTimeOut(timeout)
            except Exception:
                pass
                
        self._osa = self._ap2xxx.OSA()
        
        try:
            self._identity = self._ap2xxx.GetID().strip()
        except Exception:
            self._identity = "Unknown ID"

    def __enter__(self) -> "OSA_AP2061A":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @property
    def identity(self) -> str:
        """获取仪器标识"""
        return self._identity

    @property
    def ip(self) -> str:
        """获取 IP 地址"""
        return self._ip

    def close(self) -> None:
        """关闭连接"""
        try:
            self._ap2xxx.Close()
        except Exception:
            pass

    def configure(
        self,
        center_nm: float,
        span_nm: float,
        channel: str = "1",
    ) -> None:
        """
        配置波长设置和输入通道
        
        Args:
            center_nm: 中心波长 (nm)
            span_nm: 扫描跨度 (nm)
            channel: 偏振通道 (1, 2, 1&2 等)
        """
        channel_key = self._CHANNEL_ALIASES.get(channel.lower(), channel)
        
        try:
            self._osa.SetPolarizationMode(channel_key)
        except ApexError as exc:
            raise ValueError(f"无效的通道选择 {channel!r}: {exc}") from exc

        self._osa.SetCenter(center_nm)
        self._osa.SetSpan(span_nm)

    def acquire_once(
        self,
        scale_x: str = "nm",
        scale_y: str = "log",
        trace: int = 1,
        sweep_mode: str = "single",
    ) -> Tuple[int, List[float], List[float]]:
        """
        触发一次扫描并返回数据
        
        Args:
            scale_x: X 轴单位 (nm 或 GHz)
            scale_y: Y 轴单位 (log 或 lin)
            trace: 轨迹编号 (1-6)
            sweep_mode: 扫描模式 (single, repeat, auto)
            
        Returns:
            (轨迹编号, Y 数据列表, X 数据列表)
        """
        trace_num = self._osa.Run(sweep_mode)
        
        if trace_num <= 0:
            raise RuntimeError("OSA 未返回有效的轨迹编号；测量可能已中断")
            
        y_data, x_data = self._osa.GetData(scale_x, scale_y, trace)
        return trace_num, list(y_data), list(x_data)

    def get_peak_info(
        self,
        y_data: List[float],
        x_data: List[float],
    ) -> Tuple[float, float]:
        """
        获取峰值信息
        
        Args:
            y_data: Y 轴数据
            x_data: X 轴数据
            
        Returns:
            (峰值功率, 峰值位置)
        """
        if not y_data:
            return float('nan'), float('nan')
            
        peak_value = max(y_data)
        peak_index = y_data.index(peak_value)
        peak_x = x_data[peak_index] if peak_index < len(x_data) else float("nan")
        
        return peak_value, peak_x
