import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget,
)
from children import ChildrenStatsTab
from population import PopulationStatsTab


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Статистика по заданию")
        self.resize(900, 600)

        layout = QVBoxLayout()

        self.tabs = QTabWidget()

        self.tabs.addTab(ChildrenStatsTab(), "Дети вне брака")
        self.tabs.addTab(PopulationStatsTab(), "Популяция")
        # Сюда можно добавлять другие вкладки

        layout.addWidget(self.tabs)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
