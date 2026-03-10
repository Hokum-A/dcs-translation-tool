import zipfile
import re
import os

miz_path = r'c:\Users\Andrei\Desktop\DCS translator TOOL\test\TM01 FINAL.miz'
images = []

try:
    with zipfile.ZipFile(miz_path, 'r') as z:
        for name in z.namelist():
            if re.match(r'(?i)^KNEEBOARD/IMAGES/.*\.(jpg|png|jpeg)$', name):
                base_name = os.path.basename(name)
                images.append(base_name)
    print("FOUND KNEEBOARD FILES:", images)
except Exception as e:
    print("ERROR:", e)
