import sys
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QProgressBar, QListWidget,
    QListWidgetItem, QDialog, QGraphicsDropShadowEffect, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QShortcut, QKeySequence


# ─────────────────────────────────────────────────────────────
# Дизайн-система
# ─────────────────────────────────────────────────────────────
class Theme:
    BG          = "#F5F7FA"
    PANEL       = "#FFFFFF"
    PANEL_ALT   = "#EDF1F7"
    PANEL_INFO  = "#EAF3FF"
    BORDER      = "#DCE2EB"
    BORDER_HARD = "#BCC5D1"

    TEXT        = "#0F172A"
    TEXT_DIM    = "#475569"
    TEXT_MUTED  = "#94A3B8"

    ACCENT      = "#1E40AF"
    ACCENT_DARK = "#1E3A8A"
    ACCENT_SOFT = "#DBEAFE"

    OK      = "#15803D"
    OK_SOFT = "#DCFCE7"
    WARN    = "#C2410C"
    WARN_SOFT = "#FFEDD5"
    ERR     = "#B91C1C"
    ERR_SOFT = "#FEE2E2"
    IDLE    = "#64748B"

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


def supply_color(percent):
    """
    Динамический цвет по уровню расхода.
    > 50%  — зелёный
    20-50% — янтарный
    < 20%  — красный
    """
    if percent < 20:
        return Theme.ERR, "Критически мало"
    if percent < 50:
        return Theme.WARN, "Заканчивается"
    return Theme.OK, "Норма"


# ─────────────────────────────────────────────────────────────
# ModalDialog
# ─────────────────────────────────────────────────────────────
class ModalDialog(QDialog):
    def __init__(self, parent, title, message, kind="info",
                 yes_text="OK", no_text=None, width=520):
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
# Диалог очереди печати (с удалением задач)
# ─────────────────────────────────────────────────────────────
class QueueDialog(QDialog):
    def __init__(self, parent, printer_name, tasks):
        super().__init__(parent)
        self.setWindowTitle(f"Очередь печати · {printer_name}")
        self.setModal(True)
        self.setFixedSize(640, 500)
        self.setStyleSheet(f"QDialog {{ background: {Theme.PANEL}; }}")

        self.tasks = list(tasks)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(16)

        t = QLabel(f"Очередь печати: {printer_name}")
        t.setFont(QFont(Theme.FONT_FAMILY, 17, QFont.Bold))
        t.setStyleSheet(f"color: {Theme.TEXT};")

        self.sub = QLabel("")
        self.sub.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 13px;"
        )

        # Контейнер задач
        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {Theme.PANEL_ALT};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.BORDER_HARD};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        scroll.setWidget(self.tasks_container)

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
        close_btn.clicked.connect(self.accept)

        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(close_btn)

        layout.addWidget(t)
        layout.addWidget(self.sub)
        layout.addWidget(scroll, 1)
        layout.addLayout(bottom)

        self._rebuild()

    def _rebuild(self):
        while self.tasks_layout.count():
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.tasks:
            empty = QLabel("Очередь пуста")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                f"color: {Theme.TEXT_MUTED}; font-size: 14px; "
                f"font-style: italic; padding: 40px 0;"
            )
            self.tasks_layout.addWidget(empty)
            self.sub.setText("Нет активных задач")
            return

        self.sub.setText(
            f"{len(self.tasks)} задач в очереди. Нажмите «Отменить», "
            "чтобы удалить задачу."
        )

        for task in self.tasks:
            self.tasks_layout.addWidget(self._make_row(task))

        self.tasks_layout.addStretch()

    def _make_row(self, task):
        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
            }}
        """)
        h = QHBoxLayout(row)
        h.setContentsMargins(16, 12, 16, 12)
        h.setSpacing(14)

        icon = QLabel("📄")
        icon.setFont(QFont(Theme.FONT_FAMILY, 18))
        icon.setFixedSize(32, 32)

        info = QVBoxLayout()
        info.setSpacing(2)
        name = QLabel(task["name"])
        name.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 14px; font-weight: 600;"
        )
        detail = QLabel(f"{task['pages']} стр. · от {task['user']}")
        detail.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px;"
        )
        info.addWidget(name)
        info.addWidget(detail)

        status = QLabel(task["status"])
        status.setStyleSheet(
            f"color: {task['status_color']}; "
            f"font-size: 13px; font-weight: 600;"
        )

        cancel_btn = QPushButton("Отменить")
        cancel_btn.setFixedHeight(34)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.ERR};
                border: 1px solid {Theme.ERR};
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background: {Theme.ERR_SOFT}; }}
        """)
        cancel_btn.clicked.connect(lambda _, t=task: self._cancel_task(t))

        h.addWidget(icon)
        h.addLayout(info, 1)
        h.addWidget(status)
        h.addWidget(cancel_btn)

        return row

    def _cancel_task(self, task):
        dlg = ModalDialog(
            self,
            "Отменить задачу?",
            f"Задача «{task['name']}» будет удалена из очереди печати. "
            "Продолжить?",
            kind="warn",
            yes_text="Отменить задачу",
            no_text="Оставить",
        )
        if dlg.exec() == QDialog.Accepted:
            self.tasks = [t for t in self.tasks if t is not task]
            self._rebuild()


