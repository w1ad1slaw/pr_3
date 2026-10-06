import sys
from datetime import datetime, date, timedelta

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QProgressBar, QListWidget,
    QListWidgetItem, QDialog, QGraphicsDropShadowEffect, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QShortcut, QKeySequence


# ─────────────────────────────────────────────────────────────
# Дизайн-система v2 (спокойнее, чище)
# ─────────────────────────────────────────────────────────────
class Theme:
    BG          = "#F7F8FB"
    PANEL       = "#FFFFFF"
    PANEL_ALT   = "#F0F2F6"
    PANEL_SOFT  = "#FAFBFD"

    BORDER      = "#E2E6EC"
    BORDER_HARD = "#C9D0D9"

    TEXT        = "#0F172A"
    TEXT_DIM    = "#4B5563"
    TEXT_MUTED  = "#94A3B8"

    ACCENT      = "#2563EB"
    ACCENT_DARK = "#1D4ED8"
    ACCENT_SOFT = "#EFF6FF"

    OK      = "#16A34A"
    OK_SOFT = "#F0FDF4"
    WARN    = "#EA580C"
    WARN_SOFT = "#FFF7ED"
    ERR     = "#DC2626"
    ERR_SOFT = "#FEF2F2"
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


def status_by_deadline(deadline: date) -> dict:
    today = date.today()
    delta = (deadline - today).days
    if delta < 0:
        return {"text": "Просрочено", "color": Theme.ERR,
                "icon": "⚠", "kind": "err"}
    if delta == 0:
        return {"text": "Сегодня", "color": Theme.ERR,
                "icon": "⚠", "kind": "err"}
    if delta <= 3:
        return {"text": f"Через {delta} дн.", "color": Theme.WARN,
                "icon": "⏱", "kind": "warn"}
    return {"text": f"Через {delta} дн.", "color": Theme.TEXT_MUTED,
            "icon": "·", "kind": "idle"}


