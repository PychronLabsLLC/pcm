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
import shutil
import subprocess
import platform

import click
import requests
import yaml
from git import Repo

from pcm import util, requirements, render
from pcm.requirements import CONDA_REQUIREMENTS, PIP_REQUIREMENTS
from pcm.util import find_prog, handle_check_call, r_mkdir, conda_root

IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"
HOME = os.path.expanduser("~")
PYTHON_EXECUTABLE_ROOT = os.path.join(HOME, "miniconda3", "envs")
# EDM_ENVS_ROOT = os.path.join(HOME, ".edm", "envs")
# EDM_BIN = os.path.join(EDM_ENVS_ROOT, "edm", "bin")


def _login(env, app_id):
    # write the user
    root = os.path.join(HOME, f".pychron.{app_id}")
    user_file = os.path.join(root, "users.yaml")
    t = {
        "users": [
            "root",
        ],
        "last_login": "root",
    }
    util.write(user_file, yaml.dump(t))

    environment_file = os.path.join(root, "environments.yaml")
    pe = os.path.join(HOME, env)
    t = {
        "env": pe,
        "envs": [
            pe,
        ],
    }
    util.write(environment_file, yaml.dump(t))


def _conda(environment, app, verbose):
    click.secho("conda install", bold=True, fg="green")
    req = requirements.CONDA_REQUIREMENTS
    pip_req = requirements.PIP_REQUIREMENTS

    if app == "pyvalve":
        req.extend(requirements.VALVE_REQUIREMENTS)
    else:
        pip_req.extend(requirements.PIP_EXTRAS)

    active_python = "python"
    if environment:
        cmdargs = ["conda", "create", "-y", "-n", environment] + req

        # active_conda e.g. /home/ross/miniconda3/bin/conda
        root = conda_root()

        active_python = os.path.join(root, "envs", environment, "bin", "python")
    else:
        cmdargs = ["conda", "install", "-y"] + req

    if verbose:
        click.echo(f'requirements: {" ".join(req)}')
        click.echo(f'command: {" ".join(cmdargs)}')

    if cmdargs:
        handle_check_call(cmdargs)

        # install chaco
        handle_check_call(
            ["conda", "install", "-y", "-n", environment, "-c", "dbanas", "chaco"]
        )

    handle_check_call(
        [
            active_python,
            "-m",
            "pip",
            "install",
            # "--no-dependencies",
        ]
        + pip_req
    )


def _edm(environment, app, verbose):
    click.secho("edm install", bold=True, fg="green")
    req = requirements.EDM_REQUIREMENTS
    pip_req = requirements.PIP_REQUIREMENTS

    if app == "pyvalve":
        req.extend(requirements.VALVE_REQUIREMENTS)
    else:
        pip_req.extend(requirements.PIP_EXTRAS)

    cmdargs = ["edm", "install", "-y"] + req
    active_python = os.path.join(HOME, ".edm")
    if environment:
        active_python = os.path.join(
            active_python, "envs", environment, "bin", "python"
        )
        cmdargs.extend(["--environment", environment])

        handle_check_call(["edm", "environments", "create", environment])
    else:
        active_python = os.path.join(active_python, "bin", "python")

    if verbose:
        click.echo(f'requirements: {" ".join(req)}')
        click.echo(f'command: {" ".join(cmdargs)}')

    handle_check_call(cmdargs)
    handle_check_call(
        [
            active_python,
            "-m",
            "pip",
            "install",
            "--no-dependencies",
        ]
        + pip_req
    )


def _render_template(dargs, name, overwrite):
    d = util.r_mkdir(*dargs)
    p = os.path.join(d, name)
    util.write(p, render.render_template(name), overwrite)


def _scripts(env, use_ngx, overwrite, verbose):
    root = os.path.join(HOME, env)
    _render_template((root, "scripts"), "defaults.yaml", overwrite)

    measurement_args = "measurement", "unknown"
    extraction_args = "extraction", "extraction"
    procedure_args = "procedures", "procedure"
    post_eq_args = "post_equilibration", "post_equilibration"
    post_m_args = "post_measurement", "post_measurement"

    for name, filename in (
        measurement_args,
        extraction_args,
        procedure_args,
        post_eq_args,
        post_m_args,
    ):
        _render_template(
            (root, "scripts", name), "example_{}.py".format(filename), overwrite
        )

    for dname, pname in (("fits", "nominal.yaml"), ("hops", "hops.yaml")):
        _render_template((root, "scripts", "measurement", dname), pname, overwrite)


