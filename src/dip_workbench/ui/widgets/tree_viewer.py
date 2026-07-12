"""Tree artifact viewer."""

from __future__ import annotations

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from dip_workbench.operations import TreeNode, coerce_tree_data


class TreeViewer(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._root: TreeNode | None = None
        layout = QVBoxLayout(self)
        buttons = QHBoxLayout()
        self.expand_button = QPushButton("Expand all")
        self.collapse_button = QPushButton("Collapse all")
        buttons.addWidget(self.expand_button)
        buttons.addWidget(self.collapse_button)
        buttons.addStretch()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(("Label", "Value"))
        layout.addLayout(buttons)
        layout.addWidget(self.tree, 1)
        self.expand_button.clicked.connect(self.tree.expandAll)
        self.collapse_button.clicked.connect(self.tree.collapseAll)

    def set_tree_data(self, data: object) -> None:
        root = coerce_tree_data(data)
        self._root = root
        self.tree.clear()
        self.tree.addTopLevelItem(self._item_for_node(root))

    def tree_data(self) -> TreeNode | None:
        return self._root

    def clear(self) -> None:
        self._root = None
        self.tree.clear()

    def copy_selection(self) -> str:
        items = self.tree.selectedItems()
        text = "\n".join(
            f"{item.text(0)}: {item.text(1)}" if item.text(1) else item.text(0) for item in items
        )
        QGuiApplication.clipboard().setText(text)
        return text

    def _item_for_node(self, node: TreeNode) -> QTreeWidgetItem:
        item = QTreeWidgetItem([node.label, "" if node.value is None else str(node.value)])
        for child in node.children:
            item.addChild(self._item_for_node(child))
        return item
