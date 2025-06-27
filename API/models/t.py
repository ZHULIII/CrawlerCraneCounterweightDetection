import os

# 当前文件所在目录的绝对路径（不包含文件名）
current_dir = os.path.dirname(os.path.abspath(__file__))
print(current_dir)