def _setupfiles(env, use_ngx, overwrite, verbose):
    root = os.path.join(HOME, env)

    sf = util.r_mkdir(root, "setupfiles")

    for d, ps, enabled in (
        ("canvas2D", ("canvas.yaml", "canvas_config.xml", "alt_config.xml"), True),
        ("extractionline", ("valves.yaml",), True),
        ("monitors", ("system_monitor.cfg",), True),
        (
            "devices",
            (
                "ngx_switch_controller.cfg",
                "spectrometer_microcontroller.cfg",
                "NGXGPActuator.cfg",
            ),
            use_ngx,
        ),
        ("", ("startup_tests.yaml", "experiment_defaults.yaml"), True),
    ):
        if d:
            # out = os.path.join(sf, d)
            # util.make_dir(sf, d)
            out = util.r_mkdir(sf, d)
        else:
            out = sf

        for template in ps:
            txt = render.render_template(template)
            if template == "valves.yaml" and use_ngx:
                txt += """- name: MS_Inlet
                address: PIV
                """
            p = os.path.join(out, template)
            util.write(p, txt, overwrite, verbose)

    if use_ngx:
        _spectrometer_init("ngx", env, overwrite)


def _code(fork, branch, app_id):
    update_root = os.path.join(HOME, f".pychron.{app_id}")
    ppath = os.path.join(update_root, "pychron")
    # locate the git executable
    git = find_prog("git")
    if not git:
        click.secho("Could not locate git executable", fg="red")
        return

    if not os.path.isdir(update_root):
        os.mkdir(update_root)

    clone = True
    if os.path.isdir(ppath):
        clone = False
        if util.yes("Pychron source code already exists. Remove and re-clone [y]/n"):
            shutil.rmtree(ppath)
            clone = True

    if clone:
        url = f"https://github.com/{fork}/pychron.git"
        subprocess.call([git, "clone", url, f"--branch={branch}", ppath])
    subprocess.call([git, "status"], cwd=ppath)


def _launcher(
    conda, environment, app, org, app_id, login, msv, output, overwrite, verbose
):
    click.echo("launcher")

    if IS_MAC:
        if conda:
            template = "launcher_mac_conda"
        else:
            template = "launcher_mac"
    else:
        template = "launcher_pc"
        output = "pychron_launcher.bat"

    ctx = {
        "github_org": org,
        "app_name": app,
        "app_id": app_id,
        "use_login": login,
        "massspec_db_version": msv,
        # "edm_envs_root": EDM_ENVS_ROOT,
        # "edm_env": environment,
        # "python_executable_root": PYTHON_EXECUTABLE_ROOT,
        # "env": environment,
        "conda_env_name": environment,
        "conda_distro": conda_root(),
        "pychron_path": os.path.join(HOME, f".pychron.{app_id}", "pychron"),
        "update_db": 0,
        "alembic_url": "",
    }

    txt = render.render_template(template, **ctx)

    if output is None:
        output = "pychron_launcher.sh"

    if verbose:
        click.echo(f"Writing launcher script: {output}")
        click.echo(txt)
    util.write(output, txt, overwrite)

    if not IS_WINDOWS:
        # make launcher executable
        subprocess.call(["chmod", "+x", output])


def _email(env, overwrite):
    # copy the credentials file to appdata
    click.echo("make initialization file")
    template = "credentials.json"
    txt = render.render_template(template)
    root = os.path.join(HOME, env)
    sf = ".appdata"
    util.make_dir(root, sf)
    p = os.path.join(root, sf, template)
    util.write(p, txt, overwrite=overwrite)