# ─────────────────────────────────────────────────────────────
# Диалог диагностики — РАЗНЫЙ для разных статусов
# ─────────────────────────────────────────────────────────────
class DiagnosticsDialog(QDialog):
    def __init__(self, parent, printer_name, status_text):
        super().__init__(parent)
        self.setWindowTitle(f"Диагностика · {printer_name}")
        self.setModal(True)
        self.setFixedSize(580, 480)
        self.setStyleSheet(f"QDialog {{ background: {Theme.PANEL}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(16)

        t = QLabel(f"Состояние: {printer_name}")
        t.setFont(QFont(Theme.FONT_FAMILY, 17, QFont.Bold))
        t.setStyleSheet(f"color: {Theme.TEXT};")

        # Разные данные по статусу
        config = {
            "Занят": {
                "color": Theme.WARN,
                "led": Theme.WARN,
                "status": "Принтер выполняет задание",
                "cause": (
                    "<b>Причина:</b> принтер печатает документ, "
                    "отправленный пользователем <b>ivanov@company.ru</b>.<br><br>"
                    "<b>Задание:</b> Отчёт_Q3_2024.pdf<br>"
                    "<b>Страниц:</b> 24<br>"
                    "<b>Осталось:</b> ~3 мин"
                ),
                "actions": [
                    ("Встать в очередь", "Задание будет напечатано после текущего"),
                    ("Выбрать другой принтер", "Открыть список доступных устройств"),
                    ("Уведомить о завершении", "Получить уведомление, когда принтер освободится"),
                ],
            },
            "Не в сети": {
                "color": Theme.IDLE,
                "led": Theme.IDLE,
                "status": "Принтер недоступен",
                "cause": (
                    "<b>Причина:</b> принтер не отвечает в сети.<br>"
                    "Последний отклик: 14:12 (20 минут назад).<br><br>"
                    "<b>Возможные причины:</b><br>"
                    "• Принтер выключен<br>"
                    "• Проблема с кабелем питания<br>"
                    "• Потеря Wi-Fi соединения<br>"
                    "• Неисправен сетевой порт"
                ),
                "actions": [
                    ("Проверить питание", "Убедитесь, что индикатор горит зелёным"),
                    ("Проверить кабель", "Плотно подключите Ethernet-кабель"),
                    ("Обратиться к технику", "Если проблема сохраняется 5+ минут"),
                ],
            },
            "Ошибка": {
                "color": Theme.ERR,
                "led": Theme.ERR,
                "status": "Ошибка принтера",
                "cause": (
                    "<b>Код ошибки:</b> E-042<br>"
                    "<b>Описание:</b> замятие бумаги в заднем лотке.<br><br>"
                    "<b>Что делать:</b> откройте заднюю крышку, "
                    "извлеките лист, закройте крышку."
                ),
                "actions": [
                    ("Пошаговая инструкция", "Откроется с 4 шагами"),
                    ("Уведомить техника", "Он получит уведомление с кодом ошибки"),
                ],
            },
        }

        cfg = config.get(status_text, config["Занят"])

        # Статус
        status_row = QHBoxLayout()
        led = QLabel()
        led.setFixedSize(14, 14)
        led.setStyleSheet(f"background: {cfg['led']}; border-radius: 7px;")

        status_lbl = QLabel(cfg["status"])
        status_lbl.setStyleSheet(
            f"color: {cfg['color']}; font-size: 15px; font-weight: 700;"
        )
        status_row.addWidget(led)
        status_row.addWidget(status_lbl)
        status_row.addStretch()

        # Причина
        cause = QLabel(cfg["cause"])
        cause.setWordWrap(True)
        cause.setTextFormat(Qt.RichText)
        cause.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 14px; line-height: 22px;"
        )

        # Заголовок действий
        actions_title = QLabel("ДОСТУПНЫЕ ДЕЙСТВИЯ")
        actions_title.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"font-weight: 700; letter-spacing: 1.2px;"
        )

        actions = QVBoxLayout()
        actions.setSpacing(8)

        for text, desc in cfg["actions"]:
            row = QFrame()
            row.setStyleSheet(f"""
                QFrame {{
                    background: {Theme.PANEL_ALT};
                    border: 1px solid {Theme.BORDER};
                    border-radius: 8px;
                }}
            """)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(16, 12, 16, 12)
            rl.setSpacing(12)

            text_box = QVBoxLayout()
            text_box.setSpacing(2)
            n = QLabel(text)
            n.setStyleSheet(
                f"color: {Theme.TEXT}; font-size: 14px; font-weight: 600;"
            )
            d = QLabel(desc)
            d.setStyleSheet(
                f"color: {Theme.TEXT_MUTED}; font-size: 12px;"
            )
            text_box.addWidget(n)
            text_box.addWidget(d)

            arrow = QLabel("→")
            arrow.setStyleSheet(
                f"color: {Theme.ACCENT}; font-size: 16px; font-weight: bold;"
            )

            rl.addLayout(text_box, 1)
            rl.addWidget(arrow)

            actions.addWidget(row)

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
        close_btn.clicked.connect(self.accept)

        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(close_btn)

        layout.addWidget(t)
        layout.addLayout(status_row)
        layout.addWidget(cause)
        layout.addSpacing(4)
        layout.addWidget(actions_title)
        layout.addLayout(actions)
        layout.addStretch()
        layout.addLayout(bottom)


