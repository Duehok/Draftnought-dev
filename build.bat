pip install pyinstaller
pip install requirements.txt
rmdir .\dist /s /q
rmdir .\build /s /q
pyinstaller main.py -F --name="Draftnought"
COPY icon.ico .\dist\icon.ico
xcopy /s /i ".\data" ".\dist.\data"