def _init(env, org, data_org, use_ngx, overwrite, verbose):
    click.echo("make initialization file")
    template = "initialization.xml"
    txt = render.render_template(template)
    if verbose:
        click.echo("======== Initialization.xml contents start ========")
        click.echo(txt)
        click.echo("======== Initialization.xml contents end ========")

    root = os.path.join(HOME, env)

    d = util.r_mkdir(root, "setupfiles")

    p = os.path.join(d, "initialization.xml")
    util.write(p, txt, overwrite=overwrite)

    d = util.r_mkdir(root, "preferences")
    gctx = dict(general_organization=org, general_remote="{}/Laboratory")
    uctx = dict(
        build_repo=os.path.join(HOME, ".pychron.0", "pychron"),
        build_remote="PychronLabsLLC/pychron",
        build_branch="dev/dr",
    )

    sf = os.path.join(HOME, env, "setupfiles")
    ectx = {
        "canvas_path": os.path.join(sf, "canvas2D", "canvas.yaml"),
        "canvas_config_path": os.path.join(sf, "canvas2D", "canvas_config.xml"),
        "valves_path": os.path.join(sf, "extractionline", "valves.yaml"),
    }

    for template, ctx, flag in (
        ("general.ini", gctx, True),
        ("dvc.ini", {"org": data_org}, True),
        ("update.ini", uctx, True),
        ("arar_constants.ini", {}, True),
        ("extractionline.ini", ectx, True),
        ("ngx.ini", {}, use_ngx),
    ):
        if flag:
            txt = render.render_template(template, **ctx)
            p = os.path.join(d, template)
            util.write(p, txt, overwrite=overwrite)


def _makefile(name, env, overwrite):
    txt = render.render_template(name)
    p = os.path.join(HOME, env, name)
    util.write(p, txt, overwrite=overwrite)


def _spectrometer_init(kind, env, overwrite):
    kind = kind.lower()
    root = os.path.join(HOME, env)

    # mftable
    txt = render.render_template(f"{kind}_mftable.csv")
    p = os.path.join(root, "setupfiles", "spectrometer", "mftables", "mftable.csv")
    util.write(p, txt, overwrite)

    # config
    txt = render.render_template(f"{kind}_config.cfg")
    p = os.path.join(root, "setupfiles", "spectrometer", "configurations", "config.cfg")
    util.write(p, txt, overwrite)

    # detectors
    txt = render.render_template(f"{kind}_detectors.yaml")
    p = os.path.join(root, "setupfiles", "spectrometer", "detectors.yaml")
    util.write(p, txt, overwrite)

    if kind == "ngx":
        # preferences
        template = "ngx.ini"
        txt = render.render_template(template)
        p = os.path.join(root, "preferences", template)
        util.write(p, txt, overwrite=overwrite)


def _metarepo(name, env, overwrite):
    root = os.path.join(HOME, env, "data", ".dvc", name)
    r_mkdir(root)
    if not os.path.isfile(os.path.join(root, ".git")):
        repo = Repo.init(root)
    else:
        repo = Repo(root)

    ih = os.path.join(root, "irradiation_holders")
    r_mkdir(ih)
    template = "Grid.txt"
    p = os.path.join(ih, template)
    txt = render.render_template(template)
    util.write(p, txt, overwrite=overwrite)
    repo.index.add(p)

    noi = os.path.join(root, "NoIrradiation")
    r_mkdir(noi)

    template = "A.json"
    p = os.path.join(noi, template)
    txt = render.render_template(template)
    util.write(p, txt, overwrite=overwrite)

    prod = os.path.join(noi, "productions")
    r_mkdir(prod)
    template = "NoIrradiation.json"
    p = os.path.join(prod, template)
    txt = render.render_template(template)
    util.write(p, txt, overwrite=overwrite)

    p = os.path.join(noi, "productions.json")
    txt = '{"A"; "NoIrradiation"}'
    util.write(p, txt, overwrite=overwrite)

    p = os.path.join(noi, "chronology.txt")
    txt = ""
    util.write(p, txt, overwrite=overwrite)


def _fetch(name, env):
    output = os.path.join(HOME, env)
    base = "https://raw.githubusercontent.com/PychronLabsLLC/pychronpackages/main"
    url = f"{base}/{name}"
    resp = requests.get(url)
    print(resp)
    if resp.status_code == 200:
        name = os.path.basename(name)
        path = os.path.join(output, name)
        with open(path, "w") as wfile:
            wfile.write(resp.text)


def _req():
    """
    print the requirements list as string for pasting into the command line
    :return:
    """

    # conda
    c = " ".join(CONDA_REQUIREMENTS)
    click.secho(f">>>>  conda install {c}", fg="green")
    print()
    # pip
    p = " ".join(PIP_REQUIREMENTS)
    click.secho(f">>>>> pip install {p}", fg="green")


# ============= EOF =============================================
