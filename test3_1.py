import sys
import random
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QProgressBar, QListWidget,
    QListWidgetItem, QDialog, QGraphicsDropShadowEffect,
    QTabWidget, QSlider, QLineEdit, QPlainTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QShortcut, QKeySequence


# ─────────────────────────────────────────────────────────────
# Дизайн-система
# ─────────────────────────────────────────────────────────────
class Theme:
    BG          = "#F5F6F8"
    PANEL       = "#FFFFFF"
    PANEL_ALT   = "#EEF0F3"
    BORDER      = "#D5D9DF"
    BORDER_HARD = "#B8BEC7"

    TEXT        = "#111827"
    TEXT_DIM    = "#4B5563"
    TEXT_MUTED  = "#6B7280"

    ACCENT      = "#2563EB"
    ACCENT_DARK = "#1D4ED8"

    IDLE    = "#6B7280"
    OK      = "#16A34A"
    WARN    = "#D97706"
    ERR     = "#DC2626"
    LINK    = "#EA580C"

    FONT_FAMILY = "Segoe UI"
    FONT_SIZE   = 15
    FONT_HERO   = 32


def apply_shadow(widget, blur=14, offset_y=2, alpha=25):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, offset_y)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)


def darken(hex_color, factor=115):
    return QColor(hex_color).darker(factor).name()


