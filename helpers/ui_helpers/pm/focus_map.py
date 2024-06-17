"""FocusMap"""

# pylint: disable=c-extension-no-member


from typing import Dict, Sequence

from PyQt6 import QtCore, QtGui, QtWidgets


class FocusMap:
    """map of which item to focus next based on current item"""

    def __init__(self, focus_order: Sequence[QtWidgets.QWidget] | None = None) -> None:
        self.focus_order_map: Dict[QtWidgets.QWidget, QtWidgets.QWidget] = {}
        if focus_order is not None:
            self.add(*focus_order)

    def next_tab(self) -> None:
        """when the tab is pressed, focus the next item based on current one"""

        focus_widget = QtWidgets.QApplication.focusWidget()
        if focus_widget is None:
            return

        try:
            self.focus_order_map[focus_widget].setFocus()
        except KeyError:
            pass

    def add(self, *focus_order: QtWidgets.QWidget) -> None:
        """add new focus map group"""

        for idx, focus in enumerate(focus_order):
            try:
                self.focus_order_map[focus] = focus_order[idx + 1]
            except IndexError:
                self.focus_order_map[focus] = focus_order[0]

    def bind(self, widget: QtWidgets.QWidget) -> None:
        """bind the tab key"""

        shortcut = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Tab), widget)
        shortcut.activated.connect(self.next_tab)
