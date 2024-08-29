import setuptools
import subprocess


# 获取最新的 Git 标签作为版本号
def get_git_version():
    try:
        version = (
            subprocess.check_output(["git", "describe", "--tags"])
            .strip()
            .decode("utf-8")
        )
    except subprocess.CalledProcessError:
        version = "0.0.0"
    return version


setuptools.setup(
    name="EasyPlotLib",
    version=get_git_version(),
    author="HanYuyang",
    author_email="17766095120@163.com",
    description="A simple plotting library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/EasyPlotLib",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
