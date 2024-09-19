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
import subprocess
import os
import platform


def yes(msg):
    if not msg.endswith(" "):
        msg = f"{msg} "

    msg = f"{msg} [y]/n: "

    return input(msg).strip() in ("", "y", "yes", "Yes", "YES")


def r_mkdir(p, *args):
    p = os.path.join(p, *args)
    if p and not os.path.isdir(p):
        try:
            os.mkdir(p)
        except OSError:
            r_mkdir(os.path.dirname(p))
            os.mkdir(p)
    return p


def make_dir(root, *name):
    for d in (root, os.path.join(root, *name)):
        if not os.path.isdir(d):
            os.mkdir(d)


def write(p, t, overwrite=False, verbose=False):
    if not os.path.isfile(p) or overwrite:
        click.echo(f"wrote file: {p}")
        if verbose:
            click.secho(f"{p} contents: ==============", fg="blue")
            click.secho(t, fg="yellow", bg="black")
            click.secho(f"{p} end: ================================", fg="blue")

        head, tail = os.path.split(p)
        r_mkdir(head)
        if t is None:
            click.secho("writing an empty file", fg="yellow")

        with open(p, "w") as wfile:
            wfile.write(t or "")
    else:
        click.secho(f"file already exists skipping: {p}", fg="red")


def echo_config(**kwargs):
    click.secho("------------ Configuration -------------", fg="yellow")
    for k, v in kwargs.items():
        click.secho(f"{k:25s}= {v}", fg="yellow")
    click.secho("------------ Configuration End -------------", fg="yellow")


def is_tool(name):
    try:
        devnull = open(os.devnull)
        subprocess.Popen([name], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            return False
    return True


def find_prog(prog):
    if is_tool(prog):
        cmd = "where" if platform.system() == "Windows" else "which"
        out = subprocess.check_output([cmd, prog])
        if out is not None:
            return out.decode().strip()


def conda_root():
    return os.path.dirname(os.path.dirname(find_prog("conda")))


# def r_mkdir(p):
#     if p and not os.path.isdir(p):
#         try:
#             os.mkdir(p)
#         except OSError:
#             r_mkdir(os.path.dirname(p))
#             os.mkdir(p)


def handle_check_call(*args, **kw):
    try:
        subprocess.check_call(*args, **kw)
    except subprocess.CalledProcessError:
        import traceback

        exc = traceback.format_exc()
        click.secho(exc, fg="red")


# ============= EOF =============================================
