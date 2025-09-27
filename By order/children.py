import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem,
    QSpinBox, QHBoxLayout
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ChildrenStatsTab(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()

        self.label = QLabel("Нажмите 'Собрать статистику', чтобы отобразить данные")
        self.layout.addWidget(self.label)

        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        self.plot_widget = FigureCanvas(Figure(figsize=(5, 3)))
        self.ax = self.plot_widget.figure.add_subplot(111)
        self.layout.addWidget(self.plot_widget)

        control_layout = QHBoxLayout()
        self.n_label = QLabel("Прогноз на N лет:")
        control_layout.addWidget(self.n_label)
        self.n_spinbox = QSpinBox()
        self.n_spinbox.setRange(1, 20)
        self.n_spinbox.setValue(5)
        control_layout.addWidget(self.n_spinbox)
        self.layout.addLayout(control_layout)

        self.button = QPushButton("Собрать статистику")
        self.button.clicked.connect(self.load_and_display_data)
        self.layout.addWidget(self.button)

        self.setLayout(self.layout)

    def load_and_display_data(self):
        # Чтение файла
        df = pd.read_excel("tables/children.xlsx")
        df = df.sort_values("Год")
        df.reset_index(drop=True, inplace=True)

        # Отображение таблицы
        self.table.setRowCount(len(df))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Год", "Процент"])
        for i, row in df.iterrows():
            self.table.setItem(i, 0, QTableWidgetItem(str(row["Год"])))
            self.table.setItem(i, 1, QTableWidgetItem(f"{row["Процент"]:.2f}"))

        # Построение графика
        self.ax.clear()
        self.ax.plot(df["Год"], df["Процент"], marker='o', label="Факт")

        # Расчёт изменений
        df['Δ%'] = df['Процент'].pct_change() * 100
        max_growth = df['Δ%'].max()
        min_growth = df['Δ%'].min()

        self.label.setText(
            f"Макс. рост: {max_growth:.2f}%, Мин. рост: {min_growth:.2f}%"
        )

        # Прогнозирование (скользящая средняя)
        N = self.n_spinbox.value()
        k = 15  # длина окна скользящего среднего

        # Начальные значения — последние k точек
        values = df['Процент'].tolist()[-k:]

        forecast = []
        for _ in range(N):
            # print(len(values))
            # print(values)
            next_value = sum(values[-k:]) / k
            forecast.append(next_value)
            values = values[1:] + [next_value]  # удаляем старое, добавляем новое

        last_year = df['Год'].iloc[-1]
        forecast_years = [last_year + i for i in range(1, N + 1)]
        self.ax.plot(forecast_years, forecast, linestyle='--', color='red', marker='x', label='Прогноз')

        self.ax.set_title("Процент детей, рождённых вне брака")
        self.ax.set_xlabel("Год")
        self.ax.set_ylabel("Процент")
        self.ax.legend()
        self.ax.grid(True)

        self.plot_widget.draw()
