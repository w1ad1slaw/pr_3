import sys
import random
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QProgressBar, QListWidget,
    QListWidgetItem, QDialog, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import (
    QFont, QColor, QShortcut, QKeySequence, QPainter, QBrush, QPen,
    QLinearGradient
)


# ─────────────────────────────────────────────────────────────
# Дизайн-система (лабораторная тема, teal-акцент)
# ─────────────────────────────────────────────────────────────
class Theme:
    BG          = "#F7F9FB"
    PANEL       = "#FFFFFF"
    PANEL_ALT   = "#EEF2F6"
    BORDER      = "#E1E7ED"
    BORDER_HARD = "#C7D0DA"

    TEXT        = "#0F172A"
    TEXT_DIM    = "#475569"
    TEXT_MUTED  = "#94A3B8"

    ACCENT      = "#0D9488"   # teal
    ACCENT_DARK = "#0F766E"
    ACCENT_SOFT = "#CCFBF1"

    IDLE    = "#64748B"
    OK      = "#15803D"
    WARN    = "#C2410C"
    ERR     = "#B91C1C"
    DONE    = "#0D9488"
    LINK    = "#C2410C"

    FONT_FAMILY = "Segoe UI"
    FONT_SIZE   = 15


def apply_shadow(widget, blur=14, offset_y=2, alpha=22):
    sh = QGraphicsDropShadowEffect()
    sh.setBlurRadius(blur)
    sh.setOffset(0, offset_y)
    sh.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(sh)


def darken(hex_color, factor=118):
    return QColor(hex_color).darker(factor).name()


# ─────────────────────────────────────────────────────────────
# Пробирка — живой индикатор прогресса
# ─────────────────────────────────────────────────────────────
class TestTube(QWidget):
    """
    Визуальный индикатор заполнения пробирки.
    Уровень жидкости = progress (0..100).
    Цвет жидкости меняется по состоянию.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 320)
        self._progress = 0
        self._state = "idle"

    def set_progress(self, value):
        self._progress = max(0, min(100, value))
        self.update()

    def set_state(self, state):
        self._state = state
        self.update()

    def _liquid_colors(self):
        """(верхний цвет, нижний цвет) градиента жидкости."""
        palette = {
            "idle":     ("#CBD5E1", "#94A3B8"),   # серый — пустая
            "running":  ("#5EEAD4", "#0D9488"),   # teal — работа
            "paused":   ("#FCD34D", "#D97706"),   # янтарный — пауза
            "alert":    ("#FCA5A5", "#B91C1C"),   # красный — отклонение
            "error":    ("#FCA5A5", "#991B1B"),   # тёмно-красный — ошибка
            "done":     ("#6EE7B7", "#059669"),   # изумрудный — завершено
            "nolink":   ("#FDBA74", "#C2410C"),   # оранжевый — нет связи
        }
        return palette.get(self._state, palette["idle"])

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin_top = 40
        margin_bottom = 12
        margin_x = 40

        # ─── Верхнее горлышко ───
        neck_w = w - margin_x * 2
        neck_h = margin_top
        neck_rect = QRectF(margin_x, 4, neck_w, neck_h)
        p.setPen(QPen(QColor("#94A3B8"), 2))
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.drawRoundedRect(neck_rect, 8, 8)

        # ─── Тело пробирки ───
        body_x = margin_x - 10
        body_y = margin_top - 4
        body_w = w - (margin_x - 10) * 2
        body_h = h - body_y - margin_bottom

        body_rect = QRectF(body_x, body_y, body_w, body_h)
        p.setPen(QPen(QColor("#94A3B8"), 2))
        p.setBrush(QBrush(QColor("#F8FAFC")))
        # Нижняя часть — закруглённая
        p.drawRoundedRect(body_rect, 16, 16)

        # ─── Жидкость ───
        if self._progress > 0:
            fill_h = body_h * (self._progress / 100.0)
            fill_y = body_y + (body_h - fill_h)
            fill_rect = QRectF(
                body_x + 4, fill_y,
                body_w - 8, fill_h - 4
            )
            top_color, bottom_color = self._liquid_colors()
            grad = QLinearGradient(0, fill_y, 0, body_y + body_h)
            grad.setColorAt(0, QColor(top_color))
            grad.setColorAt(1, QColor(bottom_color))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(fill_rect, 12, 12)

            # ─── Блик ───
            highlight = QRectF(
                body_x + 10, fill_y + 6,
                (body_w - 20) * 0.35,
                8
            )
            p.setBrush(QBrush(QColor(255, 255, 255, 90)))
            p.drawRoundedRect(highlight, 4, 4)

        # ─── Шкала-деления ───
        p.setPen(QPen(QColor("#CBD5E1"), 1.5))
        for i in range(1, 5):
            y = body_y + body_h * (i / 5)
            p.drawLine(
                int(body_x + body_w - 12), int(y),
                int(body_x + body_w - 4), int(y)
            )

        # ─── Процент поверх ───
        p.setPen(QColor(Theme.TEXT))
        p.setFont(QFont(Theme.FONT_FAMILY, 20, QFont.Bold))
        p.drawText(
            QRectF(0, h / 2 - 20, w, 40),
            Qt.AlignCenter,
            f"{self._progress}%"
        )


# ─────────────────────────────────────────────────────────────
# Базовый модальный диалог
# ─────────────────────────────────────────────────────────────
class ModalDialog(QDialog):
    def __init__(self, parent, title, message, kind="info",
                 yes_text="OK", no_text=None, width=460):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedWidth(width)
        self.setStyleSheet(f"QDialog {{ background: {Theme.PANEL}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 22)
        layout.setSpacing(18)

        color = {
            "info": Theme.ACCENT, "warn": Theme.WARN,
            "err": Theme.ERR, "question": Theme.ACCENT,
        }.get(kind, Theme.ACCENT)

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
# Справка
# ─────────────────────────────────────────────────────────────
class HelpDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Справка")
        self.setModal(True)
        self.setFixedSize(620, 580)
        self.setStyleSheet(f"QDialog {{ background: {Theme.PANEL}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(16)

        t = QLabel("Справка по лабораторному HMI")
        t.setFont(QFont(Theme.FONT_FAMILY, 17, QFont.Bold))
        t.setStyleSheet(f"color: {Theme.TEXT};")

        c = QLabel("""
