from setuptools import setup, Extension
import os
import platform
import sys
import warnings
from pathlib import Path
from Cython.Build import cythonize
import numpy

def get_gsl_paths():
    """
    Finds GSL include and library paths.
    1. Checks the GSL_DIR environment variable.
    2. Searches a list of common installation locations on Windows.
    3. Searches standard locations on macOS (Homebrew).
    4. On Linux, assumes GSL is in the system path.
    """
    gsl_dir_env = os.environ.get("GSL_DIR")
    if gsl_dir_env:
        gsl_dir = Path(os.path.expandvars(gsl_dir_env))
        if gsl_dir.exists() and (gsl_dir / "include").exists() and (gsl_dir / "lib").exists():
            print(f"Using GSL from GSL_DIR environment variable: {gsl_dir}")
            return str(gsl_dir / "include"), str(gsl_dir / "lib")
        else:
            warnings.warn(f"GSL_DIR ('{gsl_dir}') is set, but it's not a valid GSL installation directory.")

    system = platform.system()
    if system == "Windows":
        candidate_paths = [
            # For vcpkg classic mode in project folder
            Path.cwd() / "vcpkg" / "packages" / "gsl_x64-windows-static",
            # For vcpkg manifest mode (`vcpkg.json`) in project folder
            Path.cwd() / "vcpkg_installed" / "x64-windows-static",
            Path("C:/gsl"),
            Path("C:/Tools/vcpkg/packages/gsl_x64-windows-static"),
            Path("D:/a/fathon/fathon/vcpkg/packages/gsl_x64-windows-static"),
            Path("./vcpkg/packages/gsl_x64-windows-static"),
            Path("./vcpkg_installed/packages/gsl_x64-windows-static"),
        ]

        search_bases = [
            Path(os.path.expandvars("%ProgramFiles%/GSL-WIN64")),
            Path(os.path.expandvars("%ProgramData%/GSL-WIN64")),
            Path.cwd() / "GSL-WIN64",
        ]

        for base in search_bases:
            if base.exists():
                version_dirs = sorted([d for d in base.glob("gsl-*") if d.is_dir()], reverse=True)
                if version_dirs:
                    candidate_paths.append(version_dirs[0])

        for path in candidate_paths:
            if path.exists() and (path / "include").exists() and (path / "lib").exists():
                print(f"Found GSL at: {path}")
                return str(path / "include"), str(path / "lib")

    elif system == "Darwin":
        if platform.processor() == "arm":
            default_path = Path("/opt/homebrew/opt/gsl")
        else:
            default_path = Path("/usr/local/opt/gsl")
        if default_path.exists():
            return str(default_path / "include"), str(default_path / "lib")
            
    else:  # Linux
        return None, None

    warnings.warn(
        "Could not find GSL automatically. "
        "Please set the GSL_DIR environment variable to your GSL installation path."
    )
    return None, None

def get_extension(module_name, src_name, gsl_inc, gsl_lib):
    sources = [src_name, os.path.join("fathon", "cLoops.c")]
    
    include_dirs = [numpy.get_include()]
    library_dirs = []
    libraries = ["gsl", "gslcblas"]
    extra_compile_args = ["-O2", "-fopenmp"]
    extra_link_args = ["-fopenmp"]

    if gsl_inc:
        include_dirs.append(gsl_inc)
    if gsl_lib:
        library_dirs.append(gsl_lib)

    system = platform.system()
    if system == "Windows":
        extra_compile_args = ["/O2", "/openmp"]
        extra_link_args = []
    elif system == "Darwin" and platform.processor() == "arm":
        llvm_path = Path("/opt/homebrew/opt/llvm")
        os.environ["CC"] = str(llvm_path / "bin/clang")
        include_dirs.append(str(llvm_path / "include"))
        library_dirs.append(str(llvm_path / "lib"))

    return Extension(
        module_name,
        sources=sources,
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        libraries=libraries,
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args
    )

if __name__ == "__main__":
    if sys.version_info[0] != 3:
        sys.exit("fathon requires Python 3.")

    gsl_include_path, gsl_library_path = get_gsl_paths()

    extensions = [
        get_extension("fathon.dfa", os.path.join("fathon", "dfa.pyx"), gsl_include_path, gsl_library_path),
        get_extension("fathon.dcca", os.path.join("fathon", "dcca.pyx"), gsl_include_path, gsl_library_path),
        get_extension("fathon.mfdfa", os.path.join("fathon", "mfdfa.pyx"), gsl_include_path, gsl_library_path),
        get_extension("fathon.mfdcca", os.path.join("fathon", "mfdcca.pyx"), gsl_include_path, gsl_library_path),
        get_extension("fathon.ht", os.path.join("fathon", "ht.pyx"), gsl_include_path, gsl_library_path),
    ]

    setup(
        ext_modules=cythonize(
            extensions,
            annotate=True,
            language_level=3
        )
    )
