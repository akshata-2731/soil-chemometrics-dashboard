import os
import glob

for f in glob.glob("logics/implementations/M*.py"):
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
    
    content = content.replace("from .logic_utils import", "from logics.implementations.logic_utils import")
    
    with open(f, "w", encoding="utf-8") as file:
        file.write(content)

print("Fixed imports")
