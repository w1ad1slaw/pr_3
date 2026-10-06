import sys
import random
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QProgressBar, QListWidget,
    QListWidgetItem, QDialog, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QFont, QColor, QShortcut, QKeySequence, QPainter, QPen, QBrush,
    QPainterPath
)


# ─────────────────────────────────────────────────────────────
# Дизайн-система
# ─────────────────────────────────────────────────────────────
class Theme:
    BG          = "#F6F8FB"
    PANEL       = "#FFFFFF"
    PANEL_ALT   = "#F0F3F8"
    PANEL_SOFT  = "#F8FAFC"
    BORDER      = "#E2E6EC"
    BORDER_HARD = "#C9D0D9"

    TEXT        = "#0F172A"
    TEXT_DIM    = "#4B5563"
    TEXT_MUTED  = "#94A3B8"

    ACCENT      = "#2563EB"
    ACCENT_DARK = "#1D4ED8"

    OK      = "#16A34A"
    WARN    = "#EA580C"
    ERR     = "#DC2626"
    IDLE    = "#64748B"

    FONT_FAMILY = "Segoe UI"
    FONT_SIZE   = 15


def apply_shadow(widget, blur=10, offset_y=1, alpha=14):
    sh = QGraphicsDropShadowEffect()
    sh.setBlurRadius(blur)
    sh.setOffset(0, offset_y)
    sh.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(sh)


def darken(hex_color, factor=118):
    return QColor(hex_color).darker(factor).name()


def plural_form(n, form1, form2, form5):
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return form1
    if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return form2
    return form5


def status_color(status: str):
    return {"ok": Theme.OK, "warn": Theme.WARN,
            "err": Theme.ERR, "idle": Theme.IDLE}.get(status, Theme.IDLE)


def status_icon(status: str):
    return {"ok": "✓", "warn": "⚠", "err": "✕", "idle": "·"}.get(status, "·")


def status_label(status: str):
    return {"ok": "Норма", "warn": "Внимание",
            "err": "Критично", "idle": "Ожидание"}.get(status, "—")


def compute_status(value, normal, span_tolerance=0.2):
    lo, hi = normal
    span = max(hi - lo, 1)
    if lo <= value <= hi:
        return "ok"
    if value < lo:
        deviation = lo - value
    else:
        deviation = value - hi
    if deviation < span * span_tolerance:
        return "warn"
    return "err"


# ─────────────────────────────────────────────────────────────
# Sparkline
# ─────────────────────────────────────────────────────────────
class Sparkline(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self._values = []
        self._color = QColor(Theme.ACCENT)

    def set_values(self, values, color=None):
        self._values = list(values)
        if color:
            self._color = QColor(color)
        self.update()

    def paintEvent(self, event):
        if len(self._values) < 2:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        pad = 6
        vmin = min(self._values)
        vmax = max(self._values)
        span = vmax - vmin if vmax != vmin else 1

        points = []
        n = len(self._values)
        for i, v in enumerate(self._values):
            x = pad + (w - 2 * pad) * i / (n - 1)
            y = h - pad - (h - 2 * pad) * (v - vmin) / span
            points.append((x, y))

        path = QPainterPath()
        path.moveTo(points[0][0], h - pad)
        for x, y in points:
            path.lineTo(x, y)
        path.lineTo(points[-1][0], h - pad)
        path.closeSubpath()

        fill = QColor(self._color)
        fill.setAlpha(40)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(fill))
        p.drawPath(path)

        pen = QPen(self._color, 2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        for i in range(len(points) - 1):
            p.drawLine(
                int(points[i][0]), int(points[i][1]),
                int(points[i + 1][0]), int(points[i + 1][1])
            )

        p.setBrush(QBrush(self._color))
        p.setPen(Qt.NoPen)
        for pt in (points[0], points[-1]):
            p.drawEllipse(int(pt[0]) - 3, int(pt[1]) - 3, 6, 6)


class SparklineBlock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.spark = Sparkline()
        self.spark.setFixedHeight(70)
        layout.addWidget(self.spark)

        axis_row = QHBoxLayout()
        axis_row.setContentsMargins(4, 0, 4, 0)

        self.min_lbl = QLabel("")
        self.min_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px; "
            f"background: transparent; border: none;"
        )
        self.period_lbl = QLabel("Последние 60 секунд")
        self.period_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px; "
            f"font-style: italic; background: transparent; border: none;"
        )
        self.period_lbl.setAlignment(Qt.AlignCenter)

        self.max_lbl = QLabel("")
        self.max_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px; "
            f"background: transparent; border: none;"
        )

        axis_row.addWidget(self.min_lbl)
        axis_row.addStretch()
        axis_row.addWidget(self.period_lbl)
        axis_row.addStretch()
        axis_row.addWidget(self.max_lbl)
        layout.addLayout(axis_row)

    def set_values(self, values, color):
        self.spark.set_values(values, color=color)
        if values:
            self.min_lbl.setText(f"min: {min(values)}")
            self.max_lbl.setText(f"max: {max(values)}")


