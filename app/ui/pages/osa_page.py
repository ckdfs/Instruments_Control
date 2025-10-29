# coding:utf-8
"""光谱分析仪控制页面"""
import threading
import queue
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from qfluentwidgets import (
    CardWidget, SubtitleLabel, BodyLabel, LineEdit,
    PrimaryPushButton, PushButton, ComboBox, SpinBox,
    DoubleSpinBox, ProgressRing, InfoBar, InfoBarPosition
)

from app.instruments.osa_ap2061a import OSA_AP2061A
from app.ui.widgets.plot_widget import PlotWidget


class OSAPage(QWidget):
    """光谱分析仪控制页面"""
    
    # 自定义信号
    data_received = pyqtSignal(list, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("osa-page")
        
        # 仪器对象
        self.osa: OSA_AP2061A = None
        self.acquisition_thread = None
        self.stop_event = threading.Event()
        self.data_queue = queue.Queue()
        
        # 定时器
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_plot)
        
        self._init_ui()
        
        # 连接信号
        self.data_received.connect(self._on_data_received)

    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 标题
        title = SubtitleLabel("光谱分析仪 (OSA AP2061A)", self)
        layout.addWidget(title)

        # 连接配置卡片
        connection_card = self._create_connection_card()
        layout.addWidget(connection_card)

        # 测量配置卡片
        config_card = self._create_config_card()
        layout.addWidget(config_card)

        # 绘图区域
        self.plot_widget = PlotWidget("光谱", self)
        self.plot_widget.set_labels("波长 (nm)", "功率 (dBm)")
        layout.addWidget(self.plot_widget, 1)

        # 状态信息
        self.status_label = BodyLabel("未连接", self)
        layout.addWidget(self.status_label)

    def _create_connection_card(self) -> CardWidget:
        """创建连接配置卡片"""
        card = CardWidget(self)
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # IP 地址
        ip_label = BodyLabel("IP 地址:", card)
        self.ip_edit = LineEdit(card)
        self.ip_edit.setText("192.168.99.198")
        self.ip_edit.setPlaceholderText("请输入仪器 IP 地址")
        card_layout.addWidget(ip_label, 0, 0)
        card_layout.addWidget(self.ip_edit, 0, 1)

        # 端口
        port_label = BodyLabel("端口:", card)
        self.port_spin = SpinBox(card)
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(5900)
        card_layout.addWidget(port_label, 0, 2)
        card_layout.addWidget(self.port_spin, 0, 3)

        # 连接按钮
        self.connect_btn = PrimaryPushButton("连接", card)
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        self.disconnect_btn = PushButton("断开", card)
        self.disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        self.disconnect_btn.setEnabled(False)
        
        card_layout.addWidget(self.connect_btn, 0, 4)
        card_layout.addWidget(self.disconnect_btn, 0, 5)

        return card

    def _create_config_card(self) -> CardWidget:
        """创建测量配置卡片"""
        card = CardWidget(self)
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # 中心波长
        center_label = BodyLabel("中心波长 (nm):", card)
        self.center_spin = DoubleSpinBox(card)
        self.center_spin.setRange(1000, 2000)
        self.center_spin.setValue(1550.0)
        self.center_spin.setDecimals(3)
        card_layout.addWidget(center_label, 0, 0)
        card_layout.addWidget(self.center_spin, 0, 1)

        # 扫描跨度
        span_label = BodyLabel("扫描跨度 (nm):", card)
        self.span_spin = DoubleSpinBox(card)
        self.span_spin.setRange(0.01, 100)
        self.span_spin.setValue(0.25)
        self.span_spin.setDecimals(3)
        card_layout.addWidget(span_label, 0, 2)
        card_layout.addWidget(self.span_spin, 0, 3)

        # 通道选择
        channel_label = BodyLabel("通道:", card)
        self.channel_combo = ComboBox(card)
        self.channel_combo.addItems(["1", "2", "1&2", "1+2"])
        card_layout.addWidget(channel_label, 1, 0)
        card_layout.addWidget(self.channel_combo, 1, 1)

        # 扫描模式
        mode_label = BodyLabel("扫描模式:", card)
        self.mode_combo = ComboBox(card)
        self.mode_combo.addItems(["single", "repeat", "auto"])
        card_layout.addWidget(mode_label, 1, 2)
        card_layout.addWidget(self.mode_combo, 1, 3)

        # 采集按钮
        self.start_btn = PrimaryPushButton("开始采集", card)
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.start_btn.setEnabled(False)
        self.stop_btn = PushButton("停止采集", card)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.setEnabled(False)
        
        card_layout.addWidget(self.start_btn, 1, 4)
        card_layout.addWidget(self.stop_btn, 1, 5)

        return card

    def _on_connect_clicked(self):
        """连接按钮点击事件"""
        try:
            ip = self.ip_edit.text()
            port = self.port_spin.value()
            
            self.osa = OSA_AP2061A(ip=ip, port=port, simulation=False)
            
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            
            self.status_label.setText(f"已连接: {self.osa.identity}")
            InfoBar.success(
                title="连接成功",
                content=f"已连接到 {ip}:{port}",
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
        if self.osa:
            self.osa.close()
            self.osa = None
            
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        self.status_label.setText("未连接")

    def _on_start_clicked(self):
        """开始采集按钮点击事件"""
        if not self.osa:
            return
            
        try:
            # 配置仪器
            center = self.center_spin.value()
            span = self.span_spin.value()
            channel = self.channel_combo.currentText()
            
            self.osa.configure(center_nm=center, span_nm=span, channel=channel)
            
            # 启动采集线程
            self.stop_event.clear()
            self.acquisition_thread = threading.Thread(
                target=self._acquisition_worker,
                daemon=True
            )
            self.acquisition_thread.start()
            
            # 启动更新定时器
            self.update_timer.start(100)
            
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("正在采集...")
            
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
        """停止采集按钮点击事件"""
        self.stop_event.set()
        self.update_timer.stop()
        
        if self.acquisition_thread:
            self.acquisition_thread.join(timeout=2.0)
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("已停止")

    def _acquisition_worker(self):
        """采集工作线程"""
        mode = self.mode_combo.currentText()
        
        try:
            while not self.stop_event.is_set():
                trace_num, y_data, x_data = self.osa.acquire_once(
                    scale_x="nm",
                    scale_y="log",
                    trace=1,
                    sweep_mode=mode
                )
                
                self.data_queue.put((x_data, y_data))
                
                if self.stop_event.wait(0.5):
                    break
                    
        except Exception as e:
            print(f"采集错误: {e}")

    def _update_plot(self):
        """更新绘图"""
        try:
            while not self.data_queue.empty():
                x_data, y_data = self.data_queue.get_nowait()
                self.data_received.emit(x_data, y_data)
        except queue.Empty:
            pass

    def _on_data_received(self, x_data, y_data):
        """数据接收处理"""
        self.plot_widget.clear_plot()
        self.plot_widget.plot_data(x_data, y_data, pen='b')
        
        # 更新峰值信息
        if self.osa and y_data:
            peak_power, peak_wavelength = self.osa.get_peak_info(y_data, x_data)
            self.status_label.setText(
                f"峰值: {peak_power:.2f} dBm @ {peak_wavelength:.3f} nm"
            )

    def closeEvent(self, event):
        """窗口关闭事件"""
        self._on_stop_clicked()
        self._on_disconnect_clicked()
        super().closeEvent(event)
