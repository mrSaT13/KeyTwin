"""KeyTwin — copy token -> Registry GUI (PySide6).
(c) 2026 mrSaT13. MIT License. See LICENSE file.
https://github.com/mrSaT13/KeyTwin
Гибрид из 3 батников:
  logic: copy_token_to_pc.bat / RU (дедуп + проверка лога по 0x00000000 + fallback -src/-dest)
  texts: copy_ep_to_reestr.bat (подробные подсказки, диагностика, PIN JaCarta PKI)
  + выбор языка RU/EN.
Запуск: python copy_token_gui.py
"""
import ctypes
import shutil
import subprocess
import sys
from pathlib import Path

APP_NAME = "KeyTwin"
APP_VERSION = "1.2.0"
APP_AUTHOR = "mrSaT13"
APP_SITE = "https://github.com/mrSaT13/KeyTwin"
APP_ORG = "KeyTwin"

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QListWidget, QLineEdit,
    QComboBox, QCheckBox, QGroupBox, QProgressBar, QMessageBox,
    QSystemTrayIcon, QMenu,
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QThread, Signal, QSettings


def resource_path(name: str) -> str:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        p = Path(base) / name
        if p.exists():
            return str(p)
    try:
        here = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    except Exception:
        here = Path.cwd()
    p = here / name
    if p.exists():
        return str(p)
    return str(Path.cwd() / name)


def app_icon() -> QIcon:
    for n in ("token_icon.ico", "token_icon.png", "app_icon.ico", "app_icon.png"):
        p = resource_path(n)
        if Path(p).exists():
            return QIcon(p)
    return QIcon()


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def find_csptest() -> str:
    cands = [
        r"C:\Program Files\Crypto Pro\CSP\csptest.exe",
        r"C:\Program Files\CryptoPro\CSP\csptest.exe",
        r"C:\Program Files (x86)\Crypto Pro\CSP\csptest.exe",
        r"C:\Program Files (x86)\CryptoPro\CSP\csptest.exe",
    ]
    for c in cands:
        if Path(c).exists():
            return c
    w = shutil.which("csptest.exe")
    return w or ""