# ─────────────────────────────────────────────────────────────
# ModalDialog — собственный диалог
# ─────────────────────────────────────────────────────────────
class ModalDialog(QDialog):
    def __init__(self, parent, title, message, kind="info",
                 yes_text="OK", no_text=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedWidth(460)
        self.setStyleSheet(f"QDialog {{ background: {Theme.PANEL}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 24)
        layout.setSpacing(18)

        color_map = {
            "info": Theme.ACCENT, "warn": Theme.WARN,
            "err": Theme.ERR, "question": Theme.ACCENT,
        }
        color = color_map.get(kind, Theme.ACCENT)

        title_label = QLabel(title)
        title_label.setFont(QFont(Theme.FONT_FAMILY, 17, QFont.Bold))
        title_label.setStyleSheet(f"color: {Theme.TEXT};")

        bar = QFrame()
        bar.setFixedHeight(3)
        bar.setStyleSheet(f"background: {color}; border-radius: 2px;")

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 15px; line-height: 22px;"
        )

        btns = QHBoxLayout()
        btns.addStretch()

        if no_text:
            no_btn = self._btn(no_text, secondary=True)
            no_btn.clicked.connect(self.reject)
            btns.addWidget(no_btn)

        yes_btn = self._btn(yes_text, color=color)
        yes_btn.clicked.connect(self.accept)
        btns.addWidget(yes_btn)

        layout.addWidget(title_label)
        layout.addWidget(bar)
        layout.addWidget(msg_label)
        layout.addLayout(btns)

    def _btn(self, text, color=None, secondary=False):
        btn = QPushButton(text)
        btn.setFixedHeight(44)
        btn.setMinimumWidth(120)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFont(QFont(Theme.FONT_FAMILY, 12, QFont.DemiBold))

        if secondary:
            btn.setStyleSheet(f"""
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
            btn.setStyleSheet(f"""
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
        return btn


class HelpDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Справка")
        self.setModal(True)
        self.setFixedSize(580, 560)
        self.setStyleSheet(f"QDialog {{ background: {Theme.PANEL}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(16)

        title = QLabel("Справка по панели управления")
        title.setFont(QFont(Theme.FONT_FAMILY, 17, QFont.Bold))
        title.setStyleSheet(f"color: {Theme.TEXT};")

        content = QLabel("""
<b>Вкладка «Управление»</b><br>
• <b>START</b> — запуск программы<br>
• <b>PAUSE</b> — пауза, продолжение по START<br>
• <b>STOP</b> — остановка с подтверждением<br>
• <b>E-STOP</b> — аварийный останов<br>
<br>
<b>Вкладка «Ручной режим»</b><br>
• <b>JOG</b> — перемещение осей с выбранным шагом<br>
• <b>Коррекция</b> — изменение скорости подачи и оборотов (50–150%)<br>
• <b>Покадрово (Single Block)</b> — пошаговое выполнение программы<br>
• <b>MDI</b> — ручной ввод команд G-кода<br>
<br>
<b>Состояния</b><br>
• <b>ГОТОВ</b> — станок подключён, ожидает команды<br>
• <b>РАБОТАЕТ</b> — выполняется программа<br>
• <b>ПАУЗА</b> — выполнение приостановлено<br>
• <b>АВАРИЯ</b> — требуется сброс и проверка<br>
• <b>НЕТ СВЯЗИ</b> — проверьте подключение<br>
<br>
<b>ВАЖНО:</b> кнопка E-STOP на экране — резервная.
На реальном станке обязательна физическая кнопка аварийного
останова (грибок), согласно ISO 13850.<br>
<br>
<b>Горячие клавиши</b><br>
• <b>F1</b> — справка<br>
• <b>Space</b> — Start / Pause<br>
• <b>Esc</b> — Stop<br>
• <b>F12</b> — аварийный останов
        """)
        content.setWordWrap(True)
        content.setTextFormat(Qt.RichText)
        content.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 14px; line-height: 22px;"
        )

        close_btn = QPushButton("Закрыть")
        close_btn.setFixedHeight(44)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                padding: 0 22px;
            }}
            QPushButton:hover {{ background: {Theme.ACCENT_DARK}; }}
        """)
        close_btn.clicked.connect(self.accept)

        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(close_btn)

        layout.addWidget(title)
        layout.addWidget(content)
        layout.addStretch()
        layout.addLayout(bottom)


class HistoryDialog(QDialog):
    def __init__(self, parent, events):
        super().__init__(parent)
        self.setWindowTitle("История событий")
        self.setModal(True)
        self.setFixedSize(640, 540)
        self.setStyleSheet(f"QDialog {{ background: {Theme.PANEL}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(16)

        title = QLabel("История событий")
        title.setFont(QFont(Theme.FONT_FAMILY, 17, QFont.Bold))
        title.setStyleSheet(f"color: {Theme.TEXT};")

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
            QListWidget::item {{ padding: 5px 0; }}
        """)
        for ts, msg, level in events:
            color = {"info": Theme.TEXT_DIM, "warn": Theme.WARN,
                     "err":  Theme.ERR}.get(level, Theme.TEXT)
            item = QListWidgetItem(f"{ts}   {msg}")
            item.setForeground(QColor(color))
            lst.addItem(item)

        close_btn = QPushButton("Закрыть")
        close_btn.setFixedHeight(44)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                padding: 0 22px;
            }}
            QPushButton:hover {{ background: {Theme.ACCENT_DARK}; }}
        """)
        close_btn.clicked.connect(self.accept)

        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(close_btn)

        layout.addWidget(title)
        layout.addWidget(lst)
        layout.addLayout(bottom)


# ─────────────────────────────────────────────────────────────
# 1. HEADER
# ─────────────────────────────────────────────────────────────
class HeaderBar(QFrame):
    def __init__(self, on_help):
        super().__init__()
        self.setFixedHeight(68)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL};
                border-bottom: 1px solid {Theme.BORDER};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(20)

        self.machine_name = QLabel("CNC-01 · Mazak VCN-530")
        self.machine_name.setFont(QFont(Theme.FONT_FAMILY, 14, QFont.DemiBold))
        self.machine_name.setStyleSheet(f"color: {Theme.TEXT};")

        self.connection = QLabel("● ПОДКЛЮЧЕНО")
        self.connection.setStyleSheet(
            f"color: {Theme.OK}; font-weight: 600; font-size: 13px;"
        )

        self.clock = QLabel("--:--:--")
        self.clock.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 14px;")

        help_btn = QPushButton("?")
        help_btn.setFixedSize(38, 38)
        help_btn.setCursor(Qt.PointingHandCursor)
        help_btn.setToolTip("Справка (F1)")
        help_btn.setFont(QFont(Theme.FONT_FAMILY, 15, QFont.Bold))
        help_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.PANEL_ALT};
                color: {Theme.TEXT_DIM};
                border: 1px solid {Theme.BORDER_HARD};
                border-radius: 19px;
            }}
            QPushButton:hover {{
                background: {Theme.ACCENT};
                color: white;
                border-color: {Theme.ACCENT};
            }}
        """)
        help_btn.clicked.connect(on_help)

        layout.addWidget(self.machine_name)
        layout.addSpacing(8)
        layout.addWidget(self.connection)
        layout.addStretch()
        layout.addWidget(self.clock)
        layout.addSpacing(12)
        layout.addWidget(help_btn)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)
        self._tick()

    def _tick(self):
        self.clock.setText(datetime.now().strftime("%H:%M:%S"))

    def set_connection(self, connected: bool):
        if connected:
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
# 2. STATUS CARD
# ─────────────────────────────────────────────────────────────
class StatusCard(QFrame):
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(22)

        status_row = QHBoxLayout()
        status_row.setSpacing(18)

        self.led = QLabel()
        self.led.setFixedSize(32, 32)

        self.state_label = QLabel("ГОТОВ")
        self.state_label.setFont(
            QFont(Theme.FONT_FAMILY, Theme.FONT_HERO, QFont.Bold)
        )

        status_row.addWidget(self.led)
        status_row.addWidget(self.state_label)
        status_row.addStretch()

        program_frame = QFrame()
        program_frame.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL_ALT};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
            }}
        """)
        pf_layout = QHBoxLayout(program_frame)
        pf_layout.setContentsMargins(18, 12, 18, 12)
        pf_layout.setSpacing(14)

        pf_label = QLabel("ПРОГРАММА")
        pf_label.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"font-weight: 700; letter-spacing: 1px;"
        )

        self.program_value = QLabel("не выбрана")
        self.program_value.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 15px; font-weight: 600;"
        )

        pf_layout.addWidget(pf_label)
        pf_layout.addWidget(self.program_value)
        pf_layout.addStretch()

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(44)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background: {Theme.PANEL_ALT};
                border: 1px solid {Theme.BORDER};
                border-radius: 10px;
            }}
            QProgressBar::chunk {{
                background: {Theme.ACCENT};
                border-radius: 9px;
            }}
        """)

        self.progress_label = QLabel("0%   ·   ожидание")
        self.progress_label.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 14px; font-weight: 500;"
        )

        self.hint = QLabel("Нажмите START для начала работы")
        self.hint.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 15px; font-style: italic;"
        )

        layout.addLayout(status_row)
        layout.addWidget(program_frame)
        layout.addWidget(self.progress)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.hint)

        self.set_state("idle")

    def set_state(self, state: str):
        config = {
            "idle":    ("ГОТОВ",     Theme.IDLE, "не выбрана",
                        "Нажмите START для начала работы"),
            "running": ("РАБОТАЕТ",  Theme.OK,   "part_0421.nc",
                        "Выполняется обработка. Не открывайте дверцу."),
            "paused":  ("ПАУЗА",     Theme.WARN, "part_0421.nc",
                        "Пауза оператором. Нажмите START для продолжения."),
            "paused_err": ("ПАУЗА ПО СБОЮ", Theme.WARN, "part_0421.nc",
                        "Проверьте сообщения и нажмите «СБРОС ОШИБКИ»."),
            "alarm":   ("АВАРИЯ",    Theme.ERR,  "—",
                        "Устраните причину и нажмите «СБРОС АВАРИИ»."),
            "nolink":  ("НЕТ СВЯЗИ", Theme.LINK, "—",
                        "Проверьте кабель и питание станка."),
        }
        text, color, program, hint = config.get(state, config["idle"])

        self.state_label.setText(text)
        self.state_label.setStyleSheet(f"color: {color};")
        self.led.setStyleSheet(f"background: {color}; border-radius: 16px;")
        self.program_value.setText(program if program != "—" else "не выбрана")
        self.hint.setText(hint)

    def update_progress(self, value: int, program: str):
        self.progress.setValue(value)
        self.program_value.setText(program)

        if value <= 0:
            self.progress_label.setText("0%   ·   ожидание")
        elif value >= 100:
            self.progress_label.setText("100%   ·   завершено")
        else:
            remaining_seconds = int((100 - value) * 2.5)
            mm, ss = divmod(remaining_seconds, 60)
            self.progress_label.setText(
                f"{value}%   ·   осталось ~{mm:02d}:{ss:02d}"
            )


