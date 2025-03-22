import os
import sys
import mysql.connector

print("Python version:", sys.version)
print("Working directory:", os.getcwd())
print("MySQL Connector version:", mysql.connector.__version__)

print("Test successful!") 