<b>Текущая партия</b><br>
Экран показывает состояние активной партии образцов:<br>
• <b>Партии в работе</b> — сколько партий сейчас обрабатывается<br>
• <b>Загружено образцов</b> — заполнение ячеек<br>
• <b>Тестов выполнено</b> — прогресс тестов<br>
<br>
<b>Пробирка</b> — визуальный индикатор заполнения партии.
Цвет жидкости меняется по состоянию:<br>
• <b>Серый</b> — ожидание<br>
• <b>Бирюзовый</b> — работа<br>
• <b>Янтарный</b> — пауза<br>
• <b>Красный</b> — отклонение<br>
• <b>Изумрудный</b> — завершено<br>
<br>
<b>Управление процессом</b><br>
• <b>START</b> — запуск партии<br>
• <b>PAUSE</b> — пауза (можно продолжить)<br>
• <b>STOP</b> — полная остановка (с подтверждением)<br>
<br>
<b>Работа с партией</b><br>
• <b>+ Добавить образец</b> — загрузка нового образца в партию<br>
• <b>Новая партия</b> — после успешного завершения<br>
<br>
<b>Горячие клавиши</b><br>
• <b>F1</b> — справка<br>
• <b>Space</b> — Start / Pause<br>
• <b>Esc</b> — Stop
        """)
        c.setWordWrap(True)
        c.setTextFormat(Qt.RichText)
        c.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 14px; line-height: 22px;"
        )

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
        cb.clicked.connect(self.accept)

        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(cb)

        layout.addWidget(t)
        layout.addWidget(c)
        layout.addStretch()
        layout.addLayout(bottom)


# ─────────────────────────────────────────────────────────────
# История событий
# ─────────────────────────────────────────────────────────────
class HistoryDialog(QDialog):
    def __init__(self, parent, events):
        super().__init__(parent)
        self.setWindowTitle("История событий")
        self.setModal(True)
        self.setFixedSize(700, 560)
        self.setStyleSheet(f"QDialog {{ background: {Theme.PANEL}; }}")

        layout = QVBoxLayout(self)
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
                border-radius: 8px;
                padding: 10px;
                color: {Theme.TEXT};
                font-family: 'Consolas', monospace;
                font-size: 14px;
            }}
            QListWidget::item {{ padding: 6px 0; }}
        """)
        for ts, msg, level in events:
            col = {"info": Theme.TEXT_DIM, "warn": Theme.WARN,
                   "err": Theme.ERR, "done": Theme.DONE}.get(level, Theme.TEXT)
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
        cb.clicked.connect(self.accept)

        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(cb)

        layout.addWidget(t)
        layout.addWidget(lst)
        layout.addLayout(bottom)


# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
class HeaderBar(QFrame):
    def __init__(self, on_help, on_history):
        super().__init__()
        self.setFixedHeight(72)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL};
                border-bottom: 1px solid {Theme.BORDER};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(20)

        # Логотип-точка
        dot = QLabel()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet(
            f"background: {Theme.ACCENT}; border-radius: 6px;"
        )

        self.title = QLabel("Лаборатория анализа")
        self.title.setFont(QFont(Theme.FONT_FAMILY, 15, QFont.Bold))
        self.title.setStyleSheet(f"color: {Theme.TEXT};")

        self.subtitle = QLabel("Смена 14:00–22:00")
        self.subtitle.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 13px;"
        )

        self.connection = QLabel("● ПОДКЛЮЧЕНО")
        self.connection.setStyleSheet(
            f"color: {Theme.OK}; font-weight: 600; font-size: 13px;"
        )

        self.clock = QLabel("--:--:--")
        self.clock.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 14px;")

        history_btn = QPushButton("История")
        history_btn.setFixedHeight(40)
        history_btn.setMinimumWidth(120)
        history_btn.setCursor(Qt.PointingHandCursor)
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
        history_btn.clicked.connect(on_history)

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
        help_btn.clicked.connect(on_help)

        layout.addWidget(dot)
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addSpacing(20)
        layout.addWidget(self.connection)
        layout.addStretch()
        layout.addWidget(self.clock)
        layout.addSpacing(12)
        layout.addWidget(history_btn)
        layout.addSpacing(6)
        layout.addWidget(help_btn)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)
        self._tick()

    def _tick(self):
        self.clock.setText(datetime.now().strftime("%H:%M:%S"))

    def set_connection(self, ok: bool):
        if ok:
            self.connection.setText("● ПОДКЛЮЧЕНО")
            self.connection.setStyleSheet(
                f"color: {Theme.OK}; font-weight: 600; font-size: 13px;"
            )
        else:
            self.connection.setText("● НЕТ СВЯЗИ")
            self.connection.setStyleSheet(
                f"color: {Theme.LINK}; font-weight: 600; font-size: 13px;"
            )


# ─────────────────────────────────────────────────────────────
# Баннер отклонения
# ─────────────────────────────────────────────────────────────
class AlertBanner(QFrame):
    def __init__(self, on_details):
        super().__init__()
        self.on_details = on_details
        self.setStyleSheet(f"""
            QFrame {{
                background: #FEF2F2;
                border: 2px solid {Theme.ERR};
                border-radius: 12px;
            }}
        """)
        apply_shadow(self)
        self.hide()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(18)

        self.icon = QLabel("⚠")
        self.icon.setFont(QFont(Theme.FONT_FAMILY, 22, QFont.Bold))
        self.icon.setStyleSheet(f"color: {Theme.ERR};")
        self.icon.setFixedSize(32, 32)
        self.icon.setAlignment(Qt.AlignCenter)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)

        self.title = QLabel("Отклонение")
        self.title.setStyleSheet(
            f"color: {Theme.ERR}; font-size: 14px; font-weight: 700;"
        )
        self.message = QLabel("")
        self.message.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 14px;"
        )
        text_box.addWidget(self.title)
        text_box.addWidget(self.message)

        details_btn = QPushButton("Подробнее")
        details_btn.setFixedHeight(40)
        details_btn.setMinimumWidth(140)
        details_btn.setCursor(Qt.PointingHandCursor)
        details_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ERR}; color: white;
                border: none; border-radius: 8px;
                font-weight: 600; padding: 0 18px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {darken(Theme.ERR)}; }}
        """)
        details_btn.clicked.connect(self.on_details)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Theme.TEXT_DIM};
                border: none; font-size: 16px; font-weight: bold;
            }}
            QPushButton:hover {{ color: {Theme.TEXT}; }}
        """)
        close_btn.clicked.connect(self.hide)

        layout.addWidget(self.icon)
        layout.addLayout(text_box, 1)
        layout.addWidget(details_btn)
        layout.addWidget(close_btn)

    def show_alert(self, title, message):
        self.title.setText(title)
        self.message.setText(message)
        self.show()

    def clear(self):
        self.hide()


