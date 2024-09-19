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
import platform

from pcm.func import (
    _login,
    _edm,
    _setupfiles,
    _code,
    _launcher,
    _init,
    _email,
    _scripts,
    _makefile,
    _spectrometer_init,
    _metarepo,
    _fetch,
    _conda,
    _req,
    _pipeline_defaults
)
from pcm.util import echo_config, yes


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--template",
    default=None,
    help="Device Template to use. Typically the device models name",
)
@click.argument("name")
def device(template, name):
    click.echo("Create a new device configuration")


@cli.command()
@click.option(
    "--app",
    default="pycrunch",
    help="Application style to install. pycrunch, pyexperiment,...",
)
@click.option("--conda/--no-conda", default=False, help="Use Conda")
@click.option("--src/--no-src", "use_src", default=True, help="install the source code")
@click.option("--app_id", default=0, help="set the app id")
@click.option("--fork", default="NMGRL", help="Name of the pychron fork to clone")
@click.option(
    "--org",
    default="NMGRL",
    help="Github organization for storing laboratory files such as Plot Options",
)
@click.option(
    "--data-org",
    default="NMGRLData",
    help="Github organization for storing data",
)
@click.option("--branch", default="dev/dr", help="Name of the pychron fork to clone")
@click.option(
    "--setupfiles/--no-setupfiles",
    "use_setupfiles",
    default=False,
    help="Install pychron setupfiles",
)
@click.option(
    "--init/--no-init",
    "use_init",
    default=True,
    help="Install pychron initalization files",
)
@click.option("--env", default="Pychron", help="Environment, aka root directory name")
@click.option(
    "--edm/--no-edm", "use_edm", default=True, help="Install the EDM environment"
)
@click.option("--environment", default="pychron", help="Name of the EDM environment")
@click.option(
    "--launcher/--no-launcher",
    "use_launcher",
    default=True,
    help="make a launcher script",
)
@click.option("--app_id", default=0, help="set the app id")
@click.option(
    "--use_login/--no-use_login", default=True, help="Write default login files"
)
@click.option(
    "--use_pipeline_defaults/--no-use_pipeline_defaults", default=True, help="Write default pipeline defaults"
)
@click.option("--login/--no-login", default=0, help="show login window at startup")
@click.option(
    "--massspec_db_version", "msv", default=16, help="massspec database version"
)
@click.option("--use_ngx/--no-ngx", default=False, help="Install NGX")
@click.option(
    "--overwrite/--no-overwrite", default=False, help="Overwrite the file if it exists"
)
@click.option("--verbose/--no-verbose", default=False, help="Verbose output")
def wizard(
    app,
    conda,
    use_src,
    app_id,
    fork,
    org,
    data_org,
    branch,
    use_setupfiles,
    use_init,
    env,
    use_edm,
    environment,
    use_launcher,
    use_login,
    use_pipeline_defaults,
    login,
    msv,
    overwrite,
    use_ngx,
    verbose,
):
    echo_config(
        application=app,
        use_conda=conda,
        clone_src=use_src,
        app_id=app_id,
        fork=fork,
        org=org,
        data_org=data_org,
        branck=branch,
        install_setupfiles=use_setupfiles,
        install_init=use_init,
        pychron_root=env,
        use_edm=use_edm,
        python_environment=environment,
        install_launcher=use_launcher,
        write_login_defaults=use_login,
        install_pipeline_defaults=use_pipeline_defaults,
        show_login_at_startup=login,
        massspec_version=msv,
        overwrite=overwrite,
        install_ngx_setupfiles=use_ngx,
        verbose=verbose,
    )
    click.secho("Install the pychron application", bold="True", fg="green")

    if not yes("OK to proceed?"):
        click.secho("Aborting", fg="red")
        return

    for sent, func, args in (
        (use_src, _code, (fork, branch, app_id)),
        (use_init, _init, (env, org, data_org, use_ngx, overwrite, verbose)),
        (use_setupfiles, _setupfiles, (env, use_ngx, overwrite, verbose)),
        (use_pipeline_defaults, _pipeline_defaults, (env, overwrite)),
        (conda, _conda, (environment, app, verbose)),
        (
            use_launcher,
            _launcher,
            (
                conda,
                environment,
                app,
                fork,
                app_id,
                login,
                msv,
                None,
                overwrite,
                verbose,
            ),
        ),
        (use_login, _login, (env, app_id)),
    ):
        print(sent, func, args)
        if sent:
            try:
                func(*args)
            except BaseException as e:
                import traceback

                traceback.print_exc()


@cli.command()
@click.option("--env", default="Pychron", help="Environment, aka root directory name")
@click.option(
    "--overwrite/--no-overwrite", default=False, help="Overwrite the file if it exists"
)
def pipeline_defaults(env, overwrite):
    _pipeline_defaults(env, overwrite)


@cli.command()
@click.option("--env", default="Pychron", help="Environment, aka root directory name")
@click.option("--app_id", default=0, help="set the app id")
def login(env, app_id):
    _login(env, app_id)


@cli.command()
@click.option("--environment", default=None, help="Name of the EDM environment")
@click.option(
    "--app",
    default="pycrunch",
    help="Application style to install. pycrunch, pyexperiment,...",
)
@click.option("--verbose/--no-verbose", default=False, help="Verbose output")
def edm(environment, app, verbose):
    _edm(environment, app, verbose)