# ─────────────────────────────────────────────────────────────
# Данные
# ─────────────────────────────────────────────────────────────
def build_maintenance_data():
    today = date.today()
    return [
        {
            "id": "daily", "title": "Ежедневно",
            "subtitle": "Проверка каждую смену",
            "deadline": today,
            "tasks": [
                {"id": "d1", "name": "Проверить уровень масла",
                 "done": True, "user": "ivanov", "at": "08:15"},
                {"id": "d2", "name": "Осмотреть шпиндель",
                 "done": True, "user": "ivanov", "at": "08:30"},
                {"id": "d3", "name": "Проверить аварийный стоп",
                 "done": True, "user": "petrov", "at": "09:00"},
                {"id": "d4", "name": "Очистить стружку",
                 "done": False, "user": None, "at": None},
                {"id": "d5", "name": "Проверить давление воздуха",
                 "done": False, "user": None, "at": None},
                {"id": "d6", "name": "Проверить датчики",
                 "done": False, "user": None, "at": None},
                {"id": "d7", "name": "Осмотр рабочей зоны",
                 "done": False, "user": None, "at": None},
            ],
        },
        {
            "id": "weekly", "title": "Еженедельно",
            "subtitle": "Обслуживание раз в неделю",
            "deadline": today + timedelta(days=2),
            "tasks": [
                {"id": "w1", "name": "Заменить фильтр СОЖ",
                 "done": True, "user": "petrov", "at": "10:20"},
                {"id": "w2", "name": "Смазать направляющие",
                 "done": True, "user": "petrov", "at": "10:45"},
                {"id": "w3", "name": "Проверить ремни привода",
                 "done": True, "user": "ivanov", "at": "11:00"},
                {"id": "w4", "name": "Калибровка осей",
                 "done": True, "user": "ivanov", "at": "11:30"},
                {"id": "w5", "name": "Проверка системы охлаждения",
                 "done": True, "user": "petrov", "at": "12:00"},
            ],
        },
        {
            "id": "monthly", "title": "Ежемесячно",
            "subtitle": "Глубокое обслуживание раз в месяц",
            "deadline": today + timedelta(days=12),
            "tasks": [
                {"id": "m1", "name": "Заменить масло в редукторе",
                 "done": False, "user": None, "at": None},
                {"id": "m2", "name": "Проверить люфты осей",
                 "done": False, "user": None, "at": None},
                {"id": "m3", "name": "Проверить электрику шкафа",
                 "done": False, "user": None, "at": None},
                {"id": "m4", "name": "Тест точности позиционирования",
                 "done": False, "user": None, "at": None},
            ],
        },
        {
            "id": "quarterly", "title": "Ежеквартально",
            "subtitle": "Капитальное обслуживание",
            "deadline": today + timedelta(days=38),
            "tasks": [
                {"id": "q1", "name": "Заменить подшипники шпинделя",
                 "done": False, "user": None, "at": None},
                {"id": "q2", "name": "Проверить геометрию станка",
                 "done": False, "user": None, "at": None},
                {"id": "q3", "name": "Проверить систему ЧПУ",
                 "done": False, "user": None, "at": None},
                {"id": "q4", "name": "Заменить уплотнения",
                 "done": False, "user": None, "at": None},
                {"id": "q5", "name": "Проверить кабельные трассы",
                 "done": False, "user": None, "at": None},
                {"id": "q6", "name": "Проверка заземления",
                 "done": False, "user": None, "at": None},
            ],
        },
    ]


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
# История
# ─────────────────────────────────────────────────────────────
class HistoryDialog(QDialog):
    def __init__(self, parent, events):
        super().__init__(parent)
        self.setWindowTitle("История обслуживания")
        self.setModal(True)
        self.setFixedSize(680, 540)
        self.setStyleSheet(f"QDialog {{ background: {Theme.PANEL}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(16)

        t = QLabel("История обслуживания")
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
        for ts, msg, level in events:
            col = {"info": Theme.TEXT_DIM, "warn": Theme.WARN,
                   "err": Theme.ERR, "done": Theme.OK}.get(level, Theme.TEXT)
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
# Карточка периода
# ─────────────────────────────────────────────────────────────
class PeriodCard(QFrame):
    def __init__(self, period, on_select):
        super().__init__()
        self.period = period
        self.on_select = on_select
        self._active = False

        self.setFixedHeight(112)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style(active=False)
        apply_shadow(self, blur=8, alpha=12)

        # Внешний layout
        self.outer = QHBoxLayout(self)
        self.outer.setContentsMargins(0, 0, 0, 0)
        self.outer.setSpacing(0)

        # Акцентная полоса слева
        self.accent_bar = QFrame()
        self.accent_bar.setFixedWidth(4)
        self.outer.addWidget(self.accent_bar)

        # Контейнер содержимого
        self.inner = QWidget()
        self.inner_layout = QHBoxLayout(self.inner)
        self.inner_layout.setContentsMargins(20, 16, 20, 16)
        self.inner_layout.setSpacing(18)
        self.outer.addWidget(self.inner, 1)

        # ─── Левая часть: название + подзаголовок ───
        left = QVBoxLayout()
        left.setSpacing(6)

        self.title_lbl = QLabel("")
        self.title_lbl.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 17px; font-weight: 700;"
        )

        self.subtitle_lbl = QLabel("")
        self.subtitle_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 13px;"
        )

        left.addWidget(self.title_lbl)
        left.addWidget(self.subtitle_lbl)
        left.addStretch()

        # ─── Центр: прогресс-бар ───
        center = QVBoxLayout()
        center.setSpacing(6)

        self.progress_lbl = QLabel("")
        self.progress_lbl.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 13px; font-weight: 600;"
        )

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        self.bar.setStyleSheet("")

        center.addWidget(self.progress_lbl)
        center.addWidget(self.bar)
        center.addStretch()

        # ─── Правая часть: статус ───
        right = QVBoxLayout()
        right.setSpacing(4)
        right.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.status_row = QHBoxLayout()
        self.status_row.setSpacing(6)
        self.status_row.setAlignment(Qt.AlignRight)

        self.status_icon = QLabel("")
        self.status_icon.setStyleSheet("font-size: 14px; font-weight: bold;")

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(
            "font-size: 13px; font-weight: 700;"
        )
        self.status_row.addWidget(self.status_icon)
        self.status_row.addWidget(self.status_lbl)

        right.addLayout(self.status_row)

        # Собираем
        self.inner_layout.addLayout(left, 3)
        self.inner_layout.addLayout(center, 4)
        self.inner_layout.addLayout(right, 2)

        # Первичная отрисовка
        self._rebuild()

    def _apply_style(self, active=False):
        bg = Theme.PANEL_SOFT if active else Theme.PANEL
        border = Theme.BORDER if not active else Theme.BORDER_HARD
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
        """)

    def _rebuild(self):
        """Полная пересборка содержимого карточки."""
        # Прогресс
        done = sum(1 for t in self.period["tasks"] if t["done"])
        total = len(self.period["tasks"])
        self.all_done = done == total
        percent = int((done / total) * 100) if total else 0

        # Статус по дедлайну
        st = status_by_deadline(self.period["deadline"])
        if self.all_done:
            st = {"text": "Выполнено", "color": Theme.OK,
                  "icon": "✓", "kind": "done"}

        self.status = st

        # Заголовок
        self.title_lbl.setText(self.period["title"])
        self.subtitle_lbl.setText(self.period["subtitle"])

        # Прогресс
        self.progress_lbl.setText(f"{done} из {total}  ·  {percent}%")
        self.bar.setRange(0, total)
        self.bar.setValue(done)
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background: {Theme.PANEL_ALT};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: {st['color']};
                border-radius: 4px;
            }}
        """)

        # Статус
        self.status_icon.setText(st["icon"])
        self.status_icon.setStyleSheet(
            f"color: {st['color']}; font-size: 14px; font-weight: bold;"
        )
        self.status_lbl.setText(st["text"])
        self.status_lbl.setStyleSheet(
            f"color: {st['color']}; font-size: 13px; font-weight: 700;"
        )

        # Акцентная полоса
        if self._active:
            self.accent_bar.setStyleSheet(
                f"background: {Theme.ACCENT}; border-top-left-radius: 12px; "
                f"border-bottom-left-radius: 12px;"
            )
        else:
            self.accent_bar.setStyleSheet(
                f"background: {st['color']}; border-top-left-radius: 12px; "
                f"border-bottom-left-radius: 12px;"
            )

    def mousePressEvent(self, event):
        self.on_select(self.period["id"])

    def set_active(self, active):
        self._active = active
        self._apply_style(active=active)
        self._rebuild()

    def refresh(self):
        """Вызывается после изменения задач."""
        self._rebuild()