# ─────────────────────────────────────────────────────────────
# Панель текущей партии
# ─────────────────────────────────────────────────────────────
class CurrentBatchPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL};
                border-radius: 14px;
                border: 1px solid {Theme.BORDER};
            }}
        """)
        apply_shadow(self)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 28)
        outer.setSpacing(36)

        # ─── Пробирка ───
        tube_box = QVBoxLayout()
        tube_box.setSpacing(8)
        self.tube = TestTube()
        tube_label = QLabel("ЗАПОЛНЕНИЕ ПАРТИИ")
        tube_label.setAlignment(Qt.AlignCenter)
        tube_label.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"font-weight: 700; letter-spacing: 1.2px;"
        )
        tube_box.addWidget(self.tube, 0, Qt.AlignHCenter)
        tube_box.addWidget(tube_label)
        tube_box.addStretch()
        outer.addLayout(tube_box)

        # ─── Данные ───
        info = QVBoxLayout()
        info.setSpacing(20)

        # Верхняя строка: статус + партия
        top = QHBoxLayout()
        top.setSpacing(16)

        self.led = QLabel()
        self.led.setFixedSize(24, 24)

        self.state = QLabel("ОЖИДАНИЕ")
        self.state.setFont(QFont(Theme.FONT_FAMILY, 26, QFont.Bold))

        top.addWidget(self.led)
        top.addWidget(self.state)
        top.addStretch()

        batch_frame = QFrame()
        batch_frame.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL_ALT};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
            }}
        """)
        bf_layout = QHBoxLayout(batch_frame)
        bf_layout.setContentsMargins(18, 10, 18, 10)
        bf_layout.setSpacing(12)

        bf_label = QLabel("ПАРТИЯ")
        bf_label.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"font-weight: 700; letter-spacing: 1px;"
        )
        self.batch_id = QLabel("#—")
        self.batch_id.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 15px; font-weight: 700;"
        )
        bf_layout.addWidget(bf_label)
        bf_layout.addWidget(self.batch_id)

        top.addWidget(batch_frame)

        info.addLayout(top)

        # Три метрики с полосами прогресса
        self.metric_batches = self._make_metric(
            "Партии в работе", Theme.ACCENT
        )
        self.metric_samples = self._make_metric(
            "Загружено образцов", Theme.OK
        )
        self.metric_tests = self._make_metric(
            "Тестов выполнено", Theme.ACCENT
        )
        info.addWidget(self.metric_batches["root"])
        info.addWidget(self.metric_samples["root"])
        info.addWidget(self.metric_tests["root"])

        # Подсказка
        self.hint = QLabel("Нажмите START для запуска обработки")
        self.hint.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 14px; font-style: italic;"
        )
        info.addWidget(self.hint)
        info.addStretch()

        outer.addLayout(info, 1)

    def _make_metric(self, title, color):
        root = QWidget()
        v = QVBoxLayout(root)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        head = QHBoxLayout()
        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"font-weight: 700; letter-spacing: 1.2px;"
        )
        value_lbl = QLabel("0 из 0")
        value_lbl.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 15px; font-weight: 700;"
        )
        head.addWidget(title_lbl)
        head.addStretch()
        head.addWidget(value_lbl)
        v.addLayout(head)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setFixedHeight(12)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background: {Theme.PANEL_ALT};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 5px;
            }}
        """)
        v.addWidget(bar)

        return {"root": root, "title": title_lbl,
                "value": value_lbl, "bar": bar}

    # ─── Обновление состояния ────────────────────────────
    def set_state(self, state):
        cfg = {
            "idle":    ("ОЖИДАНИЕ",   Theme.IDLE,
                        "Нажмите START для запуска обработки"),
            "running": ("РАБОТА",     Theme.OK,
                        "Идёт обработка партии. Следите за отклонениями."),
            "paused":  ("ПАУЗА",      Theme.WARN,
                        "Пауза оператором. Нажмите START для продолжения."),
            "alert":   ("ОТКЛОНЕНИЕ", Theme.ERR,
                        "Обнаружено отклонение. Проверьте образец."),
            "error":   ("ОШИБКА",     Theme.ERR,
                        "Устраните причину и нажмите СБРОС."),
            "done":    ("ЗАВЕРШЕНО",  Theme.DONE,
                        "Партия завершена. Нажмите «Новая партия»."),
            "nolink":  ("НЕТ СВЯЗИ",  Theme.LINK,
                        "Проверьте подключение к серверу."),
        }
        text, color, hint = cfg.get(state, cfg["idle"])

        self.state.setText(text)
        self.state.setStyleSheet(f"color: {color};")
        self.led.setStyleSheet(f"background: {color}; border-radius: 12px;")
        self.hint.setText(hint)
        self.tube.set_state(state)

    def set_batch(self, batch_id):
        self.batch_id.setText(f"#{batch_id}" if batch_id else "#—")

    def update_progress(self, value):
        self.tube.set_progress(value)

    def update_metric(self, key, current, total):
        metric = getattr(self, f"metric_{key}")
        percent = int((current / total) * 100) if total else 0
        metric["bar"].setValue(percent)
        metric["value"].setText(f"{current} из {total}")


# ─────────────────────────────────────────────────────────────
# Строка последнего события
# ─────────────────────────────────────────────────────────────
class LastEventRow(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL};
                border-radius: 12px;
                border: 1px solid {Theme.BORDER};
            }}
        """)
        apply_shadow(self, blur=8, alpha=15)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 14, 24, 14)
        layout.setSpacing(14)

        self.icon = QLabel("ℹ")
        self.icon.setFont(QFont(Theme.FONT_FAMILY, 16, QFont.Bold))
        self.icon.setStyleSheet(f"color: {Theme.ACCENT};")
        self.icon.setFixedSize(24, 24)
        self.icon.setAlignment(Qt.AlignCenter)

        self.text = QLabel("HMI запущен. Ожидание команды оператора.")
        self.text.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 14px;"
        )

        layout.addWidget(self.icon)
        layout.addWidget(self.text, 1)

    def set_text(self, text, level="info"):
        color = {"info": Theme.TEXT_DIM, "warn": Theme.WARN,
                 "err": Theme.ERR, "done": Theme.DONE}.get(level, Theme.TEXT_DIM)
        icon_color = {"info": Theme.ACCENT, "warn": Theme.WARN,
                      "err": Theme.ERR, "done": Theme.DONE}.get(level, Theme.ACCENT)
        icon_char = {"info": "ℹ", "warn": "⚠",
                     "err": "✕", "done": "✓"}.get(level, "ℹ")

        self.text.setText(text)
        self.text.setStyleSheet(f"color: {color}; font-size: 14px;")
        self.icon.setText(icon_char)
        self.icon.setStyleSheet(f"color: {icon_color};")


