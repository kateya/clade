# Copyright (c) 2018 ISP RAS (http://www.ispras.ru)
# Ivannikov Institute for System Programming of the Russian Academy of Sciences
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import pkg_resources
import os
import re
import subprocess
import sys
import ujson


def get_logger(name, with_name=True, conf=None):
    if not conf:
        conf = dict()

    logger = logging.getLogger(name)

    # Remove all old handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    if with_name:
        formatter = logging.Formatter("%(asctime)s clade {}: %(message)s".format(name), "%H:%M:%S")
    else:
        formatter = logging.Formatter("%(asctime)s clade: %(message)s", "%H:%M:%S")

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if conf.get("work_dir"):
        try:
            log_file = os.path.join(conf["work_dir"], "clade.log")
            log_file = os.path.abspath(log_file)
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            file_handler = logging.FileHandler(log_file, delay=True)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (PermissionError, OSError):
            # Can't write to clade.log file if working directory is read only
            pass

    logger.setLevel(conf.get("log_level", "INFO"))

    return logger


def merge_preset_to_conf(preset_name, conf):
    preset_file = os.path.join(
        os.path.dirname(__file__), "extensions", "presets", "presets.json"
    )

    with open(preset_file, "r") as f:
        presets = ujson.load(f)

    if preset_name not in presets:
        raise RuntimeError("Preset {!r} is not found".format(preset_name))

    preset_conf = presets[preset_name]
    parent_preset = preset_conf.get("extends")

    if parent_preset:
        preset_conf = merge_preset_to_conf(parent_preset, preset_conf)

    preset_conf.update(conf)

    return preset_conf


def get_clade_version():
    version = pkg_resources.get_distribution("clade").version
    location = pkg_resources.get_distribution("clade").location

    if not os.path.exists(os.path.join(location, ".git")):
        return version

    try:
        desc = ["git", "describe", "--tags", "--dirty"]
        version = subprocess.check_output(
            desc, cwd=location, stderr=subprocess.DEVNULL, universal_newlines=True
        ).strip()
    finally:
        return version


def get_program_version(program, version_arg="--version"):
    version = "unknown"
    try:
        version = subprocess.check_output(
            [program, version_arg], stderr=subprocess.DEVNULL, universal_newlines=True
        ).strip()
    finally:
        if version.startswith("gcc"):
            version = re.sub(r'\nCopyright[\s\S]*', '', version)
        return version
