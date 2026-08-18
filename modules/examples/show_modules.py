# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

from ...submodules.base.ui.base_class import UiModuleBase
from ...submodules.base.ui.base_tab_widget import TabModuleBase
from ...submodules.base.ui.dummy import ModuleDummy

FORM_CLASS, BASE_CLASS = UiModuleBase.get_uic_classes(__file__)


class WrongInheritanceOrder0:
    pass


class WrongInheritanceOrder1:
    pass


# here are some dummy modules to load/unload
class TestModuleDummy(ModuleDummy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_text(f"Hello I am module '{self.__class__.__name__}'.\n\n"
                      f"My object id is {id(self)}")


class TestModuleDummyInheritanceError(WrongInheritanceOrder0, WrongInheritanceOrder1, TestModuleDummy):
    def __init__(self, *args, **kwargs):
        TestModuleDummy.__init__(self, *args, **kwargs)
        self.set_text("I am not allowed to be shown?")


class TestModuleDummy1(TestModuleDummy):
    pass


class TestModuleDummy2(TestModuleDummy):
    pass


class TestModuleDummy3(TestModuleDummy):
    pass


class TestModuleDummy4(TestModuleDummy):
    pass


class TestTabModuleDummy5(TabModuleBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _, frame_0 = self.insert_module_tab(0, "Hilfe", 'dummy0')
        _, frame_1 = self.insert_module_tab(1, "TestModuleDummy1", 'dummy1')
        
        self.add_ui_module("TestModuleDummy1", frame_0, TestModuleDummy1)
        self.add_ui_module("TestModuleDummy1", frame_1, TestModuleDummy1)

        # make this single tab valid
        self.make_valid()


KEY = "Test"
LIST_TEST_CLASSES = [TestModuleDummyInheritanceError, TestModuleDummy1, TestModuleDummy2,
                     TestModuleDummy3, TestModuleDummy4, TestTabModuleDummy5]


# ClassName(base class from qt Designer (QMainWindow), a module base, collected forms as form class from ui file)
# BASE_CLASS can be replaced in to an other compatible base class, e.g. QDockWidget
# -> if you do so, you have to change BASE_CLASS.__init__ too
class TestShowModules(UiModuleBase, BASE_CLASS, FORM_CLASS):

    def __init__(self, *args, **kwargs):
        UiModuleBase.__init__(self, *args, **kwargs)
        BASE_CLASS.__init__(self, kwargs.get('parent', None))

        self.setupUi(self)

        self.connect(self.DrD_Modules.currentIndexChanged, self.drd_changed)

        self.DrD_Modules.clear()
        self.DrD_Modules.addItem("-- kein Modul --", None)
        for class_ in LIST_TEST_CLASSES:
            self.DrD_Modules.addItem(class_.__name__, class_)

    def drd_changed(self, index: int):
        # reads data from dropdown
        data = self.DrD_Modules.currentData()

        # unloads existing module and load an empty frame as place holder
        if KEY in self:
            self[KEY].replace_with_empty_frame()

        # nothing to load into Module Frame
        if data is None:
            return

        # loads ui from drd in to this Frame
        self.add_ui_module(KEY, self.Module, data)
