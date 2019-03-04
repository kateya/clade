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

import re
import os
import sys

from graphviz import Digraph

from clade.cmds import iter_cmds, get_last_id
from clade.extensions.abstract import Extension
from clade.extensions.utils import common_main


class PidGraph(Extension):
    __version__ = "1"

    def __init__(self, work_dir, conf=None, preset="base"):
        super().__init__(work_dir, conf, preset)

        self.graph = dict()
        self.graph_file = "pid_graph.json"

        self.pid_by_id = dict()
        self.pid_by_id_file = "pid_by_id.json"

        self.graph_dot = os.path.join(self.work_dir, "pid_graph.dot")

    @Extension.prepare
    def parse(self, cmds_file):
        self.log("Parsing {} commands".format(get_last_id(cmds_file, raise_exception=True)))

        for cmd in iter_cmds(cmds_file):
            self.pid_by_id[cmd["id"]] = cmd["pid"]

            self.graph[cmd["id"]] = [cmd["pid"]] + self.graph.get(cmd["pid"], [])

        self.dump_data(self.graph, self.graph_file)
        self.dump_data(self.pid_by_id, self.pid_by_id_file)

        if self.graph:
            if self.conf.get("PidGraph.as_picture"):
                self.__print_pid_graph(cmds_file)

        self.graph.clear()
        self.pid_by_id.clear()

    def __print_pid_graph(self, cmds_file, reduced=False):
        dot = Digraph(graph_attr={'rankdir': 'LR'}, node_attr={'shape': 'rectangle'})

        cmds = list(iter_cmds(cmds_file))

        for cmd in cmds:
            cmd_node = "[{}] {}".format(cmd["id"], cmd["which"])
            dot.node(cmd["id"], label=re.escape(cmd_node))

        for cmd in cmds:
            for parent_cmd in [x for x in cmds if x["id"] == cmd["pid"]]:
                dot.edge(parent_cmd["id"], cmd["id"])

        dot.render(self.graph_dot)

    def load_pid_graph(self):
        return self.load_data(self.graph_file)

    def load_pid_by_id(self):
        return self.load_data(self.pid_by_id_file)

    def filter_cmds_by_pid(self, cmds):
        graph = self.load_pid_graph()

        parsed_ids = set()
        filtered_cmds = []

        for cmd in sorted(cmds, key=lambda x: int(x["id"])):
            if not (set(graph[cmd["id"]]) & parsed_ids):
                filtered_cmds.append(cmd)

            parsed_ids.add(cmd["id"])

        return filtered_cmds


def main(args=sys.argv[1:]):
    common_main(PidGraph, args)
