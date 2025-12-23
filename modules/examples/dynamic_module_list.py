# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

from qgis.PyQt.QtWidgets import QFrame, QWidget, QGridLayout


from ...submodules.base.ui.base_class import UiModuleBase
from ...submodules.base.ui.dummy import ModuleDummy

FORM_CLASS, BASE_CLASS = UiModuleBase.get_uic_classes(__file__)
FORM_CLASS: 'Ui'
try:
    from .test_dynamic_module_list_generated_ui import Ui as FORM_CLASS

except ModuleNotFoundError:
    pass

# here are some dummy modules to load/unload
class TestModuleDummy(ModuleDummy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_text(f"Hello I am module '{self.__class__.__name__}'.\n\n"
                      f"My object id is {id(self)}")


class TestModuleDummy1(TestModuleDummy):
    pass


class TestModuleDummy2(TestModuleDummy):
    pass


class TestModuleDummy3(TestModuleDummy):
    pass


class TestModuleDummy4(TestModuleDummy):
    pass


class SubModuleContainer(UiModuleBase, QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        QFrame.__init__(self, kwargs.get("parent"))
        self.setLayout(QGridLayout())


# here are some dummy modules to load/unload
class TestModuleDynamicModules(UiModuleBase, QFrame, FORM_CLASS):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        QFrame.__init__(self, kwargs.get("parent"))

        self.setupUi(self)

        self._mapping = {
            "Frame_ModuleOne": [TestModuleDummy1, TestModuleDummy2, TestModuleDummy3],
            "Frame_ModuleTwo": [TestModuleDummy1, TestModuleDummy3],
            "Frame_ModuleThree": [TestModuleDummy1, TestModuleDummy2, TestModuleDummy3, TestModuleDummy4],
        }

        for key in self._mapping:
            self.DrD_Module_Test.addItem(key, key)

        self._prepare_components()

        self.connect(self.DrD_Module_Test.currentIndexChanged, self._drd_changed)

        self._reset()
        self._drd_changed()

    def _prepare_components(self):

        # loop throgh palce holder widgets and component list (dummys)
        for key, components in self._mapping.items():

            # get place holder frame for given module
            frame = getattr(self, key)
            frame = self.add_ui_module(key, frame, SubModuleContainer, use_directly=True)

            for component in components:

                # create new palce holder for component
                place_holder_widget = QWidget()
                place_holder_widget.setObjectName(f"{key}_{component.__name__}")

                # add place holder widget to module frame (placeholder from ui file)
                frame.layout().addWidget(place_holder_widget)

                # replace palce holder with new module (dummy n)
                frame.add_ui_module(component.__name__, place_holder_widget, component)

    def _reset(self):

        # hide all sub components
        for key in self._mapping:
            getattr(self, key).hide()

    def _drd_changed(self, *args):

        # default hide all
        self._reset()

        data = self.DrD_Module_Test.currentData()
        if data is None:
            return
        frame = getattr(self, data)
        frame.show()

        print("module", frame)
        for module in frame:
            print(module)
