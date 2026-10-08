#!/usr/bin/env python3
"""Render the real island task drawer using isolated, simulated task events."""
import os
from pathlib import Path
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication, QImage, QColor, QPainter, QFont
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from shiboken6 import getCppPointer, wrapInstance
from pulse.tasks.store import TaskStore
from pulse.ui.controller import Controller
from pulse.ui.pets import Pets
from pulse.themes.loader import load_theme
from pulse.themes.schema import qml_data

app = QGuiApplication([])
engine = QQmlApplicationEngine()
with tempfile.TemporaryDirectory(prefix='pulse-tasks-render-') as temp:
    folder = Path(temp)
    controller = Controller(engine)
    controller.tasks.start(folder / 'tasks.db')
    pets = Pets(engine, selected='shiba', preference_path=folder / 'pet.json')
    writer = TaskStore(folder / 'tasks.db')
    writer.publish('tests', title='API test suite', source='Terminal', progress=.65,
                   message='Running integration tests…')
    writer.publish('agent', title='Agent · API cleanup', source='Agent hook', state='needs-permission',
                   message='A command needs your approval. Review the request in your agent.', target='https://example.com/request')
    controller.tasks.poll()
    for name, value in [('pulseController', controller), ('pulsePets', pets), ('pulseTheme', qml_data(load_theme('default')[0]))]:
        engine.rootContext().setContextProperty(name, value)
    engine.load(QUrl.fromLocalFile(str(Path('src/pulse/ui/qml/Island.qml').resolve())))
    window = wrapInstance(getCppPointer(engine.rootObjects()[0])[0], QQuickWindow)
    window.setProperty('reducedMotion', True)
    window.show()
    window.setProperty('tasksExpanded', True)
    QTest.qWait(650)
    canvas = QImage(640, 490, QImage.Format_RGB32)
    canvas.fill(QColor('#111216'))
    painter = QPainter(canvas)
    painter.setPen(QColor('#f1f2f4'))
    painter.setFont(QFont('sans-serif', 17, QFont.DemiBold))
    painter.drawText(28, 36, 'Your tools work. Pulse keeps you in the loop.')
    painter.drawImage(110, 48, window.grabWindow())
    painter.setPen(QColor('#999da9'))
    painter.setFont(QFont('sans-serif', 9))
    painter.drawText(28, 468, 'Actual floating-island UI · simulated task events')
    painter.end()
    Path('docs/assets').mkdir(parents=True, exist_ok=True)
    canvas.save('docs/assets/tasks.png')
    controller.tasks.stop()
    writer.close()
    window.close()