# ─────────────────────────────────────────────────────────────
# ModalDialog
# ─────────────────────────────────────────────────────────────
class ModalDialog(QDialog):
    def __init__(self, parent, title, message, kind="info",
                 yes_text="OK", no_text=None, width=560):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedWidth(width)
        self.setStyleSheet(f"QDialog {{ background: {Theme.PANEL}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 22)
        layout.setSpacing(18)

        color = {"info": Theme.ACCENT, "warn": Theme.WARN,
                 "err": Theme.ERR}.get(kind, Theme.ACCENT)

        t = QLabel(title)
        t.setFont(QFont(Theme.FONT_FAMILY, 17, QFont.Bold))
        t.setStyleSheet(f"color: {Theme.TEXT};")

        bar = QFrame()
        bar.setFixedHeight(3)
        bar.setStyleSheet(f"background: {color}; border-radius: 2px;")

        m = QLabel(message)
        m.setWordWrap(True)
        m.setTextFormat(Qt.RichText)
        m.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 15px; line-height: 22px;"
        )

        btns = QHBoxLayout()
        btns.addStretch()

        if no_text:
            nb = self._btn(no_text, secondary=True)
            nb.clicked.connect(self.reject)
            btns.addWidget(nb)

        yb = self._btn(yes_text, color=color)
        yb.clicked.connect(self.accept)
        btns.addWidget(yb)

        layout.addWidget(t)
        layout.addWidget(bar)
        layout.addWidget(m)
        layout.addLayout(btns)

    def _btn(self, text, color=None, secondary=False):
        b = QPushButton(text)
        b.setFixedHeight(44)
        b.setMinimumWidth(120)
        b.setCursor(Qt.PointingHandCursor)
        b.setFont(QFont(Theme.FONT_FAMILY, 12, QFont.DemiBold))
        if secondary:
            b.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.PANEL};
                    color: {Theme.TEXT_DIM};
                    border: 1px solid {Theme.BORDER_HARD};
                    border-radius: 8px;
                    padding: 0 18px;
                }}
                QPushButton:hover {{
                    background: {Theme.PANEL_ALT};
                    color: {Theme.TEXT};
                }}
            """)
        else:
            c = color or Theme.ACCENT
            b.setStyleSheet(f"""
                QPushButton {{
                    background: {c};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 0 22px;
                    font-weight: 600;
                }}
                QPushButton:hover {{ background: {darken(c)}; }}
            """)
        return b


# ─────────────────────────────────────────────────────────────
# Список проблемных процессов
# ─────────────────────────────────────────────────────────────
class ProblemsDialog(QDialog):
    def __init__(self, parent, problems):
        super().__init__(parent)
        self.setWindowTitle("Проблемные процессы")
        self.setModal(True)
        self.setFixedSize(580, 440)
        self.setStyleSheet(f"QDialog {{ background: {Theme.PANEL}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 22)
        layout.setSpacing(14)

        t = QLabel("Требуют внимания")
        t.setFont(QFont(Theme.FONT_FAMILY, 17, QFont.Bold))
        t.setStyleSheet(f"color: {Theme.TEXT};")

        sub = QLabel(
            f"Найдено проблемных процессов: {len(problems)}. "
            "Кликните на строку, чтобы перейти к процессу."
        )
        sub.setWordWrap(True)
        sub.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 13px;"
        )

        self.selected_id = None

        for p in problems:
            row = QFrame()
            row.setCursor(Qt.PointingHandCursor)
            row.setStyleSheet(f"""
                QFrame {{
                    background: {Theme.PANEL_ALT};
                    border: 1px solid {Theme.BORDER};
                    border-radius: 8px;
                }}
                QFrame:hover {{
                    border-color: {Theme.BORDER_HARD};
                }}
            """)
            rh = QHBoxLayout(row)
            rh.setContentsMargins(16, 12, 16, 12)
            rh.setSpacing(12)

            color = status_color(p["status"])
            led = QLabel()
            led.setFixedSize(12, 12)
            led.setStyleSheet(f"background: {color}; border-radius: 6px;")

            icon = QLabel(status_icon(p["status"]))
            icon.setStyleSheet(
                f"color: {color}; font-size: 14px; font-weight: bold;"
            )

            text_box = QVBoxLayout()
            text_box.setSpacing(2)
            name = QLabel(p["title"])
            name.setStyleSheet(
                f"color: {Theme.TEXT}; font-size: 14px; font-weight: 600;"
            )
            desc = QLabel(f"{status_label(p['status'])} · {p['details']}")
            desc.setStyleSheet(
                f"color: {Theme.TEXT_MUTED}; font-size: 12px;"
            )
            desc.setWordWrap(True)
            text_box.addWidget(name)
            text_box.addWidget(desc)

            rh.addWidget(led)
            rh.addWidget(icon)
            rh.addLayout(text_box, 1)

            row.mousePressEvent = (
                lambda ev, pid=p["id"]: self._select(pid)
            )
            layout.addWidget(row)

        layout.addStretch()

        close_btn = QPushButton("Закрыть")
        close_btn.setFixedHeight(44)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT}; color: white;
                border: none; border-radius: 8px;
                font-weight: 600; padding: 0 22px;
            }}
            QPushButton:hover {{ background: {Theme.ACCENT_DARK}; }}
        """)
        close_btn.clicked.connect(self.reject)

        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)

    def _select(self, process_id):
        self.selected_id = process_id
        self.accept()


