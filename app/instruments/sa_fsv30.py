"""频谱分析仪 FSV30 控制类"""
from typing import List, Tuple, Optional
from RsInstrument import RsInstrument


class SA_FSV30:
    """R&S FSV30 频谱分析仪控制类"""

    def __init__(
        self,
        ip: str,
        visa_timeout: int = 10000,
        opc_timeout: int = 10000,
    ) -> None:
        """
        初始化频谱分析仪连接
        
        Args:
            ip: 仪器 IP 地址
            visa_timeout: VISA 超时时间 (ms)
            opc_timeout: OPC 超时时间 (ms)
        """
        self._ip = ip
        self._resource = f"TCPIP::{ip}::INSTR"
        self._instr: Optional[RsInstrument] = None
        self._visa_timeout = visa_timeout
        self._opc_timeout = opc_timeout
        self._identity = ""
        self._markers: List[Tuple[str, float]] = []

    def connect(self) -> None:
        """连接到仪器"""
        if self._instr is None:
            self._instr = RsInstrument(
                self._resource,
                reset=False,
                id_query=True
            )
            self._instr.visa_timeout = self._visa_timeout
            self._instr.opc_timeout = self._opc_timeout
            self._instr.instrument_status_checking = True
            
            self._identity = self._instr.query_str("*IDN?").strip()
            
            # 初始化设置
            self._instr.write_str("*CLS")
            self._instr.write_str("INIT:CONT OFF")
            self._instr.write_str("ABOR")
            self._instr.write_str("SYST:DISP:UPD ON")

    def disconnect(self) -> None:
        """断开连接"""
        if self._instr:
            self._instr.close()
            self._instr = None

    def __enter__(self) -> "SA_FSV30":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disconnect()

    @property
    def identity(self) -> str:
        """获取仪器标识"""
        return self._identity

    @property
    def ip(self) -> str:
        """获取 IP 地址"""
        return self._ip

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._instr is not None

    def configure(
        self,
        center_freq_hz: float,
        span_hz: float,
        rbw_hz: float = 1000,
        vbw_hz: float = 10,
    ) -> None:
        """
        配置频谱分析仪参数
        
        Args:
            center_freq_hz: 中心频率 (Hz)
            span_hz: 扫描跨度 (Hz)
            rbw_hz: 分辨率带宽 (Hz)
            vbw_hz: 视频带宽 (Hz)
        """
        if not self._instr:
            raise RuntimeError("未连接到仪器")

        self._instr.write_str_with_opc(f"SENS:FREQ:CENT {center_freq_hz}")
        self._instr.write_str_with_opc(f"SENS:FREQ:SPAN {span_hz}")
        self._instr.write_str_with_opc(f"SENS:BAND:RES {rbw_hz}")
        self._instr.write_str_with_opc(f"SENS:BAND:VID {vbw_hz}")
        self._instr.write_str_with_opc("SENS:SWE:TYPE AUTO")

    def set_marker(self, marker_num: int, freq_hz: float) -> None:
        """
        设置标记
        
        Args:
            marker_num: 标记编号 (1-4)
            freq_hz: 标记频率 (Hz)
        """
        if not self._instr:
            raise RuntimeError("未连接到仪器")
            
        marker_cmd = f"CALC:MARK{marker_num}"
        self._instr.write_str(f"{marker_cmd}:STAT ON")
        self._instr.write_str(f"{marker_cmd}:X {freq_hz}")
        
        # 保存标记信息
        found = False
        for i, (cmd, _) in enumerate(self._markers):
            if cmd == marker_cmd:
                self._markers[i] = (marker_cmd, freq_hz)
                found = True
                break
        if not found:
            self._markers.append((marker_cmd, freq_hz))

    def acquire_once(self) -> List[Tuple[int, float, float]]:
        """
        执行一次测量并读取标记值
        
        Returns:
            [(标记编号, 频率, 功率电平), ...]
        """
        if not self._instr:
            raise RuntimeError("未连接到仪器")

        self._instr.write_str("INIT:IMM")
        self._instr.query_str("*OPC?")

        readings = []
        for marker_cmd, _ in self._markers:
            marker_num = int(marker_cmd[-1])
            freq = float(self._instr.query_str(f"{marker_cmd}:X?"))
            level = float(self._instr.query_str(f"{marker_cmd}:Y?"))
            readings.append((marker_num, freq, level))

        return readings

    def get_trace_data(self) -> Tuple[List[float], List[float]]:
        """
        获取轨迹数据
        
        Returns:
            (频率列表, 功率列表)
        """
        if not self._instr:
            raise RuntimeError("未连接到仪器")
            
        # 获取频率点
        freq_start = float(self._instr.query_str("SENS:FREQ:START?"))
        freq_stop = float(self._instr.query_str("SENS:FREQ:STOP?"))
        
        # 获取轨迹数据
        trace_data = self._instr.query_bin_or_ascii_float_list("TRAC? TRACE1")
        
        # 生成频率列表
        num_points = len(trace_data)
        freq_list = [
            freq_start + i * (freq_stop - freq_start) / (num_points - 1)
            for i in range(num_points)
        ]
        
        return freq_list, trace_data
