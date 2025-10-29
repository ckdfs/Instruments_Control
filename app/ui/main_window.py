# coding:utf-8
"""主窗口"""
import sys
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import (
    NavigationItemPosition, setTheme, Theme, MSFluentWindow,
    FluentIcon as FIF
)

from app.ui.pages.home import HomePage
from app.ui.pages.osa_page import OSAPage
from app.ui.pages.sa_page import SAPage
from app.ui.pages.afg_page import AFGPage
from app.ui.pages.power_page import PowerPage


class MainWindow(MSFluentWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        
        # 创建子界面
        self.home_page = HomePage(self)
        self.osa_page = OSAPage(self)
        self.sa_page = SAPage(self)
        self.afg_page = AFGPage(self)
        self.power_page = PowerPage(self)
        
        self._init_navigation()
        self._init_window()

    def _init_navigation(self):
        """初始化导航栏"""
        # 添加主页
        self.addSubInterface(
            self.home_page,
            FIF.HOME,
            '主页',
            FIF.HOME_FILL
        )
        
        # 添加仪器控制页面
        self.addSubInterface(
            self.osa_page,
            FIF.SEARCH,
            '光谱分析仪'
        )
        
        self.addSubInterface(
            self.sa_page,
            FIF.IOT,
            '频谱分析仪'
        )
        
        self.addSubInterface(
            self.afg_page,
            FIF.DEVELOPER_TOOLS,
            '函数发生器'
        )
        
        self.addSubInterface(
            self.power_page,
            FIF.POWER_BUTTON,
            '可编程电源'
        )
        
        # 添加底部导航项
        self.navigationInterface.addItem(
            routeKey='Settings',
            icon=FIF.SETTING,
            text='设置',
            onClick=self._show_settings,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )
        
        # 设置默认页面
        self.navigationInterface.setCurrentItem(self.home_page.objectName())

    def _init_window(self):
        """初始化窗口"""
        self.resize(1200, 800)
        self.setWindowTitle('仪器控制系统')
        
        # 居中显示
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def _show_settings(self):
        """显示设置"""
        # TODO: 实现设置页面
        pass
