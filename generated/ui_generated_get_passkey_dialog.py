# pylint: disable=all
# type: ignore
# Form implementation generated from reading ui file 'ui/get_passkey_dialog.ui'
#
# Created by: PyQt6 UI code generator 6.7.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_PasskeyDialog(object):
    def setupUi(self, PasskeyDialog):
        PasskeyDialog.setObjectName("PasskeyDialog")
        PasskeyDialog.resize(175, 302)
        self.centralwidget = QtWidgets.QWidget(parent=PasskeyDialog)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_title = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_title.setObjectName("label_title")
        self.verticalLayout.addWidget(self.label_title)
        self.list_view = QtWidgets.QListView(parent=self.centralwidget)
        self.list_view.setObjectName("list_view")
        self.verticalLayout.addWidget(self.list_view)
        self.checkbutton_send_enter = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.checkbutton_send_enter.setChecked(True)
        self.checkbutton_send_enter.setObjectName("checkbutton_send_enter")
        self.verticalLayout.addWidget(self.checkbutton_send_enter)
        self.buttonbox_ok_cancel = QtWidgets.QDialogButtonBox(parent=self.centralwidget)
        self.buttonbox_ok_cancel.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel|QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonbox_ok_cancel.setObjectName("buttonbox_ok_cancel")
        self.verticalLayout.addWidget(self.buttonbox_ok_cancel)
        PasskeyDialog.setCentralWidget(self.centralwidget)

        self.retranslateUi(PasskeyDialog)
        QtCore.QMetaObject.connectSlotsByName(PasskeyDialog)

    def retranslateUi(self, PasskeyDialog):
        _translate = QtCore.QCoreApplication.translate
        PasskeyDialog.setWindowTitle(_translate("PasskeyDialog", "PasskeyDialog"))
        self.label_title.setText(_translate("PasskeyDialog", "Please select the value"))
        self.checkbutton_send_enter.setText(_translate("PasskeyDialog", "send enter"))