# ─────────────────────────────────────────────────────────────
# Справка
# ─────────────────────────────────────────────────────────────
class HelpDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Справка")
        self.setModal(True)
        self.setFixedSize(620, 540)
        self.setStyleSheet(f"QDialog {{ background: {Theme.PANEL}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(16)

        t = QLabel("Справка по подключению принтера")
        t.setFont(QFont(Theme.FONT_FAMILY, 17, QFont.Bold))
        t.setStyleSheet(f"color: {Theme.TEXT};")

        c = QLabel("""
<b>Способы подключения</b><br>
• Wi-Fi — беспроводная сеть<br>
• Ethernet — локальная сеть офиса<br>
• USB — прямое подключение кабелем<br>
<br>
<b>Master-Detail</b><br>
Слева — список принтеров. Справа — детали выбранного:<br>
имя, IP, статус, уровень бумаги и тонера.<br>
<br>
<b>Подключение</b><br>
Кнопка в правой панели меняется по контексту:<br>
• <b>Подключить</b> — если принтер не выбран как активный<br>
• <b>Отключить</b> — если уже подключён<br>
<br>
<b>Очередь печати</b><br>
Нажмите на строку «Очередь: N задач» → откроется список задач,
где можно отменить лишние.<br>
<br>
<b>Пауза очереди</b><br>
Кнопка «Пауза» → меняется на «Возобновить».
Пока очередь пуста, кнопка недоступна.<br>
<br>
<b>Диагностика</b><br>
Если принтер «Занят», «Не в сети» или «Ошибка» — рядом кнопка ℹ.
Она откроет объяснение проблемы и доступные действия.<br>
<br>
<b>Горячие клавиши</b><br>
• F1 — справка
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
# Карточка канала
# ─────────────────────────────────────────────────────────────
class ChannelCard(QFrame):
    def __init__(self, key, title, subtitle, icon_text, on_select):
        super().__init__()
        self.key = key
        self.on_select = on_select
        self._active = False

        self.setFixedHeight(88)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL};
                border: 2px solid {Theme.BORDER};
                border-radius: 12px;
            }}
            QFrame:hover {{ border-color: {Theme.ACCENT}; }}
        """)
        apply_shadow(self, blur=8, alpha=15)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(14)

        self.icon = QLabel(icon_text)
        self.icon.setFont(QFont(Theme.FONT_FAMILY, 26))
        self.icon.setFixedSize(48, 48)
        self.icon.setAlignment(Qt.AlignCenter)
        self.icon.setStyleSheet(f"""
            background: {Theme.PANEL_ALT};
            border-radius: 12px;
            color: {Theme.TEXT_DIM};
        """)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        self.title = QLabel(title)
        self.title.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 16px; font-weight: 700;"
        )
        self.subtitle = QLabel(subtitle)
        self.subtitle.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px;"
        )
        text_box.addWidget(self.title)
        text_box.addWidget(self.subtitle)

        self.check = QLabel("✓")
        self.check.setFont(QFont(Theme.FONT_FAMILY, 20, QFont.Bold))
        self.check.setFixedSize(32, 32)
        self.check.setAlignment(Qt.AlignCenter)
        self.check.setStyleSheet(f"color: {Theme.OK};")
        self.check.hide()

        layout.addWidget(self.icon)
        layout.addLayout(text_box, 1)
        layout.addWidget(self.check)

    def mousePressEvent(self, event):
        self.on_select(self.key)

    def set_active(self, active):
        self._active = active
        if active:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {Theme.PANEL};
                    border: 2px solid {Theme.ACCENT};
                    border-radius: 12px;
                }}
            """)
            self.icon.setStyleSheet(f"""
                background: {Theme.ACCENT_SOFT};
                border-radius: 12px;
                color: {Theme.ACCENT};
            """)
            self.check.show()
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {Theme.PANEL};
                    border: 2px solid {Theme.BORDER};
                    border-radius: 12px;
                }}
                QFrame:hover {{ border-color: {Theme.ACCENT}; }}
            """)
            self.icon.setStyleSheet(f"""
                background: {Theme.PANEL_ALT};
                border-radius: 12px;
                color: {Theme.TEXT_DIM};
            """)
            self.check.hide()