# ─────────────────────────────────────────────────────────────
# 3. EQUIPMENT STRIP
# ─────────────────────────────────────────────────────────────
class EquipmentStrip(QFrame):
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

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 18, 28, 18)
        layout.setSpacing(36)

        title = QLabel("ОБОРУДОВАНИЕ")
        title.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"font-weight: 700; letter-spacing: 1px;"
        )
        layout.addWidget(title)
        layout.addSpacing(8)

        self.items = {}
        items = [
            ("Шпиндель",    "Главный привод станка"),
            ("Охлаждение",  "Подача смазочно-охлаждающей жидкости (СОЖ)"),
            ("Воздух",      "Давление в пневмосистеме"),
            ("Температура", "Нагрев шпинделя"),
        ]
        for name, tooltip in items:
            w = self._make_item(name, tooltip)
            layout.addWidget(w["root"])
            self.items[name] = w

        layout.addStretch()

    def _make_item(self, name, tooltip):
        root = QWidget()
        root.setToolTip(tooltip)

        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(10)

        led = QLabel()
        led.setFixedSize(12, 12)
        led.setStyleSheet(f"background: {Theme.IDLE}; border-radius: 6px;")

        label = QLabel(name)
        label.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 14px; font-weight: 500;"
        )

        value = QLabel("—")
        value.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 14px; font-weight: 700;"
        )

        h.addWidget(led)
        h.addWidget(label)
        h.addWidget(value)

        return {"root": root, "led": led, "value": value}

    def set_value(self, name, value, status="ok"):
        color_map = {
            "ok": Theme.OK, "warn": Theme.WARN,
            "err": Theme.ERR, "idle": Theme.IDLE,
        }
        color = color_map.get(status, Theme.IDLE)
        self.items[name]["led"].setStyleSheet(
            f"background: {color}; border-radius: 6px;"
        )
        self.items[name]["value"].setText(value)


# ─────────────────────────────────────────────────────────────
# 4. LAST EVENT
# ─────────────────────────────────────────────────────────────
class LastEvent(QFrame):
    def __init__(self, on_history):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL};
                border-radius: 14px;
                border: 1px solid {Theme.BORDER};
            }}
        """)
        apply_shadow(self)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 18, 28, 18)
        layout.setSpacing(18)

        self.icon = QLabel("ℹ")
        self.icon.setFont(QFont(Theme.FONT_FAMILY, 18, QFont.Bold))
        self.icon.setStyleSheet(f"color: {Theme.ACCENT};")
        self.icon.setFixedSize(28, 28)
        self.icon.setAlignment(Qt.AlignCenter)

        self.text = QLabel("HMI запущен. Ожидание команды оператора.")
        self.text.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 14px;"
        )

        history_btn = QPushButton("История")
        history_btn.setFixedHeight(38)
        history_btn.setCursor(Qt.PointingHandCursor)
        history_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.PANEL_ALT};
                color: {Theme.TEXT_DIM};
                border: 1px solid {Theme.BORDER_HARD};
                border-radius: 8px;
                padding: 0 18px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {Theme.ACCENT};
                color: white;
                border-color: {Theme.ACCENT};
            }}
        """)
        history_btn.clicked.connect(on_history)

        layout.addWidget(self.icon)
        layout.addWidget(self.text, 1)
        layout.addWidget(history_btn)

    def set_text(self, text, level="info"):
        color = {"info": Theme.TEXT_DIM, "warn": Theme.WARN,
                 "err":  Theme.ERR}.get(level, Theme.TEXT_DIM)
        icon_color = {"info": Theme.ACCENT, "warn": Theme.WARN,
                      "err":  Theme.ERR}.get(level, Theme.ACCENT)
        icon_char = {"info": "ℹ", "warn": "⚠", "err": "✕"}.get(level, "ℹ")

        self.text.setText(text)
        self.text.setStyleSheet(f"color: {color}; font-size: 14px;")
        self.icon.setText(icon_char)
        self.icon.setStyleSheet(f"color: {icon_color};")


