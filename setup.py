from cx_Freeze import setup, Executable
import sys

productName = "ProductName"

exe = Executable(
      script="main.py",
      # base="Win32GUI",
      targetName="DegiroPeek.exe"
     )
setup(
      name="DegiroPeek.exe",
      version="1.0",
      author="Me",
      description="Using PhantomJS driver, app peeks into degiro and shows some data",
      executables=[exe],
      scripts=[
               'main.py'
               ]
      )