@cli.command()
@click.option("--environment", default=None, help="Name of the Conda environment")
@click.option(
    "--app",
    default="pycrunch",
    help="Application style to install. pycrunch, pyexperiment,...",
)
@click.option("--verbose/--no-verbose", default=False, help="Verbose output")
def conda(environment, app, verbose):
    _conda(environment, app, verbose)


@cli.command()
@click.option("--env", default="Pychron", help="Environment, aka root directory name")
@click.option("--use_ngx/--no-ngx", default=False, help="Install NGX")
@click.option(
    "--overwrite/--no-overwrite", default=False, help="Overwrite the file if it exists"
)
@click.option("--verbose/--no-verbose", default=False, help="Verbose output")
def setupfiles(env, use_ngx, overwrite, verbose):
    _setupfiles(env, use_ngx, overwrite, verbose)


@cli.command()
@click.option("--env", default="Pychron", help="Environment, aka root directory name")
@click.option("--use_ngx/--no-ngx", default=False, help="Install NGX")
@click.option(
    "--overwrite/--no-overwrite", default=False, help="Overwrite the file if it exists"
)
@click.option("--verbose/--no-verbose", default=False, help="Verbose output")
def scripts(env, use_ngx, overwrite, verbose):
    _scripts(env, use_ngx, overwrite, verbose)


@cli.command()
@click.option("--env", default="Pychron", help="Environment, aka root directory name")
@click.option(
    "--org",
    default="NMGRL",
    help="Github organization for storing laboratory files such as Plot Options",
)
@click.option(
    "--data-org",
    default="NMGRLData",
    help="Github organization for storing data",
)
@click.option("--use_ngx/--no-ngx", default=False, help="Install NGX")
@click.option(
    "--overwrite/--no-overwrite", default=False, help="Overwrite the file if it exists"
)
@click.option("--verbose/--no-verbose", default=False, help="Verbose output")
def buildenv(env, org, data_org, use_ngx, overwrite, verbose):
    _init(env, org, data_org, use_ngx, overwrite, verbose)
    _setupfiles(env, use_ngx, overwrite, verbose)
    _scripts(env, use_ngx, overwrite, verbose)


@cli.command()
@click.option("--fork", help="Name of the pychron fork to clone")
@click.option("--branch", default="dev/dr", help="Name of the pychron fork to clone")
@click.option("--app_id", default=0, help="set the app id")
def code(fork, branch, app_id):
    _code(fork, branch, app_id)


@cli.command()
@click.option("--conda/--no-conda", default=False, help="Use the conda package manager")
@click.option("--environment", default="pychron", help="Python environment name")
@click.option("--app", default="pycrunch", help="application name")
@click.option("--org", default="PychronLabsLLC", help="Github organization")
@click.option("--app_id", default=0, help="set the app id")
@click.option("--login/--no-login", default=0, help="show login window at startup")
@click.option(
    "--massspec_db_version", "msv", default=16, help="massspec database version"
)
@click.option("--output", default="pychron_launcher.sh", help="Output path")
@click.option(
    "--overwrite/--no-overwrite", default=False, help="Overwrite the file if it exists"
)
@click.option("--verbose/--no-verbose", default=False, help="Verbose output")
def launcher(
    conda, environment, app, org, app_id, login, msv, output, overwrite, verbose
):
    _launcher(
        conda, environment, app, org, app_id, login, msv, output, overwrite, verbose
    )


@cli.command()
@click.option("--env", default="Pychron", help="Environment, aka root directory name")
@click.option(
    "--org",
    default="NMGRL",
    help="Github organization for storing laboratory files such as Plot Options",
)
@click.option(
    "--data-org",
    default="NMGRLData",
    help="Github organization for storing data",
)
@click.option("--use_ngx/--no-ngx", default=False, help="Install NGX")
@click.option(
    "--overwrite/--no-overwrite", default=False, help="Overwrite the file if it exists"
)
@click.option("--verbose/--no-verbose", default=False, help="Verbose output")
def init(env, org, data_org, use_ngx, overwrite, verbose):
    _init(env, org, data_org, use_ngx, overwrite, verbose)


@cli.command()
@click.option("--env", default="Pychron", help="Environment, aka root directory name")
@click.option(
    "--overwrite/--no-overwrite", default=False, help="Overwrite the file if it exists"
)
def email(env, overwrite):
    _email(env, overwrite)


@cli.command()
@click.argument("name")
@click.option("--env", default="Pychron", help="Environment, aka root directory name")
@click.option(
    "--overwrite/--no-overwrite", default=False, help="Overwrite the file if it exists"
)
def makefile(name, env, overwrite):
    """ """
    _makefile(name, env, overwrite)


@cli.command()
@click.argument(
    "kind", type=click.Choice(["ngx", "argus", "helix"], case_sensitive=False)
)
@click.option("--env", default="Pychron", help="Environment, aka root directory name")
@click.option(
    "--overwrite/--no-overwrite", default=False, help="Overwrite the file if it exists"
)
def spectrometer_init(kind, env, overwrite):
    """ """
    _spectrometer_init(kind, env, overwrite)


@cli.command()
@click.argument("name", default="MetaData")
@click.option("--env", default="Pychron", help="Environment, aka root directory name")
@click.option(
    "--overwrite/--no-overwrite", default=False, help="Overwrite the file if it exists"
)
def metarepo(name, env, overwrite):
    """ """
    _metarepo(name, env, overwrite)


@cli.command()
@click.argument("name")
@click.option("--env", default="Pychron", help="Environment, aka root directory name")
def fetch(name, env):
    _fetch(name, env)


@cli.command()
def req():
    _req()


if __name__ == "__main__":
    cli()
# ============= EOF =============================================
