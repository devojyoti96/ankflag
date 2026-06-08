import traceback
import platform
import ctypes
import os

POSIX_FADV_DONTNEED = 4
libc = ctypes.CDLL("libc.so.6")


#####################################
# Resource management
#####################################
def drop_file_cache(filepath, verbose=False):
    """
    Advise the OS to drop the given file from the page cache.
    Safe, per-file, no sudo required.
    """
    if platform.system() != "Linux":
        raise NotImplementedError("drop_file_cache is only supported on Linux")
    try:
        if os.path.exists(filepath) is False:
            return
        if not os.path.isfile(filepath):
            return
        fd = os.open(filepath, os.O_RDONLY)
        result = libc.posix_fadvise(fd, 0, 0, POSIX_FADV_DONTNEED)
        os.close(fd)
        if verbose:
            if result == 0:
                print(f"[cache drop] Released: {filepath}")
            else:
                print(f"[cache drop] Failed ({result}) for: {filepath}")
    except Exception as e:
        if verbose:
            print(f"[cache drop] Error for {filepath}: {e}")
            traceback.print_exc()


def drop_cache(path, verbose=False):
    """
    Drop file cache for a file or all files under a directory.

    Parameters
    ----------
    path : str
        File or directory path
    """
    if platform.system() != "Linux":
        raise NotImplementedError("drop_file_cache is only supported on Linux")
    if os.path.isfile(path):
        drop_file_cache(path, verbose=verbose)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for f in files:
                full_path = os.path.join(root, f)
                drop_file_cache(full_path, verbose=verbose)
    else:
        if verbose:
            print(f"[cache drop] Path does not exist or is not valid: {path}")
