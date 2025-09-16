import subprocess

env = "pipenv"
req = "requirements"

pip_upgrade = ["pip", "install", "--upgrade", "pip"]
update_dependencies_cmd = [env, "update"]
update_requirements_cmd = [env, req]
update_dev_requirements_cmd = [env, req, "--dev"]

requirements_file = open("requirements.txt", mode="w")
requirements_dev_file = open("requirements_dev.txt", mode="w")

subprocess.run(pip_upgrade)
subprocess.run(update_dependencies_cmd)
subprocess.run(update_requirements_cmd, stdout=requirements_file)
requirements_file.close()
subprocess.run(update_dev_requirements_cmd, stdout=requirements_dev_file)
requirements_dev_file.close()