# ─────────────────────────────────────────────────────────────
# Карточка задачи
# ─────────────────────────────────────────────────────────────
class TaskRow(QFrame):
    def __init__(self, task, on_toggle):
        super().__init__()
        self.task = task
        self.on_toggle = on_toggle

        self.setFixedHeight(76)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: {Theme.BORDER_HARD};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(14)

        # Иконка статуса
        self.icon = QLabel()
        self.icon.setFont(QFont(Theme.FONT_FAMILY, 20, QFont.Bold))
        self.icon.setFixedSize(36, 36)
        self.icon.setAlignment(Qt.AlignCenter)

        if task["done"]:
            self.icon.setText("✓")
            self.icon.setStyleSheet(f"color: {Theme.OK};")
        else:
            self.icon.setText("○")
            self.icon.setStyleSheet(f"color: {Theme.TEXT_MUTED};")

        # Название и подпись
        text_box = QVBoxLayout()
        text_box.setSpacing(3)

        name = QLabel(task["name"])
        if task["done"]:
            name.setStyleSheet(
                f"color: {Theme.TEXT_MUTED}; font-size: 14px; font-weight: 500;"
            )
        else:
            name.setStyleSheet(
                f"color: {Theme.TEXT}; font-size: 14px; font-weight: 700;"
            )

        if task["done"] and task["user"]:
            detail_text = f"Выполнено: {task['user']} · {task['at']}"
        else:
            detail_text = "Ожидает выполнения"

        detail = QLabel(detail_text)
        detail.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px;"
        )

        text_box.addWidget(name)
        text_box.addWidget(detail)

        layout.addWidget(self.icon)
        layout.addLayout(text_box, 1)

        # Кнопка
        if task["done"]:
            btn = QPushButton("Вернуть")
            btn.setFixedHeight(36)
            btn.setMinimumWidth(110)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Theme.TEXT_DIM};
                    border: 1px solid {Theme.BORDER_HARD};
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 0 14px;
                }}
                QPushButton:hover {{
                    background: {Theme.PANEL_ALT};
                    color: {Theme.TEXT};
                }}
            """)
        else:
            btn = QPushButton("Выполнено")
            btn.setFixedHeight(36)
            btn.setMinimumWidth(120)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.OK};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 0 16px;
                }}
                QPushButton:hover {{ background: {darken(Theme.OK)}; }}
            """)

        btn.clicked.connect(lambda: self.on_toggle(self.task))
        layout.addWidget(btn)