# ─────────────────────────────────────────────────────────────
# CONTROL BAR — две группы
# ─────────────────────────────────────────────────────────────
class ControlBar(QFrame):
    def __init__(self, on_action):
        super().__init__()
        self.on_action = on_action
        self.setFixedHeight(128)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL};
                border-top: 1px solid {Theme.BORDER};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 22, 32, 22)
        layout.setSpacing(20)

        # ─── ГРУППА 1: работа с партией ───
        group1 = QVBoxLayout()
        group1.setSpacing(6)
        g1_label = QLabel("РАБОТА С ПАРТИЕЙ")
        g1_label.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px; "
            f"font-weight: 700; letter-spacing: 1.2px;"
        )
        g1_row = QHBoxLayout()
        g1_row.setSpacing(12)

        self.btn_add = self._btn(
            "+ Добавить образец", Theme.ACCENT, 220, outline=True
        )
        self.btn_new = self._btn(
            "Новая партия", Theme.ACCENT, 180, outline=True
        )
        self.btn_add.clicked.connect(lambda: self.on_action("add_sample"))
        self.btn_new.clicked.connect(lambda: self.on_action("new_batch"))
        g1_row.addWidget(self.btn_add)
        g1_row.addWidget(self.btn_new)

        group1.addWidget(g1_label)
        group1.addLayout(g1_row)
        layout.addLayout(group1)

        # ─── Вертикальный разделитель ───
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background: {Theme.BORDER};")
        layout.addSpacing(20)
        layout.addWidget(sep)
        layout.addSpacing(20)

        # ─── ГРУППА 2: управление процессом ───
        group2 = QVBoxLayout()
        group2.setSpacing(6)
        g2_label = QLabel("УПРАВЛЕНИЕ ПРОЦЕССОМ")
        g2_label.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px; "
            f"font-weight: 700; letter-spacing: 1.2px;"
        )
        g2_row = QHBoxLayout()
        g2_row.setSpacing(12)

        self.btn_pause = self._btn("PAUSE", Theme.WARN, 150)
        self.btn_start = self._btn("START", Theme.OK, 170)
        self.btn_stop  = self._btn("STOP", Theme.ERR, 150)
        self.btn_reset = self._btn("СБРОС", Theme.ACCENT, 150)

        self.btn_start.clicked.connect(lambda: self.on_action("start"))
        self.btn_pause.clicked.connect(lambda: self.on_action("pause"))
        self.btn_stop.clicked.connect(lambda: self.on_action("stop"))
        self.btn_reset.clicked.connect(lambda: self.on_action("reset"))

        g2_row.addWidget(self.btn_pause)
        g2_row.addWidget(self.btn_start)
        g2_row.addWidget(self.btn_stop)
        g2_row.addWidget(self.btn_reset)

        group2.addWidget(g2_label)
        group2.addLayout(g2_row)
        layout.addLayout(group2)

        layout.addStretch()

    def _btn(self, text, color, width, outline=False):
        b = QPushButton(text)
        b.setFixedSize(width, 76)
        b.setCursor(Qt.PointingHandCursor)
        b.setFont(QFont(Theme.FONT_FAMILY, 14, QFont.Bold))

        if outline:
            b.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.PANEL};
                    color: {color};
                    border: 2px solid {color};
                    border-radius: 10px;
                }}
                QPushButton:hover:!disabled {{
                    background: {color};
                    color: white;
                }}
                QPushButton:pressed:!disabled {{
                    background: {darken(color, 130)};
                }}
                QPushButton:disabled {{
                    border-color: {Theme.BORDER};
                    color: {Theme.TEXT_MUTED};
                    background: {Theme.PANEL_ALT};
                }}
            """)
        else:
            b.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border: none;
                    border-radius: 10px;
                }}
                QPushButton:hover:!disabled {{
                    background: {darken(color, 115)};
                }}
                QPushButton:pressed:!disabled {{
                    background: {darken(color, 130)};
                }}
                QPushButton:disabled {{
                    background: {Theme.PANEL_ALT};
                    color: {Theme.TEXT_MUTED};
                }}
            """)
        return b

    def apply_state(self, state: str):
        # Работа с партией
        if state in ("idle", "running", "paused", "alert"):
            self.btn_add.show()
            self.btn_add.setEnabled(True)
        else:
            self.btn_add.setEnabled(False)

        if state == "done":
            self.btn_new.show()
            self.btn_new.setEnabled(True)
        else:
            self.btn_new.hide()

        # Управление процессом
        if state == "idle":
            self.btn_start.setEnabled(True)
            self.btn_pause.setEnabled(False)
            self.btn_stop.setEnabled(False)
            self.btn_reset.hide()
        elif state == "running":
            self.btn_start.setEnabled(False)
            self.btn_pause.setEnabled(True)
            self.btn_stop.setEnabled(True)
            self.btn_reset.hide()
        elif state == "paused":
            self.btn_start.setEnabled(True)
            self.btn_pause.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.btn_reset.hide()
        elif state == "alert":
            self.btn_start.setEnabled(False)
            self.btn_pause.setEnabled(True)
            self.btn_stop.setEnabled(True)
            self.btn_reset.hide()
        elif state == "done":
            self.btn_start.setEnabled(False)
            self.btn_pause.setEnabled(False)
            self.btn_stop.setEnabled(False)
            self.btn_reset.hide()
        elif state in ("error", "nolink"):
            self.btn_start.setEnabled(False)
            self.btn_pause.setEnabled(False)
            self.btn_stop.setEnabled(False)
            self.btn_reset.show()


