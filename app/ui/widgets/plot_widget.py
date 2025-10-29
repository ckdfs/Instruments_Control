# coding:utf-8
"""实时数据绘图组件"""
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from qfluentwidgets import CardWidget


class PlotWidget(CardWidget):
    """基于 pyqtgraph 的实时绘图组件"""

    def __init__(self, title: str = "数据图表", parent=None):
        super().__init__(parent)
        self.title = title
        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        self.vBoxLayout = QVBoxLayout(self)
        
        # 创建 pyqtgraph 绘图控件
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', self.title)
        
        # 启用抗锯齿
        self.plot_widget.setAntialiasing(True)
        
        self.vBoxLayout.addWidget(self.plot_widget)
        self.vBoxLayout.setContentsMargins(10, 10, 10, 10)

    def plot_data(self, x_data, y_data, pen='b', name=None):
        """
        绘制数据
        
        Args:
            x_data: X 轴数据
            y_data: Y 轴数据
            pen: 线条颜色/样式
            name: 曲线名称
        """
        self.plot_widget.plot(x_data, y_data, pen=pen, name=name)

    def clear_plot(self):
        """清除图表"""
        self.plot_widget.clear()

    def set_labels(self, xlabel: str = None, ylabel: str = None):
        """
        设置坐标轴标签
        
        Args:
            xlabel: X 轴标签
            ylabel: Y 轴标签
        """
        if xlabel:
            self.plot_widget.setLabel('bottom', xlabel)
        if ylabel:
            self.plot_widget.setLabel('left', ylabel)
