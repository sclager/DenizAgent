from __future__ import annotations

import ctypes

from PySide6.QtCore import QObject, QTimer, Signal


class HotkeyManager(QObject):
    hotkey_pressed = Signal()

    VK_CONTROL = 0x11
    VK_SHIFT = 0x10
    VK_D = 0x44

    def __init__(
        self,
        hotkey: str = "ctrl+shift+d",
    ) -> None:
        super().__init__()

        self.hotkey = hotkey
        self._registered = False
        self._combination_was_pressed = False

        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(
            self._check_hotkey
        )

        self.user32 = ctypes.windll.user32

    def register(self) -> None:
        if self._registered:
            return

        self._registered = True
        self.timer.start()

        print(
            "[OK] Global kısayol aktif: "
            "Ctrl + Shift + D"
        )

    def unregister(self) -> None:
        if not self._registered:
            return

        self.timer.stop()
        self._registered = False
        self._combination_was_pressed = False

    def _is_key_pressed(
        self,
        virtual_key: int,
    ) -> bool:
        return bool(
            self.user32.GetAsyncKeyState(
                virtual_key
            )
            & 0x8000
        )

    def _check_hotkey(self) -> None:
        ctrl_pressed = self._is_key_pressed(
            self.VK_CONTROL
        )

        shift_pressed = self._is_key_pressed(
            self.VK_SHIFT
        )

        d_pressed = self._is_key_pressed(
            self.VK_D
        )

        combination_pressed = (
            ctrl_pressed
            and shift_pressed
            and d_pressed
        )

        # Tuşlara basılı tutulduğu sürece menünün sürekli
        # açılıp kapanmasını engeller.
        if (
            combination_pressed
            and not self._combination_was_pressed
        ):
            self._combination_was_pressed = True
            self.hotkey_pressed.emit()

        if not combination_pressed:
            self._combination_was_pressed = False