# ─────────────────────────────────────────────────────────────
# 5. MANUAL MODE PANEL
# ─────────────────────────────────────────────────────────────
class ManualModePanel(QWidget):
    def __init__(self, on_action):
        super().__init__()
        self.on_action = on_action
        self._jog_step = 0.1
        self._coords = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        self._last_slider_pair = None
        self._base_feed = 500      # мм/мин базовая подача
        self._base_rpm = 8500      # об/мин базовые обороты

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        layout.addWidget(self._build_jog_panel(), 5)

        right = QVBoxLayout()
        right.setSpacing(16)
        right.addWidget(self._build_override_panel(), 3)
        right.addWidget(self._build_switches_panel())
        right.addWidget(self._build_mdi_panel(), 5)
        layout.addLayout(right, 4)

    # ─── JOG ─────────────────────────────────────────────
    def _build_jog_panel(self):
        card = self._card("ПЕРЕМЕЩЕНИЕ ОСЕЙ (JOG)")

        step_row = QHBoxLayout()
        step_row.setSpacing(6)
        step_label = QLabel("Шаг:")
        step_label.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 14px;"
        )
        step_row.addWidget(step_label)

        self.step_buttons = []
        for step, text in [(0.01, "0.01"), (0.1, "0.1"),
                           (1.0, "1 мм"), (10.0, "10 мм")]:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedSize(84, 40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setChecked(step == 0.1)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.PANEL_ALT};
                    color: {Theme.TEXT_DIM};
                    border: 1px solid {Theme.BORDER_HARD};
                    border-radius: 6px;
                    font-size: 13px;
                }}
                QPushButton:checked {{
                    background: {Theme.ACCENT};
                    color: white;
                    font-weight: 600;
                    border-color: {Theme.ACCENT};
                }}
            """)
            btn.clicked.connect(lambda _, s=step: self._set_step(s))
            self.step_buttons.append(btn)
            step_row.addWidget(btn)

        step_row.addStretch()
        card.layout().addLayout(step_row)
        card.layout().addSpacing(14)

        # Сетка JOG — вертикальные колонки по осям
        grid = QWidget()
        gl = QHBoxLayout(grid)
        gl.setContentsMargins(0, 0, 0, 0)
        gl.setSpacing(24)
        gl.addStretch()
        for axis in ["X", "Y", "Z"]:
            gl.addWidget(self._axis_column(axis))
        gl.addStretch()
        card.layout().addWidget(grid)

        card.layout().addSpacing(20)

        # Координаты
        coords_frame = QFrame()
        coords_frame.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL_ALT};
                border: 1px solid {Theme.BORDER};
                border-radius: 10px;
            }}
        """)
        cf_layout = QHBoxLayout(coords_frame)
        cf_layout.setContentsMargins(24, 18, 24, 18)
        cf_layout.setSpacing(32)

        self.coord_labels = {}
        for axis in ["X", "Y", "Z"]:
            lbl = QLabel(f"{axis}:  {self._coords[axis]:>8.3f}")
            lbl.setStyleSheet(
                f"color: {Theme.TEXT}; font-family: 'Consolas', monospace; "
                f"font-size: 22px; font-weight: 700;"
            )
            self.coord_labels[axis] = lbl
            cf_layout.addWidget(lbl)
        cf_layout.addStretch()
        card.layout().addWidget(coords_frame)
        card.layout().addStretch()

        return card

    def _axis_column(self, axis):
        col = QWidget()
        v = QVBoxLayout(col)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(10)

        plus = self._jog_btn(f"{axis} +")
        plus.clicked.connect(lambda: self._jog(axis, +1))

        label = QLabel(axis)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 20px; "
            f"font-weight: 700; letter-spacing: 1px;"
        )

        minus = self._jog_btn(f"{axis} −")
        minus.clicked.connect(lambda: self._jog(axis, -1))

        v.addWidget(plus)
        v.addWidget(label)
        v.addWidget(minus)
        return col

    def _jog_btn(self, text):
        btn = QPushButton(text)
        btn.setFixedSize(140, 82)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFont(QFont(Theme.FONT_FAMILY, 16, QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.PANEL};
                color: {Theme.TEXT};
                border: 2px solid {Theme.BORDER_HARD};
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background: {Theme.ACCENT};
                color: white;
                border-color: {Theme.ACCENT};
            }}
            QPushButton:pressed {{
                background: {Theme.ACCENT_DARK};
                color: white;
            }}
        """)
        return btn

    def _set_step(self, step):
        self._jog_step = step
        for btn, s in zip(self.step_buttons, [0.01, 0.1, 1.0, 10.0]):
            btn.setChecked(s == step)

    def _jog(self, axis, direction):
        delta = self._jog_step * direction
        self._coords[axis] += delta
        self.coord_labels[axis].setText(
            f"{axis}:  {self._coords[axis]:>8.3f}"
        )
        self.on_action("jog", {
            "axis": axis, "delta": delta, "step": self._jog_step
        })

    # ─── Override ────────────────────────────────────────
    def _build_override_panel(self):
        card = self._card("КОРРЕКЦИЯ РЕЖИМОВ")

        card.layout().addWidget(
            self._slider_row("Подача (Feed)", 100,
                             unit_fn=lambda v: f"≈ {int(self._base_feed * v / 100)} мм/мин")
        )
        self.feed_slider, self.feed_value, self.feed_unit = self._last_slider_pair
        card.layout().addSpacing(8)

        card.layout().addWidget(
            self._slider_row("Шпиндель", 100,
                             unit_fn=lambda v: f"≈ {int(self._base_rpm * v / 100)} об/мин")
        )
        self.spindle_slider, self.spindle_value, self.spindle_unit = self._last_slider_pair

        return card

    def _slider_row(self, label_text, initial, unit_fn=None):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        head = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 14px;")
        val = QLabel(f"{initial}%")
        val.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 14px; font-weight: 700;"
        )
        head.addWidget(lbl)
        head.addStretch()
        head.addWidget(val)
        v.addLayout(head)

        # Единицы измерения
        unit_label = QLabel(unit_fn(initial) if unit_fn else "")
        unit_label.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; font-style: italic;"
        )
        v.addWidget(unit_label)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(50, 150)
        slider.setValue(initial)
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 8px;
                background: {Theme.PANEL_ALT};
                border-radius: 4px;
            }}
            QSlider::sub-page:horizontal {{
                background: {Theme.ACCENT};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {Theme.ACCENT};
                width: 22px;
                margin: -8px 0;
                border-radius: 11px;
                border: 2px solid white;
            }}
        """)
        slider.valueChanged.connect(lambda v: val.setText(f"{v}%"))
        if unit_fn:
            slider.valueChanged.connect(lambda v: unit_label.setText(unit_fn(v)))
        slider.valueChanged.connect(
            lambda v, name=label_text: self.on_action(
                "override", {"name": name, "value": v}
            )
        )
        v.addWidget(slider)

        self._last_slider_pair = (slider, val, unit_label)
        return w

    # ─── Покадрово ───────────────────────────────────────
    def _build_switches_panel(self):
        card = self._card("РЕЖИМ ОТЛАДКИ")

        self.single_block_btn = QPushButton("Покадрово (Single Block): ВЫКЛ")
        self.single_block_btn.setCheckable(True)
        self.single_block_btn.setFixedHeight(52)
        self.single_block_btn.setCursor(Qt.PointingHandCursor)
        self.single_block_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.PANEL_ALT};
                color: {Theme.TEXT_DIM};
                border: 1px solid {Theme.BORDER_HARD};
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 16px;
            }}
            QPushButton:checked {{
                background: {Theme.ACCENT};
                color: white;
                border-color: {Theme.ACCENT};
            }}
        """)
        self.single_block_btn.toggled.connect(self._toggle_single_block)
        card.layout().addWidget(self.single_block_btn)
        self.single_block_btn.setToolTip(
            "Пошаговое выполнение программы.\n"
            "Каждый кадр выполняется по отдельной команде."
        )

        return card

    def _toggle_single_block(self, checked):
        self.single_block_btn.setText(
            f"Покадрово (Single Block): {'ВКЛ' if checked else 'ВЫКЛ'}"
        )
        self.on_action("single_block", {"enabled": checked})

    # ─── MDI ─────────────────────────────────────────────
    def _build_mdi_panel(self):
        card = self._card("MDI — РУЧНОЙ ВВОД КОМАНД")

        self.mdi_history = QPlainTextEdit()
        self.mdi_history.setReadOnly(True)
        self.mdi_history.setFixedHeight(140)
        self.mdi_history.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {Theme.PANEL_ALT};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                color: {Theme.TEXT_DIM};
                font-family: 'Consolas', monospace;
                font-size: 13px;
                padding: 10px;
            }}
        """)
        self.mdi_history.setPlainText(
            "История команд пуста.\n"
            "Введите G-код и нажмите «Ввод»."
        )
        card.layout().addWidget(self.mdi_history)

        examples = QLabel(
            "Примеры: G01 X100 F500 · G00 Z50 · M03 S3000 · M05"
        )
        examples.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"font-style: italic;"
        )
        card.layout().addWidget(examples)

        card.layout().addSpacing(4)

        self.mdi_input = QLineEdit()
        self.mdi_input.setPlaceholderText("Введите команду…")
        self.mdi_input.setFixedHeight(48)
        self.mdi_input.setStyleSheet(f"""
            QLineEdit {{
                background: {Theme.PANEL};
                color: {Theme.TEXT};
                border: 2px solid {Theme.BORDER_HARD};
                border-radius: 8px;
                padding: 0 14px;
                font-family: 'Consolas', monospace;
                font-size: 15px;
            }}
            QLineEdit:focus {{
                border-color: {Theme.ACCENT};
            }}
        """)
        self.mdi_input.returnPressed.connect(self._execute_mdi)
        card.layout().addWidget(self.mdi_input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        exec_btn = QPushButton("Ввод")
        exec_btn.setFixedHeight(46)
        exec_btn.setMinimumWidth(140)
        exec_btn.setCursor(Qt.PointingHandCursor)
        exec_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 22px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: {Theme.ACCENT_DARK}; }}
        """)
        exec_btn.clicked.connect(self._execute_mdi)

        btn_row.addWidget(exec_btn)
        card.layout().addLayout(btn_row)

        return card

    def _execute_mdi(self):
        cmd = self.mdi_input.text().strip()
        if not cmd:
            return
        self.mdi_input.clear()
        allowed = set("GMXYZSFIJKRT0123456789.- ")
        bad = [ch for ch in cmd if ch.upper() not in allowed]
        if bad:
            self._append_mdi(
                f"✕ Команда отклонена\n   Недопустимые символы: {' '.join(bad)}",
                error=True
            )
            self.on_action("mdi_error", {"command": cmd, "reason": "bad_chars"})
            return
        self._append_mdi(f"✓ Команда принята\n   {cmd}")
        self.on_action("mdi", {"command": cmd})

    def _append_mdi(self, text, error=False):
        current = self.mdi_history.toPlainText()
        if ("История команд пуста" in current
                or "История команд очищена" in current):
            current = ""
        current = current + ("\n\n" if current else "") + text
        blocks = current.split("\n\n")
        if len(blocks) > 5:
            blocks = blocks[-5:]
        self.mdi_history.setPlainText("\n\n".join(blocks))
        self.mdi_history.verticalScrollBar().setValue(
            self.mdi_history.verticalScrollBar().maximum()
        )

    # ─── Карточка ────────────────────────────────────────
    def _card(self, title_text):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL};
                border-radius: 14px;
                border: 1px solid {Theme.BORDER};
            }}
        """)
        apply_shadow(card)

        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(12)

        title = QLabel(title_text)
        title.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"font-weight: 700; letter-spacing: 1.2px;"
        )
        v.addWidget(title)

        return card

    def set_enabled_for_state(self, state):
        """В ручном режиме блокируем редактирование при работе."""
        editable = state in ("idle", "paused", "paused_err")
        for w in self.findChildren(QPushButton):
            w.setEnabled(editable)
        for w in self.findChildren(QSlider):
            w.setEnabled(editable)
        for w in self.findChildren(QLineEdit):
            w.setEnabled(editable)


