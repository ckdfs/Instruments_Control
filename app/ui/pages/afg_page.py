# coding:utf-8
"""任意函数发生器控制页面"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout
from qfluentwidgets import (
    CardWidget, SubtitleLabel, BodyLabel, LineEdit,
    PrimaryPushButton, PushButton, ComboBox,
    DoubleSpinBox, SwitchButton, InfoBar, InfoBarPosition
)

from app.instruments.afg_afg1062 import AFG_AFG1062


class AFGPage(QWidget):
    """任意函数发生器控制页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("afg-page")
        
        self.afg: AFG_AFG1062 = None
        
        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = SubtitleLabel("任意函数发生器 (AFG1062)", self)
        layout.addWidget(title)

        connection_card = self._create_connection_card()
        layout.addWidget(connection_card)

        ch1_card = self._create_channel_card("通道 1", 1)
        layout.addWidget(ch1_card)

        ch2_card = self._create_channel_card("通道 2", 2)
        layout.addWidget(ch2_card)

        layout.addStretch(1)

        self.status_label = BodyLabel("未连接 (功能待实现)", self)
        layout.addWidget(self.status_label)

    def _create_connection_card(self) -> CardWidget:
        """创建连接配置卡片"""
        card = CardWidget(self)
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        ip_label = BodyLabel("IP 地址:", card)
        self.ip_edit = LineEdit(card)
        self.ip_edit.setText("192.168.1.100")
        card_layout.addWidget(ip_label, 0, 0)
        card_layout.addWidget(self.ip_edit, 0, 1)

        self.connect_btn = PrimaryPushButton("连接", card)
        self.connect_btn.setEnabled(False)  # 待实现
        self.disconnect_btn = PushButton("断开", card)
        self.disconnect_btn.setEnabled(False)
        
        card_layout.addWidget(self.connect_btn, 0, 2)
        card_layout.addWidget(self.disconnect_btn, 0, 3)

        return card

    def _create_channel_card(self, title: str, channel: int) -> CardWidget:
        """创建通道配置卡片"""
        card = CardWidget(self)
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # 标题
        ch_title = SubtitleLabel(title, card)
        card_layout.addWidget(ch_title, 0, 0, 1, 4)

        # 波形类型
        wave_label = BodyLabel("波形:", card)
        wave_combo = ComboBox(card)
        wave_combo.addItems(["正弦波", "方波", "三角波", "锯齿波", "脉冲"])
        card_layout.addWidget(wave_label, 1, 0)
        card_layout.addWidget(wave_combo, 1, 1)

        # 频率
        freq_label = BodyLabel("频率 (Hz):", card)
        freq_spin = DoubleSpinBox(card)
        freq_spin.setRange(0.001, 60e6)
        freq_spin.setValue(1000)
        freq_spin.setDecimals(3)
        card_layout.addWidget(freq_label, 1, 2)
        card_layout.addWidget(freq_spin, 1, 3)

        # 幅度
        amp_label = BodyLabel("幅度 (V):", card)
        amp_spin = DoubleSpinBox(card)
        amp_spin.setRange(0.001, 10)
        amp_spin.setValue(1.0)
        amp_spin.setDecimals(3)
        card_layout.addWidget(amp_label, 2, 0)
        card_layout.addWidget(amp_spin, 2, 1)

        # 偏移
        offset_label = BodyLabel("偏移 (V):", card)
        offset_spin = DoubleSpinBox(card)
        offset_spin.setRange(-5, 5)
        offset_spin.setValue(0.0)
        offset_spin.setDecimals(3)
        card_layout.addWidget(offset_label, 2, 2)
        card_layout.addWidget(offset_spin, 2, 3)

        # 输出开关
        output_label = BodyLabel("输出:", card)
        output_switch = SwitchButton(card)
        output_switch.setEnabled(False)  # 待实现
        card_layout.addWidget(output_label, 3, 0)
        card_layout.addWidget(output_switch, 3, 1)

        return card