# ─────────────────────────────────────────────────────────────
# ГЛАВНОЕ ОКНО
# ─────────────────────────────────────────────────────────────
class LabHMI(QMainWindow):
    TOTAL_BATCHES = 10
    TOTAL_SAMPLES = 12
    TOTAL_TESTS = 250
    BASE_TESTS_PER_MIN = 4.2

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторный HMI · Current Batch Status")
        self.resize(1400, 900)
        self._apply_theme()

        # Состояние
        self._state = "idle"
        self._events = []
        self._simulate_timer = None
        self._progress = 0

        self._batches = 0
        self._samples = 0
        self._tests = 0
        self._batch_id = None

        self._sample_alerted = False  # флаг, чтобы отклонение не срабатывало много раз

        # UI
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header = HeaderBar(self._show_help, self._show_history)
        root.addWidget(self.header)

        content = QWidget()
        content.setStyleSheet(f"background: {Theme.BG};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(32, 22, 32, 22)
        cl.setSpacing(16)

        self.alert = AlertBanner(self._show_alert_details)
        cl.addWidget(self.alert)

        self.batch_panel = CurrentBatchPanel()
        cl.addWidget(self.batch_panel, 1)

        self.last_event = LastEventRow()
        cl.addWidget(self.last_event)

        root.addWidget(content, 1)

        self.controls = ControlBar(self._handle_action)
        root.addWidget(self.controls)

        # Инициализация
        self._apply_state("idle")
        self._refresh_all()
        self._log("HMI запущен. Ожидание команды оператора.")

        self._setup_shortcuts()

    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow {{ background: {Theme.BG}; }}
            QLabel {{
                color: {Theme.TEXT};
                font-family: {Theme.FONT_FAMILY};
                font-size: {Theme.FONT_SIZE}px;
            }}
        """)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("F1"),    self, self._show_help)
        QShortcut(QKeySequence("Space"), self, self._shortcut_start_pause)
        QShortcut(QKeySequence("Esc"),   self, lambda: self._handle_action("stop"))

    def _shortcut_start_pause(self):
        if self._state == "running":
            self._handle_action("pause")
        elif self._state in ("idle", "paused"):
            self._handle_action("start")

    # ─── Лог ──────────────────────────────────────────────
    def _log(self, message, level="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self._events.insert(0, (ts, message, level))
        if len(self._events) > 200:
            self._events.pop()
        self.last_event.set_text(f"{ts} — {message}", level)

    def _show_help(self):
        HelpDialog(self).exec()

    def _show_history(self):
        HistoryDialog(self, self._events).exec()

    def _show_alert_details(self):
        ModalDialog(
            self,
            "Отклонение образца",
            "<b>Образец #A-0421</b><br>"
            "Партия #1287 · Тест: pH<br><br>"
            "Показатель: <b>4.2</b> (норма: 6.5–7.5)<br>"
            "Отклонение: <b>−35%</b><br><br>"
            "Рекомендация: проверить подготовку образца "
            "и повторить тест.",
            kind="warn",
            yes_text="Понятно",
        ).exec()

    # ─── Состояние ────────────────────────────────────────
    def _apply_state(self, state):
        self._state = state
        self.batch_panel.set_state(state)
        self.controls.apply_state(state)
        self.header.set_connection(state != "nolink")

    def _refresh_all(self):
        self.batch_panel.update_progress(self._progress)
        self.batch_panel.update_metric("batches", self._batches, self.TOTAL_BATCHES)
        self.batch_panel.update_metric("samples", self._samples, self.TOTAL_SAMPLES)
        self.batch_panel.update_metric("tests", self._tests, self.TOTAL_TESTS)
        self.batch_panel.set_batch(self._batch_id)

    # ─── Действия ─────────────────────────────────────────
    def _handle_action(self, action):
        if action == "start":
            if self._state in ("idle", "paused"):
                self._start_run()
        elif action == "pause":
            if self._state in ("running", "alert"):
                self._pause_run()
        elif action == "stop":
            if self._state in ("running", "paused", "alert"):
                self._stop_run()
        elif action == "add_sample":
            if self._state in ("idle", "running", "paused", "alert"):
                self._add_sample()
        elif action == "new_batch":
            if self._state == "done":
                self._new_batch()
        elif action == "reset":
            if self._state in ("error", "nolink"):
                self._reset()

    def _start_run(self):
        # Если партии нет — создаём
        if self._batch_id is None:
            self._batch_id = 1287
            self._log(f"Создана партия #{self._batch_id}", "info")

        self._apply_state("running")
        self.alert.clear()
        self._log("Обработка партии запущена")
        self._start_simulation()

    def _pause_run(self):
        self._stop_simulation()
        self._apply_state("paused")
        self._log("Обработка на паузе", "warn")

    def _stop_run(self):
        dlg = ModalDialog(
            self,
            "Остановить обработку?",
            "Текущая партия будет прервана, а результаты "
            "незавершённых тестов — потеряны. Продолжить?",
            kind="warn",
            yes_text="Остановить",
            no_text="Отмена",
        )
        if dlg.exec() != QDialog.Accepted:
            return

        self._progress = 0
        self._batches = 0
        self._samples = 0
        self._tests = 0
        self._batch_id = None
        self._sample_alerted = False
        self._apply_state("idle")
        self.alert.clear()
        self._refresh_all()
        self._stop_simulation()
        self._log("Обработка остановлена оператором")

    def _add_sample(self):
        if self._samples >= self.TOTAL_SAMPLES:
            ModalDialog(
                self,
                "Все ячейки заняты",
                f"В партии уже {self.TOTAL_SAMPLES} образцов — "
                "это максимум для текущего цикла. "
                "Дождитесь завершения части тестов.",
                kind="info", yes_text="Понятно"
            ).exec()
            return

        self._samples += 1
        self._log(f"Добавлен образец #{self._samples}", "info")
        self._refresh_all()

    def _new_batch(self):
        # После завершения — сброс и готовность к новой партии
        self._progress = 0
        self._batches = 0
        self._samples = 0
        self._tests = 0
        self._batch_id = None
        self._sample_alerted = False
        self._apply_state("idle")
        self._refresh_all()
        self._log("Готово к новой партии")

    def _reset(self):
        self._apply_state("idle")
        self._refresh_all()
        self.alert.clear()
        self._log("Ошибка сброшена. Система готова.")

    # ─── Имитация ─────────────────────────────────────────
    def _start_simulation(self):
        if self._simulate_timer is not None:
            return
        self._simulate_timer = QTimer(self)
        self._simulate_timer.timeout.connect(self._tick)
        self._simulate_timer.start(700)

    def _stop_simulation(self):
        if self._simulate_timer is not None:
            self._simulate_timer.stop()
            self._simulate_timer = None

    def _tick(self):
        # Прогресс
        self._progress = min(100, self._progress + 1)

        # Партии в работе — пропорционально прогрессу
        self._batches = min(
            self.TOTAL_BATCHES,
            max(1, int(self._progress / 10) + 1)
        )

        # Образцы — постепенно растут
        if self._samples < 9 and random.random() < 0.4:
            self._samples += 1

        # Тесты — пропорционально прогрессу
        self._tests = int(self.TOTAL_TESTS * (self._progress / 100.0))
        self._tests = min(self._tests, self.TOTAL_TESTS)

        self._refresh_all()

        # Случайное отклонение (один раз за партию)
        if (30 <= self._progress <= 65
                and not self._sample_alerted
                and random.random() < 0.05):
            self._sample_alerted = True
            self._trigger_deviation()
            return

        # Завершение
        if self._progress >= 100:
            self._stop_simulation()
            self._tests = self.TOTAL_TESTS
            self._refresh_all()
            self._apply_state("done")
            self._log("Партия завершена успешно", "done")
            return

    def _trigger_deviation(self):
        self._stop_simulation()
        self._apply_state("alert")
        self.alert.show_alert(
            "Отклонение в образце #A-0421",
            "pH = 4.2 (норма 6.5–7.5) · Партия #1287 · Отклонение −35%"
        )
        self._log("⚠ Отклонение: образец #A-0421 (pH = 4.2)", "warn")


# ─────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setFont(QFont(Theme.FONT_FAMILY, Theme.FONT_SIZE))
    window = LabHMI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()