# ─────────────────────────────────────────────────────────────
# 6. CONTROL BAR — глобальные кнопки
# ─────────────────────────────────────────────────────────────
class ControlBar(QFrame):
    def __init__(self, on_action):
        super().__init__()
        self.on_action = on_action
        self.setFixedHeight(124)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL};
                border-top: 1px solid {Theme.BORDER};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 22, 32, 22)
        layout.setSpacing(14)

        layout.addStretch()

        # Глобальные кнопки управления
        self.btn_pause = self._action_btn("PAUSE", Theme.WARN, 160)
        self.btn_start = self._action_btn("START", Theme.OK, 180)
        self.btn_stop  = self._action_btn("STOP",  Theme.ERR, 160)
        self.btn_reset_err = self._secondary_action_btn("СБРОС ОШИБКИ")
        self.btn_reset_alarm = self._action_btn("СБРОС АВАРИИ", Theme.ACCENT, 200)
        self.btn_reset_err.hide()
        self.btn_reset_alarm.hide()

        self.btn_start.clicked.connect(lambda: self.on_action("start"))
        self.btn_pause.clicked.connect(lambda: self.on_action("pause"))
        self.btn_stop.clicked.connect(lambda: self.on_action("stop"))
        self.btn_reset_err.clicked.connect(lambda: self.on_action("reset_error"))
        self.btn_reset_alarm.clicked.connect(lambda: self.on_action("reset_alarm"))

        layout.addWidget(self.btn_pause)
        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)
        layout.addWidget(self.btn_reset_err)
        layout.addWidget(self.btn_reset_alarm)

        layout.addStretch()

        # Разделители вокруг E-STOP
        sep_l = QFrame()
        sep_l.setFixedWidth(2)
        sep_l.setStyleSheet(f"background: {Theme.BORDER_HARD};")
        layout.addSpacing(10)
        layout.addWidget(sep_l)
        layout.addSpacing(10)

        # E-STOP — крупнее, с двойной рамкой
        self.btn_estop = QPushButton("E-STOP")
        self.btn_estop.setFixedSize(220, 80)
        self.btn_estop.setCursor(Qt.PointingHandCursor)
        self.btn_estop.setFont(QFont(Theme.FONT_FAMILY, 20, QFont.Bold))
        self.btn_estop.setToolTip(
            "Аварийный останов (F12).\n\n"
            "ВНИМАНИЕ: на реальном станке обязательна ФИЗИЧЕСКАЯ\n"
            "кнопка аварийного останова (грибок) согласно ISO 13850.\n"
            "Эта экранная кнопка — только резерв."
        )
        self.btn_estop.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ERR};
                color: white;
                border: 5px solid {darken(Theme.ERR, 130)};
                border-radius: 14px;
                letter-spacing: 3px;
            }}
            QPushButton:hover {{ background: #B91C1C; }}
            QPushButton:pressed {{ background: #991B1B; }}
            QPushButton:disabled {{
                background: {Theme.BORDER};
                color: {Theme.TEXT_MUTED};
                border-color: {Theme.BORDER_HARD};
            }}
        """)
        self.btn_estop.clicked.connect(lambda: self.on_action("estop"))
        layout.addWidget(self.btn_estop)

        sep_r = QFrame()
        sep_r.setFixedWidth(2)
        sep_r.setStyleSheet(f"background: {Theme.BORDER_HARD};")
        layout.addSpacing(10)
        layout.addWidget(sep_r)

    def _action_btn(self, text, color, width):
        btn = QPushButton(text)
        btn.setFixedSize(width, 80)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFont(QFont(Theme.FONT_FAMILY, 16, QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.PANEL};
                color: {color};
                border: 3px solid {color};
                border-radius: 12px;
                letter-spacing: 1px;
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
        return btn

    def _secondary_action_btn(self, text):
        btn = QPushButton(text)
        btn.setFixedHeight(80)
        btn.setMinimumWidth(180)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFont(QFont(Theme.FONT_FAMILY, 14, QFont.DemiBold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.PANEL_ALT};
                color: {Theme.TEXT_DIM};
                border: 2px solid {Theme.BORDER_HARD};
                border-radius: 12px;
                padding: 0 18px;
            }}
            QPushButton:hover {{
                background: {Theme.PANEL};
                color: {Theme.TEXT};
                border-color: {Theme.ACCENT};
            }}
        """)
        return btn

    def apply_state(self, state: str):
        """
        ВАЖНО: STOP и PAUSE всегда активны, если станок движется,
        независимо от вкладки (требование безопасности).
        """
        if state == "idle":
            self.btn_start.setEnabled(True)
            self.btn_pause.setEnabled(False)
            self.btn_stop.setEnabled(False)
            self.btn_reset_err.hide()
            self.btn_reset_alarm.hide()
            self.btn_estop.setEnabled(True)

        elif state == "running":
            self.btn_start.setEnabled(False)
            self.btn_pause.setEnabled(True)
            self.btn_stop.setEnabled(True)   # всегда доступен при работе
            self.btn_reset_err.hide()
            self.btn_reset_alarm.hide()
            self.btn_estop.setEnabled(True)

        elif state == "paused":
            self.btn_start.setEnabled(True)
            self.btn_pause.setEnabled(False)
            self.btn_stop.setEnabled(True)   # можно остановить с паузы
            self.btn_reset_err.hide()
            self.btn_reset_alarm.hide()
            self.btn_estop.setEnabled(True)

        elif state == "paused_err":
            self.btn_start.setEnabled(True)
            self.btn_pause.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.btn_reset_err.show()
            self.btn_reset_alarm.hide()
            self.btn_estop.setEnabled(True)

        elif state == "alarm":
            self.btn_start.setEnabled(False)
            self.btn_pause.setEnabled(False)
            self.btn_stop.setEnabled(False)
            self.btn_reset_err.hide()
            self.btn_reset_alarm.show()
            self.btn_estop.setEnabled(False)

        elif state == "nolink":
            self.btn_start.setEnabled(False)
            self.btn_pause.setEnabled(False)
            self.btn_stop.setEnabled(False)
            self.btn_reset_err.hide()
            self.btn_reset_alarm.hide()
            self.btn_estop.setEnabled(False)


# ─────────────────────────────────────────────────────────────
# 7. ГЛАВНОЕ ОКНО
# ─────────────────────────────────────────────────────────────
class MachineHMI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC Control · HMI v4.0")
        self.resize(1440, 900)
        self._apply_theme()

        self._state = "idle"
        self._events = []
        self._simulate_timer = None
        self._progress_value = 0
        self._pause_cause = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header = HeaderBar(self._show_help)
        root.addWidget(self.header)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {Theme.BG};
            }}
            QTabBar::tab {{
                background: {Theme.PANEL};
                color: {Theme.TEXT_DIM};
                padding: 14px 32px;
                border: 1px solid {Theme.BORDER};
                border-bottom: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-size: 14px;
                font-weight: 600;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background: {Theme.BG};
                color: {Theme.ACCENT};
            }}
            QTabBar::tab:hover:!selected {{
                color: {Theme.TEXT};
            }}
        """)

        # Вкладка «Управление»
        control_tab = QWidget()
        ct_layout = QVBoxLayout(control_tab)
        ct_layout.setContentsMargins(32, 26, 32, 26)
        ct_layout.setSpacing(20)
        self.status_card = StatusCard()
        self.equipment = EquipmentStrip()
        self.last_event = LastEvent(self._show_history)
        ct_layout.addWidget(self.status_card)
        ct_layout.addWidget(self.equipment)
        ct_layout.addWidget(self.last_event)
        ct_layout.addStretch()

        # Вкладка «Ручной режим»
        manual_tab = QWidget()
        mt_layout = QVBoxLayout(manual_tab)
        mt_layout.setContentsMargins(32, 26, 32, 26)
        self.manual_panel = ManualModePanel(self._handle_action)
        mt_layout.addWidget(self.manual_panel)

        self.tabs.addTab(control_tab, "Управление")
        self.tabs.addTab(manual_tab, "Ручной режим")

        root.addWidget(self.tabs, 1)

        self.controls = ControlBar(self._handle_action)
        root.addWidget(self.controls)

        # Начальные значения оборудования
        self.equipment.set_value("Шпиндель",    "0 rpm",    "idle")
        self.equipment.set_value("Охлаждение",  "выкл",     "idle")
        self.equipment.set_value("Воздух",      "0.6 МПа",  "ok")
        self.equipment.set_value("Температура", "24 °C",    "ok")

        self._apply_state("idle")
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
        QShortcut(QKeySequence("F12"),   self, lambda: self._handle_action("estop"))

    def _shortcut_start_pause(self):
        if self._state == "running":
            self._handle_action("pause")
        elif self._state in ("idle", "paused", "paused_err"):
            self._handle_action("start")

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

    def _apply_state(self, state: str):
        self._state = state
        self.status_card.set_state(state)
        self.controls.apply_state(state)
        self.header.set_connection(state != "nolink")

        if hasattr(self, "manual_panel"):
            self.manual_panel.set_enabled_for_state(state)

    def _handle_action(self, action, payload=None):
        if action == "start":
            if self._state in ("idle", "paused", "paused_err"):
                self._start_run()
        elif action == "pause":
            if self._state == "running":
                self._pause_run_operator()
        elif action == "stop":
            if self._state in ("running", "paused", "paused_err"):
                self._stop_run()
        elif action == "estop":
            self._emergency_stop()
        elif action == "reset_alarm":
            if self._state == "alarm":
                self._reset_alarm()
        elif action == "reset_error":
            if self._state == "paused_err":
                self._reset_error()
        elif action == "jog":
            self._log(
                f"JOG {payload['axis']}: {payload['delta']:+.3f} мм "
                f"(шаг {payload['step']})", "info"
            )
        elif action == "override":
            self._log(
                f"Коррекция «{payload['name']}»: {payload['value']}%", "info"
            )
        elif action == "single_block":
            st = "включён" if payload["enabled"] else "выключен"
            self._log(f"Режим «Покадрово» {st}",
                      "warn" if payload["enabled"] else "info")
        elif action == "mdi":
            self._log(f"MDI: {payload['command']}", "info")
        elif action == "mdi_error":
            self._log(f"MDI отклонена: {payload['command']}", "err")

    def _start_run(self):
        if self._state == "paused_err":
            self._log("Восстановление после сбоя. Программа продолжена", "warn")

        self._apply_state("running")
        self.status_card.update_progress(self._progress_value, "part_0421.nc")
        self.equipment.set_value("Шпиндель",   "8500 rpm", "ok")
        self.equipment.set_value("Охлаждение", "вкл",      "ok")
        self._log("Программа part_0421.nc запущена")
        self._pause_cause = None
        self._start_simulation()

    def _pause_run_operator(self):
        self._pause_cause = "operator"
        self._stop_simulation()
        self._apply_state("paused")
        self.equipment.set_value("Шпиндель", "0 rpm", "warn")
        self._log("Пауза оператором", "warn")

    def _pause_run_fault(self):
        self._pause_cause = "fault"
        self._stop_simulation()
        self._apply_state("paused_err")
        self.equipment.set_value("Шпиндель", "0 rpm", "warn")
        self._log("Пауза по сбою: превышение нагрузки", "err")

    def _stop_run(self):
        dlg = ModalDialog(
            self,
            "Остановить программу?",
            "Текущий цикл обработки будет прерван. "
            "Заготовка может быть испорчена. Продолжить?",
            kind="warn",
            yes_text="Остановить",
            no_text="Отмена",
        )
        if dlg.exec() != QDialog.Accepted:
            return

        self._progress_value = 0
        self._apply_state("idle")
        self.status_card.update_progress(0, "—")
        self._stop_simulation()
        self.equipment.set_value("Шпиндель",   "0 rpm", "idle")
        self.equipment.set_value("Охлаждение", "выкл",  "idle")
        self._log("Программа остановлена оператором")

    def _emergency_stop(self):
        self._stop_simulation()
        self._apply_state("alarm")
        self.equipment.set_value("Шпиндель",   "0 rpm", "err")
        self.equipment.set_value("Охлаждение", "выкл",  "err")
        self._log("!!! АВАРИЙНЫЙ ОСТАНОВ !!!", "err")

        ModalDialog(
            self,
            "Аварийный останов",
            "Станок остановлен.\n\n"
            "Проверьте оборудование и нажмите «СБРОС АВАРИИ» для возврата "
            "в рабочее состояние.\n\n"
            "Внимание: на реальном станке E-STOP — физическая кнопка. "
            "Экранная кнопка является резервной.",
            kind="err",
            yes_text="Понятно",
        ).exec()

    def _reset_alarm(self):
        self._progress_value = 0
        self._apply_state("idle")
        self.status_card.update_progress(0, "—")
        self.equipment.set_value("Шпиндель",   "0 rpm", "idle")
        self.equipment.set_value("Охлаждение", "выкл",  "idle")
        self._log("Авария сброшена. Станок готов к работе.")

    def _reset_error(self):
        self._pause_cause = None
        self._apply_state("paused")
        self.equipment.set_value("Шпиндель", "0 rpm", "warn")
        self._log("Ошибка сброшена. Можно продолжить программу по START.")

    def _start_simulation(self):
        if self._simulate_timer is not None:
            return
        self._simulate_timer = QTimer(self)
        self._simulate_timer.timeout.connect(self._tick_simulation)
        self._simulate_timer.start(500)

    def _stop_simulation(self):
        if self._simulate_timer is not None:
            self._simulate_timer.stop()
            self._simulate_timer = None

    def _tick_simulation(self):
        self._progress_value = min(100, self._progress_value + 1)
        self.status_card.update_progress(self._progress_value, "part_0421.nc")

        rpm = int(8500 + random.uniform(-250, 250))
        self.equipment.set_value("Шпиндель", f"{rpm} rpm", "ok")

        temp = 24 + self._progress_value * 0.08
        status = "ok" if temp < 60 else "warn" if temp < 80 else "err"
        self.equipment.set_value("Температура", f"{temp:.1f} °C", status)

        if self._progress_value == 40 and random.random() < 0.15:
            self._pause_run_fault()
            return

        if self._progress_value >= 100:
            self._stop_simulation()
            self._apply_state("idle")
            self.status_card.update_progress(0, "—")
            self.equipment.set_value("Шпиндель",   "0 rpm", "idle")
            self.equipment.set_value("Охлаждение", "выкл",  "idle")
            self.equipment.set_value("Температура", "24 °C", "ok")
            self._log("Программа завершена успешно")


# ─────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setFont(QFont(Theme.FONT_FAMILY, Theme.FONT_SIZE))
    window = MachineHMI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()