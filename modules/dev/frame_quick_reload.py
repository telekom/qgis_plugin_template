# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2025 Deutsche Telekom Technik GmbH <f.vonstudsinske@telekom.de>
# SPDX-License-Identifier: GPL-3.0-only

""" Developer tool for picking a live Plan[Goo] frame and reloading its module. """

import importlib
import sys
import traceback
from typing import List, Optional, Tuple, Type

import sip
from qgis.PyQt.QtCore import QEvent, QObject, QPoint, QRect, Qt, QTimer
from qgis.PyQt.QtGui import QColor, QCursor, QFont, QPainter, QPen
from qgis.PyQt.QtWidgets import QAction, QApplication, QGridLayout, QLayout, QWidget

from ...submodules.base.ui.base_class import ModuleBase, UiModuleBase
from ...submodules.base.ui.base_plugin import Plugin


class FrameReloader:
    """Reloads modules and resolves reloadable frames for the picker."""

    @staticmethod
    def is_alive(obj) -> bool:
        """ Check if a QObject is still alive (not deleted).

            :param obj: The QObject to check.
            :return: True if the object is alive, False otherwise.
        """
        return obj is not None and not sip.isdeleted(obj)

    def _main_widget(self, module: ModuleBase) -> Optional[QWidget]:
        """ Return the main widget of a module, if it exists and is alive.

            :param module: The module to check.
            :return: The main widget of the module, or None if it doesn't exist or is not alive.
        """
        widget = getattr(module, "MainWidget", None)
        return widget if self.is_alive(widget) else None

    @staticmethod
    def _module_names(prefix: str) -> List[str]:
        """ Return a list of module names in sys.modules that match the given prefix.

            :param prefix: The prefix to match module names against.
            :return: A list of module names that match the prefix.
        """
        return [
            name for name in list(sys.modules)
            if name == prefix or name.startswith(prefix + ".")
        ]

    @staticmethod
    def _reload_prefix(module_name: str) -> str:
        """ Determine the base package prefix for reloading a module.

            :param module_name: The name of the module to reload.
            :return: The base package prefix for reloading.
        """
        module = sys.modules.get(module_name)
        base_pkg = module_name
        if not hasattr(module, "__path__"):
            base_pkg = module_name.rsplit(".", 1)[0]

        parts = base_pkg.split(".")
        return base_pkg if len(parts) >= 3 and parts[1] == "modules" else module_name

    def _restore_modules(self, prefix: str, modules: dict):
        """ Restore previously purged modules in sys.modules.

            :param prefix: The prefix of the modules to restore.
            :param modules: A dictionary of module names to module objects to restore.
        """
        for name in self._module_names(prefix):
            sys.modules.pop(name, None)
        sys.modules.update(modules)

    def reload_module_source(self, cls: Type[UiModuleBase]) -> Type[UiModuleBase]:
        """ Reload the class source, purging sibling files for feature modules.

            :param cls: The class to reload.
            :return: The reloaded class.
            :raises AttributeError: If the class is not found in the reloaded module.
        """
        module_name = cls.__module__
        purge_prefix = self._reload_prefix(module_name)
        purge_names = self._module_names(purge_prefix)
        purged_modules = {name: sys.modules[name] for name in purge_names}

        for name in purge_names:
            sys.modules.pop(name, None)

        try:
            fresh_module = importlib.import_module(module_name)
        except Exception:
            self._restore_modules(purge_prefix, purged_modules)
            raise

        try:
            return getattr(fresh_module, cls.__name__)
        except AttributeError as exc:
            self._restore_modules(purge_prefix, purged_modules)
            raise AttributeError(
                f"Klasse '{cls.__name__}' wurde nach dem Neuladen nicht in "
                f"'{module_name}' gefunden."
            ) from exc

    @staticmethod
    def _layout_for(widget: QWidget) -> QLayout:
        """ Return the layout of the parent container of the given widget.

            :param widget: The widget whose parent layout is to be retrieved.
            :return: The layout of the parent container.
            :raises NotImplementedError: If the parent container has no layout.
        """
        container = widget.parent()
        layout = container.layout() if container is not None else None
        if layout is None:
            raise NotImplementedError(
                "Der Eltern-Container des Frames besitzt kein Layout und kann "
                "nicht neu geladen werden.")
        return layout

    def _create_replacement_module(self, parent: ModuleBase, keyword: str,
                                   module_class: Type[UiModuleBase],
                                   use_directly: bool,
                                   widget_parent: Optional[QWidget]) -> UiModuleBase:
        """ Create a new instance of the module class and emit signals for its addition.

            :param parent: The parent module to which the new module will be added.
            :param keyword: The keyword/name of the module.
            :param module_class: The class of the module to instantiate.
            :param use_directly: Whether the module is used directly as a widget.
            :param widget_parent: The parent widget for the new module, if applicable.
            
            :return: The newly created module instance.
            
            :raises Exception: If the main widget cannot be created or is invalid.
        """
        parent.moduleAdding.emit(keyword, module_class)
        plugin = parent.get_plugin()
        module = module_class(
            parent=widget_parent if use_directly else None,
            parent_module=parent,
            name=keyword,
            module_name=keyword,
            plugin=plugin,
            logging_file_path=plugin.log_file_path,
            logging_level_debug=plugin.logging_level_debug,
        )
        parent.uiModuleAdding.emit(module)

        try:
            if use_directly:
                module.make_valid()

            widget = self._main_widget(module)
            if widget is None:
                raise AttributeError(
                    f"missing MainWidget object name on "
                    f"{module.__class__.__name__}/in ui file")
            widget._ui_module_base = module
        except Exception:
            module.unload(self_unload=False)
            raise

        return module

    @staticmethod
    def _emit_plugin_signal(parent: ModuleBase, signal: str, module: UiModuleBase):
        """ Emit a signal from the parent plugin, if it exists.

            :param parent: The parent module whose plugin signal is to be emitted.
            :param signal: The name of the signal to emit.
            :param module: The module to pass as an argument to the signal.
        """
        try:
            getattr(parent.get_plugin(), signal).emit(parent, module)
        except (StopIteration, ModuleNotFoundError):
            ...

    def _emit_replacement_added(self, parent: ModuleBase, module: UiModuleBase):
        """ Emit signals indicating that a new module has been added to the parent.

            :param parent: The parent module to which the new module has been added.
            :param module: The newly added module.
        """
        parent.moduleAdded.emit(module)
        self._emit_plugin_signal(parent, "submoduleAdded", module)
        parent.uiModuleAdded.emit(module)
        self._emit_plugin_signal(parent, "uiSubmoduleAdded", module)

    def _install_replacement_module(self, parent: ModuleBase, layout: QLayout,
                                    current_widget: QWidget,
                                    new_module: UiModuleBase):
        """ Replace the current widget in the layout with the new module's main widget.

            :param parent: The parent module containing the layout.
            :param layout: The layout in which the current widget resides.
            :param current_widget: The widget to be replaced.
            :param new_module: The new module whose main widget will replace the current widget.

            :raises RuntimeError: If the current widget is not found in the layout, or if the new module's main widget is invalid.
        """
        if layout.indexOf(current_widget) < 0:
            raise RuntimeError("Frame-Widget wurde in seinem Layout nicht gefunden.")

        object_name = current_widget.objectName()
        parent.is_object_name_valid(object_name)

        widget = self._main_widget(new_module)
        if widget is None:
            raise RuntimeError("Ersatzmodul besitzt kein gültiges 'MainWidget'.")

        replaced_item = layout.replaceWidget(current_widget, widget)
        if replaced_item is None:
            raise RuntimeError("Frame-Widget konnte im Layout nicht ersetzt werden.")

        widget.show()
        current_widget.hide()
        current_widget.setParent(None)

        replaced_widget = replaced_item.widget()
        if replaced_widget is not None:
            layout.removeWidget(replaced_widget)

        setattr(parent, object_name, widget)
        widget.setObjectName(object_name)

    @staticmethod
    def _add_layout_item(layout: QLayout, item,
                         grid_position: Optional[Tuple[int, int, int, int]]):
        """ Add a layout item (widget or layout) to the specified layout at the given grid position.

            :param layout: The layout to which the item will be added.
            :param item: The layout item (widget or layout) to add.
            :param grid_position: The grid position (row, column, rowSpan, columnSpan
                for QGridLayout) or None for other layouts.
        """
        widget = item.widget()
        child_layout = item.layout()

        if isinstance(layout, QGridLayout) and grid_position is not None:
            if widget is not None:
                layout.addWidget(widget, *grid_position)
            elif child_layout is not None:
                layout.addLayout(child_layout, *grid_position)
            else:
                layout.addItem(item, *grid_position)
        elif widget is not None:
            layout.addWidget(widget)
        else:
            layout.addItem(item)

    def _move_layout_contents(self, source: QWidget, target: QWidget):
        source_layout = source.layout()
        target_layout = target.layout()
        if source_layout is None or target_layout is None or source_layout is target_layout:
            return

        items = []
        for index in reversed(range(source_layout.count())):
            position = None
            if isinstance(source_layout, QGridLayout):
                position = source_layout.getItemPosition(index)

            item = source_layout.takeAt(index)
            if item is not None:
                items.append((item, position))

        for item, position in reversed(items):
            self._add_layout_item(target_layout, item, position)

    @staticmethod
    def _raise_for_direct_module_conflicts(current_module: UiModuleBase,
                                           new_module: UiModuleBase):
        """ Raise a KeyError if the new module has child modules with the same names as the current module.

            :param current_module: The current module being replaced.
            :param new_module: The new module being added.

            :raises KeyError: If there are conflicting child module names.
        """
        conflicts = set(new_module._modules).intersection(current_module._modules)
        if conflicts:
            raise KeyError(
                "Reload-Ersatzmodul enthält bereits Kind-Module mit gleichen "
                f"Namen: {', '.join(sorted(conflicts))}")

    def _adopt_direct_module_contents(self, current_module: UiModuleBase,
                                      new_module: UiModuleBase):
        """ Keep runtime-added child modules/widgets when a direct widget is reloaded.

            :param current_module: The current module being replaced.
            :param new_module: The new module being added.
        """
        self._move_layout_contents(current_module.MainWidget, new_module.MainWidget)

        child_modules = current_module._modules
        current_module._modules = {}
        new_module._modules.update(child_modules)

        for child_module in child_modules.values():
            child_module._parent = new_module
            child_widget = self._main_widget(child_module)
            object_name = child_widget.objectName() if child_widget is not None else ""
            if object_name:
                setattr(new_module, object_name, child_widget)

        new_module.MainWidget.updateGeometry()
        container = new_module.MainWidget.parent()
        if container is not None:
            container.updateGeometry()

    def reload_frame_in_place(self, module: UiModuleBase) -> UiModuleBase:
        """ Reload ``module`` and replace its live frame with a fresh instance.

            :param module: The module to reload.
            
            :return: The newly created module instance that replaces the old one.

            :raises ValueError: If the module has no parent or no valid main widget.
        """
        parent = module.get_parent()
        if parent is None:
            raise ValueError("Frame besitzt kein Eltern-Modul und kann nicht "
                             "neu geladen werden.")

        main_widget = self._main_widget(module)
        if main_widget is None:
            raise ValueError("Frame besitzt kein gültiges 'MainWidget'.")

        keyword = module.module_name
        use_directly = main_widget is module
        if not main_widget.objectName():
            raise ValueError("Frame-Widget besitzt keinen objectName und kann "
                             "nicht eindeutig ersetzt werden.")

        fresh_class = self.reload_module_source(module.__class__)
        layout = self._layout_for(main_widget)
        new_module = self._create_replacement_module(
            parent, keyword, fresh_class, use_directly, main_widget.parent())

        if use_directly:
            self._raise_for_direct_module_conflicts(module, new_module)

        try:
            self._install_replacement_module(parent, layout, main_widget, new_module)
            if use_directly:
                self._adopt_direct_module_contents(module, new_module)
        except Exception:
            new_module.unload(self_unload=False)
            raise

        module.unload(self_unload=True)
        if not use_directly and self.is_alive(main_widget):
            main_widget.deleteLater()

        parent._modules[keyword] = new_module
        self._emit_replacement_added(parent, new_module)
        return new_module

    def resolve_module_chain(self, widget: Optional[QWidget]) -> List[UiModuleBase]:
        """ Return reloadable modules from innermost clicked frame to outermost.

            :param widget: The widget under the mouse cursor.
            :return: A list of reloadable modules, innermost first.
        """
        if widget is None:
            return []

        try:
            module = UiModuleBase._get_module(widget)
        except StopIteration:
            return []

        chain: List[UiModuleBase] = []
        for _ in range(100):
            if not isinstance(module, ModuleBase) or isinstance(module, Plugin):
                break

            if (isinstance(module, UiModuleBase)
                    and self._main_widget(module) is not None
                    and module.__class__.__name__ != "TabModuleBase"
                    and (not chain or chain[-1] is not module)):
                chain.append(module)
            module = module.get_parent()

        return chain

    def module_global_rect(self, module: UiModuleBase) -> Optional[QRect]:
        """ Return the global rectangle of the module's main widget, if it exists and is visible.

            :param module: The module whose main widget's global rectangle is to be retrieved.
            :return: The global rectangle of the main widget, or None if it doesn't exist or
        """
        widget = self._main_widget(module)
        if widget is None or not widget.isVisible():
            return None
        return QRect(widget.mapToGlobal(QPoint(0, 0)), widget.size())


