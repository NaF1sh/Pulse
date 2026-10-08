#!/usr/bin/env python3
"""Record the real QML interface with simulated data; no desktop capture required."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from shiboken6 import getCppPointer, wrapInstance

from pulse.settings import Settings
from pulse.sources.fake import script
from pulse.themes.loader import load_theme
from pulse.themes.schema import qml_data
from pulse.ui.controller import Controller
from pulse.ui.pets import Pets
from pulse.ui.preferences import Preferences


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('docs/assets'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    app = QGuiApplication([])
    engine = QQmlApplicationEngine()
    with tempfile.TemporaryDirectory(prefix='pulse-demo-') as temporary:
        directory = Path(temporary)
        controller = Controller(engine)
        pets = Pets(engine, selected='shiba', preference_path=directory / 'pet.json')
        preferences = Preferences(controller, Settings(), directory / 'history.sqlite3', engine,
                                  path=directory / 'preferences.json')
        for name, value in [('pulseController', controller), ('pulsePets', pets),
                            ('pulsePreferences', preferences),
                            ('pulseTheme', qml_data(load_theme('default')[0]))]:
            engine.rootContext().setContextProperty(name, value)
        source = Path(__file__).resolve().parents[1] / 'src/pulse/ui/qml/Island.qml'
        engine.load(QUrl.fromLocalFile(str(source)))
        if not engine.rootObjects():
            raise RuntimeError('Cannot render Pulse')
        window = wrapInstance(getCppPointer(engine.rootObjects()[0])[0], QQuickWindow)
        window.show()
        QTest.qWait(200)
        timeline = [0.0]
        controller.manager.clock = lambda: timeline[0]
        events = list(script())
        for index in range(480):
            timeline[0] = index / 20
            while events and events[0][0] + 1.5 <= timeline[0]:
                _, item = events.pop(0)
                controller.submit(item, record_history=False)
            controller.tick()
            QTest.qWait(50)
            frame = QImage(800, 280, QImage.Format_RGB32)
            frame.fill(QColor('#111216'))
            painter = QPainter(frame)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QColor('#f1f2f4'))
            painter.setFont(QFont('sans-serif', 22, QFont.DemiBold))
            painter.drawText(32, 46, 'Pulse')
            painter.setFont(QFont('sans-serif', 11))
            painter.setPen(QColor('#999da9'))
            painter.drawText(32, 73, 'A quiet companion for your Linux desktop.')
            painter.drawImage(190, 101, window.grabWindow())
            painter.setFont(QFont('sans-serif', 9))
            painter.drawText(32, 254, 'MESSAGES  /  MUSIC  /  VOLUME')
            painter.drawText(602, 254, 'Actual UI · demo data')
            painter.end()
            frame.save(str(directory / f'{index:04}.png'))
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-framerate', '20',
                        '-i', str(directory / '%04d.png'), '-filter_complex',
                        '[0:v]split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3',
                        '-loop', '0', str(args.output / 'pulse-demo.gif')], check=True)
        window.openSettings()
        settings = wrapInstance(getCppPointer(window.findChild(QObject, 'pulseSettings'))[0], QQuickWindow)
        QTest.qWait(200)
        settings.grabWindow().save(str(args.output / 'settings.png'))
        preferences.enable_welcome()
        QTest.qWait(100)
        settings.grabWindow().save(str(args.output / 'welcome.png'))
        settings.close()
        window.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
