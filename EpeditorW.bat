set venvpath=%cd%\venv
set venvpathscripts=%cd%\venv\Scripts
set pyqt5Plugin=%cd%\venv\Lib\site-packages\PyQt5\Qt5\plugins
set path=%venvpath%;%venvpathscripts%;%pyqt5Plugin%;%path%
echo Connecting to MoosasQA...
python37 EpeditorW.py