class _HighlightOverlay(QWidget):
    """Frameless, click-through overlay that marks the frame to be reloaded."""

    def __init__(self):
        flags = (Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                 | Qt.Tool | Qt.WindowTransparentForInput)
        super().__init__(None, flags)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self._text = ""

    def show_for(self, global_rect: QRect, text: str):
        """ Show the overlay for the given global rectangle and display the specified text.

            :param global_rect: The global rectangle to highlight.
            :param text: The text to display on the overlay.
        """
        self._text = text
        self.setGeometry(global_rect)
        self.show()
        self.raise_()
        self.update()

    def paintEvent(self, event):
        """ Paint the overlay with a semi-transparent fill and a border, and display the text if provided.

            :param event: The paint event.
        """
        painter = QPainter(self)
        rect = self.rect().adjusted(0, 0, -1, -1)
        painter.fillRect(rect, QColor(0, 120, 215, 45))

        pen = QPen(QColor(0, 120, 215))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(rect)

        if not self._text:
            return

        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        band = QRect(rect.left(), rect.top(), rect.width(), min(22, rect.height()))
        painter.fillRect(band, QColor(0, 120, 215, 210))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            band.adjusted(5, 0, -5, 0),
            Qt.AlignVCenter | Qt.AlignLeft,
            self._text)