# ─────────────────────────────────────────────────────────────
# Карточка принтера
# ─────────────────────────────────────────────────────────────
class PrinterCard(QFrame):
    def __init__(self, printer, on_select, on_info):
        super().__init__()
        self.printer = printer
        self.on_select = on_select
        self.on_info = on_info
        self._active = False

        self.setFixedHeight(84)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 10px;
            }}
            QFrame:hover {{ border-color: {Theme.ACCENT}; }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # LED — цветной только для проблемных
        status_text = printer["status"]["text"]
        is_problem = status_text != "Готов"
        led_color = printer["status"]["color"] if is_problem else Theme.OK

        self.led = QLabel()
        self.led.setFixedSize(12, 12)
        self.led.setStyleSheet(
            f"background: {led_color}; border-radius: 6px;"
        )

        icon = QLabel("🖨")
        icon.setFont(QFont(Theme.FONT_FAMILY, 22))
        icon.setFixedSize(40, 40)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"""
            background: {Theme.PANEL_ALT};
            border-radius: 10px;
        """)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        name = QLabel(printer["name"])
        name.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 15px; font-weight: 700;"
        )
        detail = QLabel(f"{printer['model']}  ·  {printer['ip']}")
        detail.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px;"
        )
        text_box.addWidget(name)
        text_box.addWidget(detail)

        # Статус — серый для «Готов», цветной для проблемных
        if is_problem:
            status_color = printer["status"]["color"]
            status_style = "font-weight: 700;"
        else:
            status_color = Theme.TEXT_MUTED
            status_style = "font-weight: 500;"

        status_lbl = QLabel(status_text)
        status_lbl.setStyleSheet(
            f"color: {status_color}; font-size: 13px; {status_style}"
        )

        # Кнопка ℹ — только для проблемных
        info_btn = None
        if is_problem:
            info_btn = QPushButton("ℹ")
            info_btn.setFixedSize(32, 32)
            info_btn.setCursor(Qt.PointingHandCursor)
            info_btn.setToolTip(f"Подробнее: {status_text}")
            info_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Theme.WARN};
                    border: 1px solid {Theme.WARN};
                    border-radius: 16px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {Theme.WARN};
                    color: white;
                }}
            """)
            info_btn.clicked.connect(
                lambda _, p=printer: self.on_info(p["name"], p["status"]["text"])
            )

        layout.addWidget(self.led)
        layout.addWidget(icon)
        layout.addLayout(text_box, 1)
        layout.addWidget(status_lbl)
        if info_btn:
            layout.addWidget(info_btn)

    def mousePressEvent(self, event):
        if isinstance(self.childAt(event.pos()), QPushButton):
            return
        self.on_select(self.printer["name"])

    def set_active(self, active):
        self._active = active
        if active:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {Theme.ACCENT_SOFT};
                    border: 2px solid {Theme.ACCENT};
                    border-radius: 10px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {Theme.PANEL};
                    border: 1px solid {Theme.BORDER};
                    border-radius: 10px;
                }}
                QFrame:hover {{ border-color: {Theme.ACCENT}; }}
            """)


