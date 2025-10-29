# coding:utf-8
"""可编程电源控制页面"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout
from qfluentwidgets import (
    CardWidget, SubtitleLabel, BodyLabel, LineEdit,
    PrimaryPushButton, PushButton, DoubleSpinBox,
    SwitchButton, InfoBar, InfoBarPosition
)

from app.instruments.power_e3631a import PowerSupply_E3631A


class PowerPage(QWidget):
    """可编程电源控制页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("power-page")
        
        self.power_supply: PowerSupply_E3631A = None
        
        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = SubtitleLabel("可编程电源 (E3631A)", self)
        layout.addWidget(title)

        connection_card = self._create_connection_card()
        layout.addWidget(connection_card)

        p6v_card = self._create_channel_card("P6V 通道", "P6V", 0, 6, 0, 5)
        layout.addWidget(p6v_card)

        p25v_card = self._create_channel_card("P25V 通道", "P25V", 0, 25, 0, 1)
        layout.addWidget(p25v_card)

        n25v_card = self._create_channel_card("N25V 通道", "N25V", -25, 0, 0, 1)
        layout.addWidget(n25v_card)

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
        self.ip_edit.setText("192.168.1.101")
        card_layout.addWidget(ip_label, 0, 0)
        card_layout.addWidget(self.ip_edit, 0, 1)

        self.connect_btn = PrimaryPushButton("连接", card)
        self.connect_btn.setEnabled(False)  # 待实现
        self.disconnect_btn = PushButton("断开", card)
        self.disconnect_btn.setEnabled(False)
        
        card_layout.addWidget(self.connect_btn, 0, 2)
        card_layout.addWidget(self.disconnect_btn, 0, 3)

        # 主输出开关
        output_label = BodyLabel("主输出:", card)
        self.main_output_switch = SwitchButton(card)
        self.main_output_switch.setEnabled(False)
        card_layout.addWidget(output_label, 0, 4)
        card_layout.addWidget(self.main_output_switch, 0, 5)

        return card

    def _create_channel_card(
        self,
        title: str,
        channel: str,
        v_min: float,
        v_max: float,
        i_min: float,
        i_max: float
    ) -> CardWidget:
        """创建通道配置卡片"""
        card = CardWidget(self)
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # 标题
        ch_title = SubtitleLabel(title, card)
        card_layout.addWidget(ch_title, 0, 0, 1, 4)

        # 电压设置
        voltage_label = BodyLabel("电压 (V):", card)
        voltage_spin = DoubleSpinBox(card)
        voltage_spin.setRange(v_min, v_max)
        voltage_spin.setValue(0.0)
        voltage_spin.setDecimals(3)
        card_layout.addWidget(voltage_label, 1, 0)
        card_layout.addWidget(voltage_spin, 1, 1)

        # 电流限制
        current_label = BodyLabel("电流限制 (A):", card)
        current_spin = DoubleSpinBox(card)
        current_spin.setRange(i_min, i_max)
        current_spin.setValue(0.1)
        current_spin.setDecimals(3)
        card_layout.addWidget(current_label, 1, 2)
        card_layout.addWidget(current_spin, 1, 3)

        # 应用按钮
        apply_btn = PrimaryPushButton("应用", card)
        apply_btn.setEnabled(False)
        card_layout.addWidget(apply_btn, 1, 4)

        # 测量显示
        measured_label = BodyLabel("测量值:", card)
        measured_value = BodyLabel("-- V, -- A", card)
        card_layout.addWidget(measured_label, 2, 0)
        card_layout.addWidget(measured_value, 2, 1, 1, 3)

        return card
