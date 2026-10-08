"""Pulse: compact notification island with fake and read-only D-Bus sources."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
from pulse.platforms import is_windows


def choose_backend(requested, qt_version):
    if requested != "auto":
        return requested
    if is_windows():
        return "windows"
    if os.environ.get("XDG_SESSION_TYPE") != "wayland":
        return "xcb"
    try:
        system_qt = subprocess.check_output(
            ["qmake6", "-query", "QT_VERSION"], text=True, timeout=3
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "xcb"
    module = Path("/usr/lib/qt6/qml/org/kde/layershell/qmldir")
    return "layer-shell" if system_qt == qt_version and module.exists() else "xcb"


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] in ('task', 'run'):
        from pulse.tasks.cli import main as task_main
        return task_main(arguments)
    parser = argparse.ArgumentParser(description=__doc__, epilog="Tasks: pulse run -- COMMAND [ARGS...]; pulse task --help")
    parser.add_argument("--backend", choices=["auto", "windows", "xcb", "layer-shell", "offscreen"], default="auto")
    sources = parser.add_mutually_exclusive_group()
    sources.add_argument("--demo", action="store_true", help="play scripted fake notifications")
    sources.add_argument("--observe", action="store_true", help="mirror desktop notifications without owning the bus")
    parser.add_argument("--music", action=argparse.BooleanOptionalAction, default=None,
                        help="watch music (enabled by default on Windows, or with --observe on Linux)")
    parser.add_argument("--volume", action=argparse.BooleanOptionalAction, default=None,
                        help="watch output volume changes (enabled with --observe)")
    parser.add_argument("--tasks", action=argparse.BooleanOptionalAction, default=True,
                        help="show explicitly published local task events (disabled in demo mode)")
    parser.add_argument("--settings", action="store_true", help="open the settings window at startup")
    parser.add_argument("--doctor", action="store_true", help="check desktop dependencies and exit")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--renderer", choices=["auto", "software", "hardware"], default="auto",
                        help="auto uses software on XWayland/X11 to avoid GLX startup failures")
    parser.add_argument("--reduced-motion", action="store_true")
    parser.add_argument("--theme", help="theme name (default, ocean, rose) or JSON file path")
    from pulse.ui.pet_catalog import BY_ID
    parser.add_argument("--pet", choices=tuple(BY_ID), help="choose an idle pet for this run")
    parser.add_argument("--list-pets", action="store_true", help="list available pet IDs and exit")
    parser.add_argument("--config", type=Path, help="read settings from this TOML file")
    parser.add_argument("--dnd", action="store_true", help="suppress ordinary Pulse cards; allow critical by default")
    parser.add_argument("--quit-after", type=float, default=0, metavar="SECONDS")
    history_commands = parser.add_mutually_exclusive_group()
    history_commands.add_argument("--history", type=int, nargs="?", const=20, metavar="COUNT",
                                  help="print recent saved notifications (default: 20) and exit")
    history_commands.add_argument("--clear-history", action="store_true", help="delete saved notification history and exit")
    parser.add_argument("--history-file", type=Path, help="override the SQLite history path")
    parser.add_argument("--no-history", action="store_true", help="do not save live notifications for this run")
    args = parser.parse_args(argv)
    if args.doctor:
        from pulse.diagnostics import report
        return report()
    if is_windows() and (args.observe or args.volume):
        parser.error('Desktop notification and volume sources are Linux-only in this preview. On Windows, launch Pulse without these flags for the island and task events.')
    if args.backend == 'windows' and not is_windows():
        parser.error('--backend windows requires Windows')
    if is_windows() and args.backend in ('xcb', 'layer-shell'):
        parser.error('Use --backend auto or windows on Windows')
    if args.demo and (args.music or args.volume):
        parser.error("--demo cannot be combined with live --music or --volume")
    if args.list_pets:
        for id, pet in BY_ID.items():
            print(f"{id:20} {pet['name']}")
        return 0
    from pulse.core.history import History, default_history_path
    import sqlite3
    history_path = args.history_file or default_history_path()
    if args.history is not None or args.clear_history:
        if args.demo or args.observe or args.music or args.volume:
            parser.error("history commands cannot be combined with --demo or --observe")
        if args.history is not None and args.history < 1:
            parser.error("history count must be positive")
        if not history_path.exists():
            print("No saved notifications.")
            return 0
        try:
            history = History(history_path)
            try:
                if args.clear_history:
                    print(f"Cleared {history.clear()} saved notifications.")
                else:
                    import json
                    entries = history.recent(args.history)
                    for entry in entries:
                        print(json.dumps({key: entry[key] for key in
                                          ("received_at", "app", "title", "body")}, ensure_ascii=False))
                    if not entries:
                        print("No saved notifications.")
            finally:
                history.close()
        except (OSError, sqlite3.Error) as error:
            parser.error(f"Cannot access history: {error}")
        return 0
    from dataclasses import replace
    from pulse.settings import default_config_path, load_settings
    try:
        settings = load_settings(args.config or default_config_path(), required=args.config is not None)
    except ValueError as error:
        parser.error(str(error))
    from pulse.ui.preferences import Preferences
    preferences_path = default_config_path().with_name("preferences.json")
    saved = Preferences.read(preferences_path)
    settings = replace(settings, rules=replace(settings.rules, dnd=saved.get("dnd", settings.rules.dnd)),
                       reduced_motion=saved.get("motion", settings.reduced_motion),
                       theme=saved.get("theme", settings.theme))
    if args.dnd:
        settings = replace(settings, rules=replace(settings.rules, dnd=True))
    from pulse.themes.loader import load_theme
    from pulse.themes.schema import qml_data
    config_path = args.config or default_config_path()
    theme, theme_warning = load_theme(args.theme or settings.theme,
                                     base_dir=None if args.theme else config_path.parent)
    if theme_warning:
        print(f"Pulse: {theme_warning}", file=sys.stderr, flush=True)
    from PySide6.QtCore import QTimer, QUrl, qVersion
    backend = choose_backend(args.backend, qVersion())
    if args.renderer == "software":
        os.environ["QT_QUICK_BACKEND"] = "software"
    elif args.renderer == "hardware":
        os.environ.pop("QT_QUICK_BACKEND", None)
    elif backend in ("xcb", "windows"):
        os.environ.setdefault("QT_QUICK_BACKEND", "software")
    if backend == "layer-shell":
        if choose_backend("auto", qVersion()) != "layer-shell":
            parser.error("LayerShellQt requires a matching system Qt/PySide6 installation; use --backend xcb")
        os.environ["QT_QPA_PLATFORM"] = "wayland"
        os.environ["QT_WAYLAND_SHELL_INTEGRATION"] = "layer-shell"
    else:
        os.environ["QT_QPA_PLATFORM"] = backend
        os.environ.pop("QT_WAYLAND_SHELL_INTEGRATION", None)
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    app = QGuiApplication([sys.argv[0]])
    app.setApplicationName("Pulse")
    app.setDesktopFileName("io.github.NaF1sh.Pulse")
    app.setQuitOnLastWindowClosed(False)
    session = None
    if backend != 'offscreen':
        from pulse.runtime import Session
        try:
            session = Session(app)
            if not session.acquire():
                print('Pulse is already running. Opening Settings.', flush=True)
                return 0
        except OSError as error:
            print(f'Pulse could not establish its desktop session: {error}', file=sys.stderr)
            return 2
        app.aboutToQuit.connect(session.close)
    engine = QQmlApplicationEngine()
    from pulse.ui.pets import Pets
    pets = Pets(engine, selected=args.pet)
    pets.failed.connect(lambda text: print(f"Pulse: {text}", file=sys.stderr, flush=True))
    engine.rootContext().setContextProperty("pulsePets", pets)
    engine.rootContext().setContextProperty("pulseTheme", qml_data(theme))
    from pulse.ui.controller import Controller
    history = None
    if args.observe and not args.no_history:
        try:
            history = History(history_path)
        except (OSError, sqlite3.Error) as error:
            print(f"Pulse: history unavailable: {error}", file=sys.stderr, flush=True)
    if history is not None:
        app.aboutToQuit.connect(history.close)
    controller = Controller(engine, rules=settings.rules, history=history)
    controller.historyFailed.connect(lambda text: print(f"Pulse: {text}", file=sys.stderr, flush=True))
    engine.rootContext().setContextProperty("pulseController", controller)
    if args.observe:
        from pulse.sources.dbus_observer import Observer
        from pulse.ui.interactions import Interactions
        observer = Observer(app, default_timeout=settings.default_timeout)
        interactions = Interactions(observer.decoder, app)
        controller.set_interactions(interactions)
        observer.metadataChanged.connect(controller.changed)
        app.aboutToQuit.connect(interactions.stop)
        QTimer.singleShot(0, interactions.start)
        interactions.failed.connect(lambda text: print(f"Pulse: {text}", file=sys.stderr, flush=True))
    if args.tasks and not args.demo:
        controller.tasks.start()
        app.aboutToQuit.connect(controller.tasks.stop)
    preferences = Preferences(controller, settings, history_path, engine, path=preferences_path,
                              theme=args.theme or settings.theme,
                              reduced_motion=args.reduced_motion or settings.reduced_motion)
    engine.rootContext().setContextProperty("pulsePreferences", preferences)
    controller.historyFailed.connect(lambda text: preferences.source_status('Notification history', text, problem=True))

    def update_appearance():
        selected_theme, warning = load_theme(preferences.theme, base_dir=config_path.parent)
        engine.rootContext().setContextProperty("pulseTheme", qml_data(selected_theme))
        if engine.rootObjects():
            engine.rootObjects()[0].setProperty("reducedMotion", preferences.motion)

    preferences.appearanceChanged.connect(update_appearance)
    source = Path(__file__).parent / "ui/qml/Island.qml"
    if backend == "layer-shell":
        engine.addImportPath("/usr/lib/qt6/qml")
        app.addLibraryPath("/usr/lib/qt6/plugins")
        qml = source.read_text().replace("import QtQuick.Window", "import QtQuick.Window\nimport org.kde.layershell 1.0 as LS")
        qml = qml.replace('id: root', '''id: root
    LS.Window.anchors: LS.Window.AnchorTop | LS.Window.AnchorLeft
    LS.Window.layer: LS.Window.LayerOverlay
    LS.Window.exclusionZone: -1
    LS.Window.keyboardInteractivity: LS.Window.KeyboardInteractivityNone
    LS.Window.scope: "pulse"''', 1)
        engine.loadData(qml.encode(), QUrl.fromLocalFile(str(source)))
    else:
        engine.load(QUrl.fromLocalFile(str(source)))
    if not engine.rootObjects():
        if history is not None:
            history.close()
        return 1
    window = engine.rootObjects()[0]
    window.setProperty("reducedMotion", args.reduced_motion or settings.reduced_motion)
    window.setProperty("debugVisible", args.debug)

    from pulse.ui.window import WindowIntegration
    integration = WindowIntegration(window, backend)
    window.syncMask()
    window.show()
    if session is not None:
        session.activated.connect(window.openSettings)
    if (args.observe or is_windows()) and backend != 'offscreen':
        preferences.enable_welcome()
    if args.settings or preferences.welcomeNeeded:
        window.openSettings()
    preferences.source_status('Mode', 'Demo — notifications are simulated' if args.demo else
                              'Live desktop notifications' if args.observe else 'Floating island and local tasks' if is_windows() else 'Companion only')
    preferences.source_status('Notification history', 'Saved locally on this device' if history is not None
                              else 'Not saved in this session')
    preferences.source_status('Window system', f'{backend} · Qt {qVersion()}')
    if is_windows():
        preferences.source_status('Desktop integrations', 'Windows preview: task events, agents, pets, backgrounds and timers. Windows music uses system media sessions. Notification capture and volume are not implemented yet.')
    live_sources = []
    music_enabled = args.music if args.music is not None else (args.observe or (is_windows() and not args.demo))
    volume_enabled = args.volume if args.volume is not None else args.observe
    if music_enabled:
        if is_windows():
            from pulse.sources.windows_media import WindowsMedia
            music_source = WindowsMedia(app)
        else:
            from pulse.sources.mpris import Mpris
            music_source = Mpris(app)
        controller.set_music_source(music_source)
        music_source.notification.connect(controller.set_media)
        music_source.cleared.connect(controller.clear_media)
        live_sources.append(('Music', music_source))
    if volume_enabled:
        from pulse.sources.audio import Audio
        audio_source = Audio(app)
        audio_source.notification.connect(controller.submit_system)
        live_sources.append(('Volume', audio_source))
    for name, live_source in live_sources:
        preferences.source_status(name, 'Connecting…')
        live_source.status.connect(lambda text, label=name: preferences.source_status(label, text))
        live_source.status.connect(lambda text: print(f"Pulse: {text}", flush=True))
        app.aboutToQuit.connect(live_source.stop)
        QTimer.singleShot(0, live_source.start)
    if args.observe:
        from pulse.sources.plasma_popups import PlasmaPopups
        popup_control = PlasmaPopups(app)
        popup_control.status.connect(lambda text, problem: preferences.source_status('Plasma popups', text, problem=problem))
        preferences.changed.connect(lambda: popup_control.set_enabled(preferences.quiet_plasma))
        observer.readinessChanged.connect(popup_control.set_monitor_ready)
        popup_control.set_enabled(preferences.quiet_plasma)
        app.aboutToQuit.connect(popup_control.stop)
        observer.notification.connect(controller.submit)
        observer.closed.connect(controller.close)
        observer.status.connect(lambda text: print(f"Pulse: {text}", flush=True))

        preferences.source_status('Notifications', 'Connecting…')
        observer.status.connect(lambda text: preferences.source_status('Notifications', text))
        retry_timer = QTimer(app)
        retry_timer.setSingleShot(True)
        retry_timer.setInterval(15000)
        retry_timer.timeout.connect(observer.start)
        retry_timer.timeout.connect(interactions.start)
        app.aboutToQuit.connect(retry_timer.stop)
        failure_shown = False

        def retry_notifications():
            retry_timer.stop()
            observer.stop()
            observer.start()
            interactions.start()

        preferences.retryRequested.connect(retry_notifications)

        def observer_failed(text):
            nonlocal failure_shown
            print(f"Pulse observer unavailable: {text}", file=sys.stderr, flush=True)
            preferences.source_status('Notifications', 'Connection unavailable. Retrying every 15 seconds. '
                                      'Check that Pulse is running in your desktop session.', problem=True)
            retry_timer.start()
            if not failure_shown and backend != 'offscreen':
                window.openSettings()
                failure_shown = True

        observer.failed.connect(observer_failed)
        app.aboutToQuit.connect(observer.stop)
        QTimer.singleShot(0, observer.start)
    timer = QTimer(window)
    if args.demo:
        from pulse.sources.fake import script

        def play_demo():
            for offset, notification in script():
                QTimer.singleShot(int(offset * 1000), controller,
                                  lambda item=notification: controller.submit(item))

        timer.timeout.connect(play_demo)
        timer.start(22000)
        play_demo()
    if args.quit_after > 0:
        QTimer.singleShot(int(args.quit_after * 1000), app.quit)
    print(f"Pulse: backend={backend}, renderer={os.environ.get('QT_QUICK_BACKEND') or 'hardware'}, Qt={qVersion()}", flush=True)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
