
import subprocess

user_input = input("Enter an expression: ")

result = eval(user_input)

exec("print('Dynamic execution')")

subprocess.run("dir", shell=True)
