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
import yaml

from pcm import util, requirements, render

IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"
HOME = os.path.expanduser("~")
EDM_ENVS_ROOT = os.path.join(HOME, ".edm", "envs")
EDM_BIN = os.path.join(EDM_ENVS_ROOT, "edm", "bin")

if IS_WINDOWS:
    GIT = "C:\\Git\\bin\\git"
else:
    GIT = "git"


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


def _edm(environment, app, verbose):
    click.secho("edm install", bold=True, fg="green")
    req = requirements.EDM_REQUIREMENTS
    pip_req = ["uncertainties", "qimage2ndarray", "pymysql"]

    if app == "pyvalve":
        req.extend(["pyserial", "twisted"])
    else:
        pip_req.extend(["peakutils", "utm"])

    cmdargs = ["edm", "install", "-y"] + req
    active_python = os.path.join(HOME, ".edm")
    if environment:
        active_python = os.path.join(
            active_python, "envs", environment, "bin", "python"
        )
        cmdargs.extend(["--environment", environment])
    else:
        active_python = os.path.join(active_python, "bin", "python")

    if verbose:
        click.echo(f'requirements: {" ".join(req)}')
        click.echo(f'command: {" ".join(cmdargs)}')

    subprocess.call(cmdargs)
    subprocess.call(
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
        util.r_mkdir(root, "spectrometer", "mftables")
        name = "mftable.csv"
        p = os.path.join(d, name)
        util.write(p, render.render_template(name), overwrite)


def _code(fork, branch, app_id):
    update_root = os.path.join(HOME, f".pychron.{app_id}")
    ppath = os.path.join(update_root, "pychron")

    if not os.path.isdir(update_root):
        os.mkdir(update_root)

    if os.path.isdir(ppath):
        if not util.yes(
            "Pychron source code already exists. Remove and re-clone [y]/n"
        ):
            subprocess.call([GIT, "status"], cwd=ppath)
            return

        shutil.rmtree(ppath)

    url = f"https://github.com/{fork}/pychron.git"

    subprocess.call([GIT, "clone", url, f"--branch={branch}", ppath])
    subprocess.call([GIT, "status"], cwd=ppath)


def _launcher(
    conda, environment, app, org, app_id, login, msv, output, overwrite, verbose
):
    click.echo("launcher")
    template = "failed to make tmplate"
    if IS_MAC:
        if conda:
            template = "launcher_mac_conda"
        else:
            template = "launcher_mac"

    ctx = {
        "github_org": org,
        "app_name": app,
        "app_id": app_id,
        "use_login": login,
        "massspec_db_version": msv,
        "edm_envs_root": EDM_ENVS_ROOT,
        "edm_env": environment,
        "pychron_path": os.path.join(HOME, f".pychron.{app_id}", "pychron"),
    }

    txt = render.render_template(template, **ctx)

    if output is None:
        output = "pychron_launcher.sh"

    if verbose:
        click.echo(f"Writing launcher script: {output}")
        click.echo(txt)
    util.write(output, txt, overwrite)

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


def _init(env, org, use_ngx, overwrite, verbose):
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
        ("dvc.ini", {}, True),
        ("update.ini", uctx, True),
        ("arar_constants.ini", {}, True),
        ("extractionline.ini", ectx, True),
        ("ngx.ini", {}, use_ngx),
    ):
        if flag:
            txt = render.render_template(template, **ctx)
            p = os.path.join(d, template)
            util.write(p, txt, overwrite=overwrite)


# ============= EOF =============================================
