from contextlib import suppress
from pathlib import Path
from setuptools import Command, setup
from setuptools.command.build import build
import subprocess
import shutil


class CustomTommath(Command):
    def initialize_options(self) -> None:
        self.build_lib = None

    def finalize_options(self) -> None:
        with suppress(Exception):
            self.build_lib = Path(self.get_finalized_command("build").build_lib)

    def run(self) -> None:
        if self.build_lib:
            tommath_dir = Path("..") / self.build_lib / Path("pyecsca/codegen/tommath")
            subprocess.run(["make", "host", "nano", "stm32f0", "stm32f3", f"TOMMATH_DIR={tommath_dir}"], cwd="ext")
            


class CustomBuild(build):
    sub_commands = build.sub_commands + [('build_tommath', None)]


setup(cmdclass={'build': CustomBuild, 'build_tommath': CustomTommath})
