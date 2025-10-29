# coding:utf-8
"""主页面"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, BodyLabel, CardWidget,
    PrimaryPushButton, setFont
)


class HomePage(QWidget):
    """主页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("home-page")
        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 标题
        title = TitleLabel("仪器控制系统", self)
        setFont(title, 32)
        layout.addWidget(title, 0, Qt.AlignTop)

        # 欢迎卡片
        welcome_card = self._create_welcome_card()
        layout.addWidget(welcome_card)

        # 仪器状态卡片
        status_card = self._create_status_card()
        layout.addWidget(status_card)

        layout.addStretch(1)

    def _create_welcome_card(self) -> CardWidget:
        """创建欢迎卡片"""
        card = CardWidget(self)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)

        subtitle = SubtitleLabel("欢迎使用仪器控制系统", card)
        description = BodyLabel(
            "本系统支持以下仪器的控制与数据采集：\n"
            "• 光谱分析仪 (OSA AP2061A)\n"
            "• 频谱分析仪 (SA FSV30)\n"
            "• 任意函数发生器 (AFG1062)\n"
            "• 可编程电源 (E3631A)",
            card
        )
        description.setWordWrap(True)

        card_layout.addWidget(subtitle)
        card_layout.addWidget(description)

        return card

    def _create_status_card(self) -> CardWidget:
        """创建状态卡片"""
        card = CardWidget(self)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)

        subtitle = SubtitleLabel("快速开始", card)
        instruction = BodyLabel(
            "1. 点击左侧导航栏选择要控制的仪器\n"
            "2. 配置仪器连接参数（IP 地址等）\n"
            "3. 点击「连接」按钮建立通信\n"
            "4. 配置测量参数并开始数据采集",
            card
        )
        instruction.setWordWrap(True)

        card_layout.addWidget(subtitle)
        card_layout.addWidget(instruction)

        return card
