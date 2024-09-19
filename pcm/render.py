# ===============================================================================
# Copyright 2021 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import os

import click


def render_template(template_name, template_root=None, **ctx):
    root = os.path.abspath(os.path.dirname(__file__))

    if template_root:
        p = os.path.join(root, "templates", template_root, f"{template_name}.template")
    else:
        p = os.path.join(root, "templates", f"{template_name}.template")

    if os.path.isfile(p):
        with open(p, "r") as rfile:
            txt = rfile.read()
            if not template_name.endswith(".json"):
                txt = txt.format(**ctx)
            return txt
    else:
        click.echo(f"{p} not a valid template")


# ============= EOF =============================================
