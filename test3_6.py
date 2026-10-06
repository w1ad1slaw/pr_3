import sys
import random
from datetime import datetime, timedelta, date
import calendar as cal_module

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QLineEdit, QCheckBox, QGridLayout,
    QGraphicsDropShadowEffect, QComboBox, QDialog, QListWidget,
    QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QFont, QColor, QShortcut, QKeySequence, QPainter, QPen, QBrush
)


# ─────────────────────────────────────────────────────────────
# Дизайн-система
# ─────────────────────────────────────────────────────────────
class Theme:
    BG          = "#1A2226"
    PANEL       = "#232B2F"
    PANEL_ALT   = "#2A3338"
    PANEL_HOVER = "#2F383D"
    BORDER      = "#3A444A"
    BORDER_HARD = "#4A555C"

    TEXT        = "#FFFFFF"
    TEXT_DIM    = "#C8D0D5"
    TEXT_MUTED  = "#9DA8AE"

    ACCENT      = "#2ECC71"
    ACCENT_DARK = "#27AE60"
    ACCENT_SOFT = "#2ECC7130"

    ACTIVE      = "#2563EB"
    SELECT      = "#3498DB"

    ERR         = "#E74C3C"
    ERR_SOFT    = "#E74C3C30"
    WARN        = "#F39C12"
    WARN_SOFT   = "#F39C1230"
    INFO        = "#3498DB"

    FONT_FAMILY = "Segoe UI"
    FONT_SIZE   = 14


def apply_shadow(widget, blur=14, offset_y=2, alpha=60):
    sh = QGraphicsDropShadowEffect()
    sh.setBlurRadius(blur)
    sh.setOffset(0, offset_y)
    sh.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(sh)


def darken(hex_color, factor=115):
    return QColor(hex_color).darker(factor).name()


# ─────────────────────────────────────────────────────────────
# Данные
# ─────────────────────────────────────────────────────────────
EVENT_COLORS = {
    "calibration": "#00D4FF",
    "sampling":    "#2ECC71",
    "maintenance": "#F39C12",
}

EVENT_LABELS = {
    "calibration": "Калибровка",
    "sampling":    "Отбор проб",
    "maintenance": "ТО",
}


