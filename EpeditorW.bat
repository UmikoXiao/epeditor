set venvpath=%cd%\venv
set venvpathscripts=%cd%\venv\Scripts
set path=%venvpath%;%venvpathscripts%;%path%
echo Connecting to MoosasQA...
python37 EpeditorW.py