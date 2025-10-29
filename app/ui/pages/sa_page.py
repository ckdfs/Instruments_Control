# coding:utf-8
"""频谱分析仪控制页面"""
import threading
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout
from qfluentwidgets import (
    CardWidget, SubtitleLabel, BodyLabel, LineEdit,
    PrimaryPushButton, PushButton, SpinBox,
    DoubleSpinBox, InfoBar, InfoBarPosition
)

from app.instruments.sa_fsv30 import SA_FSV30
from app.ui.widgets.plot_widget import PlotWidget


class SAPage(QWidget):
    """频谱分析仪控制页面"""
    
    data_received = pyqtSignal(list, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sa-page")
        
        self.sa: SA_FSV30 = None
        self.acquisition_thread = None
        self.is_acquiring = False
        
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._on_acquire)
        
        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = SubtitleLabel("频谱分析仪 (SA FSV30)", self)
        layout.addWidget(title)

        connection_card = self._create_connection_card()
        layout.addWidget(connection_card)

        config_card = self._create_config_card()
        layout.addWidget(config_card)

        self.plot_widget = PlotWidget("频谱", self)
        self.plot_widget.set_labels("频率 (MHz)", "功率 (dBm)")
        layout.addWidget(self.plot_widget, 1)

        self.status_label = BodyLabel("未连接", self)
        layout.addWidget(self.status_label)

    def _create_connection_card(self) -> CardWidget:
        """创建连接配置卡片"""
        card = CardWidget(self)
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        ip_label = BodyLabel("IP 地址:", card)
        self.ip_edit = LineEdit(card)
        self.ip_edit.setText("192.168.99.209")
        card_layout.addWidget(ip_label, 0, 0)
        card_layout.addWidget(self.ip_edit, 0, 1)

        self.connect_btn = PrimaryPushButton("连接", card)
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        self.disconnect_btn = PushButton("断开", card)
        self.disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        self.disconnect_btn.setEnabled(False)
        
        card_layout.addWidget(self.connect_btn, 0, 2)
        card_layout.addWidget(self.disconnect_btn, 0, 3)

        return card

    def _create_config_card(self) -> CardWidget:
        """创建测量配置卡片"""
        card = CardWidget(self)
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        center_label = BodyLabel("中心频率 (MHz):", card)
        self.center_spin = DoubleSpinBox(card)
        self.center_spin.setRange(0.01, 30000)
        self.center_spin.setValue(10.5)
        self.center_spin.setDecimals(3)
        card_layout.addWidget(center_label, 0, 0)
        card_layout.addWidget(self.center_spin, 0, 1)

        span_label = BodyLabel("跨度 (MHz):", card)
        self.span_spin = DoubleSpinBox(card)
        self.span_spin.setRange(0.01, 30000)
        self.span_spin.setValue(8.0)
        self.span_spin.setDecimals(3)
        card_layout.addWidget(span_label, 0, 2)
        card_layout.addWidget(self.span_spin, 0, 3)

        rbw_label = BodyLabel("RBW (Hz):", card)
        self.rbw_spin = SpinBox(card)
        self.rbw_spin.setRange(1, 1000000)
        self.rbw_spin.setValue(1000)
        card_layout.addWidget(rbw_label, 1, 0)
        card_layout.addWidget(self.rbw_spin, 1, 1)

        vbw_label = BodyLabel("VBW (Hz):", card)
        self.vbw_spin = SpinBox(card)
        self.vbw_spin.setRange(1, 1000000)
        self.vbw_spin.setValue(10)
        card_layout.addWidget(vbw_label, 1, 2)
        card_layout.addWidget(self.vbw_spin, 1, 3)

        self.start_btn = PrimaryPushButton("开始测量", card)
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.start_btn.setEnabled(False)
        self.stop_btn = PushButton("停止测量", card)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.setEnabled(False)
        
        card_layout.addWidget(self.start_btn, 1, 4)
        card_layout.addWidget(self.stop_btn, 1, 5)

        return card

    def _on_connect_clicked(self):
        """连接按钮点击事件"""
        try:
            ip = self.ip_edit.text()
            self.sa = SA_FSV30(ip=ip)
            self.sa.connect()
            
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            
            self.status_label.setText(f"已连接: {self.sa.identity}")
            InfoBar.success(
                title="连接成功",
                content=f"已连接到 {ip}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            self.status_label.setText(f"连接失败: {str(e)}")
            InfoBar.error(
                title="连接失败",
                content=str(e),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def _on_disconnect_clicked(self):
        """断开按钮点击事件"""
        if self.sa:
            self.sa.disconnect()
            self.sa = None
            
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        self.status_label.setText("未连接")

    def _on_start_clicked(self):
        """开始测量按钮点击事件"""
        if not self.sa:
            return
            
        try:
            center_freq = self.center_spin.value() * 1e6  # MHz to Hz
            span = self.span_spin.value() * 1e6
            rbw = self.rbw_spin.value()
            vbw = self.vbw_spin.value()
            
            self.sa.configure(
                center_freq_hz=center_freq,
                span_hz=span,
                rbw_hz=rbw,
                vbw_hz=vbw
            )
            
            # 设置标记
            self.sa.set_marker(1, (center_freq - span/4))
            self.sa.set_marker(2, (center_freq + span/4))
            
            self.is_acquiring = True
            self.update_timer.start(2000)  # 每 2 秒更新一次
            
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("正在测量...")
            
        except Exception as e:
            InfoBar.error(
                title="启动失败",
                content=str(e),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def _on_stop_clicked(self):
        """停止测量按钮点击事件"""
        self.is_acquiring = False
        self.update_timer.stop()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("已停止")

    def _on_acquire(self):
        """执行测量并更新显示"""
        if not self.sa or not self.is_acquiring:
            return
            
        try:
            # 获取轨迹数据
            freq_list, power_list = self.sa.get_trace_data()
            
            # 转换为 MHz
            freq_mhz = [f / 1e6 for f in freq_list]
            
            # 更新绘图
            self.plot_widget.clear_plot()
            self.plot_widget.plot_data(freq_mhz, power_list, pen='b')
            
            # 获取标记值
            readings = self.sa.acquire_once()
            marker_info = " | ".join(
                f"M{num}: {freq/1e6:.3f}MHz, {level:.2f}dBm"
                for num, freq, level in readings
            )
            self.status_label.setText(marker_info)
            
        except Exception as e:
            print(f"测量错误: {e}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        self._on_stop_clicked()
        self._on_disconnect_clicked()
        super().closeEvent(event)