class DataStore:
    def __init__(self):
        today = date.today()
        self.events = {
            today + timedelta(days=2): [
                {"type": "calibration", "label": "Калибровка датчиков"}
            ],
            today + timedelta(days=5): [
                {"type": "sampling", "label": "Отбор проб партии #1287"},
                {"type": "maintenance", "label": "Плановое ТО"},
            ],
            today - timedelta(days=3): [
                {"type": "maintenance", "label": "Замена фильтров"}
            ],
        }
        self.logs = []

    def add_event(self, d, ev_type, label):
        self.events.setdefault(d, []).append(
            {"type": ev_type, "label": label}
        )

    def remove_event(self, d, ev):
        if d in self.events and ev in self.events[d]:
            self.events[d].remove(ev)
            if not self.events[d]:
                del self.events[d]

    def get_events(self, d):
        return self.events.get(d, [])

    def log(self, message, level="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.logs.insert(0, (ts, message, level, datetime.now()))
        if len(self.logs) > 200:
            self.logs.pop()


STORE = DataStore()


USERS = {
    "admin":        {"password": "admin",    "name": "Администратор",
                     "role": "Администратор"},
    "operator":     {"password": "operator", "name": "Оператор №1",
                     "role": "Оператор"},
    "admin@lab.ru": {"password": "admin123", "name": "Администратор",
                     "role": "Администратор"},
}


# ─────────────────────────────────────────────────────────────
# Toast — компактный, под шапкой
# ─────────────────────────────────────────────────────────────
class Toast(QFrame):
    def __init__(self, parent, message, kind="info", on_undo=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setMinimumWidth(260)
        self.setMaximumWidth(360)
        self._on_undo = on_undo

        colors = {
            "info":    Theme.INFO,
            "ok":      Theme.ACCENT,
            "warn":    Theme.WARN,
            "err":     Theme.ERR,
        }
        accent = colors.get(kind, Theme.INFO)
        icons = {"info": "ℹ", "ok": "✓", "warn": "⚠", "err": "✕"}
        icon = icons.get(kind, "ℹ")

        self.setStyleSheet(f"""
            Toast {{
                background: {Theme.PANEL};
                border: 1px solid {Theme.BORDER};
                border-left: 4px solid {accent};
                border-radius: 8px;
            }}
        """)
        apply_shadow(self, blur=18, offset_y=4, alpha=110)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 8, 8)
        layout.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(20, 20)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"color: {accent}; font-size: 14px; font-weight: bold; "
            f"background: transparent; border: none;"
        )

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 12px; font-weight: 500; "
            f"background: transparent; border: none;"
        )

        layout.addWidget(icon_lbl)
        layout.addWidget(msg_lbl, 1)

        if on_undo:
            undo_btn = QPushButton("Отменить")
            undo_btn.setFixedHeight(28)
            undo_btn.setCursor(Qt.PointingHandCursor)
            undo_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Theme.ACCENT};
                    border: 1px solid {Theme.ACCENT};
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 700;
                    padding: 0 10px;
                }}
                QPushButton:hover {{
                    background: {Theme.ACCENT_SOFT};
                }}
            """)
            undo_btn.clicked.connect(self._do_undo)
            layout.addWidget(undo_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_MUTED};
                border: none;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ color: {Theme.TEXT}; }}
        """)
        close_btn.clicked.connect(self._fade_out)
        layout.addWidget(close_btn)

        QTimer.singleShot(5000, self._fade_out)

    def _do_undo(self):
        if self._on_undo:
            self._on_undo()
        self._fade_out()

    def _fade_out(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.finished.connect(self.deleteLater)
        self.anim.start()


class ToastManager:
    HEADER_HEIGHT = 110  # Toast появляется НИЖЕ шапки

    def __init__(self, parent):
        self.parent = parent
        self.toasts = []

    def show(self, message, kind="info", on_undo=None):
        toast = Toast(self.parent, message, kind, on_undo=on_undo)
        toast.adjustSize()
        self.toasts.append(toast)

        if len(self.toasts) > 3:
            old = self.toasts.pop(0)
            try:
                old.deleteLater()
            except Exception:
                pass

        self._reposition()
        toast.show()
        toast.setWindowOpacity(0.0)
        anim = QPropertyAnimation(toast, b"windowOpacity")
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()
        toast.anim_in = anim

        QTimer.singleShot(5300, lambda: self._remove(toast))

    def _remove(self, toast):
        if toast in self.toasts:
            self.toasts.remove(toast)
            self._reposition()

    def _reposition(self):
        margin = 20
        y = self.HEADER_HEIGHT
        for t in reversed(self.toasts):
            t.move(self.parent.width() - t.width() - margin, y)
            y += t.height() + 10


# ─────────────────────────────────────────────────────────────
# Диалог событий дня
# ─────────────────────────────────────────────────────────────
class DayEventsDialog(QDialog):
    def __init__(self, parent, d: date, toast_manager=None):
        super().__init__(parent)
        self.d = d
        self.toast = toast_manager
        self.setWindowTitle(f"События на {d.strftime('%d.%m.%Y')}")
        self.setModal(True)
        self.setFixedSize(480, 520)
        self.setStyleSheet(f"QDialog {{ background: {Theme.PANEL}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        title = QLabel(f"События на {d.strftime('%d.%m.%Y')}")
        title.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 17px; font-weight: 700;"
        )
        layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background: {Theme.PANEL_ALT};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 8px;
                color: {Theme.TEXT};
                font-size: 13px;
            }}
            QListWidget::item {{ padding: 8px 4px; }}
        """)
        layout.addWidget(self.list_widget, 1)

        add_frame = QFrame()
        add_frame.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL_ALT};
                border-radius: 8px;
            }}
        """)
        add_layout = QVBoxLayout(add_frame)
        add_layout.setContentsMargins(14, 12, 14, 12)
        add_layout.setSpacing(8)

        add_lbl = QLabel("ДОБАВИТЬ СОБЫТИЕ")
        add_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px; "
            f"font-weight: 700; letter-spacing: 1px;"
        )
        add_layout.addWidget(add_lbl)

        form_row = QHBoxLayout()
        form_row.setSpacing(8)

        self.type_combo = QComboBox()
        for key, label in EVENT_LABELS.items():
            self.type_combo.addItem(label, key)
        self.type_combo.setFixedHeight(38)
        self.type_combo.setStyleSheet(f"""
            QComboBox {{
                background: {Theme.PANEL};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox QAbstractItemView {{
                background: {Theme.PANEL};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER};
                selection-background-color: {Theme.ACCENT};
            }}
        """)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Название события")
        self.name_edit.setFixedHeight(38)
        self.name_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {Theme.PANEL};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {Theme.ACCENT}; }}
        """)
        self.name_edit.returnPressed.connect(self._add_event)

        form_row.addWidget(self.type_combo)
        form_row.addWidget(self.name_edit, 1)
        add_layout.addLayout(form_row)

        self.add_btn = QPushButton("+ Добавить событие")
        self.add_btn.setFixedHeight(38)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT};
                color: {Theme.BG};
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background: {Theme.ACCENT_DARK}; }}
        """)
        self.add_btn.clicked.connect(self._add_event)
        add_layout.addWidget(self.add_btn)

        layout.addWidget(add_frame)

        close_btn = QPushButton("Готово")
        close_btn.setFixedHeight(44)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_DIM};
                border: 1px solid {Theme.BORDER_HARD};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {Theme.PANEL_ALT};
                color: {Theme.TEXT};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._rebuild()

    def _rebuild(self):
        self.list_widget.clear()
        events = STORE.get_events(self.d)
        if not events:
            item = QListWidgetItem("Нет событий на эту дату")
            item.setForeground(QColor(Theme.TEXT_MUTED))
            self.list_widget.addItem(item)
            return

        for ev in events:
            item = QListWidgetItem()
            widget = self._make_row(ev)
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def _make_row(self, ev):
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(4, 4, 4, 4)
        h.setSpacing(12)

        dot = QLabel()
        dot.setFixedSize(14, 14)
        dot.setStyleSheet(f"""
            QLabel {{
                background: {EVENT_COLORS[ev['type']]};
                border: 1px solid #FFFFFF;
                border-radius: 7px;
            }}
        """)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        name = QLabel(ev["label"])
        name.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 13px; font-weight: 600;"
        )
        typ = QLabel(EVENT_LABELS[ev["type"]])
        typ.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px;"
        )
        text_box.addWidget(name)
        text_box.addWidget(typ)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(32, 32)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setToolTip("Удалить событие")
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_MUTED};
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {Theme.ERR_SOFT};
                color: {Theme.ERR};
            }}
        """)
        del_btn.clicked.connect(lambda _, e=ev: self._delete_event(e))

        h.addWidget(dot)
        h.addLayout(text_box, 1)
        h.addWidget(del_btn)
        return row

    def _add_event(self):
        label = self.name_edit.text().strip()
        if not label:
            self.name_edit.setStyleSheet(f"""
                QLineEdit {{
                    background: {Theme.PANEL};
                    color: {Theme.TEXT};
                    border: 2px solid {Theme.ERR};
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 13px;
                }}
            """)
            QTimer.singleShot(1500, self._reset_edit_style)
            return

        ev_type = self.type_combo.currentData()
        STORE.add_event(self.d, ev_type, label)
        STORE.log(f"Добавлено событие: {label}", "ok")
        if self.toast:
            self.toast.show(f"Событие добавлено: {label}", "ok")
        self.name_edit.clear()
        self._rebuild()

    def _reset_edit_style(self):
        self.name_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {Theme.PANEL};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {Theme.ACCENT}; }}
        """)

    def _delete_event(self, ev):
        reply = QMessageBox.question(
            self,
            "Удалить событие?",
            f"Событие «{ev['label']}» будет удалено без возможности отмены.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        STORE.remove_event(self.d, ev)
        STORE.log(f"Удалено событие: {ev['label']}", "warn")
        if self.toast:
            self.toast.show(f"Событие удалено", "warn")
        self._rebuild()


# ─────────────────────────────────────────────────────────────
# КАЛЕНДАРЬ
# ─────────────────────────────────────────────────────────────
class CalendarWidget(QFrame):
    date_applied = Signal(date)

    MONTHS = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    WEEKDAYS = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]

    def __init__(self, parent=None, toast_manager=None):
        super().__init__(parent)
        self.toast = toast_manager
        self.setFixedWidth(420)
        self.setMinimumHeight(700)
        self.setStyleSheet(f"""
            CalendarWidget {{
                background: {Theme.PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 12px;
            }}
        """)
        apply_shadow(self)

        self.current_date = date.today()
        self.selected_date = date.today()
        self.applied_date = None
        self.view_year = self.current_date.year
        self.view_month = self.current_date.month

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        active_row = QHBoxLayout()
        active_row.setSpacing(8)

        self.active_lbl = QLabel("Активная дата: —")
        self.active_lbl.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 14px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        active_row.addWidget(self.active_lbl)
        active_row.addStretch()
        layout.addLayout(active_row)

        self.selection_lbl = QLabel("Выбрано: —")
        self.selection_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self.selection_lbl)

        self.title_lbl = QLabel("")
        self.title_lbl.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 15px; font-weight: 600; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self.title_lbl)

        nav_row = QHBoxLayout()
        nav_row.setSpacing(6)
        self.prev_month_btn = self._nav_btn("‹")
        self.prev_month_btn.clicked.connect(self._prev_month)
        self.month_combo = QComboBox()
        self.month_combo.addItems(self.MONTHS)
        self.month_combo.setFixedHeight(38)
        self.month_combo.setStyleSheet(self._combo_style())
        self.month_combo.currentIndexChanged.connect(self._on_month_changed)
        self.next_month_btn = self._nav_btn("›")
        self.next_month_btn.clicked.connect(self._next_month)
        nav_row.addWidget(self.prev_month_btn)
        nav_row.addWidget(self.month_combo, 1)
        nav_row.addWidget(self.next_month_btn)
        layout.addLayout(nav_row)

        year_row = QHBoxLayout()
        year_row.setSpacing(6)
        self.prev_year_btn = self._nav_btn("‹")
        self.prev_year_btn.clicked.connect(self._prev_year)
        self.year_combo = QComboBox()
        for y in range(self.current_date.year - 5,
                       self.current_date.year + 6):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(self.view_year))
        self.year_combo.setFixedHeight(38)
        self.year_combo.setStyleSheet(self._combo_style())
        self.year_combo.currentIndexChanged.connect(self._on_year_changed)
        self.next_year_btn = self._nav_btn("›")
        self.next_year_btn.clicked.connect(self._next_year)
        year_row.addWidget(self.prev_year_btn)
        year_row.addWidget(self.year_combo, 1)
        year_row.addWidget(self.next_year_btn)
        layout.addLayout(year_row)

        weekdays_row = QHBoxLayout()
        weekdays_row.setSpacing(0)
        for wd in self.WEEKDAYS:
            lbl = QLabel(wd)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedHeight(28)
            lbl.setStyleSheet(
                f"color: {Theme.TEXT_DIM}; font-size: 12px; "
                f"font-weight: 700; letter-spacing: 1px; "
                f"background: transparent; border: none;"
            )
            weekdays_row.addWidget(lbl, 1)
        layout.addLayout(weekdays_row)

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(4)
        layout.addWidget(self.grid_widget)

        hint = QLabel("💡 Двойной клик — редактирование событий")
        hint.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px; "
            f"font-style: italic; background: transparent; border: none;"
        )
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        legend_frame = QFrame()
        legend_frame.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL_ALT};
                border-radius: 10px;
            }}
        """)
        legend = QHBoxLayout(legend_frame)
        legend.setContentsMargins(14, 10, 14, 10)
        legend.setSpacing(16)
        for key, color in EVENT_COLORS.items():
            item = QHBoxLayout()
            item.setSpacing(8)
            dot = QLabel()
            dot.setFixedSize(12, 12)
            dot.setStyleSheet(f"""
                QLabel {{
                    background: {color};
                    border: 1px solid #FFFFFF;
                    border-radius: 6px;
                }}
            """)
            lbl = QLabel(EVENT_LABELS[key])
            lbl.setStyleSheet(
                f"color: {Theme.TEXT_DIM}; font-size: 13px; "
                f"font-weight: 600; background: transparent; border: none;"
            )
            item.addWidget(dot)
            item.addWidget(lbl)
            legend.addLayout(item)
        legend.addStretch()
        layout.addWidget(legend_frame)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(8)

        self.clear_btn = QPushButton("Очистить выбор")
        self.clear_btn.setFixedHeight(46)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setToolTip(
            "Убрать текущий выбор, вернуться к активной дате"
        )
        self.clear_btn.setStyleSheet(f"""
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
        self.clear_btn.clicked.connect(self._clear_selection)

        self.today_btn = QPushButton("Сегодня")
        self.today_btn.setFixedHeight(46)
        self.today_btn.setCursor(Qt.PointingHandCursor)
        self.today_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.ACCENT};
                border: 1px solid {Theme.ACCENT};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background: {Theme.ACCENT_SOFT}; }}
        """)
        self.today_btn.clicked.connect(self._go_today)

        self.apply_btn = QPushButton("Применить")
        self.apply_btn.setFixedHeight(46)
        self.apply_btn.setCursor(Qt.PointingHandCursor)
        self.apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT};
                color: {Theme.BG};
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 0.5px;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background: {Theme.ACCENT_DARK}; }}
            QPushButton:disabled {{
                background: {Theme.PANEL_HOVER};
                color: {Theme.TEXT_MUTED};
            }}
        """)
        self.apply_btn.clicked.connect(self._apply)

        buttons_row.addWidget(self.clear_btn)
        buttons_row.addWidget(self.today_btn)
        buttons_row.addWidget(self.apply_btn, 1)
        layout.addLayout(buttons_row)

        self.month_combo.blockSignals(True)
        self.month_combo.setCurrentIndex(self.view_month - 1)
        self.month_combo.blockSignals(False)

        self._rebuild()

    def _combo_style(self):
        return f"""
            QComboBox {{
                background: {Theme.PANEL_ALT};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox QAbstractItemView {{
                background: {Theme.PANEL_ALT};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER};
                selection-background-color: {Theme.ACCENT};
            }}
        """

    def _nav_btn(self, text):
        btn = QPushButton(text)
        btn.setFixedSize(38, 38)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.PANEL_ALT};
                color: {Theme.TEXT};
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {Theme.ACCENT};
                color: {Theme.BG};
            }}
        """)
        return btn

    def _prev_month(self):
        self.view_month -= 1
        if self.view_month < 1:
            self.view_month = 12
            self.view_year -= 1
        self._sync_combos()
        self._rebuild()

    def _next_month(self):
        self.view_month += 1
        if self.view_month > 12:
            self.view_month = 1
            self.view_year += 1
        self._sync_combos()
        self._rebuild()

    def _prev_year(self):
        self.view_year -= 1
        self._sync_combos()
        self._rebuild()

    def _next_year(self):
        self.view_year += 1
        self._sync_combos()
        self._rebuild()

    def _on_month_changed(self, idx):
        self.view_month = idx + 1
        self._rebuild()

    def _on_year_changed(self, idx):
        year = self.year_combo.itemData(idx)
        if year:
            self.view_year = year
            self._rebuild()

    def _sync_combos(self):
        self.month_combo.blockSignals(True)
        self.year_combo.blockSignals(True)
        self.month_combo.setCurrentIndex(self.view_month - 1)
        idx = self.year_combo.findData(self.view_year)
        if idx >= 0:
            self.year_combo.setCurrentIndex(idx)
        self.month_combo.blockSignals(False)
        self.year_combo.blockSignals(False)

    def _go_today(self):
        today = date.today()
        self.view_year = today.year
        self.view_month = today.month
        self.selected_date = today
        self._sync_combos()
        self._rebuild()
        self.selection_lbl.setText(
            f"Выбрано: {self.selected_date.strftime('%d.%m.%Y')}"
        )
        STORE.log("Переход к сегодняшней дате", "info")
        if self.toast:
            self.toast.show("Переход к сегодняшней дате", "info")

    def _clear_selection(self):
        """Убирает текущий выбор, возвращая подсветку на активную дату."""
        target = self.applied_date if self.applied_date else date.today()
        self.selected_date = target
        self.view_year = target.year
        self.view_month = target.month
        self.selection_lbl.setText("Выбрано: —")
        self.selection_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"background: transparent; border: none;"
        )
        self._sync_combos()
        self._rebuild()
        STORE.log("Выбор очищен", "info")
        if self.toast:
            self.toast.show("Выбор очищен", "info")

    def _apply(self):
        self.applied_date = self.selected_date
        self.date_applied.emit(self.selected_date)

        # Контекстная кнопка
        self.apply_btn.setEnabled(False)
        self.apply_btn.setText("Применение…")

        def _finish():
            self.apply_btn.setText("✓ Применено")
            QTimer.singleShot(1500, _reset_btn)

        def _reset_btn():
            self.apply_btn.setText("Применить")
            self.apply_btn.setEnabled(True)

        QTimer.singleShot(500, _finish)

        self.active_lbl.setText(
            f"Активная дата: {self.selected_date.strftime('%d.%m.%Y')}"
        )
        self.active_lbl.setStyleSheet(
            f"color: {Theme.ACCENT}; font-size: 14px; font-weight: 700; "
            f"background: transparent; border: none;"
        )

        self.setStyleSheet(f"""
            CalendarWidget {{
                background: {Theme.PANEL};
                border: 2px solid {Theme.ACCENT};
                border-radius: 12px;
            }}
        """)
        QTimer.singleShot(2000, self._reset_border)

        STORE.log(
            f"Дата применена: {self.selected_date.strftime('%d.%m.%Y')}",
            "ok"
        )

        # Toast с возможностью отмены
        if self.toast:
            prev_applied = self.applied_date
            self.toast.show(
                f"Дата применена: {self.selected_date.strftime('%d.%m.%Y')}",
                "ok",
                on_undo=lambda: self._undo_apply(prev_applied)
            )

        self._rebuild()

    def _undo_apply(self, prev):
        self.applied_date = prev
        if prev:
            self.active_lbl.setText(
                f"Активная дата: {prev.strftime('%d.%m.%Y')}"
            )
        else:
            self.active_lbl.setText("Активная дата: —")
            self.active_lbl.setStyleSheet(
                f"color: {Theme.TEXT}; font-size: 14px; font-weight: 700; "
                f"background: transparent; border: none;"
            )
        STORE.log("Применение даты отменено", "warn")
        if self.toast:
            self.toast.show("Применение отменено", "warn")
        self._rebuild()

    def _reset_border(self):
        self.setStyleSheet(f"""
            CalendarWidget {{
                background: {Theme.PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 12px;
            }}
        """)

    def _select_day(self, d: int):
        self.selected_date = date(self.view_year, self.view_month, d)
        self.selection_lbl.setText(
            f"Выбрано: {self.selected_date.strftime('%d.%m.%Y')} "
            f"(нажмите «Применить»)"
        )
        self.selection_lbl.setStyleSheet(
            f"color: {Theme.SELECT}; font-size: 12px; font-weight: 600; "
            f"background: transparent; border: none;"
        )
        self._rebuild()

    def _edit_day(self, d: int):
        cell_date = date(self.view_year, self.view_month, d)
        dialog = DayEventsDialog(self, cell_date, self.toast)
        dialog.exec()
        self._rebuild()

    def _rebuild(self):
        self.title_lbl.setText(
            f"{self.MONTHS[self.view_month - 1]} {self.view_year}"
        )

        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        first_weekday, days_in_month = cal_module.monthrange(
            self.view_year, self.view_month
        )
        offset = (first_weekday + 1) % 7
        today = date.today()

        row = 0
        col = offset
        for day in range(1, days_in_month + 1):
            cell_date = date(self.view_year, self.view_month, day)
            widget = self._day_widget(day, cell_date, today)
            self.grid.addWidget(widget, row, col)
            col += 1
            if col > 6:
                col = 0
                row += 1

    def _day_widget(self, day, cell_date, today):
        container = QWidget()
        container.setFixedSize(48, 56)
        container.setCursor(Qt.PointingHandCursor)

        is_applied = (self.applied_date is not None
                      and cell_date == self.applied_date)
        is_selected = (cell_date == self.selected_date
                       and not is_applied)
        is_today = (cell_date == today
                    and not is_applied and not is_selected)
        is_weekend = cell_date.weekday() >= 5

        if is_applied:
            bg = Theme.ACTIVE
            border = "none"
            text_color = "#FFFFFF"
            weight = "700"
        elif is_selected:
            bg = "transparent"
            border = f"2px solid {Theme.SELECT}"
            text_color = Theme.SELECT
            weight = "700"
        elif is_today:
            bg = "transparent"
            border = f"2px solid {Theme.ACCENT}"
            text_color = Theme.ACCENT
            weight = "700"
        else:
            bg = "transparent"
            border = "2px solid transparent"
            text_color = Theme.TEXT_MUTED if is_weekend else Theme.TEXT
            weight = "500"

        container.setStyleSheet(f"""
            QWidget {{
                background: {bg};
                border: {border};
                border-radius: 8px;
            }}
            QWidget:hover {{ background: {Theme.PANEL_HOVER}; }}
        """)

        events = STORE.get_events(cell_date)
        if events:
            tip_lines = [f"{cell_date.strftime('%d.%m.%Y')}"]
            for ev in events:
                tip_lines.append(f"• {ev['label']}")
            tip_lines.append("")
            tip_lines.append("Двойной клик — редактировать")
            container.setToolTip("\n".join(tip_lines))

        v = QVBoxLayout(container)
        v.setContentsMargins(0, 6, 0, 4)
        v.setSpacing(3)

        # БЕЗ галочки — только цифра
        day_lbl = QLabel(str(day))
        day_lbl.setAlignment(Qt.AlignCenter)
        day_lbl.setStyleSheet(
            f"color: {text_color}; font-size: 14px; font-weight: {weight}; "
            f"background: transparent; border: none;"
        )
        v.addWidget(day_lbl)

        dots_row = QHBoxLayout()
        dots_row.setSpacing(3)
        dots_row.setAlignment(Qt.AlignCenter)
        dots_row.setContentsMargins(0, 0, 0, 0)
        for ev in events[:3]:
            dot = QLabel()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"""
                QLabel {{
                    background: {EVENT_COLORS[ev['type']]};
                    border: 1px solid #FFFFFF;
                    border-radius: 4px;
                }}
            """)
            dots_row.addWidget(dot)
        v.addLayout(dots_row)

        container.mousePressEvent = (
            lambda ev, d=day: self._select_day(d)
        )
        container.mouseDoubleClickEvent = (
            lambda ev, d=day: self._edit_day(d)
        )
        return container


# ─────────────────────────────────────────────────────────────
# ФОРМА ВХОДА
# ─────────────────────────────────────────────────────────────
class InputField(QFrame):
    def __init__(self, placeholder, icon_text="",
                 password=False, show_validation=False):
        super().__init__()
        self.setFixedHeight(54)
        self._focused = False
        self._error = False
        self._valid = False
        self._show_validation = show_validation
        self._apply_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(10)

        # Иконка слева
        if icon_text:
            icon_lbl = QLabel(icon_text)
            icon_lbl.setFixedSize(20, 20)
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setStyleSheet(
                f"color: {Theme.TEXT_MUTED}; font-size: 16px; "
                f"background: transparent; border: none;"
            )
            layout.addWidget(icon_lbl)

        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setEchoMode(
            QLineEdit.Password if password else QLineEdit.Normal
        )
        self.edit.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {Theme.TEXT};
                font-size: 14px;
                padding: 0;
            }}
            QLineEdit::placeholder {{ color: {Theme.TEXT_MUTED}; }}
        """)
        self.edit.focusInEvent = self._on_focus_in
        self.edit.focusOutEvent = self._on_focus_out

        layout.addWidget(self.edit, 1)

        # Индикатор валидации (справа)
        self.validation_lbl = QLabel("")
        self.validation_lbl.setFixedSize(24, 24)
        self.validation_lbl.setAlignment(Qt.AlignCenter)
        self.validation_lbl.setStyleSheet(
            "background: transparent; border: none;"
        )
        if self._show_validation:
            layout.addWidget(self.validation_lbl)

    def _apply_style(self):
        if self._error:
            border = Theme.ERR
        elif self._valid:
            border = Theme.ACCENT
        elif self._focused:
            border = Theme.SELECT
        else:
            border = "transparent"
        self.setStyleSheet(f"""
            InputField {{
                background: {Theme.PANEL_ALT};
                border: 2px solid {border};
                border-radius: 10px;
            }}
        """)

    def _on_focus_in(self, event):
        self._focused = True
        self._apply_style()
        QLineEdit.focusInEvent(self.edit, event)

    def _on_focus_out(self, event):
        self._focused = False
        self._apply_style()
        QLineEdit.focusOutEvent(self.edit, event)

    def set_error(self, error: bool):
        self._error = error
        if error:
            self._valid = False
        self._apply_style()

    def set_valid(self, valid: bool):
        self._valid = valid
        if valid:
            self._error = False
        self._apply_style()
        if self._show_validation:
            if valid:
                self.validation_lbl.setText("✓")
                self.validation_lbl.setStyleSheet(
                    f"color: {Theme.ACCENT}; font-size: 16px; "
                    f"font-weight: bold; background: transparent; "
                    f"border: none;"
                )
            elif self._error:
                self.validation_lbl.setText("✕")
                self.validation_lbl.setStyleSheet(
                    f"color: {Theme.ERR}; font-size: 16px; "
                    f"font-weight: bold; background: transparent; "
                    f"border: none;"
                )
            else:
                self.validation_lbl.setText("")

    def text(self):
        return self.edit.text()

    def clear(self):
        self.edit.clear()