# ─────────────────────────────────────────────────────────────
# ГЛАВНОЕ ОКНО
# ─────────────────────────────────────────────────────────────
class MaintenanceWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Планирование ТО · Maintenance")
        self.resize(1360, 900)
        self._apply_theme()

        self.periods = build_maintenance_data()
        self.events = []
        self.active_period_id = "daily"

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        content = QWidget()
        content.setStyleSheet(f"background: {Theme.BG};")
        cl = QHBoxLayout(content)
        cl.setContentsMargins(36, 24, 36, 24)
        cl.setSpacing(28)

        # ─── Левая колонка ───
        left = QVBoxLayout()
        left.setSpacing(14)

        left_title = QLabel("ПЕРИОДЫ ОБСЛУЖИВАНИЯ")
        left_title.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"font-weight: 700; letter-spacing: 1.4px;"
        )
        left.addWidget(left_title)

        self.period_cards = {}
        for period in self.periods:
            card = PeriodCard(period, self._select_period)
            left.addWidget(card)
            self.period_cards[period["id"]] = card
        left.addStretch()

        left_container = QWidget()
        left_container.setLayout(left)
        cl.addWidget(left_container, 5)

        # ─── Правая колонка ───
        right = QVBoxLayout()
        right.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        self.detail_title = QLabel("")
        self.detail_title.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 16px; font-weight: 700;"
        )

        self.detail_subtitle = QLabel("")
        self.detail_subtitle.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 13px;"
        )

        header_row.addWidget(self.detail_title)
        header_row.addStretch()
        header_row.addWidget(self.detail_subtitle)

        right.addLayout(header_row)

        # Скролл задач
        self.tasks_scroll = QScrollArea()
        self.tasks_scroll.setWidgetResizable(True)
        self.tasks_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tasks_scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
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
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(0, 0, 8, 0)
        self.tasks_layout.setSpacing(10)
        self.tasks_layout.addStretch()
        self.tasks_scroll.setWidget(self.tasks_container)

        right.addWidget(self.tasks_scroll, 1)

        right_container = QWidget()
        right_container.setLayout(right)
        cl.addWidget(right_container, 6)

        root.addWidget(content, 1)

        self._select_period("daily")
        self._log("Система планирования ТО запущена.", "info")

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
        hl.setContentsMargins(36, 0, 36, 0)
        hl.setSpacing(18)

        title = QLabel("Техническое обслуживание")
        title.setFont(QFont(Theme.FONT_FAMILY, 18, QFont.Bold))
        title.setStyleSheet(f"color: {Theme.TEXT};")

        self.summary_lbl = QLabel("")
        self.summary_lbl.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-weight: 600; font-size: 13px;"
        )

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
        hl.addSpacing(24)
        hl.addWidget(self.summary_lbl)
        hl.addStretch()
        hl.addWidget(history_btn)
        hl.addSpacing(6)
        hl.addWidget(help_btn)

        return header

    def _get_period(self, period_id):
        return next(p for p in self.periods if p["id"] == period_id)

    def _select_period(self, period_id):
        self.active_period_id = period_id
        for pid, card in self.period_cards.items():
            card.set_active(pid == period_id)
        self._refresh_tasks()

    def _refresh_tasks(self):
        period = self._get_period(self.active_period_id)

        self.detail_title.setText(period["title"].upper())
        done = sum(1 for t in period["tasks"] if t["done"])
        total = len(period["tasks"])
        self.detail_subtitle.setText(f"Выполнено {done} из {total}")

        # Очистить
        while self.tasks_layout.count():
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Добавить
        for task in period["tasks"]:
            self.tasks_layout.addWidget(TaskRow(task, self._toggle_task))
        self.tasks_layout.addStretch()

        self._refresh_summary()

    def _refresh_summary(self):
        total_tasks = 0
        done_tasks = 0
        overdue = 0
        today = date.today()

        for period in self.periods:
            for t in period["tasks"]:
                total_tasks += 1
                if t["done"]:
                    done_tasks += 1
            if (not all(t["done"] for t in period["tasks"])
                    and period["deadline"] <= today):
                overdue += 1

        text = f"{done_tasks} из {total_tasks} задач выполнено"
        if overdue:
            text += f"  ·  ⚠ просрочено периодов: {overdue}"
        self.summary_lbl.setText(text)

    def _toggle_task(self, task):
        period = self._get_period(self.active_period_id)

        if task["done"]:
            dlg = ModalDialog(
                self,
                "Вернуть задачу?",
                f"Задача «{task['name']}» вернётся в статус «ожидает». "
                "Продолжить?",
                kind="warn",
                yes_text="Вернуть",
                no_text="Оставить",
            )
            if dlg.exec() != QDialog.Accepted:
                return
            task["done"] = False
            task["user"] = None
            task["at"] = None
            self._log(f"Возврат: {task['name']}", "warn")
        else:
            now = datetime.now().strftime("%H:%M")
            task["done"] = True
            task["user"] = "operator"
            task["at"] = now
            self._log(f"Выполнено: {task['name']}", "done")

        # ─── ВАЖНО: обновляем и левую панель, и правую ───
        self.period_cards[period["id"]].refresh()
        self._refresh_tasks()

        # Проверка завершения периода
        if all(t["done"] for t in period["tasks"]):
            ModalDialog(
                self,
                "Период завершён",
                f"<b>{period['title']}</b> — все задачи выполнены.<br>"
                f"Отличная работа!",
                kind="info",
                yes_text="Понятно",
            ).exec()
            self._log(f"Период завершён: {period['title']}", "done")

    def _log(self, message, level="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.events.insert(0, (ts, message, level))
        if len(self.events) > 200:
            self.events.pop()

    def _show_history(self):
        HistoryDialog(self, self.events).exec()

    def _show_help(self):
        ModalDialog(
            self,
            "Справка",
            "<b>Периоды обслуживания</b><br>"
            "Слева — список периодов. У каждого виден прогресс "
            "и статус по дедлайну.<br><br>"
            "<b>Цвета статусов</b><br>"
            "• 🔴 Красный — просрочено или сегодня<br>"
            "• 🟠 Янтарный — приближается (≤ 3 дней)<br>"
            "• 🟢 Зелёный — завершено или в запасе<br>"
            "• ⚪ Серый — в запасе времени<br><br>"
            "<b>Задачи</b><br>"
            "Клик по периоду — справа откроется список.<br>"
            "Кнопка «Выполнено» отмечает задачу.<br>"
            "Кнопка «Вернуть» — возвращает в работу.<br><br>"
            "<b>История</b><br>"
            "Кнопка в шапке — журнал всех действий.",
            kind="info",
            yes_text="Понятно",
        ).exec()


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont(Theme.FONT_FAMILY, Theme.FONT_SIZE))
    window = MaintenanceWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()