# ─────────────────────────────────────────────────────────────
# Панель деталей
# ─────────────────────────────────────────────────────────────
class PrinterDetailsPanel(QFrame):
    def __init__(self, on_connect, on_disconnect, on_queue_click,
                 on_queue_pause):
        super().__init__()
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_queue_click = on_queue_click
        self.on_queue_pause = on_queue_pause

        self._connected = False
        self._queue_paused = False
        self._queue_count = 0

        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL_INFO};
                border: 1px solid {Theme.ACCENT_SOFT};
                border-left: 4px solid {Theme.ACCENT};
                border-radius: 12px;
            }}
        """)
        apply_shadow(self, blur=20, offset_y=4, alpha=30)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        # Заголовок секции
        header_row = QHBoxLayout()
        title = QLabel("ИНФОРМАЦИЯ О ПРИНТЕРЕ")
        title.setStyleSheet(
            f"color: {Theme.ACCENT}; font-size: 11px; "
            f"font-weight: 700; letter-spacing: 1.2px;"
        )
        header_row.addWidget(title)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Имя + статус
        name_row = QHBoxLayout()
        name_row.setSpacing(14)

        self.icon = QLabel("🖨")
        self.icon.setFont(QFont(Theme.FONT_FAMILY, 30))
        self.icon.setFixedSize(56, 56)
        self.icon.setAlignment(Qt.AlignCenter)
        self.icon.setStyleSheet(f"""
            background: {Theme.PANEL};
            border-radius: 14px;
        """)

        name_box = QVBoxLayout()
        name_box.setSpacing(2)
        self.name_lbl = QLabel("—")
        self.name_lbl.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 17px; font-weight: 700;"
        )
        self.detail_lbl = QLabel("—")
        self.detail_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 13px;"
        )
        name_box.addWidget(self.name_lbl)
        name_box.addWidget(self.detail_lbl)

        name_row.addWidget(self.icon)
        name_row.addLayout(name_box, 1)
        layout.addLayout(name_row)

        # Статус принтера — просто текст
        self.status_row = QHBoxLayout()
        self.status_row.setSpacing(10)

        self.status_led = QLabel()
        self.status_led.setFixedSize(12, 12)

        self.status_lbl = QLabel("—")
        self.status_lbl.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 14px; font-weight: 600;"
        )
        self.status_row.addWidget(self.status_led)
        self.status_row.addWidget(self.status_lbl)
        self.status_row.addStretch()
        layout.addLayout(self.status_row)

        # Разделитель
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {Theme.BORDER};")
        layout.addWidget(sep)

        # Расходники
        self.paper = self._supply("Бумага", 78)
        self.toner = self._supply("Тонер", 45)
        layout.addWidget(self.paper["root"])
        layout.addWidget(self.toner["root"])

        # Разделитель
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {Theme.BORDER};")
        layout.addWidget(sep2)

        # Очередь
        queue_label = QLabel("ОЧЕРЕДЬ ПЕЧАТИ")
        queue_label.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px; "
            f"font-weight: 700; letter-spacing: 1.2px;"
        )
        layout.addWidget(queue_label)

        queue_row = QHBoxLayout()
        queue_row.setSpacing(10)

        self.queue_btn = QPushButton("Очередь пуста")
        self.queue_btn.setFixedHeight(46)
        self.queue_btn.setCursor(Qt.PointingHandCursor)
        self.queue_btn.setToolTip("Открыть список задач в очереди")
        self.queue_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.PANEL};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER_HARD};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 16px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: {Theme.ACCENT_SOFT};
                border-color: {Theme.ACCENT};
                color: {Theme.ACCENT};
            }}
            QPushButton:disabled {{
                background: {Theme.PANEL_ALT};
                color: {Theme.TEXT_MUTED};
                border-color: {Theme.BORDER};
            }}
        """)
        self.queue_btn.clicked.connect(self.on_queue_click)

        self.pause_btn = QPushButton("Пауза")
        self.pause_btn.setFixedHeight(46)
        self.pause_btn.setMinimumWidth(130)
        self.pause_btn.setCursor(Qt.PointingHandCursor)
        self._set_pause_btn_style(paused=False)
        self.pause_btn.clicked.connect(self._on_pause_click)

        queue_row.addWidget(self.queue_btn, 1)
        queue_row.addWidget(self.pause_btn)
        layout.addLayout(queue_row)

        # Разделитель
        sep3 = QFrame()
        sep3.setFixedHeight(1)
        sep3.setStyleSheet(f"background: {Theme.BORDER};")
        layout.addWidget(sep3)

        # Главная кнопка действия — ВСЕГДА видима
        self.action_hint = QLabel("")
        self.action_hint.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"font-style: italic;"
        )
        layout.addWidget(self.action_hint)

        self.action_btn = QPushButton("Подключить")
        self.action_btn.setFixedHeight(48)
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.clicked.connect(self._on_action_click)
        self._set_action_style(connected=False)
        layout.addWidget(self.action_btn)

        layout.addStretch()

        self.set_visible(False)

    def _supply(self, name, percent):
        root = QWidget()
        v = QVBoxLayout(root)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        head = QHBoxLayout()
        n = QLabel(name)
        n.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 13px; font-weight: 600;"
        )

        color, status_text = supply_color(percent)

        p = QLabel(f"{percent}%  ·  {status_text}")
        p.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: 700;"
        )
        head.addWidget(n)
        head.addStretch()
        head.addWidget(p)
        v.addLayout(head)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(percent)
        bar.setTextVisible(False)
        bar.setFixedHeight(10)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background: {Theme.PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 4px;
            }}
        """)
        v.addWidget(bar)

        return {"root": root, "bar": bar, "label": p}

    # ─── Кнопка действия ─────────────────────────────────
    def _on_action_click(self):
        if self._connected:
            self.on_disconnect()
        else:
            self.on_connect()

    def _set_action_style(self, connected):
        if connected:
            self.action_btn.setText("Отключить")
            self.action_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Theme.ERR};
                    border: 2px solid {Theme.ERR};
                    border-radius: 10px;
                    font-weight: 700;
                    font-size: 14px;
                }}
                QPushButton:hover {{ background: {Theme.ERR_SOFT}; }}
            """)
        else:
            self.action_btn.setText("Подключить")
            self.action_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.ACCENT};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-weight: 700;
                    font-size: 14px;
                }}
                QPushButton:hover {{ background: {Theme.ACCENT_DARK}; }}
            """)

    # ─── Кнопка паузы ────────────────────────────────────
    def _set_pause_btn_style(self, paused):
        if paused:
            self.pause_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.WARN};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: 700; font-size: 13px;
                    padding: 0 16px;
                }}
                QPushButton:hover {{ background: {darken(Theme.WARN)}; }}
                QPushButton:disabled {{
                    background: {Theme.PANEL_ALT};
                    color: {Theme.TEXT_MUTED};
                }}
            """)
        else:
            self.pause_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.PANEL};
                    color: {Theme.ACCENT};
                    border: 1px solid {Theme.ACCENT};
                    border-radius: 8px;
                    font-weight: 700; font-size: 13px;
                    padding: 0 16px;
                }}
                QPushButton:hover {{
                    background: {Theme.ACCENT};
                    color: white;
                }}
                QPushButton:disabled {{
                    background: {Theme.PANEL_ALT};
                    color: {Theme.TEXT_MUTED};
                    border-color: {Theme.BORDER};
                }}
            """)

    def _on_pause_click(self):
        if self._queue_count == 0:
            return
        self._queue_paused = not self._queue_paused
        self._set_pause_btn_style(paused=self._queue_paused)
        if self._queue_paused:
            self.pause_btn.setText("Возобновить")
            self._refresh_queue_label(paused=True)
        else:
            self.pause_btn.setText("Пауза")
            self._refresh_queue_label(paused=False)
        self.on_queue_pause(self._queue_paused)

    def _refresh_queue_label(self, paused=False):
        if self._queue_count == 0:
            self.queue_btn.setText("Очередь пуста")
        elif paused:
            self.queue_btn.setText(
                f"Очередь: {self._queue_count} задач  ·  ПАУЗА"
            )
            self.queue_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.WARN_SOFT};
                    color: {Theme.WARN};
                    border: 1px solid {Theme.WARN};
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 0 16px;
                    text-align: left;
                }}
            """)
        else:
            self.queue_btn.setText(
                f"Очередь: {self._queue_count} задач  ·  ~5 мин"
            )
            self.queue_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.PANEL};
                    color: {Theme.TEXT};
                    border: 1px solid {Theme.BORDER_HARD};
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 0 16px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background: {Theme.ACCENT_SOFT};
                    border-color: {Theme.ACCENT};
                    color: {Theme.ACCENT};
                }}
            """)

    # ─── Публичные методы ────────────────────────────────
    def set_visible(self, visible):
        self.setVisible(visible)

    def show_printer(self, name, model, ip, status_text, status_color,
                     queue_count):
        self.name_lbl.setText(name)
        self.detail_lbl.setText(f"{model}  ·  {ip}")

        # Статус — LED + текст
        self.status_led.setStyleSheet(
            f"background: {status_color}; border-radius: 6px;"
        )
        self.status_lbl.setText(status_text)
        self.status_lbl.setStyleSheet(
            f"color: {status_color}; font-size: 14px; font-weight: 700;"
        )

        self._queue_count = queue_count
        self._queue_paused = False
        self.pause_btn.setText("Пауза")
        self._set_pause_btn_style(paused=False)
        self._refresh_queue_label(paused=False)
        self.pause_btn.setEnabled(queue_count > 0)
        self.queue_btn.setEnabled(queue_count > 0)

        # Кнопка действия
        self._connected = False
        self._set_action_style(connected=False)
        self.action_hint.setText("")

        self.set_visible(True)

    def set_connected(self, connected, other_connected_name=None):
        """
        connected — этот принтер подключён?
        other_connected_name — имя другого подключённого принтера (если есть).
        """
        self._connected = connected
        if connected:
            self._set_action_style(connected=True)
            self.action_hint.setText("Этот принтер сейчас активен.")
        elif other_connected_name:
            self._set_action_style(connected=False)
            self.action_hint.setText(
                f"Сейчас подключено: {other_connected_name}"
            )
        else:
            self._set_action_style(connected=False)
            self.action_hint.setText("")

    def clear(self):
        self.set_visible(False)
        self._connected = False


# ─────────────────────────────────────────────────────────────
# ГЛАВНОЕ ОКНО
# ─────────────────────────────────────────────────────────────
class ConnectionsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connections · Подключение принтера")
        self.resize(1320, 880)
        self._apply_theme()

        self._active_channel = "printer"
        self._selected_printer = None
        self._connected_printer = None
        self._queue_paused = False

        self.printers = {
            "printer": [
                {"name": "HP LaserJet M404",
                 "model": "HP LaserJet M404dn",
                 "ip": "192.168.1.42",
                 "status": {"text": "Готов", "color": Theme.OK}},
                {"name": "Canon i-SENSYS",
                 "model": "Canon i-SENSYS LBP223",
                 "ip": "192.168.1.43",
                 "status": {"text": "Занят", "color": Theme.WARN}},
                {"name": "Xerox VersaLink",
                 "model": "Xerox VersaLink C405",
                 "ip": "192.168.1.44",
                 "status": {"text": "Готов", "color": Theme.OK}},
                {"name": "Kyocera Ecosys",
                 "model": "Kyocera Ecosys P2040",
                 "ip": "192.168.1.45",
                 "status": {"text": "Готов", "color": Theme.OK}},
                {"name": "Brother HL-L5100",
                 "model": "Brother HL-L5100DN",
                 "ip": "192.168.1.46",
                 "status": {"text": "Не в сети", "color": Theme.IDLE}},
            ],
            "wifi": [
                {"name": "Brother HL-L2350DW",
                 "model": "Brother HL-L2350DW",
                 "ip": "10.0.0.15",
                 "status": {"text": "Готов", "color": Theme.OK}},
                {"name": "Epson WorkForce",
                 "model": "Epson WorkForce WF-2830",
                 "ip": "10.0.0.18",
                 "status": {"text": "Готов", "color": Theme.OK}},
            ],
            "usb": [
                {"name": "HP DeskJet 2320",
                 "model": "HP DeskJet 2320 (USB)",
                 "ip": "USB001",
                 "status": {"text": "Готов", "color": Theme.OK}},
            ],
        }

        self.queue_tasks = [
            {"name": "Отчёт_Q3_2024.pdf", "pages": 24,
             "user": "ivanov", "status": "Печатается",
             "status_color": Theme.OK},
            {"name": "Договор_№412.docx", "pages": 8,
             "user": "petrova", "status": "В очереди",
             "status_color": Theme.TEXT_MUTED},
            {"name": "Презентация_клиенту.pptx", "pages": 32,
             "user": "sidorov", "status": "В очереди",
             "status_color": Theme.TEXT_MUTED},
        ]

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = self._build_header()
        root.addWidget(header)

        content = QWidget()
        content.setStyleSheet(f"background: {Theme.BG};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(32, 22, 32, 22)
        cl.setSpacing(18)

        section1 = QLabel("СПОСОБ ПОДКЛЮЧЕНИЯ")
        section1.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"font-weight: 700; letter-spacing: 1.2px;"
        )
        cl.addWidget(section1)

        channels_row = QHBoxLayout()
        channels_row.setSpacing(14)
        self.channel_cards = {}
        for key, title, subtitle, icon in [
            ("wifi", "Wi-Fi", "Беспроводная сеть", "📶"),
            ("printer", "Сеть (Ethernet)", "Локальная сеть офиса", "🌐"),
            ("usb", "USB", "Прямое подключение", "🔌"),
        ]:
            card = ChannelCard(key, title, subtitle, icon, self._select_channel)
            channels_row.addWidget(card, 1)
            self.channel_cards[key] = card
        cl.addLayout(channels_row)

        section2 = QLabel("ДОСТУПНЫЕ ПРИНТЕРЫ")
        section2.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"font-weight: 700; letter-spacing: 1.2px;"
        )
        cl.addWidget(section2)

        master_detail = QHBoxLayout()
        master_detail.setSpacing(20)

        self.list_scroll = QScrollArea()
        self.list_scroll.setWidgetResizable(True)
        self.list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {Theme.PANEL_ALT};
                width: 8px;
                border-radius: 4px;
                margin: 4px 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.BORDER_HARD};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 8, 0)
        self.list_layout.setSpacing(10)
        self.list_layout.addStretch()
        self.list_scroll.setWidget(self.list_container)

        self.details = PrinterDetailsPanel(
            on_connect=self._connect_printer,
            on_disconnect=self._disconnect_printer,
            on_queue_click=self._show_queue,
            on_queue_pause=self._on_queue_pause,
        )

        master_detail.addWidget(self.list_scroll, 3)
        master_detail.addWidget(self.details, 2)
        cl.addLayout(master_detail, 1)

        root.addWidget(content, 1)

        self._select_channel("printer")
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
        QShortcut(QKeySequence("F1"), self, self._show_help)

    def _build_header(self):
        header = QFrame()
        header.setFixedHeight(72)
        header.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL};
                border-bottom: 1px solid {Theme.BORDER};
            }}
        """)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(32, 0, 32, 0)
        hl.setSpacing(16)

        title = QLabel("Подключения")
        title.setFont(QFont(Theme.FONT_FAMILY, 18, QFont.Bold))
        title.setStyleSheet(f"color: {Theme.TEXT};")

        # Только LED — без дублирования имени
        self.connection_led = QLabel()
        self.connection_led.setFixedSize(12, 12)
        self.connection_led.setStyleSheet(
            f"background: {Theme.TEXT_MUTED}; border-radius: 6px;"
        )

        self.connection_lbl = QLabel("Не подключено")
        self.connection_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-weight: 600; font-size: 13px;"
        )

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
        hl.addSpacing(20)
        hl.addWidget(self.connection_led)
        hl.addWidget(self.connection_lbl)
        hl.addStretch()
        hl.addWidget(help_btn)

        return header

    def _select_channel(self, key):
        self._active_channel = key
        for k, card in self.channel_cards.items():
            card.set_active(k == key)
        self._refresh_printers()
        self.details.clear()
        self._selected_printer = None

    def _refresh_printers(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._printer_cards = {}
        for printer in self.printers.get(self._active_channel, []):
            card = PrinterCard(
                printer,
                on_select=self._select_printer,
                on_info=self._show_diagnostics,
            )
            self.list_layout.addWidget(card)
            self._printer_cards[printer["name"]] = card
        self.list_layout.addStretch()

    def _select_printer(self, name):
        self._selected_printer = name
        for n, card in self._printer_cards.items():
            card.set_active(n == name)

        printer = next(
            (p for p in self.printers[self._active_channel]
             if p["name"] == name), None
        )
        if printer:
            queue_count = len(self.queue_tasks) if self._connected_printer == name else 0
            self.details.show_printer(
                printer["name"], printer["model"], printer["ip"],
                printer["status"]["text"], printer["status"]["color"],
                queue_count,
            )
            # Синхронизируем состояние
            if self._connected_printer == name:
                self.details.set_connected(True)
            elif self._connected_printer:
                self.details.set_connected(
                    False, other_connected_name=self._connected_printer
                )
            else:
                self.details.set_connected(False)

    def _show_diagnostics(self, printer_name, status_text):
        DiagnosticsDialog(self, printer_name, status_text).exec()

    def _show_queue(self):
        if not self._selected_printer:
            return
        QueueDialog(self, self._selected_printer, self.queue_tasks).exec()

    def _on_queue_pause(self, paused):
        self._queue_paused = paused

    def _connect_printer(self):
        if not self._selected_printer:
            return
        self._connected_printer = self._selected_printer
        self.details.set_connected(True)
        self.connection_led.setStyleSheet(
            f"background: {Theme.OK}; border-radius: 6px;"
        )
        self.connection_lbl.setText(f"Подключено: {self._connected_printer}")
        self.connection_lbl.setStyleSheet(
            f"color: {Theme.OK}; font-weight: 600; font-size: 13px;"
        )
        # Обновить очередь
        self.details._queue_count = len(self.queue_tasks)
        self.details.pause_btn.setEnabled(True)
        self.details.queue_btn.setEnabled(True)
        self.details._refresh_queue_label(paused=False)

    def _disconnect_printer(self):
        dlg = ModalDialog(
            self,
            "Отключить принтер?",
            f"Соединение с {self._connected_printer} будет разорвано. "
            "Задачи в очереди останутся на принтере.",
            kind="warn",
            yes_text="Отключить",
            no_text="Отмена",
        )
        if dlg.exec() != QDialog.Accepted:
            return

        self._connected_printer = None
        self.details.set_connected(False)
        self.connection_led.setStyleSheet(
            f"background: {Theme.TEXT_MUTED}; border-radius: 6px;"
        )
        self.connection_lbl.setText("Не подключено")
        self.connection_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-weight: 600; font-size: 13px;"
        )
        self.details._queue_count = 0
        self.details.pause_btn.setEnabled(False)
        self.details.queue_btn.setEnabled(False)
        self.details._refresh_queue_label(paused=False)

    def _show_help(self):
        HelpDialog(self).exec()


# ─────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setFont(QFont(Theme.FONT_FAMILY, Theme.FONT_SIZE))
    window = ConnectionsWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()