class PasswordStrength(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(6)
        self._level = 0

    def set_password(self, password):
        if not password:
            self._level = 0
        elif len(password) < 4:
            self._level = 1
        elif len(password) < 8 or not any(c.isdigit() for c in password):
            self._level = 2
        else:
            self._level = 3
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        seg_w = (w - 8) / 3
        colors = [Theme.ERR, Theme.WARN, Theme.ACCENT]
        for i in range(3):
            x = i * (seg_w + 4)
            if i < self._level:
                p.setBrush(QBrush(QColor(colors[self._level - 1])))
            else:
                p.setBrush(QBrush(QColor(Theme.PANEL_HOVER)))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(int(x), 0, int(seg_w), h, 3, 3)


class LoginForm(QFrame):
    logged_in = Signal(dict)
    logged_out = Signal()

    def __init__(self, parent=None, toast_manager=None):
        super().__init__(parent)
        self.toast = toast_manager
        self.setFixedSize(400, 720)
        self.setStyleSheet(f"""
            LoginForm {{
                background: {Theme.PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 12px;
            }}
        """)
        apply_shadow(self)

        self.password_visible = False
        self.current_user = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(32, 32, 32, 28)
        self.layout.setSpacing(12)

        self._build_login_view()

        self.caps_timer = QTimer(self)
        self.caps_timer.timeout.connect(self._check_caps_lock)
        self.caps_timer.start(500)

    def _clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def _clear_sub_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def _build_login_view(self):
        self._clear_layout()

        title = QLabel("Вход в систему")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 22px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        subtitle = QLabel("Лабораторная информационная система")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 13px; "
            f"background: transparent; border: none;"
        )
        self.layout.addWidget(title)
        self.layout.addWidget(subtitle)
        self.layout.addSpacing(6)

        # Логин с иконкой @ и валидацией
        self.login_field = InputField(
            "Логин или Email", icon_text="@", show_validation=True
        )
        self.login_field.edit.textChanged.connect(self._on_login_changed)
        self.layout.addWidget(self.login_field)

        # Пароль с иконкой 🔒
        self.password_field = InputField(
            "Пароль", icon_text="🔒", password=True
        )
        self.password_field.edit.textChanged.connect(self._on_password_changed)
        self.password_field.edit.returnPressed.connect(self._submit)
        self.layout.addWidget(self.password_field)

        # Показать пароль
        show_row = QHBoxLayout()
        show_row.setContentsMargins(0, 0, 0, 0)
        self.show_btn = QPushButton("👁 Показать пароль")
        self.show_btn.setFixedHeight(28)
        self.show_btn.setCursor(Qt.PointingHandCursor)
        self.show_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_DIM};
                border: none;
                font-size: 12px;
                text-align: left;
                padding: 0;
            }}
            QPushButton:hover {{ color: {Theme.ACCENT}; }}
        """)
        self.show_btn.clicked.connect(self._toggle_password)
        show_row.addWidget(self.show_btn)
        show_row.addStretch()
        self.layout.addLayout(show_row)

        # Индикатор силы пароля
        self.strength_bar = PasswordStrength()
        self.layout.addWidget(self.strength_bar)

        self.strength_lbl = QLabel("")
        self.strength_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px; "
            f"background: transparent; border: none;"
        )
        self.layout.addWidget(self.strength_lbl)

        self.caps_lbl = QLabel("")
        self.caps_lbl.setStyleSheet(
            f"color: {Theme.WARN}; font-size: 13px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        self.layout.addWidget(self.caps_lbl)

        # Подсказка
        hint_frame = QFrame()
        hint_frame.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL_ALT};
                border-radius: 8px;
            }}
        """)
        hint_layout = QVBoxLayout(hint_frame)
        hint_layout.setContentsMargins(12, 10, 12, 10)
        hint_layout.setSpacing(4)

        hint_title = QLabel("ТЕСТОВЫЕ УЧЁТНЫЕ ЗАПИСИ")
        hint_title.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 10px; "
            f"font-weight: 700; letter-spacing: 1px;"
        )
        hint1 = QLabel("admin / admin")
        hint1.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 12px; "
            f"font-family: 'Consolas', monospace;"
        )
        hint2 = QLabel("operator / operator")
        hint2.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 12px; "
            f"font-family: 'Consolas', monospace;"
        )
        hint_layout.addWidget(hint_title)
        hint_layout.addWidget(hint1)
        hint_layout.addWidget(hint2)
        self.layout.addWidget(hint_frame)

        self.remember = QCheckBox("Запомнить меня")
        self.remember.setCursor(Qt.PointingHandCursor)
        self.remember.setStyleSheet(f"""
            QCheckBox {{
                color: {Theme.TEXT_DIM};
                font-size: 13px;
                background: transparent;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border-radius: 4px;
                border: 1px solid {Theme.BORDER_HARD};
                background: {Theme.PANEL_ALT};
            }}
            QCheckBox::indicator:checked {{
                background: {Theme.ACCENT};
                border-color: {Theme.ACCENT};
            }}
        """)
        self.layout.addWidget(self.remember)

        self.layout.addStretch()

        # Кнопка Login
        self.login_btn = QPushButton("Войти")
        self.login_btn.setFixedHeight(50)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.PANEL_HOVER};
                color: {Theme.TEXT_MUTED};
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
            QPushButton:enabled {{
                background: {Theme.ACCENT};
                color: {Theme.BG};
            }}
            QPushButton:enabled:hover {{
                background: {Theme.ACCENT_DARK};
            }}
        """)
        self.login_btn.clicked.connect(self._submit)
        self.login_btn.setEnabled(False)
        self.layout.addWidget(self.login_btn)

        # Ссылка «Забыли пароль?»
        forgot_btn = QPushButton("Забыли пароль?")
        forgot_btn.setFixedHeight(28)
        forgot_btn.setCursor(Qt.PointingHandCursor)
        forgot_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_MUTED};
                border: none;
                font-size: 12px;
            }}
            QPushButton:hover {{ color: {Theme.ACCENT}; }}
        """)
        forgot_btn.clicked.connect(self._show_forgot)
        self.layout.addWidget(forgot_btn)

    def _show_forgot(self):
        QMessageBox.information(
            self,
            "Восстановление пароля",
            "Для сброса пароля обратитесь к администратору системы.\n\n"
            "Телефон: +7 (495) 123-45-67\n"
            "Email: admin@lab.ru"
        )

    def _on_login_changed(self, text):
        text = text.strip()
        if len(text) < 3:
            self.login_field.set_valid(False)
            self.login_field.set_error(False)
        elif text in USERS:
            self.login_field.set_valid(True)
        else:
            if "@" in text and "." in text.split("@")[-1]:
                self.login_field.set_valid(True)
            else:
                self.login_field.set_valid(False)
        self._validate()

    def _on_password_changed(self, text):
        self.strength_bar.set_password(text)
        if not text:
            self.strength_lbl.setText("")
        elif len(text) < 4:
            self.strength_lbl.setText("Слабый пароль")
            self.strength_lbl.setStyleSheet(
                f"color: {Theme.ERR}; font-size: 11px; "
                f"background: transparent; border: none;"
            )
        elif len(text) < 8:
            self.strength_lbl.setText("Средний пароль")
            self.strength_lbl.setStyleSheet(
                f"color: {Theme.WARN}; font-size: 11px; "
                f"background: transparent; border: none;"
            )
        else:
            self.strength_lbl.setText("Надёжный пароль")
            self.strength_lbl.setStyleSheet(
                f"color: {Theme.ACCENT}; font-size: 11px; "
                f"background: transparent; border: none;"
            )
        self._validate()

    def _toggle_password(self):
        self.password_visible = not self.password_visible
        self.password_field.edit.setEchoMode(
            QLineEdit.Normal if self.password_visible else QLineEdit.Password
        )
        self.show_btn.setText(
            "🚫 Скрыть пароль" if self.password_visible
            else "👁 Показать пароль"
        )

    def _check_caps_lock(self):
        if not hasattr(self, "caps_lbl"):
            return
        try:
            from ctypes import windll
            caps = windll.user32.GetKeyState(0x14) & 1
            self.caps_lbl.setText(
                "⚠  Caps Lock включён" if caps else ""
            )
        except Exception:
            self.caps_lbl.setText("")

    def _validate(self):
        login = self.login_field.text().strip()
        password = self.password_field.text()
        ok = len(login) >= 3 and len(password) >= 3
        self.login_btn.setEnabled(ok)

    def _submit(self):
        login = self.login_field.text().strip()
        password = self.password_field.text()

        if login not in USERS or USERS[login]["password"] != password:
            self.login_field.set_error(True)
            self.login_field.set_valid(False)
            self.password_field.set_error(True)
            self.password_field.clear()
            STORE.log(f"Неудачная попытка входа: {login}", "err")
            if self.toast:
                self.toast.show("Неверный логин или пароль", "err")
            return

        user = USERS[login]
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Вход…")
        QTimer.singleShot(700, lambda: self._finish_login(login, user))

    def _finish_login(self, login, user):
        self.current_user = user
        self.current_login = login
        STORE.log(f"Вход выполнен: {user['name']}", "ok")
        if self.toast:
            self.toast.show(f"Добро пожаловать, {user['name']}", "ok")
        self.logged_in.emit(user)
        self._build_success_view(user)

    def _build_success_view(self, user):
        self._clear_layout()

        icon = QLabel("✓")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(80, 80)
        icon.setStyleSheet(f"""
            QLabel {{
                background: {Theme.ACCENT_SOFT};
                color: {Theme.ACCENT};
                border-radius: 40px;
                font-size: 40px;
                font-weight: bold;
            }}
        """)
        self.layout.addSpacing(40)
        self.layout.addWidget(icon, 0, Qt.AlignHCenter)
        self.layout.addSpacing(20)

        title = QLabel("Добро пожаловать,")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 15px; "
            f"background: transparent; border: none;"
        )
        name = QLabel(user["name"])
        name.setAlignment(Qt.AlignCenter)
        name.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 20px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        role = QLabel(user["role"])
        role.setAlignment(Qt.AlignCenter)
        role.setStyleSheet(
            f"color: {Theme.ACCENT}; font-size: 13px; font-weight: 700; "
            f"letter-spacing: 1px; background: transparent; border: none;"
        )

        self.layout.addWidget(title)
        self.layout.addWidget(name)
        self.layout.addWidget(role)
        self.layout.addSpacing(30)

        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL_ALT};
                border-radius: 10px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 14, 16, 14)
        info_layout.setSpacing(6)

        login_info = QLabel(f"Логин: {self.current_login}")
        login_info.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 13px; "
            f"font-family: 'Consolas', monospace;"
        )
        time_info = QLabel(
            f"Время входа: {datetime.now().strftime('%H:%M:%S')}"
        )
        time_info.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 13px;"
        )
        info_layout.addWidget(login_info)
        info_layout.addWidget(time_info)
        self.layout.addWidget(info_frame)
        self.layout.addStretch()

        logout_btn = QPushButton("Выйти")
        logout_btn.setFixedHeight(48)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.ERR};
                border: 2px solid {Theme.ERR};
                border-radius: 10px;
                font-size: 14px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{ background: {Theme.ERR_SOFT}; }}
        """)
        logout_btn.clicked.connect(self._logout)
        self.layout.addWidget(logout_btn)

    def _logout(self):
        STORE.log("Выход из системы", "info")
        if self.toast:
            self.toast.show("Вы вышли из системы", "info")
        self.current_user = None
        self.logged_out.emit()
        self._build_login_view()


# ─────────────────────────────────────────────────────────────
# УСЛОВИЯ В ЛАБОРАТОРИИ
# ─────────────────────────────────────────────────────────────
class LabConditionsCard(QFrame):
    NORMAL_TEMP = (20, 24)
    NORMAL_HUMIDITY = (40, 60)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(420)
        self.setMinimumHeight(720)
        self._apply_style("ok")
        apply_shadow(self)

        self.last_update = datetime.now()
        self.seconds_until_update = 5

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("УСЛОВИЯ В ЛАБОРАТОРИИ №1")
        title.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 12px; font-weight: 700; "
            f"letter-spacing: 1.5px; background: transparent; border: none;"
        )
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(10, 10)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.status_dot)
        layout.addLayout(header)

        self.status_lbl = QLabel("ВСЁ В НОРМЕ")
        self.status_lbl.setStyleSheet(
            f"font-size: 16px; font-weight: 700; letter-spacing: 0.5px; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self.status_lbl)

        self.updated_lbl = QLabel("")
        self.updated_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self.updated_lbl)

        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(12)
        self.temp_card = self._metric_card("Температура", "22", "°C")
        self.hum_card = self._metric_card("Влажность", "48", "%")
        metrics_row.addWidget(self.temp_card["root"])
        metrics_row.addWidget(self.hum_card["root"])
        layout.addLayout(metrics_row)

        chart_title = QLabel("ТРЕНД ЗА 24 ЧАСА")
        chart_title.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px; font-weight: 700; "
            f"letter-spacing: 1.2px; background: transparent; border: none;"
        )
        layout.addWidget(chart_title)

        self.chart = TrendChart()
        self.chart.setFixedHeight(180)
        self._generate_trend()
        layout.addWidget(self.chart)

        extra_row = QHBoxLayout()
        extra_row.setSpacing(8)
        self.pressure_chip = self._small_chip(
            "Давление", "748", "мм рт. ст."
        )
        self.wind_chip = self._small_chip(
            "Приток воздуха", "0.4", "м/с"
        )
        extra_row.addWidget(self.pressure_chip["root"])
        extra_row.addWidget(self.wind_chip["root"])
        layout.addLayout(extra_row)

        layout.addStretch()

        control_row = QHBoxLayout()
        control_row.setSpacing(10)

        self.auto_lbl = QLabel("")
        self.auto_lbl.setStyleSheet(
            f"color: {Theme.ACCENT}; font-size: 12px; font-weight: 600; "
            f"background: transparent; border: none;"
        )

        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setFixedSize(44, 44)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setToolTip("Обновить данные вручную")
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.INFO};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background: {darken(Theme.INFO, 115)}; }}
        """)
        self.refresh_btn.clicked.connect(self._manual_refresh)

        control_row.addWidget(self.auto_lbl)
        control_row.addStretch()
        control_row.addWidget(self.refresh_btn)
        layout.addLayout(control_row)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._tick_auto_update)
        self.update_timer.start(1000)

        self._update_ui()

    def _apply_style(self, status):
        border_color = {
            "ok": Theme.BORDER,
            "warn": Theme.WARN,
            "err": Theme.ERR,
        }.get(status, Theme.BORDER)
        self.setStyleSheet(f"""
            LabConditionsCard {{
                background: {Theme.PANEL};
                border: 2px solid {border_color};
                border-radius: 12px;
            }}
        """)

    def _metric_card(self, label, value, unit):
        root = QFrame()
        root.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL_ALT};
                border-radius: 10px;
            }}
        """)
        v = QVBoxLayout(root)
        v.setContentsMargins(14, 12, 14, 12)
        v.setSpacing(4)

        name_lbl = QLabel(label)
        name_lbl.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 12px; "
            f"font-weight: 600; background: transparent; border: none;"
        )
        value_row = QHBoxLayout()
        value_row.setSpacing(4)
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 30px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        unit_lbl = QLabel(unit)
        unit_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 13px; "
            f"font-weight: 500; background: transparent; border: none;"
        )
        unit_lbl.setAlignment(Qt.AlignBottom)
        unit_lbl.setContentsMargins(0, 0, 0, 6)
        value_row.addWidget(val_lbl)
        value_row.addWidget(unit_lbl)
        value_row.addStretch()

        v.addWidget(name_lbl)
        v.addLayout(value_row)
        return {"root": root, "value": val_lbl}

    def _small_chip(self, label, value, unit):
        root = QFrame()
        root.setStyleSheet(f"""
            QFrame {{
                background: {Theme.PANEL_ALT};
                border-radius: 8px;
            }}
        """)
        h = QHBoxLayout(root)
        h.setContentsMargins(12, 10, 12, 10)
        h.setSpacing(8)

        name_lbl = QLabel(label)
        name_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px; "
            f"background: transparent; border: none;"
        )
        val_lbl = QLabel(f"{value} {unit}")
        val_lbl.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 12px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        h.addWidget(name_lbl)
        h.addStretch()
        h.addWidget(val_lbl)
        return {"root": root, "value": val_lbl}

    def _generate_trend(self):
        self.temp_trend = []
        self.hum_trend = []
        base_temp = 22
        base_hum = 48
        for hour in range(24):
            # Живые колебания: синус + шум
            t = (base_temp
                 + 1.5 * (hour / 23 - 0.5)
                 + 0.8 * random.uniform(-1, 1)
                 + 0.5 * (random.random() - 0.5))
            h = (base_hum
                 + 5 * (hour / 23 - 0.5)
                 + 2.0 * random.uniform(-1, 1))
            self.temp_trend.append(t)
            self.hum_trend.append(h)
        self.chart.set_data(self.temp_trend, self.hum_trend)

    def _update_ui(self):
        temp = self.temp_trend[-1]
        hum = self.hum_trend[-1]
        self.temp_card["value"].setText(f"{temp:.1f}")
        self.hum_card["value"].setText(f"{hum:.0f}")

        t_lo, t_hi = self.NORMAL_TEMP
        h_lo, h_hi = self.NORMAL_HUMIDITY

        temp_status = "ok"
        if temp < t_lo or temp > t_hi:
            temp_status = "warn"
        if temp < t_lo - 3 or temp > t_hi + 3:
            temp_status = "err"

        hum_status = "ok"
        if hum < h_lo or hum > h_hi:
            hum_status = "warn"
        if hum < h_lo - 15 or hum > h_hi + 15:
            hum_status = "err"

        overall = "ok"
        if "warn" in (temp_status, hum_status):
            overall = "warn"
        if "err" in (temp_status, hum_status):
            overall = "err"

        colors = {"ok": Theme.ACCENT, "warn": Theme.WARN, "err": Theme.ERR}
        labels = {"ok": "ВСЁ В НОРМЕ", "warn": "ЕСТЬ ОТКЛОНЕНИЯ",
                  "err": "КРИТИЧНО"}

        self._apply_style(overall)
        self.status_dot.setStyleSheet(
            f"background: {colors[overall]}; border-radius: 5px;"
        )
        self.status_lbl.setText(labels[overall])
        self.status_lbl.setStyleSheet(
            f"color: {colors[overall]}; font-size: 16px; font-weight: 700; "
            f"letter-spacing: 0.5px; background: transparent; border: none;"
        )
        self.updated_lbl.setText(
            f"Обновлено: {self.last_update.strftime('%H:%M:%S')}"
        )

    def _tick_auto_update(self):
        self.seconds_until_update -= 1
        if self.seconds_until_update <= 0:
            self.seconds_until_update = 5
            self._auto_refresh()
        self.auto_lbl.setText(
            f"● Автообновление ВКЛ · через {self.seconds_until_update} с"
        )

    def _auto_refresh(self):
        self.temp_trend.append(
            max(15, min(30, self.temp_trend[-1] + random.uniform(-0.4, 0.4)))
        )
        self.hum_trend.append(
            max(25, min(75, self.hum_trend[-1] + random.uniform(-1.0, 1.0)))
        )
        if len(self.temp_trend) > 24:
            self.temp_trend.pop(0)
            self.hum_trend.pop(0)
        self.chart.set_data(self.temp_trend, self.hum_trend)
        self.last_update = datetime.now()
        self._update_ui()

    def _manual_refresh(self):
        self.seconds_until_update = 5
        self._auto_refresh()


# ─────────────────────────────────────────────────────────────
# График
# ─────────────────────────────────────────────────────────────
class TrendChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._temps = []
        self._hums = []

    def set_data(self, temps, hums):
        self._temps = list(temps)
        self._hums = list(hums)
        self.update()

    def paintEvent(self, event):
        if len(self._temps) < 2:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        pad_left = 40
        pad_right = 14
        pad_top = 12
        pad_bottom = 28
        chart_w = w - pad_left - pad_right
        chart_h = h - pad_top - pad_bottom

        vmin, vmax = 15, 35
        span = vmax - vmin

        def x_of(i):
            n = len(self._temps)
            return pad_left + chart_w * i / (n - 1)

        def y_of(v):
            return pad_top + chart_h * (1 - (v - vmin) / span)

        t_lo, t_hi = LabConditionsCard.NORMAL_TEMP
        y_lo = y_of(t_lo)
        y_hi = y_of(t_hi)
        band = QColor(Theme.ACCENT)
        band.setAlpha(25)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(band))
        p.drawRect(pad_left, int(y_hi), chart_w, int(y_lo - y_hi))

        p.setFont(QFont(Theme.FONT_FAMILY, 9))
        for v in [15, 20, 25, 30, 35]:
            y = y_of(v)
            p.setPen(QPen(QColor(Theme.BORDER), 1, Qt.DotLine))
            p.drawLine(pad_left, int(y), w - pad_right, int(y))
            p.setPen(QColor(Theme.TEXT_DIM))
            p.drawText(6, int(y) + 3, f"{v}")

        p.setPen(QColor(Theme.TEXT_DIM))
        for i, label in enumerate(["00:00", "06:00", "12:00",
                                    "18:00", "24:00"]):
            x = pad_left + chart_w * i / 4
            p.drawText(int(x) - 18, h - 6, label)

        p.setPen(QPen(QColor(Theme.BORDER_HARD), 1))
        p.drawLine(pad_left, pad_top, pad_left, pad_top + chart_h)
        p.drawLine(pad_left, pad_top + chart_h, w - pad_right,
                   pad_top + chart_h)

        self._draw_line(p, self._temps, QColor(Theme.ERR), x_of, y_of)
        self._draw_line(p, self._hums, QColor(Theme.INFO), x_of, y_of)

        self._draw_dot(p, x_of, y_of, self._temps[-1], QColor(Theme.ERR))
        self._draw_dot(p, x_of, y_of, self._hums[-1], QColor(Theme.INFO))

        p.setFont(QFont(Theme.FONT_FAMILY, 9, QFont.Bold))
        p.setPen(QColor(Theme.ERR))
        p.drawText(pad_left + 4, pad_top + 12, "— Температура, °C")
        p.setPen(QColor(Theme.INFO))
        p.drawText(pad_left + 4, pad_top + 24, "— Влажность, %")

    def _draw_line(self, p, values, color, x_of, y_of):
        pen = QPen(color, 2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        prev = None
        for i, v in enumerate(values):
            x = x_of(i)
            y = y_of(v)
            if prev:
                p.drawLine(int(prev[0]), int(prev[1]), int(x), int(y))
            prev = (x, y)

    def _draw_dot(self, p, x_of, y_of, value, color):
        x = x_of(len(self._temps) - 1)
        y = y_of(value)
        p.setPen(QPen(QColor(Theme.PANEL), 2))
        p.setBrush(QBrush(color))
        p.drawEllipse(int(x) - 4, int(y) - 4, 8, 8)


# ─────────────────────────────────────────────────────────────
# ЖУРНАЛ
# ─────────────────────────────────────────────────────────────
class JournalPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            JournalPanel {{
                background: {Theme.PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 12px;
            }}
        """)
        apply_shadow(self, blur=8, alpha=40)

        self._collapsed = True
        self._filter_type = "all"
        self._filter_period = "all"
        self._search_text = ""

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 12, 20, 12)
        self.layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(12)

        self.toggle_btn = QPushButton("▸  Журнал операций")
        self.toggle_btn.setFixedHeight(32)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT};
                border: none;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 1px;
                text-align: left;
                padding: 0;
            }}
            QPushButton:hover {{ color: {Theme.ACCENT}; }}
        """)
        self.toggle_btn.clicked.connect(self._toggle)

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
            f"background: transparent; border: none;"
        )

        header.addWidget(self.toggle_btn)
        header.addWidget(self.count_lbl)
        header.addStretch()
        self.layout.addLayout(header)

        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        filters_row = QHBoxLayout()
        filters_row.setSpacing(8)

        self.type_combo = QComboBox()
        self.type_combo.addItem("Все типы", "all")
        self.type_combo.addItem("Только ошибки", "err")
        self.type_combo.addItem("Предупреждения", "warn")
        self.type_combo.addItem("Успешные", "ok")
        self.type_combo.addItem("Информационные", "info")
        self.type_combo.setFixedHeight(32)
        self.type_combo.setStyleSheet(self._combo_style())
        self.type_combo.currentIndexChanged.connect(self._on_filter_change)

        self.period_combo = QComboBox()
        self.period_combo.addItem("За всё время", "all")
        self.period_combo.addItem("За час", "hour")
        self.period_combo.addItem("За смену (8ч)", "shift")
        self.period_combo.setFixedHeight(32)
        self.period_combo.setStyleSheet(self._combo_style())
        self.period_combo.currentIndexChanged.connect(self._on_filter_change)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск по тексту…")
        self.search_edit.setFixedHeight(32)
        self.search_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {Theme.PANEL_ALT};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: {Theme.ACCENT}; }}
        """)
        self.search_edit.textChanged.connect(self._on_search)

        filters_row.addWidget(self.type_combo)
        filters_row.addWidget(self.period_combo)
        filters_row.addWidget(self.search_edit, 1)
        content_layout.addLayout(filters_row)

        self.list_widget = QListWidget()
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.setFixedHeight(140)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background: {Theme.PANEL_ALT};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 8px;
                color: {Theme.TEXT_DIM};
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }}
            QListWidget::item {{ padding: 2px 0; }}
        """)
        content_layout.addWidget(self.list_widget)

        self.content.hide()
        self.layout.addWidget(self.content)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh)
        self.refresh_timer.start(500)

        self._refresh()

    def _combo_style(self):
        return f"""
            QComboBox {{
                background: {Theme.PANEL_ALT};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 0 10px;
                font-size: 12px;
                min-width: 140px;
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background: {Theme.PANEL_ALT};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER};
                selection-background-color: {Theme.ACCENT};
            }}
        """

    def _toggle(self):
        self._collapsed = not self._collapsed
        if self._collapsed:
            self.content.hide()
            self.toggle_btn.setText("▸  Журнал операций")
        else:
            self.content.show()
            self.toggle_btn.setText("▾  Журнал операций")

    def _on_filter_change(self):
        self._filter_type = self.type_combo.currentData()
        self._filter_period = self.period_combo.currentData()
        self._refresh()

    def _on_search(self, text):
        self._search_text = text.lower()
        self._refresh()

    def _filtered_logs(self):
        now = datetime.now()
        result = []
        for entry in STORE.logs:
            ts, msg, level, dt = entry
            if self._filter_type != "all" and level != self._filter_type:
                continue
            if self._filter_period == "hour":
                if (now - dt).total_seconds() > 3600:
                    continue
            elif self._filter_period == "shift":
                if (now - dt).total_seconds() > 8 * 3600:
                    continue
            if self._search_text and self._search_text not in msg.lower():
                continue
            result.append(entry)
        return result

    def _refresh(self):
        filtered = self._filtered_logs()
        total = len(STORE.logs)

        if self._collapsed:
            self.count_lbl.setText(
                f"({total} записей)  ·  нажмите, чтобы развернуть"
            )
            self.count_lbl.setStyleSheet(
                f"color: {Theme.TEXT_MUTED}; font-size: 12px; "
                f"background: transparent; border: none;"
            )
        else:
            self.count_lbl.setText(
                f"({len(filtered)} из {total} записей)  ·  нажмите, чтобы свернуть"
            )
            self.count_lbl.setStyleSheet(
                f"color: {Theme.ACCENT}; font-size: 12px; "
                f"background: transparent; border: none;"
            )

        if self._collapsed:
            return

        self.list_widget.clear()
        for ts, msg, level, dt in filtered[:50]:
            col = {"info": Theme.TEXT_DIM, "warn": Theme.WARN,
                   "err": Theme.ERR, "ok": Theme.ACCENT}.get(level, Theme.TEXT)
            item = QListWidgetItem(f"{ts}   {msg}")
            item.setForeground(QColor(col))
            self.list_widget.addItem(item)


# ─────────────────────────────────────────────────────────────
# ГЛАВНОЕ ОКНО
# ─────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    SESSION_TIMEOUT = 5 * 60

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LIMS · Лаборатория №1")
        self.resize(1480, 1020)
        self._apply_theme()

        self.session_left = self.SESSION_TIMEOUT
        self.current_user = None
        self.session_locked = False

        self.toast = ToastManager(self)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(16)

        # Шапка
        header_row = QHBoxLayout()
        header_row.setSpacing(16)

        title = QLabel("Лаборатория №1")
        title.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 20px; font-weight: 700;"
        )
        subtitle = QLabel("Планирование, мониторинг, авторизация")
        subtitle.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 13px;"
        )

        self.user_lbl = QLabel("Не авторизован")
        self.user_lbl.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 13px; font-weight: 600; "
            f"background: {Theme.PANEL_ALT}; padding: 8px 14px; "
            f"border-radius: 8px;"
        )

        self.session_lbl = QLabel("")
        self.session_lbl.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 12px; font-weight: 600; "
            f"background: {Theme.PANEL_ALT}; padding: 8px 14px; "
            f"border-radius: 8px;"
        )

        header_row.addWidget(title)
        header_row.addWidget(subtitle)
        header_row.addStretch()
        header_row.addWidget(self.user_lbl)
        header_row.addWidget(self.session_lbl)
        root.addLayout(header_row)

        # Компоненты
        row = QHBoxLayout()
        row.setSpacing(24)
        row.setAlignment(Qt.AlignTop)

        self.calendar = CalendarWidget(toast_manager=self.toast)
        self.login = LoginForm(toast_manager=self.toast)
        self.lab = LabConditionsCard()

        row.addWidget(self.calendar)
        row.addWidget(self.login)
        row.addWidget(self.lab)
        root.addLayout(row)

        self.journal = JournalPanel()
        root.addWidget(self.journal)

        self.session_timer = QTimer(self)
        self.session_timer.timeout.connect(self._tick_session)
        self.session_timer.start(1000)

        self.login.logged_in.connect(self._on_logged_in)
        self.login.logged_out.connect(self._on_logged_out)

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.toast._reposition()

    def mousePressEvent(self, event):
        self.session_left = self.SESSION_TIMEOUT
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self.session_left = self.SESSION_TIMEOUT
        super().keyPressEvent(event)

    def _tick_session(self):
        if self.session_locked:
            return
        self.session_left -= 1
        if self.session_left <= 0:
            self._lock_session()
            return
        m, s = divmod(self.session_left, 60)
        self.session_lbl.setText(f"⏱ Автовыход {m:02d}:{s:02d}")

    def _lock_session(self):
        self.session_locked = True
        STORE.log("Сессия заблокирована из-за бездействия", "warn")
        if self.toast:
            self.toast.show(
                "Сессия заблокирована из-за бездействия", "warn"
            )

        reply = QMessageBox.question(
            self,
            "Сессия истекла",
            "Из-за длительного бездействия сессия будет заблокирована.\n\n"
            "Продолжить работу?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            self.session_locked = False
            self.session_left = self.SESSION_TIMEOUT
            self.session_lbl.setText("⏱ Автовыход 05:00")
        else:
            if self.current_user:
                self.login._logout()
            self.session_locked = False
            self.session_left = self.SESSION_TIMEOUT
            self.session_lbl.setText("⏱ Автовыход 05:00")

    def _on_logged_in(self, user):
        self.current_user = user
        self.user_lbl.setText(f"👤 {user['name']}  ·  {user['role']}")
        self.user_lbl.setStyleSheet(
            f"color: {Theme.ACCENT}; font-size: 13px; font-weight: 700; "
            f"background: {Theme.ACCENT_SOFT}; padding: 8px 14px; "
            f"border-radius: 8px;"
        )

    def _on_logged_out(self):
        self.current_user = None
        self.user_lbl.setText("Не авторизован")
        self.user_lbl.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 13px; font-weight: 600; "
            f"background: {Theme.PANEL_ALT}; padding: 8px 14px; "
            f"border-radius: 8px;"
        )

    def _show_help(self):
        QMessageBox.information(
            self, "Справка",
            "LIMS · Лаборатория №1:\n\n"
            "• Календарь:\n"
            "   - одиночный клик — выбор\n"
            "   - двойной клик — редактирование событий\n"
            "   - «Применить» — закрепить выбор\n"
            "   - «Очистить выбор» — снять выделение\n"
            "   - «Сегодня» — быстрый переход\n"
            "• Форма входа — admin/admin или operator/operator.\n"
            "• Условия в лаборатории — мониторинг в реальном времени.\n"
            "• Журнал операций — внизу, свёрнут, разворачивается кликом."
        )


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont(Theme.FONT_FAMILY, Theme.FONT_SIZE))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()