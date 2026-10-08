"""An external publisher updates the real floating island and its input region."""
import os
from pathlib import Path
import subprocess
import sys


def test_task_events_drawer_and_click_actions(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, '-c', SCRIPT, str(tmp_path)], cwd=root,
                            env=dict(os.environ, PYTHONPATH=str(root/'src'),
                                     QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software'),
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    for error in ('Error', 'Unable to assign', 'failed to load'):
        assert error not in result.stderr


SCRIPT = r'''
import os, sys, subprocess
from pathlib import Path
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from shiboken6 import wrapInstance, getCppPointer
from pulse.ui.controller import Controller
from pulse.ui.pets import Pets
from pulse.tasks.store import TaskStore
from pulse.themes.schema import Theme, qml_data
path=Path(sys.argv[1])
app=QGuiApplication([])
engine=QQmlApplicationEngine()
controller=Controller(engine)
controller.tasks.start(path/'pulse/tasks.sqlite3')
pets=Pets(engine, preference_path=path/'pet.json')
for name,value in [('pulseController',controller),('pulsePets',pets),('pulseTheme',qml_data(Theme()))]:
    engine.rootContext().setContextProperty(name,value)
engine.load(str(Path('src/pulse/ui/qml/Island.qml').resolve()))
assert engine.rootObjects()
window=wrapInstance(getCppPointer(engine.rootObjects()[0])[0],QQuickWindow)
window.setProperty('reducedMotion',True)
regions=[]
window.maskChanged.connect(lambda x,y,w,h,r: regions.append((w,h)))
window.show()
env=dict(os.environ,XDG_DATA_HOME=str(path))
subprocess.run([sys.executable,'-m','pulse.main','task','emit','agent','--title','Agent review','--state','needs-permission','--message','Review the command in your agent.','--open','https://example.com/request'],env=env,check=True,capture_output=True)
QTest.qWait(750)
assert window.property('displayed').toVariant()['taskState']=='needs-permission'
assert controller.tasks.summary['attention']==1
surface=window.findChild(QObject,'islandSurface')
assert surface.property('height') == 90
button=window.findChild(QObject,'toggleTaskDrawer')
point=button.mapToScene(QPointF(button.width()/2,button.height()/2)).toPoint()
QTest.mouseClick(window,Qt.LeftButton,Qt.NoModifier,point)
QTest.qWait(180)
assert window.property('tasksExpanded')
assert surface.property('height')==370
assert regions[-1] == (350,370)
assert window.findChild(QObject,'taskDrawer').property('visible')
assert not window.grabWindow().isNull()
opened=[]
controller.tasks.opener=lambda url: opened.append(url.toString()) or True
controller.tasks.open('agent')
assert opened==['https://example.com/request']
assert controller.tasks.head['state']=='needs-permission'
controller.tasks.dismiss('agent')
assert controller.tasks.card is None
assert window.property('tasksExpanded')
store=TaskStore(path/'pulse/tasks.sqlite3')
store.publish('agent',state='done')
QTest.qWait(700)
assert controller.tasks.head['state']=='done'
controller.tasks.clearFinished()
QTest.qWait(180)
assert not window.property('tasksExpanded')
store.close(); controller.tasks.stop(); window.close()
'''
