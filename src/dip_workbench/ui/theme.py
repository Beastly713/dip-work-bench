"""Deterministic application theme."""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def apply_application_theme(application: QApplication) -> None:
    """Apply one readable light Fusion theme to the whole application."""
    application.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f3f4f6"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f9fafb"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#e5e7eb"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#2563eb"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#111827"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#6b7280"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#6b7280"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, QColor("#f3f4f6"))
    application.setPalette(palette)
    application.setStyleSheet(
        """
        QWidget {
            color: #111827;
            background: #f3f4f6;
        }
        QFrame, QGroupBox, QScrollArea, QStackedWidget {
            border: none;
        }
        QLabel {
            background: transparent;
        }
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTableView, QTableWidget {
            background: #ffffff;
            color: #111827;
            border: 1px solid #9ca3af;
            border-radius: 4px;
            padding: 3px 5px;
        }
        QPushButton, QToolButton {
            background: #e5e7eb;
            color: #111827;
            border: 1px solid #9ca3af;
            border-radius: 4px;
            padding: 5px 8px;
        }
        QPushButton:hover, QToolButton:hover {
            background: #dbeafe;
            border-color: #2563eb;
        }
        QPushButton:pressed, QToolButton:pressed {
            background: #bfdbfe;
        }
        QPushButton:disabled, QToolButton:disabled, QComboBox:disabled,
        QSpinBox:disabled, QDoubleSpinBox:disabled {
            color: #6b7280;
            background: #f3f4f6;
            border-color: #d1d5db;
        }
        QSplitter::handle {
            background: #d1d5db;
        }
        QScrollArea {
            background: transparent;
        }
        QFrame#dropArea, QWidget#moduleCard {
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
        }
        QWidget#moduleCard:hover {
            border-color: #2563eb;
        }
        """
    )