# ─────────────────────────────────────────────────────────────
# Данные
# ─────────────────────────────────────────────────────────────
def build_process_data():
    return [
        {"id": "tests", "title": "Tests in Process",
         "subtitle": "Тесты в обработке",
         "value": 20, "total": 25, "unit": "из 25",
         "normal": (15, 25), "status": "ok",
         "trend": [12, 14, 16, 17, 18, 19, 20, 20, 20],
         "recommendation": "Продолжайте мониторинг. Показатель в норме.",
         "details": "Идёт параллельная обработка 20 образцов."},
        {"id": "qc", "title": "QC",
         "subtitle": "Контроль качества",
         "value": 94, "total": 100, "unit": "%",
         "normal": (90, 100), "status": "ok",
         "trend": [92, 93, 91, 94, 95, 94, 94, 94, 94],
         "recommendation": "Показатель стабилен. Отклонений нет.",
         "details": "Все проверки QC пройдены."},
        {"id": "reagents", "title": "Reagents",
         "subtitle": "Реагенты",
         "value": 18, "total": 100, "unit": "% остаток",
         "normal": (30, 100), "status": "warn",
         "trend": [45, 40, 36, 32, 28, 24, 22, 20, 18],
         "recommendation": "Закажите новую партию реагентов. "
                          "Планируйте замену в течение 1–2 дней.",
         "details": "Уровень реагентов ниже нормы."},
        {"id": "calibration", "title": "Calibration",
         "subtitle": "Калибровка",
         "value": 3, "total": 7, "unit": "дня",
         "normal": (0, 7), "status": "warn",
         "trend": [1, 1, 2, 2, 2, 3, 3, 3, 3],
         "recommendation": "Запланируйте калибровку в течение недели.",
         "details": "Прошло 3 дня с последней калибровки. "
                    "Рекомендуемый интервал — не более 7 дней."},
        {"id": "supplies", "title": "Supplies & Waste",
         "subtitle": "Расходники и отходы",
         "value": 82, "total": 100, "unit": "% заполнено",
         "normal": (0, 70), "status": "err",
         "trend": [40, 48, 55, 60, 66, 70, 74, 78, 82],
         "recommendation": "Требуется СРОЧНАЯ замена контейнера. "
                          "Приостановите процесс до устранения.",
         "details": "Контейнер отходов переполнен (82% при норме до 70%)."},
        {"id": "process_path", "title": "Process Path",
         "subtitle": "Путь процесса",
         "value": 4, "total": 5, "unit": "этап из 5",
         "normal": (1, 5), "status": "ok",
         "stages": [
             "Пробоподготовка",
             "Дозирование",
             "Инкубация",
             "Измерение",
             "Отчёт",
         ],
         "trend": [1, 1, 2, 2, 3, 3, 4, 4, 4],
         "recommendation": "Процесс продолжается стабильно.",
         "details": "Процесс на 4-м этапе из 5."},
    ]


