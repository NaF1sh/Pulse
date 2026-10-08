"""Rendered pixels and real mouse input through the new daily-use flows."""
import os
from pathlib import Path
import subprocess
import sys


def test_background_pixels_focus_buttons_and_music_transport(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, '-c', SCRIPT, str(tmp_path)], cwd=root,
                            env=dict(os.environ, PYTHONPATH=str(root / 'src'),
                                     QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software'),
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert 'Error' not in result.stderr


SCRIPT = r'''
import sys
from pathlib import Path
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QGuiApplication, QImage, QColor, QPainter
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from shiboken6 import getCppPointer, wrapInstance
from pulse.ui.controller import Controller
from pulse.ui.preferences import Preferences
from pulse.ui.pets import Pets
from pulse.sources.mpris import Mpris
from pulse.settings import Settings
from pulse.themes.schema import Theme, qml_data
app=QGuiApplication([])
engine=QQmlApplicationEngine()
path=Path(sys.argv[1])
controller=Controller(engine)
prefs=Preferences(controller, Settings(), path/'history.db', engine, path=path/'preferences.json')
pets=Pets(engine, preference_path=path/'pet.json')
for name,value in [('pulseController',controller),('pulsePreferences',prefs),('pulsePets',pets),('pulseTheme',qml_data(Theme()))]:
    engine.rootContext().setContextProperty(name,value)
engine.load(str(Path('src/pulse/ui/qml/Island.qml').resolve()))
assert engine.rootObjects()
window=wrapInstance(getCppPointer(engine.rootObjects()[0])[0],QQuickWindow)
window.setProperty('reducedMotion', True)
window.show()
prefs.setBackgroundColor('#b8d9dc')
prefs.previewNotification()
QTest.qWait(300)
assert window.grabWindow().pixelColor(210,61).name() == '#b8d9dc'
image=QImage(200,400,QImage.Format_RGB32)
image.fill(QColor('red'))
painter=QPainter(image); painter.fillRect(0,200,200,200,QColor('blue')); painter.end()
assert image.save(str(path/'wallpaper.png'))
prefs.importBackground(str(path/'wallpaper.png'))
prefs.setBackgroundPosition(0)
QTest.qWait(150)
upper=window.grabWindow().pixelColor(210,61)
assert upper.red() > 40 and upper.blue() < 10, upper.name()
prefs.setBackgroundPosition(1)
QTest.qWait(150)
lower=window.grabWindow().pixelColor(210,61)
assert lower.blue() > 40 and lower.red() < 10, lower.name()
assert window.grabWindow().pixelColor(70,12).alpha() == 0
window.openSettings()
settings=wrapInstance(getCppPointer(window.findChild(QObject,'pulseSettings'))[0],QQuickWindow)
settings.setProperty('tab',5)
QTest.qWait(150)
def children(item):
    yield item
    for child in item.childItems():
        yield from children(child)
def click(window,name):
    item=next(item for item in children(window.contentItem()) if item.objectName()==name)
    point=item.mapToScene(QPointF(item.width()/2,item.height()/2)).toPoint()
    QTest.mouseClick(window,Qt.LeftButton,Qt.NoModifier,point)
settings.setProperty('tab',2)
prefs.importBackground(str(path/'missing.png'))
assert prefs.backgroundError
QTest.qWait(100)
field=next(item for item in children(settings.contentItem()) if item.objectName()=='backgroundImagePath')
field.forceActiveFocus()
app.clipboard().setText(' "' + str(path/'wallpaper.png') + '" ')
QTest.keyClick(settings, Qt.Key_V, Qt.ControlModifier)
assert field.property('text') == app.clipboard().text()
QTest.keyClick(settings, Qt.Key_Return)
assert not prefs.backgroundError
assert prefs.backgroundMode == 'image'
settings.setProperty('tab',5)
QTest.qWait(100)
click(settings,'startFocus')
assert controller.focus.state['phase']=='focus'
QTest.qWait(80)
click(settings,'pauseFocus')
assert controller.focus.state['paused']
controller.dismiss()
QTest.qWait(180)
assert window.property('displayed').toVariant()['status']=='Focus'
controller.focus.stop()
source=Mpris(engine)
source.executable='/usr/bin/busctl'
controller.set_music_source(source)
source.notification.connect(controller.set_media)
calls=[]
source.action.start=lambda program,args: calls.append(args) or True
source.samples=[dict(service='org.mpris.MediaPlayer2.test', title='Song', artist='Artist',track='1',status='Playing',artwork='',capabilities=dict(CanControl=True,CanPlay=True,CanPause=True,CanGoNext=True,CanGoPrevious=False))]
source.publish()
QTest.qWait(200)
click(window,'music-next')
assert calls[-1][-1]=='Next'
click(window,'music-previous')
assert len(calls)==1
settings.close(); window.close()
'''