class FramePicker(ModuleBase, QObject):
    """Interactive picker that hot-reloads the clicked Plan[Goo] frame."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        QObject.__init__(self, None)

        self._active = False
        self._reloader = FrameReloader()
        self._overlay: Optional[_HighlightOverlay] = None
        self._depth = 0
        self._last_innermost: Optional[UiModuleBase] = None
        self._action: Optional[QAction] = None

        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self.connect(self._timer.timeout, self._update_hover)

    def set_action(self, action: QAction):
        """ Set the QAction that toggles the frame picker. """
        self._action = action

    @property
    def is_active(self) -> bool:
        """ Return whether the frame picker is currently active. """
        return self._active

    def toggle(self):
        """ Toggle the frame picker on or off. """
        self.cancel() if self._active else self.start()

    def start(self):
        """ Start the frame picker, enabling interactive frame selection and reloading. """
        if self._active:
            return
        self._active = True
        self._depth = 0
        self._last_innermost = None
        self._overlay = _HighlightOverlay()
        QApplication.setOverrideCursor(Qt.CrossCursor)
        QApplication.instance().installEventFilter(self)
        self._timer.start()
        self._set_action_checked(True)
        self._status("Frame-Picker aktiv – Frame anklicken zum Neuladen. "
                     "Mausrad: Eltern-Frame · Esc/Rechtsklick: Abbrechen.")

    def cancel(self):
        """ Cancel the frame picker, restoring the previous state. """
        was_active = self._active
        self._stop()
        if was_active:
            self._status("Frame-Picker abgebrochen.", timeout=3000)

    def unload(self, self_unload: bool = False):
        """ Unload the frame picker, stopping any active selection and cleaning up resources. """
        self._stop()
        super().unload(self_unload)

    def _is_alive(self, obj) -> bool:
        """ Check if the given object is still alive (not deleted). """
        return self._reloader.is_alive(obj)

    def _stop(self):
        """ Stop the frame picker, removing event filters and hiding the overlay. """
        if not self._active:
            return
        self._active = False
        self._timer.stop()
        QApplication.instance().removeEventFilter(self)
        QApplication.restoreOverrideCursor()
        if self._is_alive(self._overlay):
            self._overlay.hide()
            self._overlay.deleteLater()
        self._overlay = None
        self._set_action_checked(False)

    def _set_action_checked(self, checked: bool):
        """ Set the checked state of the associated QAction, if it is still alive. """
        if self._is_alive(self._action):
            self._action.blockSignals(True)
            self._action.setChecked(checked)
            self._action.blockSignals(False)

    def _hide_overlay(self):
        """ Hide the overlay if it is still alive. """
        if self._is_alive(self._overlay):
            self._overlay.hide()

    def _widget_at(self, global_pos: QPoint) -> Optional[QWidget]:
        """ Return the widget at the given global position, temporarily hiding the overlay if necessary. """
        widget = QApplication.widgetAt(global_pos)
        if (self._is_alive(self._overlay) and widget is not None
                and widget.window() is self._overlay):
            self._overlay.hide()
            widget = QApplication.widgetAt(global_pos)
            self._overlay.show()
        return widget

    def _resolve_target(self, global_pos: QPoint
                        ) -> Tuple[Optional[UiModuleBase], List[UiModuleBase]]:
        """ Resolve the target module and its chain of parent modules at the given global position."""
        chain = self._reloader.resolve_module_chain(self._widget_at(global_pos))
        if not chain:
            self._last_innermost = None
            self._depth = 0
            return None, []

        if chain[0] is not self._last_innermost:
            self._last_innermost = chain[0]
            self._depth = 0

        return chain[min(self._depth, len(chain) - 1)], chain

    def _update_hover(self):
        """ Update the overlay and status message based on the current mouse position and depth. """
        if not self._active:
            return

        target, chain = self._resolve_target(QCursor.pos())
        if target is None:
            self._hide_overlay()
            self._status("Kein Plan[Goo]-Frame unter dem Mauszeiger.")
            return

        rect = self._reloader.module_global_rect(target)
        if rect is None:
            self._hide_overlay()
            return

        index = min(self._depth, len(chain) - 1)
        depth_info = f"  [{index + 1}/{len(chain)}]" if len(chain) > 1 else ""
        if self._is_alive(self._overlay):
            self._overlay.show_for(rect, f"{target.__class__.__name__}{depth_info}")
        self._status(f"Neu laden: {target.__class__.__name__} "
                     f"({target.module_name}) – Klick zum Neuladen, "
                     f"Mausrad für Eltern-Frame ({index + 1}/{len(chain)}).")

    def eventFilter(self, obj, event):
        """ Event filter to handle mouse and keyboard events for the frame picker. """
        if not self._active:
            return False

        etype = event.type()
        if etype == QEvent.MouseButtonPress:
            self._commit(QCursor.pos()) if event.button() == Qt.LeftButton else self.cancel()
            return True

        if etype in (QEvent.MouseButtonRelease, QEvent.MouseButtonDblClick):
            return True

        if etype == QEvent.Wheel:
            delta = event.angleDelta().y()
            if delta:
                self._depth = max(0, min(99, self._depth + (1 if delta > 0 else -1)))
                self._update_hover()
            return True

        if etype == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self.cancel()
            return True

        return False

    def _commit(self, global_pos: QPoint):
        """ Commit the selection of the frame under the mouse cursor and initiate the reload process. """
        target, _ = self._resolve_target(global_pos)
        self._stop()
        if target is None:
            self._status("Kein Frame ausgewählt.", timeout=4000)
            return
        QTimer.singleShot(0, lambda: self._do_reload(target))

    def _do_reload(self, module: UiModuleBase):
        """ Reload the specified module and handle any exceptions that occur during the process. """
        name = module.__class__.__name__
        try:
            new_module = self._reloader.reload_frame_in_place(module)
        except Exception as exc:  # dev tool: surface every failure
            self.log(f"Frame-Reload fehlgeschlagen für {name}: "
                     f"{traceback.format_exc()}", level=self.ERROR)
            self._message_error(
                f"Frame '{name}' konnte nicht neu geladen werden:\n\n{exc}")
            return

        self.log(f"Frame '{name}' neu geladen.", level=self.INFO)
        self._message_success(
            f"Frame '{new_module.__class__.__name__}' neu geladen.")

    def _status(self, text: str, timeout: int = 0):
        """ Show a status message in the QGIS main window's status bar, if available. """
        iface = self.iface
        if iface is not None and iface.mainWindow() is not None:
            iface.mainWindow().statusBar().showMessage(text, timeout)

    def _message_success(self, text: str):
        """ Show a success message in the QGIS message bar, if available. """
        if self.iface is not None:
            self.iface.messageBar().pushSuccess("Frame-Picker", text)

    def _message_error(self, text: str):
        """ Show an error message in the QGIS message bar, if available. """
        if self.iface is not None:
            self.iface.messageBar().pushWarning("Frame-Picker", text)
