pip install pyinstaller
pip install requirements.txt
rmdir .\dist /s /q
rmdir .\build /s /q
pyinstaller main.py -F --name="Draftnought"
COPY icon.ico .\dist\icon.ico
COPY hull_shapes.json .\dist\hull_shapes.json
COPY lengths.json .\dist\lengths.json
COPY turrets_outlines.json .\dist\turrets_outlines.json
COPY turrets_positions.json .\dist\turrets_positions.json
COPY turrets_scale.json .\dist\turrets_scale.json