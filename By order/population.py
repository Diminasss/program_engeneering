import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHBoxLayout, QSpinBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PopulationStatsTab(QWidget):
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
        df = pd.read_excel("tables/population.xlsx")
        df = df.sort_values("Год")
        df.reset_index(drop=True, inplace=True)

        # Таблица
        self.table.setRowCount(len(df))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Год", "Население (млн)"])
        for i, row in df.iterrows():
            self.table.setItem(i, 0, QTableWidgetItem(str(row["Год"])))
            self.table.setItem(i, 1, QTableWidgetItem(f"{row['Население']:.2f}"))

        # График
        self.ax.clear()
        self.ax.plot(df["Год"], df["Население"], marker='o', label="Факт")

        # Процентные изменения
        df["Δ%"] = df["Население"].pct_change() * 100
        max_growth = df["Δ%"].max()
        min_growth = df["Δ%"].min()

        self.label.setText(
            f"Макс. прирост: {max_growth:.2f}%, Мин. убыль: {min_growth:.2f}%"
        )

        # Прогнозирование (скользящее среднее с движущимся окном)
        N = self.n_spinbox.value()
        k = 15  # длина окна, можно заменить на переменную

        # Убедимся, что данных минимум k
        if len(df) < k:
            self.label.setText("Недостаточно данных для расчёта скользящей средней.")
            return

        # последние k значений
        values = df['Население'].tolist()[-k:]
        forecast = []

        for _ in range(N):
            next_value = sum(values) / k
            forecast.append(next_value)
            print(values)
            values = values[1:] + [next_value]

        last_year = df['Год'].iloc[-1]
        forecast_years = [last_year + i for i in range(1, N + 1)]

        # Рисуем прогноз
        self.ax.plot(forecast_years, forecast, linestyle='--', color='red', marker='x', label='Прогноз')

        self.ax.set_title("Численность населения России")
        self.ax.set_xlabel("Год")
        self.ax.set_ylabel("Млн человек")
        self.ax.grid(True)
        self.ax.legend()
        self.plot_widget.draw()
