import traceback
import tempfile
import os
import subprocess
import numpy as np
from .ankdata import init_ankflag_data, get_datadir


####################
# uDOCKER related
####################

def set_udocker_env():
    datadir = get_datadir()
    if (
        datadir is None
        or os.path.exists(datadir) is False
        or os.path.exists(f"{datadir}/udocker-englib-1.2.11.tar.gz") is False
    ):
        print("aNKflag data directory and docker environment is not setup yet")
        return 
    udocker_dir = f"{datadir}/udocker"
    os.makedirs(udocker_dir, exist_ok=True)
    os.environ["UDOCKER_DIR"] = udocker_dir
    os.environ["UDOCKER_TARBALL"] = f"{datadir}/udocker-englib-1.2.11.tar.gz"
    return datadir


def init_udocker():
    set_udocker_env()
    os.system("udocker install")


def check_udocker_container(name):
    """
    Check whether a docker container is present or not

    Parameters
    ----------
    name : str
        Container name

    Returns
    -------
    bool
        Whether present or not
    """
    set_udocker_env()
    env = os.environ.copy()
    try:
        result = subprocess.run(
            ["udocker", "--insecure", "--quiet", "inspect", name],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode == 0:
            return True
        else:
            return False
    except Exception:
        return False


def initialize_container(image_name, name, update=False, verbose=False):
    """
    Initialize container

    Parameters
    ----------
    image_name: str
        Docker image name
    name : str
        Container name
    update : bool, optional
        Update or not
    verbose : bool, optional
        Verbose output

    Returns
    -------
    bool
        Whether initialized successfully or not
    """
    set_udocker_env()
    env = os.environ.copy()
    check_cmd = f"udocker images | grep -q {image_name}"
    image_exists = os.system(check_cmd)
    container_exists = check_udocker_container(name)
    if image_exists != 0:
        if container_exists:
            if verbose:
                subprocess.run(
                    ["udocker", "rm", f"{name}"],
                    env=env,
                )
            else:
                subprocess.run(
                    ["udocker", "rm", f"{name}"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        if verbose:
            result = subprocess.run(
                ["udocker", "pull", f"{image_name}"],
                env=env,
            )
        else:
            result = subprocess.run(
                ["udocker", "pull", f"{image_name}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
            )
        a = result.returncode
        if a == 0:
            create_container = True
        else:
            create_container = False
    else:
        if update:
            if verbose:
                if container_exists:
                    subprocess.run(
                        ["udocker", "rm", f"{name}"],
                        env=env,
                    )
                subprocess.run(
                    ["udocker", "rmi", f"{image_name}"],
                    env=env,
                )
            else:
                if container_exists:
                    subprocess.run(
                        ["udocker", "rm", f"{name}"],
                        env=env,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                subprocess.run(
                    ["udocker", "rmi", f"{image_name}"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            print("Re-downloading docker image.")
            if verbose:
                result = subprocess.run(
                    ["udocker", "pull", f"{image_name}"],
                    env=env,
                )
            else:
                result = subprocess.run(
                    ["udocker", "pull", f"{image_name}"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            a = result.returncode
            if a == 0:
                print("Re-downloaded docker image.")
                create_container = True
            else:
                print("Re-downloading container image is failed.")
                create_container = False
                return
        else:
            print(f"Image {image_name} already present.")
            if container_exists is False:
                create_container = True
            else:
                return name
    if create_container:
        if verbose:
            result = subprocess.run(
                ["udocker", "create", f"--name={name}", f"{image_name}"],
                env=env,
            )
        else:
            result = subprocess.run(
                ["udocker", "create", f"--name={name}", f"{image_name}"],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        a = result.returncode
        print(f"Container started with name : {name}")
        return name
    else:
        print(f"Container could not be created with name : {name}")
        return


def initialize_ankflag_container(name="ankflag", update=False, verbose=False):
    """
    Initialize aNKflag container

    Parameters
    ----------
    name : str, optional
        Name of the container
    update : bool, optional
        Update container

    Returns
    -------
    bool
        Whether initialized successfully or not
    """
    set_udocker_env()
    print("Initializing aNKflag container.")
    image_name = "devojyoti96/ankflag-nonpol:latest"
    msg = initialize_container(image_name, f"{name}-nonpol", update=update, verbose=verbose)
    if msg!=None:
        print("Non-polar version of aNKflag container is initialized.")
    else:
        print("Non-polar version of aNKflag container could not be initialized.")
        return msg
    image_name = "devojyoti96/ankflag-fullpol:latest"
    msg = initialize_container(image_name, f"{name}-fullpol", update=update, verbose=verbose)
    if msg!=None:
        print("Full-polar version of aNKflag container is initialized.")
    else:
        print("Full-polar version of aNKflag container could not be initialized.")
        return msg
   

def run_ankflag(
    scratchdir,
    logfile,
    npol=2,
    container_name="ankflag",
    check_container=False,
    verbose=False,
):
    """
    Run ankflag inside a udocker container (no root permission required).

    Parameters
    ----------
    scratchdir : str
        aNKflag scratch directory
    logfile : str
        Log file name
    container_name : str, optional
        Container name
    check_container : bool, optional
        Check container presence or not
    verbose : bool, optional
        Verbose output or not

    Returns
    -------
    int
        Success message
    str
        Fits file name
    """
    set_udocker_env()
    if check_container:
        container_present = check_udocker_container(container_name)
        if not container_present:
            print(f"Initializing {container_name}...")
            container_name = initialize_lta_container(name=container_name, verbose=True)
            if container_name is None:
                print(
                    f"Container {container_name} is not initiated. First initiate container and then run."
                )
                return 1, ""
    try:
        scrpath = os.path.dirname(scratchdir)
        temp_name = "ankflag_udocker_" + next(tempfile._get_candidate_names())
        temp_docker_path = os.path.join(scrpath, temp_name)
        temp_scratchdir = f"{os.path.basename(scratchdir)}"

        #########################
        # Run ankflag
        #########################
        if npol==4:
            full_command = [
                "udocker",
                "run",
                "--nobanner",
                f"--volume={scrpath}:{temp_docker_path}",
                "--workdir",
                f"{temp_docker_path}",
                f"{container_name}-fullpol",
                "bash",
                "-c",
                f"cd /src && ankflag {temp_docker_path} {npol} > {temp_docker_path}/{logfile}",
            ]
        else:
            full_command = [
                "udocker",
                "run",
                "--nobanner",
                f"--volume={scrpath}:{temp_docker_path}",
                "--workdir",
                f"{temp_docker_path}",
                f"{container_name}-nonpol",
                "bash",
                "-c",
                f"cd /src && ankflag {temp_docker_path} {npol} > {temp_docker_path}/{logfile}",
            ]
        if verbose:
            result = subprocess.run(
                full_command,
            )
        else:
            result = subprocess.run(
                full_command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        exit_code = result.returncode
        if exit_code == 0:
            return 0
        else:
            return 1
    except Exception:
        traceback.print_exc()
        return 1