def run_raw(exe: str, args: list) -> str:
    """Запуск csptest, декодируем как получится (utf-8/cp866/cp1251)."""
    try:
        pr = subprocess.run([exe] + args, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=120)
        raw = pr.stdout or b""
    except FileNotFoundError as e:
        return f"[ERROR] {e}"
    except subprocess.TimeoutExpired:
        return "[ERROR] timeout"
    for enc in ("utf-8", "cp866", "cp1251"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", errors="replace")


def short_name(src: str) -> str:
    s = src.strip().strip('"')
    parts = [p for p in s.replace("/", "\\").split("\\") if p.strip()]
    return parts[-1].strip() if parts else "copy1"


def mask_secrets(text: str, secrets: list) -> str:
    """Вырезать PIN/пароли из текста лога. Лог всегда маскирован,
    чекбокс 'Показать пароли' влияет только на поля ввода."""
    out = str(text or "")
    for s in secrets:
        if s:
            out = out.replace(s, "***")
    return out


STR = {
    "ru": {
        "title": "KeyTwin — копия ЭЦП с токена в реестр (КриптоПро 5)",
        "lang": "Язык:", "admin_yes": "● Админ", "admin_no": "● НЕ админ",
        "admin_tip": "Контейнеры пользователя и админа различаются. Если токен не виден — попробуйте БЕЗ запуска от админа, и наоборот.",
        "cspt_ok": "КриптоПро:", "cspt_bad": "csptest.exe НЕ НАЙДЕН — установите КриптоПро CSP 5",
        "g1": "Шаг 1. Контейнер на токене (токен должен быть вставлен)",
        "refresh": "🔄 Обновить список", "reading": "Сканирую контейнеры...",
        "found": "Найдено контейнеров:", "manual_cb": "Ввести вручную:",
        "manual_ph": "ПОЛНОЕ имя контейнера, напр. \\\\.\\Aladdin\\...",
        "nfound": "Контейнеры не найдены. Проверьте: 1) токен вставлен/светится 2) виден в Панели Рутокен/JaCarta 3) в КриптоПро CSP → Оборудование → Считыватели есть Rutoken/JaCarta 4) попробуйте без прав админа 5) Инструменты КриптоПро → Контейнеры.",
        "g2": "Шаг 2. Имя копии в реестре",
        "dst_ph": "Имя копии, напр. ivanov-copy",
        "dest_to": "Копия будет: \\\\.\\REGISTRY\\",
        "g3": "Шаг 3. PIN-коды",
        "pin_tip": "Стандартные PIN: Рутокен — 12345678 • JaCarta — 11111111 (PKI: 1234567890) • eToken — 1234567890. Если меняли — вводите свой.",
        "pin1": "PIN токена (пусто = без пароля):",
        "pin2": "Пароль копии в ПК (пусто = без пароля, но лучше задать):",
        "show": "Показать пароли",
        "run": "▶ Скопировать в реестр + установить сертификат",
        "running": "Выполняю, ждите...",
        "need_src": "Выберите контейнер из списка или введите вручную.",
        "need_dst": "Введите имя копии.",
        "need_cspt": "Не найден csptest.exe. Установите КриптоПро CSP 5.",
        "copying": "ШАГ 2. Копирование → РЕЕСТР",
        "fallback": "Новый синтаксис не дал 0x00000000 — пробую старый -src/-dest...",
        "cinstall": "ШАГ 3. Установка сертификата в хранилище ЛИЧНЫЕ",
        "done": "ГОТОВО! Скопировано в \\\\.\\REGISTRY\\",
        "check": "Проверка: КриптоПро CSP → Сервис → Посмотреть сертификаты в контейнере → выберите REGISTRY-копию. Перезапустите браузер. ВАЖНО: оригинал токена не теряйте! Копия умрёт вместе с Windows. Ключ теперь всегда подключён — поставьте пароль на ПК.",
        "err_copy": "ОШИБКА КОПИРОВАНИЯ. Причины: 1) неверный PIN 2) такое имя уже есть в реестре 3) ключ НЕЭКСПОРТИРУЕМЫЙ 0x8009000B (токены ФНС после 2022 копировать нельзя) 4) нужен запуск от администратора.",
        "readers": "Считыватели:",
        "ok_box": "Готово", "err_box": "Ошибка",
        "about_btn": "ⓘ О программе",
        "about_title": "О программе KeyTwin",
        "about_text": (
            "<b>KeyTwin {ver}</b> — копия ключа ЭЦП с токена (Рутокен / JaCarta / eToken) "
            "в реестр Windows через штатный <b>КриптоПро CSP 5 (csptest)</b>.<br><br>"
            "<b>Разработчик:</b> {author}<br>"
            "<b>GitHub:</b> <a href='{site}'>{site}</a><br><br>"
            "<b>Что нужно:</b> Windows, лицензионный КриптоПро CSP 5, вставленный токен, "
            "установленные драйверы носителя.<br><br>"
            "<b>Как пользоваться:</b><br>"
            "1. Нажми «Обновить список» и выбери контейнер.<br>"
            "2. Введи имя копии (латиницей, напр. ivanov-copy).<br>"
            "3. Введи PIN токена и придумай пароль копии.<br>"
            "4. Нажми «Скопировать» и дождись 0x00000000.<br>"
            "5. Проверь: КриптоПро → Сервис → Посмотреть сертификаты в контейнере → REGISTRY-копия.<br><br>"
            "PIN в лог <b>никогда не пишется</b> (там ***). Галочка «Показать пароли» "
            "открывает только поля ввода на экране.<br>"
            "Копируй только свои ключи. Неэкспортируемые ключи (ФНС после 2022) скопировать нельзя — это нормально.<br>"
            "Копия умирает вместе с Windows — храни оригинал токена!"
        ),
    },
    "en": {
        "title": "KeyTwin — copy ECP from token to PC registry (CryptoPro 5)",
        "lang": "Language:", "admin_yes": "● Admin", "admin_no": "● NOT admin",
        "admin_tip": "User and admin containers differ. If token invisible — try WITHOUT admin run and vice versa.",
        "cspt_ok": "CryptoPro:", "cspt_bad": "csptest.exe NOT FOUND — install CryptoPro CSP 5",
        "g1": "Step 1. Token container (token must be inserted)",
        "refresh": "🔄 Rescan", "reading": "Scanning containers...",
        "found": "Containers found:", "manual_cb": "Enter manually:",
        "manual_ph": "FULL container name, e.g. \\\\.\\Aladdin\\...",
        "nfound": "No containers found. Check: 1) token inserted/LED on 2) visible in Rutoken/JaCarta panel 3) CryptoPro CSP → Hardware → Readers has Rutoken/JaCarta 4) try without admin rights 5) CryptoPro Tools → Containers.",
        "g2": "Step 2. Registry copy name",
        "dst_ph": "Copy name, e.g. ivanov-copy",
        "dest_to": "Will copy to: \\\\.\\REGISTRY\\",
        "g3": "Step 3. PINs",
        "pin_tip": "Defaults: Rutoken — 12345678 • JaCarta — 11111111 (PKI: 1234567890) • eToken — 1234567890.",
        "pin1": "Token PIN (empty = none):",
        "pin2": "PC copy password (empty = none, better set one):",
        "show": "Show passwords",
        "run": "▶ Copy to registry + install certificate",
        "running": "Working, please wait...",
        "need_src": "Select a container or enter it manually.",
        "need_dst": "Enter a copy name.",
        "need_cspt": "csptest.exe not found. Install CryptoPro CSP 5.",
        "copying": "STEP 2. Copying → REGISTRY",
        "fallback": "New syntax gave no 0x00000000 — trying legacy -src/-dest...",
        "cinstall": "STEP 3. Installing certificate to Personal store",
        "done": "DONE! Copied to \\\\.\\REGISTRY\\",
        "check": "Verify: CryptoPro CSP → Service → View certs in container → pick REGISTRY copy. Restart browser. NOTE: keep the token! Registry copy dies with Windows. Set a PC password — key is now always attached.",
        "err_copy": "COPY ERROR. Reasons: 1) wrong token PIN 2) name already exists 3) NON-EXPORTABLE key 0x8009000B (FNS tokens after 2022 can't be copied) 4) run as Administrator.",
        "readers": "Readers:",
        "ok_box": "Done", "err_box": "Error",
        "about_btn": "ⓘ About",
        "about_title": "About KeyTwin",
        "about_text": (
            "<b>KeyTwin {ver}</b> — copy an E-Signature key from a token (Rutoken / JaCarta / eToken) "
            "to the Windows registry via stock <b>CryptoPro CSP 5 (csptest)</b>.<br><br>"
            "<b>Developer:</b> {author}<br>"
            "<b>GitHub:</b> <a href='{site}'>{site}</a><br><br>"
            "<b>Requirements:</b> Windows, licensed CryptoPro CSP 5, token inserted, carrier drivers installed.<br><br>"
            "<b>How to use:</b><br>"
            "1. Press Rescan and pick a container.<br>"
            "2. Enter a copy name (latin, e.g. ivanov-copy).<br>"
            "3. Enter the token PIN and set a password for the copy.<br>"
            "4. Press Copy and wait for 0x00000000.<br>"
            "5. Verify: CryptoPro → Service → View certs in container → REGISTRY copy.<br><br>"
            "PINs are <b>never written to the log</b> (shown as ***). The 'Show passwords' checkbox "
            "only reveals the input fields on screen.<br>"
            "Copy only your own keys. Non-exportable keys (FNS after 2022) cannot be copied — that's expected.<br>"
            "A registry copy dies with Windows — keep the original token!"
        ),
    },
}


class ScanThread(QThread):
    done = Signal(str, list)  # raw, containers

    def __init__(self, exe: str):
        super().__init__()
        self.exe = exe

    def run(self):
        raw1 = run_raw(self.exe, ["-keyset", "-enum_cont", "-fqcn", "-verifyc"])
        raw2 = run_raw(self.exe, ["-keyset", "-enum_cont", "-fqcn", "-verifyc", "-machinekeys"])
        raw = (raw1 + "\n" + raw2).strip()
        seen, out = set(), []
        for line in raw.splitlines():
            s = line.strip()
            if len(s) >= 2 and s[:2] == "\\\\":
                if s not in seen:  # дедуп как в copy_token_to_pc.bat (лучше чем в ep_to_reestr)
                    seen.add(s)
                    out.append(s)
        self.done.emit(raw, out)


class CopyThread(QThread):
    line = Signal(str)
    finished_ok = Signal(bool, str)  # ok, log

    def __init__(self, exe, src, dst, pin1, pin2):
        super().__init__()
        self.exe, self.src, self.dst = exe, src, dst
        self.pin1, self.pin2 = pin1, pin2

    def run(self):
        dest = f"\\\\.\\REGISTRY\\{self.dst}"
        secrets = [self.pin1, self.pin2]
        # новый синтаксис (в лог — только маскированная версия!)
        cmd = [self.exe, "-keycopy", "-contsrc", self.src, "-contdest", dest]
        disp = [self.exe, "-keycopy", "-contsrc", self.src, "-contdest", dest]
        if self.pin1:
            cmd += ["-pinsrc", self.pin1]
            disp += ["-pinsrc", "***"]
        cmd += ["-pindest", self.pin2 if self.pin2 else ""]
        disp += ["-pindest", "***" if self.pin2 else "(пусто)"]
        self.line.emit(mask_secrets(" ".join(f'"{c}"' if " " in c else c for c in disp), secrets))
        log1 = run_raw(self.exe, cmd[1:])
        self.line.emit(mask_secrets(log1, secrets))
        if "0x00000000" in log1:
            self.finished_ok.emit(True, log1)
            return
        self.line.emit(STR["ru"]["fallback"] if False else "fallback: -src/-dest ...")
        cmd2 = [self.exe, "-keycopy", "-src", self.src, f"-pinsrc={self.pin1}",
                "-dest", dest, f"-pindest={self.pin2}"]
        disp2 = [self.exe, "-keycopy", "-src", self.src, "-pinsrc=***",
                 "-dest", dest, "-pindest=***"]
        self.line.emit(mask_secrets(" ".join(f'"{c}"' if " " in c else c for c in disp2), secrets))
        log2 = run_raw(self.exe, cmd2[1:])
        self.line.emit(mask_secrets(log2, secrets))
        self.finished_ok.emit("0x00000000" in log2, log1 + "\n" + log2)


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(app_icon())
        self.setWindowTitle(f"{APP_NAME} — копирование ЭЦП с токена в реестр")
        self._allow_quit = False
        self.cfg = QSettings(APP_ORG, APP_NAME)
        self.lang = self.cfg.value("lang", "ru")
        if self.lang not in STR:
            self.lang = "ru"
        self.cspt = find_csptest()
        self.containers: list = []
        self._build()
        self.retranslate()
        self.resize(760, 720)
        self.setup_tray()

    def setup_tray(self):
        """Трей с иконкой и меню: Показать / Обновить / Копировать / Выход."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = None
            return
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(app_icon())
        self.tray.setToolTip(f"{APP_NAME} — копия ЭЦП с токена в реестр")
        menu = QMenu(self)

        act_show = QAction("Показать / Скрыть", self)
        act_show.triggered.connect(self.toggle_window)
        menu.addAction(act_show)

        act_scan = QAction("🔄 Обновить список", self)
        act_scan.triggered.connect(self.scan_from_tray)
        menu.addAction(act_scan)

        act_run = QAction("▶ Скопировать в реестр", self)
        act_run.triggered.connect(self.copy_from_tray)
        menu.addAction(act_run)

        act_about = QAction("ⓘ О программе", self)
        act_about.triggered.connect(self.show_about)
        menu.addAction(act_about)

        menu.addSeparator()

        act_quit = QAction("Выход", self)
        act_quit.triggered.connect(self.quit_from_tray)
        menu.addAction(act_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def toggle_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_window()

    def scan_from_tray(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.scan()

    def copy_from_tray(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.copy_flow()

    def tray_notify(self, title, text):
        try:
            if getattr(self, "tray", None):
                self.tray.showMessage(title, text, QSystemTrayIcon.Information, 5000)
        except Exception:
            pass

    def quit_from_tray(self):
        self._allow_quit = True
        QApplication.quit()

    def show_about(self):
        """Модальное окно 'О программе': кто сделал, версия, как пользоваться."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle(self.t("about_title"))
        dlg.setWindowIcon(app_icon())
        dlg.setModal(True)
        dlg.resize(520, 480)
        lay = QVBoxLayout(dlg)
        lbl = QLabel(self.t("about_text").format(ver=APP_VERSION, author=APP_AUTHOR, site=APP_SITE))
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.RichText)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        lay.addWidget(lbl)
        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.accepted.connect(dlg.accept)
        lay.addWidget(btns)
        dlg.exec()

    def closeEvent(self, event):
        # крестик -> свернуть в трей вместо закрытия
        if not self._allow_quit and getattr(self, "tray", None) is not None and self.tray.isVisible():
            event.ignore()
            self.hide()
            self.tray_notify(APP_NAME, "Свернуто в трей. Правый клик — меню, двойной клик — показать.")
            return
        # затереть PIN из памяти при реальном выходе
        try:
            self.inp_p1.clear()
            self.inp_p2.clear()
        except Exception:
            pass
        super().closeEvent(event)

    def t(self, k: str) -> str:
        return STR[self.lang].get(k, k)

    def _build(self):
        c = QWidget()
        self.setCentralWidget(c)
        v = QVBoxLayout(c)
        v.setSpacing(10)

        top = QHBoxLayout()
        self.lbl_lang = QLabel()
        self.cb_lang = QComboBox()
        self.cb_lang.addItems(["ru", "en"])
        self.cb_lang.setCurrentText(self.lang)
        self.cb_lang.currentTextChanged.connect(self._chlang)
        self.lbl_admin = QLabel()
        adm = is_admin()
        self.lbl_admin.setText(f"{'🟢' if adm else '🟡'} {STR[self.lang]['admin_yes' if adm else 'admin_no']}")
        self.lbl_admin.setToolTip(STR[self.lang]["admin_tip"])
        self.lbl_cspt = QLabel()
        self.lbl_cspt.setTextInteractionFlags(Qt.TextSelectableByMouse)
        top.addWidget(self.lbl_lang)
        top.addWidget(self.cb_lang)
        top.addStretch(1)
        top.addWidget(self.lbl_admin)
        self.btn_about = QPushButton()
        self.btn_about.clicked.connect(self.show_about)
        top.addWidget(self.btn_about)
        v.addLayout(top)
        v.addWidget(self.lbl_cspt)

        g1 = QGroupBox()
        self.g1 = g1
        l1 = QVBoxLayout(g1)
        row = QHBoxLayout()
        self.btn_scan = QPushButton()
        self.btn_scan.clicked.connect(self.scan)
        row.addWidget(self.btn_scan)
        row.addStretch(1)
        l1.addLayout(row)
        self.lst = QListWidget()
        self.lst.itemSelectionChanged.connect(self._pick)
        l1.addWidget(self.lst)
        mrow = QHBoxLayout()
        self.cb_manual = QCheckBox()
        self.cb_manual.toggled.connect(lambda on: self.inp_manual.setEnabled(on))
        self.inp_manual = QLineEdit()
        self.inp_manual.setEnabled(False)
        self.inp_manual.textChanged.connect(lambda _: self._pick())
        mrow.addWidget(self.cb_manual)
        mrow.addWidget(self.inp_manual, 1)
        l1.addLayout(mrow)
        v.addWidget(g1)

        g2 = QGroupBox()
        self.g2 = g2
        l2 = QVBoxLayout(g2)
        self.inp_dst = QLineEdit()
        self.inp_dst.textChanged.connect(self._dst_tip)
        l2.addWidget(self.inp_dst)
        self.lbl_dest = QLabel()
        l2.addWidget(self.lbl_dest)
        v.addWidget(g2)

        g3 = QGroupBox()
        self.g3 = g3
        l3 = QVBoxLayout(g3)
        self.lbl_pin_tip = QLabel()
        self.lbl_pin_tip.setWordWrap(True)
        l3.addWidget(self.lbl_pin_tip)
        f1 = QHBoxLayout()
        self.lbl_p1 = QLabel()
        self.inp_p1 = QLineEdit()
        self.inp_p1.setEchoMode(QLineEdit.Password)
        f1.addWidget(self.lbl_p1)
        f1.addWidget(self.inp_p1, 1)
        l3.addLayout(f1)
        f2 = QHBoxLayout()
        self.lbl_p2 = QLabel()
        self.inp_p2 = QLineEdit()
        self.inp_p2.setEchoMode(QLineEdit.Password)
        f2.addWidget(self.lbl_p2)
        f2.addWidget(self.inp_p2, 1)
        l3.addLayout(f2)
        self.cb_show = QCheckBox()
        self.cb_show.toggled.connect(self._show)
        l3.addWidget(self.cb_show)
        v.addWidget(g3)

        self.btn_run = QPushButton()
        self.btn_run.setMinimumHeight(44)
        self.btn_run.clicked.connect(self.copy_flow)
        v.addWidget(self.btn_run)

        self.bar = QProgressBar()
        self.bar.setRange(0, 0)
        self.bar.hide()
        v.addWidget(self.bar)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFontFamily("Consolas")
        v.addWidget(self.log, 1)

        self.setStyleSheet("""
            QMainWindow, QWidget { font-size: 13px; }
            QPushButton { padding: 8px 14px; border-radius: 8px; }
            QPushButton#run { background: #16a34a; color: white; font-weight: bold; font-size: 14px; }
            QPushButton#run:disabled { background: #9ca3af; }
            QListWidget { border-radius: 8px; padding: 4px; }
            QLineEdit { padding: 7px; border-radius: 8px; border: 1px solid #9ca3af; }
            QGroupBox { font-weight: bold; border: 1px solid #9ca3af; border-radius: 10px; margin-top: 12px; padding-top: 14px; }
            QTextEdit { border-radius: 8px; background: #111827; color: #d1fae5; }
        """)
        self.btn_run.setObjectName("run")

    # ---- i18n ----
    def _chlang(self, l):
        self.lang = l if l in STR else "ru"
        self.cfg.setValue("lang", self.lang)
        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(self.t("title"))
        self.lbl_lang.setText(self.t("lang"))
        adm = is_admin()
        self.lbl_admin.setText(f"{'🟢' if adm else '🟡'} {self.t('admin_yes' if adm else 'admin_no')}")
        self.lbl_admin.setToolTip(self.t("admin_tip"))
        self.lbl_cspt.setText(f"{self.t('cspt_ok')} {self.cspt}" if self.cspt else self.t("cspt_bad"))
        self.g1.setTitle(self.t("g1"))
        self.btn_scan.setText(self.t("refresh"))
        self.cb_manual.setText(self.t("manual_cb"))
        self.inp_manual.setPlaceholderText(self.t("manual_ph"))
        self.g2.setTitle(self.t("g2"))
        self.inp_dst.setPlaceholderText(self.t("dst_ph"))
        self.g3.setTitle(self.t("g3"))
        self.lbl_pin_tip.setText(self.t("pin_tip"))
        self.lbl_p1.setText(self.t("pin1"))
        self.lbl_p2.setText(self.t("pin2"))
        self.cb_show.setText(self.t("show"))
        self.btn_run.setText(self.t("run"))
        self.btn_about.setText(self.t("about_btn"))
        self._dst_tip()

    # ---- logic ----
    def _show(self, on):
        m = QLineEdit.Normal if on else QLineEdit.Password
        self.inp_p1.setEchoMode(m)
        self.inp_p2.setEchoMode(m)

    def _dst_tip(self):
        d = self.inp_dst.text().strip() or "…"
        self.lbl_dest.setText(f"{self.t('dest_to')}{d}")

    def _pick(self):
        """При выборе — подставить имя копии по умолчанию: short-copy."""
        src = self.current_src()
        if src and not getattr(self, "_dst_touched", False):
            self.inp_dst.setText(f"{short_name(src)}-copy")

    def current_src(self) -> str:
        if self.cb_manual.isChecked():
            return self.inp_manual.text().strip().strip('"')
        it = self.lst.currentItem()
        return it.text().strip() if it else ""

    def append(self, s: str):
        self.log.append(s)

    def scan(self):
        if not self.cspt:
            QMessageBox.critical(self, self.t("err_box"), self.t("need_cspt"))
            return
        self.btn_scan.setEnabled(False)
        self.bar.show()
        self.append(self.t("reading"))
        self.th = ScanThread(self.cspt)
        self.th.done.connect(self._scanned)
        self.th.start()

    def _scanned(self, raw, items):
        self.bar.hide()
        self.btn_scan.setEnabled(True)
        self.append(raw)
        self.containers = items
        self.lst.clear()
        for i in items:
            self.lst.addItem(i)
        if items:
            self.append(f"{self.t('found')} {len(items)}")
            self.lst.setCurrentRow(0)
        else:
            self.append(self.t("nfound"))
            self.append(self.t("readers"))
            self.append(run_raw(self.cspt, ["-enum", "-info", "-type", "PP_ENUMREADERS"]))

    def copy_flow(self):
        if not self.cspt:
            QMessageBox.critical(self, self.t("err_box"), self.t("need_cspt"))
            return
        src = self.current_src()
        dst = self.inp_dst.text().strip().strip('"').strip("\\")
        if not src:
            QMessageBox.warning(self, self.t("err_box"), self.t("need_src"))
            return
        if not dst or dst == "…":
            QMessageBox.warning(self, self.t("err_box"), self.t("need_dst"))
            return
        # уберечь от ввода полного dest-пути — оставить только имя
        dst = short_name(dst) if "\\" in dst else dst
        self.inp_dst.setText(dst)
        self.btn_run.setEnabled(False)
        self.bar.show()
        self.append(f"{self.t('copying')}: {src} → \\\\.\\REGISTRY\\{dst}")
        self.cth = CopyThread(self.cspt, src, dst, self.inp_p1.text(), self.inp_p2.text())
        self.cth.line.connect(self.append)
        self.cth.finished_ok.connect(lambda ok, lg: self._copied(ok, dst))
        self.cth.start()

    def _copied(self, ok: bool, dst: str):
        if not ok:
            self.bar.hide()
            self.btn_run.setEnabled(True)
            self.append(self.t("err_copy"))
            QMessageBox.critical(self, self.t("err_box"), self.t("err_copy"))
            return
        self.append(self.t("cinstall"))
        out = run_raw(self.cspt, ["-property", "-cinstall", "-cont", f"\\\\.\\REGISTRY\\{dst}"])
        self.append(out)
        self.bar.hide()
        self.btn_run.setEnabled(True)
        self.append(f"{self.t('done')}{dst}")
        self.append(self.t("check"))
        self.tray_notify(APP_NAME, f"{self.t('done')}{dst}")
        QMessageBox.information(self, self.t("ok_box"), f"{self.t('done')}{dst}")


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(app_icon())
    app.setQuitOnLastWindowClosed(False)  # чтобы крестик сворачивал в трей
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_ORG)
    w = Main()
    w.show()
    if w.cspt:
        w.scan()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