# ─────────────────────────────────────────────────────────────
# Карточка процесса
# ─────────────────────────────────────────────────────────────
class ProcessCard(QFrame):
    def __init__(self, process, on_select):
        super().__init__()
        self.process = process
        self.on_select = on_select
        self._active = False

        self.setMinimumHeight(180)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style()

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.accent_bar = QFrame()
        self.accent_bar.setFixedWidth(4)
        outer.addWidget(self.accent_bar)

        inner = QWidget()
        inner.setStyleSheet("background: transparent; border: none;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(20, 16, 20, 16)
        inner_layout.setSpacing(8)
        outer.addWidget(inner, 1)

        # Верх: заголовок + статус
        top = QHBoxLayout()
        top.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.setContentsMargins(0, 0, 0, 0)

        title = QLabel(process["title"])
        title.setFixedHeight(22)
        title.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 15px; font-weight: 700; "
            f"background: transparent; border: none; padding: 0;"
        )
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        subtitle = QLabel(process["subtitle"])
        subtitle.setFixedHeight(18)
        subtitle.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"background: transparent; border: none; padding: 0;"
        )
        subtitle.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        # LED + иконка
        status_box = QHBoxLayout()
        status_box.setSpacing(6)
        status_box.setAlignment(Qt.AlignRight | Qt.AlignTop)
        color = status_color(process["status"])

        self.led = QLabel()
        self.led.setFixedSize(10, 10)
        self.led.setStyleSheet(
            f"background: {color}; border-radius: 5px; border: none;"
        )

        self.status_icon_lbl = QLabel(status_icon(process["status"]))
        self.status_icon_lbl.setStyleSheet(
            f"color: {color}; font-size: 14px; font-weight: bold; "
            f"background: transparent; border: none;"
        )

        status_box.addWidget(self.led)
        status_box.addWidget(self.status_icon_lbl)

        top.addLayout(title_box, 1)
        top.addLayout(status_box)
        inner_layout.addLayout(top)

        # Значение
        value_row = QHBoxLayout()
        value_row.setSpacing(8)
        value_row.setContentsMargins(0, 4, 0, 0)

        self.value_lbl = QLabel(str(process["value"]))
        self.value_lbl.setFixedHeight(46)
        self.value_lbl.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 34px; font-weight: 700; "
            f"background: transparent; border: none; padding: 0;"
        )
        self.value_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.unit_lbl = QLabel(process["unit"])
        self.unit_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 13px; "
            f"font-weight: 500; background: transparent; border: none;"
        )
        self.unit_lbl.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        self.unit_lbl.setContentsMargins(0, 0, 0, 10)

        value_row.addWidget(self.value_lbl)
        value_row.addWidget(self.unit_lbl)
        value_row.addStretch()
        inner_layout.addLayout(value_row)

        # Подпись
        self.hint_lbl = QLabel("")
        self.hint_lbl.setFixedHeight(18)
        self.hint_lbl.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 12px; "
            f"background: transparent; border: none;"
        )
        self.hint_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        inner_layout.addWidget(self.hint_lbl)

        # Прогресс-бар
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(6)
        inner_layout.addWidget(self.bar)

        inner_layout.addStretch()

        self._refresh_card()

    def _apply_style(self):
        bg = Theme.PANEL_SOFT if self._active else Theme.PANEL
        self.setStyleSheet(f"""
            ProcessCard {{
                background: {bg};
                border: 1px solid {Theme.BORDER};
                border-radius: 12px;
            }}
        """)

    def _refresh_card(self):
        p = self.process
        color = status_color(p["status"])

        self.led.setStyleSheet(
            f"background: {color}; border-radius: 5px; border: none;"
        )
        self.status_icon_lbl.setText(status_icon(p["status"]))
        self.status_icon_lbl.setStyleSheet(
            f"color: {color}; font-size: 14px; font-weight: bold; "
            f"background: transparent; border: none;"
        )

        self.accent_bar.setStyleSheet(
            f"background: {color}; "
            f"border-top-left-radius: 12px; "
            f"border-bottom-left-radius: 12px;"
        )

        self.value_lbl.setText(str(p["value"]))
        self.unit_lbl.setText(p["unit"])

        if p["id"] == "calibration":
            n = p["value"]
            word = plural_form(n, "день", "дня", "дней")
            self.hint_lbl.setText(f"Прошло {n} {word}")
        elif p["id"] == "process_path" and "stages" in p:
            idx = p["value"] - 1
            if 0 <= idx < len(p["stages"]):
                self.hint_lbl.setText(f"Этап {p['value']}: {p['stages'][idx]}")
            else:
                self.hint_lbl.setText(f"Этап {p['value']}")
        else:
            self.hint_lbl.setText("")

        percent = int((p["value"] / p["total"]) * 100)
        percent = min(100, max(0, percent))
        self.bar.setValue(percent)
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background: {Theme.PANEL_ALT};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 3px;
            }}
        """)

    def mousePressEvent(self, event):
        self.on_select(self.process["id"])

    def set_active(self, active):
        self._active = active
        self._apply_style()
        self._refresh_card()


# ─────────────────────────────────────────────────────────────
# Панель деталей
# ─────────────────────────────────────────────────────────────
class DetailsPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            DetailsPanel {{
                background: {Theme.PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 12px;
            }}
        """)
        apply_shadow(self, blur=12, alpha=14)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        self.header = QLabel("ДЕТАЛИ ПРОЦЕССА")
        self.header.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px; "
            f"font-weight: 700; letter-spacing: 1.4px;"
        )
        layout.addWidget(self.header)

        self.name_lbl = QLabel("—")
        self.name_lbl.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 18px; font-weight: 700;"
        )
        self.name_lbl.setWordWrap(True)
        layout.addWidget(self.name_lbl)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {Theme.BORDER};")
        layout.addWidget(sep)

        self.normal_lbl = QLabel("")
        self.normal_lbl.setWordWrap(True)
        self.normal_lbl.setTextFormat(Qt.RichText)
        self.normal_lbl.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 13px; line-height: 20px;"
        )
        layout.addWidget(self.normal_lbl)

        # Этапы
        self.stages_frame = QFrame()
        self.stages_frame.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL_ALT};
                border-radius: 8px;
            }}
        """)
        self.stages_layout = QVBoxLayout(self.stages_frame)
        self.stages_layout.setContentsMargins(16, 12, 16, 12)
        self.stages_layout.setSpacing(6)
        self.stages_frame.hide()
        layout.addWidget(self.stages_frame)

        # График
        self.spark_block = SparklineBlock()
        layout.addWidget(self.spark_block)

        self.details_lbl = QLabel("")
        self.details_lbl.setWordWrap(True)
        self.details_lbl.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 14px; line-height: 20px;"
        )
        layout.addWidget(self.details_lbl)

        # Рекомендация
        self.rec_frame = QFrame()
        self.rec_frame.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL_ALT};
                border-radius: 8px;
            }}
        """)
        rec_layout = QVBoxLayout(self.rec_frame)
        rec_layout.setContentsMargins(16, 12, 16, 12)
        rec_layout.setSpacing(4)

        rec_title = QLabel("РЕКОМЕНДАЦИЯ")
        rec_title.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px; "
            f"font-weight: 700; letter-spacing: 1.2px;"
        )
        self.rec_lbl = QLabel("")
        self.rec_lbl.setWordWrap(True)
        self.rec_lbl.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 13px; line-height: 18px;"
        )
        rec_layout.addWidget(rec_title)
        rec_layout.addWidget(self.rec_lbl)
        layout.addWidget(self.rec_frame)

        # Кнопки
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.diag_btn = QPushButton("Диагностика")
        self.diag_btn.setFixedHeight(44)
        self.diag_btn.setCursor(Qt.PointingHandCursor)
        self.diag_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.PANEL};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER_HARD};
                border-radius: 8px;
                font-weight: 600; font-size: 13px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background: {Theme.PANEL_ALT};
                border-color: {Theme.ACCENT};
                color: {Theme.ACCENT};
            }}
        """)
        self.diag_btn.clicked.connect(self._show_diagnostics)

        self.history_btn = QPushButton("История процесса")
        self.history_btn.setFixedHeight(44)
        self.history_btn.setCursor(Qt.PointingHandCursor)
        self.history_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600; font-size: 13px;
                padding: 0 20px;
            }}
            QPushButton:hover {{ background: {Theme.ACCENT_DARK}; }}
        """)
        self.history_btn.clicked.connect(self._show_history)

        btn_row.addWidget(self.diag_btn)
        btn_row.addWidget(self.history_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()
        self._current = None

    def show_process(self, process):
        self._current = process
        color = status_color(process["status"])

        self.name_lbl.setText(process["title"] + "  ·  " + process["subtitle"])

        lo, hi = process["normal"]
        value = process["value"]

        if process["id"] == "calibration":
            n = value
            word = plural_form(n, "день", "дня", "дней")
            normal_text = (
                f"<b>Прошло:</b> {n} {word} с последней калибровки<br>"
                f"<b>Рекомендуемый интервал:</b> до 7 дней"
            )
        else:
            normal_text = (
                f"<b>Норма:</b> {lo}–{hi}<br>"
                f"<b>Текущее:</b> {value}"
            )
            if value < lo:
                normal_text += (
                    f"  ·  <span style='color:{color}'>"
                    f"ниже нормы на {lo - value}</span>"
                )
            elif value > hi:
                normal_text += (
                    f"  ·  <span style='color:{color}'>"
                    f"выше нормы на {value - hi}</span>"
                )
            else:
                normal_text += (
                    f"  ·  <span style='color:{Theme.OK}'>в норме</span>"
                )

        self.normal_lbl.setText(normal_text)

        if process["id"] == "process_path" and "stages" in process:
            while self.stages_layout.count():
                item = self.stages_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            current_idx = process["value"] - 1
            for i, stage in enumerate(process["stages"]):
                if i < current_idx:
                    icon = "✓"
                    clr = Theme.OK
                elif i == current_idx:
                    icon = "▶"
                    clr = Theme.ACCENT
                else:
                    icon = "·"
                    clr = Theme.TEXT_MUTED

                row = QLabel(f"{icon}   {i + 1}. {stage}")
                row.setStyleSheet(
                    f"color: {clr}; font-size: 13px; "
                    f"font-weight: {700 if i == current_idx else 500};"
                )
                self.stages_layout.addWidget(row)

            self.stages_frame.show()
        else:
            self.stages_frame.hide()

        self.spark_block.set_values(process["trend"], color=color)
        self.details_lbl.setText(process["details"])
        self.rec_lbl.setText(process.get("recommendation", "—"))

    def _show_diagnostics(self):
        if not self._current:
            return
        p = self._current
        lo, hi = p["normal"]
        ModalDialog(
            self,
            f"Диагностика · {p['title']}",
            f"<b>Текущее значение:</b> {p['value']} {p['unit']}<br>"
            f"<b>Норма:</b> {lo}–{hi}<br>"
            f"<b>Статус:</b> {status_label(p['status'])}<br><br>"
            f"{p['details']}<br><br>"
            f"<b>Рекомендация:</b><br>{p.get('recommendation', '—')}",
            kind="warn" if p["status"] in ("warn", "err") else "info",
            yes_text="Понятно",
        ).exec()

    def _show_history(self):
        if not self._current:
            return
        p = self._current
        ModalDialog(
            self,
            f"История · {p['title']}",
            "Последние 9 значений (окно ~60 секунд):<br><br>"
            + "<br>".join(
                f"&nbsp;&nbsp;•&nbsp; {v}" for v in p["trend"]
            ),
            kind="info",
            yes_text="Закрыть",
        ).exec()


# ─────────────────────────────────────────────────────────────
# ГЛАВНОЕ ОКНО
# ─────────────────────────────────────────────────────────────
class MonitoringWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BSQ · Статус мониторинга процессов")
        self.resize(1400, 900)
        self._apply_theme()

        self.processes = build_process_data()
        self.events = []
        self.active_process_id = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_status_bar())

        content = QWidget()
        content.setStyleSheet(f"background: {Theme.BG};")
        cl = QHBoxLayout(content)
        cl.setContentsMargins(32, 22, 32, 22)
        cl.setSpacing(24)

        left = QVBoxLayout()
        left.setSpacing(14)

        left_title = QLabel("ПРОЦЕССЫ")
        left_title.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"font-weight: 700; letter-spacing: 1.4px;"
        )
        left.addWidget(left_title)

        self.grid_container = QWidget()
        self.grid = QVBoxLayout(self.grid_container)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(14)

        self.card_widgets = {}
        for row in range(3):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(14)
            for col in range(2):
                idx = row * 2 + col
                if idx < len(self.processes):
                    process = self.processes[idx]
                    card = ProcessCard(process, self._select_process)
                    row_layout.addWidget(card, 1)
                    self.card_widgets[process["id"]] = card
            self.grid.addLayout(row_layout)

        left.addWidget(self.grid_container, 1)

        left_container = QWidget()
        left_container.setLayout(left)
        cl.addWidget(left_container, 5)

        self.details = DetailsPanel()
        cl.addWidget(self.details, 3)

        root.addWidget(content, 1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._auto_update)
        self.timer.start(3000)

        self._select_process(self.processes[0]["id"])
        self._refresh_overall()
        self._log("Мониторинг запущен.", "info")

        QShortcut(QKeySequence("F1"), self, self._show_help)

    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow {{ background: {Theme.BG}; }}
            QLabel {{
                color: {Theme.TEXT};
                font-family: {Theme.FONT_FAMILY};
                font-size: {Theme.FONT_SIZE}px;
            }}
        """)

    def _build_header(self):
        header = QFrame()
        header.setFixedHeight(76)
        header.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL};
                border-bottom: 1px solid {Theme.BORDER};
            }}
        """)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(32, 0, 32, 0)
        hl.setSpacing(16)

        title = QLabel("BSQ")
        title.setFont(QFont(Theme.FONT_FAMILY, 22, QFont.Bold))
        title.setStyleSheet(f"color: {Theme.TEXT};")

        subtitle = QLabel("Система мониторинга процессов")
        subtitle.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 13px;"
        )

        self.update_lbl = QLabel("")
        self.update_lbl.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 13px; font-weight: 500;"
        )

        history_btn = QPushButton("История событий")
        history_btn.setFixedHeight(40)
        history_btn.setMinimumWidth(150)
        history_btn.setCursor(Qt.PointingHandCursor)
        history_btn.setToolTip("Общий журнал всех событий")
        history_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.PANEL_ALT};
                color: {Theme.TEXT_DIM};
                border: 1px solid {Theme.BORDER_HARD};
                border-radius: 8px;
                padding: 0 18px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {Theme.ACCENT};
                color: white;
                border-color: {Theme.ACCENT};
            }}
        """)
        history_btn.clicked.connect(self._show_history)

        help_btn = QPushButton("?")
        help_btn.setFixedSize(40, 40)
        help_btn.setCursor(Qt.PointingHandCursor)
        help_btn.setToolTip("Справка (F1)")
        help_btn.setFont(QFont(Theme.FONT_FAMILY, 15, QFont.Bold))
        help_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.PANEL_ALT};
                color: {Theme.TEXT_DIM};
                border: 1px solid {Theme.BORDER_HARD};
                border-radius: 20px;
            }}
            QPushButton:hover {{
                background: {Theme.ACCENT};
                color: white;
                border-color: {Theme.ACCENT};
            }}
        """)
        help_btn.clicked.connect(self._show_help)

        hl.addWidget(title)
        hl.addSpacing(12)
        hl.addWidget(subtitle)
        hl.addStretch()
        hl.addWidget(self.update_lbl)
        hl.addSpacing(12)
        hl.addWidget(history_btn)
        hl.addSpacing(6)
        hl.addWidget(help_btn)

        return header

    def _build_status_bar(self):
        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(64)
        self.status_bar.setCursor(Qt.PointingHandCursor)
        self.status_bar.setToolTip("Показать проблемные процессы")
        self._apply_status_bar_style(hover=False)
        self.status_bar.mousePressEvent = self._on_status_clicked

        hl = QHBoxLayout(self.status_bar)
        hl.setContentsMargins(32, 0, 32, 0)
        hl.setSpacing(14)

        self.overall_led = QLabel()
        self.overall_led.setFixedSize(16, 16)

        self.overall_lbl = QLabel("")
        self.overall_lbl.setFont(
            QFont(Theme.FONT_FAMILY, 16, QFont.DemiBold)
        )

        self.overall_hint = QLabel("")
        self.overall_hint.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 13px;"
        )

        self.overall_action = QLabel("→")
        self.overall_action.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 16px; font-weight: bold;"
        )

        hl.addWidget(self.overall_led)
        hl.addWidget(self.overall_lbl)
        hl.addSpacing(12)
        hl.addWidget(self.overall_hint)
        hl.addStretch()
        hl.addWidget(self.overall_action)

        return self.status_bar

    def _apply_status_bar_style(self, hover=False):
        bg = "#F8FAFC" if hover else Theme.PANEL
        self.status_bar.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-bottom: 1px solid {Theme.BORDER};
            }}
        """)

    def _on_status_clicked(self, event):
        problems = [p for p in self.processes if p["status"] in ("warn", "err")]
        if not problems:
            ModalDialog(
                self,
                "Все в порядке",
                "Все процессы работают в пределах нормы.",
                kind="info",
                yes_text="Понятно",
            ).exec()
            return

        dlg = ProblemsDialog(self, problems)
        dlg.exec()
        if dlg.selected_id:
            self._select_process(dlg.selected_id)

    def _refresh_overall(self):
        statuses = [p["status"] for p in self.processes]
        if "err" in statuses:
            overall = "err"
            text = "Требуется вмешательство"
            hint = "Обнаружены критические отклонения"
        elif "warn" in statuses:
            overall = "warn"
            text = "Есть предупреждения"
            hint = "Проверьте процессы с меткой ⚠"
        else:
            overall = "ok"
            text = "Все процессы в норме"
            hint = "Система работает стабильно"

        color = status_color(overall)
        self.overall_led.setStyleSheet(
            f"background: {color}; border-radius: 8px;"
        )
        self.overall_lbl.setText(text)
        self.overall_lbl.setStyleSheet(
            f"color: {color}; font-size: 16px; font-weight: 700;"
        )
        self.overall_hint.setText(hint)

        if overall == "ok":
            self.overall_action.setText("")
        else:
            self.overall_action.setText("→")

        self.update_lbl.setText(
            f"Обновлено: {datetime.now().strftime('%H:%M:%S')}"
        )

    def _select_process(self, process_id):
        self.active_process_id = process_id
        for pid, card in self.card_widgets.items():
            card.set_active(pid == process_id)
        process = next(p for p in self.processes if p["id"] == process_id)
        self.details.show_process(process)

    def _auto_update(self):
        for p in self.processes:
            if p["id"] == "calibration":
                continue
            delta = random.choice([-1, 0, 0, 1])
            p["value"] = max(0, p["value"] + delta)
            p["status"] = compute_status(p["value"], p["normal"])

            p["trend"].append(p["value"])
            if len(p["trend"]) > 12:
                p["trend"].pop(0)

        for p in self.processes:
            self.card_widgets[p["id"]]._refresh_card()

        self._refresh_overall()
        if self.active_process_id:
            process = next(
                p for p in self.processes if p["id"] == self.active_process_id
            )
            self.details.show_process(process)

    def _log(self, message, level="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.events.insert(0, (ts, message, level))
        if len(self.events) > 200:
            self.events.pop()

    def _show_history(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("История событий")
        dlg.setModal(True)
        dlg.setFixedSize(680, 540)
        dlg.setStyleSheet(f"QDialog {{ background: {Theme.PANEL}; }}")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(16)

        t = QLabel("История событий")
        t.setFont(QFont(Theme.FONT_FAMILY, 17, QFont.Bold))
        t.setStyleSheet(f"color: {Theme.TEXT};")

        lst = QListWidget()
        lst.setFocusPolicy(Qt.NoFocus)
        lst.setStyleSheet(f"""
            QListWidget {{
                background: {Theme.PANEL_ALT};
                border: 1px solid {Theme.BORDER};
                border-radius: 10px;
                padding: 10px;
                color: {Theme.TEXT};
                font-family: 'Consolas', monospace;
                font-size: 13px;
            }}
            QListWidget::item {{ padding: 6px 0; }}
        """)
        for ts, msg, level in self.events:
            col = {"info": Theme.TEXT_DIM, "warn": Theme.WARN,
                   "err": Theme.ERR, "ok": Theme.OK}.get(level, Theme.TEXT)
            item = QListWidgetItem(f"{ts}   {msg}")
            item.setForeground(QColor(col))
            lst.addItem(item)

        cb = QPushButton("Закрыть")
        cb.setFixedHeight(44)
        cb.setCursor(Qt.PointingHandCursor)
        cb.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT}; color: white;
                border: none; border-radius: 8px;
                font-weight: 600; padding: 0 22px;
            }}
            QPushButton:hover {{ background: {Theme.ACCENT_DARK}; }}
        """)
        cb.clicked.connect(dlg.accept)

        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(cb)

        layout.addWidget(t)
        layout.addWidget(lst)
        layout.addLayout(bottom)
        dlg.exec()

    def _show_help(self):
        ModalDialog(
            self,
            "Справка",
            "<b>Общий статус (сверху)</b><br>"
            "• 🟢 Все процессы в норме<br>"
            "• 🟠 Есть предупреждения<br>"
            "• 🔴 Требуется вмешательство<br>"
            "<i>Клик по статус-бару → список проблемных процессов.</i><br><br>"
            "<b>Карточки процессов</b><br>"
            "• Название и подзаголовок<br>"
            "• Текущее значение + единицы<br>"
            "• Прогресс-бар (цвет = статус)<br>"
            "• LED + иконка статуса<br>"
            "• Цветная полоса слева<br>"
            "• Подпись этапа или срока<br><br>"
            "<b>Панель деталей</b><br>"
            "• Название процесса<br>"
            "• Норма и отклонение<br>"
            "• Список этапов (для Process Path)<br>"
            "• График тренда с осями min/max<br>"
            "• Описание и рекомендация<br>"
            "• Кнопки «Диагностика» / «История процесса»<br><br>"
            "<b>Данные обновляются каждые 3 секунды.</b>",
            kind="info",
            yes_text="Понятно",
        ).exec()


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont(Theme.FONT_FAMILY, Theme.FONT_SIZE))
    window = MonitoringWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()