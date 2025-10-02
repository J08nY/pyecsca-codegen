"""Rendering and building of implementation configurations."""

import os
import shutil
import subprocess
import tempfile
from os import path
from os import makedirs
from typing import Optional, List, Set, Mapping, MutableMapping, Any, Tuple

from jinja2 import Environment, PackageLoader
from importlib_resources import files
from public import public
from pyecsca.ec.configuration import (
    HashType,
    RandomMod,
    Reduction,
    Multiplication,
    Squaring,
)
from pyecsca.ec.coordinates import CoordinateModel
from pyecsca.ec.formula import Formula
from pyecsca.ec.model import CurveModel
from pyecsca.ec.mult import (
    ScalarMultiplier,
    LTRMultiplier,
    RTLMultiplier,
    CoronMultiplier,
    LadderMultiplier,
    SimpleLadderMultiplier,
    DifferentialLadderMultiplier,
    BinaryNAFMultiplier,
    WindowNAFMultiplier,
    SlidingWindowMultiplier,
    FixedWindowLTRMultiplier,
    FullPrecompMultiplier,
    BGMWMultiplier,
    CombMultiplier,
    AccumulationOrder,
    ProcessingDirection,
    WindowBoothMultiplier,
)
from pyecsca.ec.op import OpType, CodeOp

from pyecsca.codegen.common import Platform, DeviceConfiguration

env = Environment(loader=PackageLoader("pyecsca.codegen"))

# Make some Python functions available in the templates.
env.globals["isinstance"] = isinstance
env.globals["bin"] = bin
env.globals["AccumulationOrder"] = AccumulationOrder
env.globals["ProcessingDirection"] = ProcessingDirection


def render_op(
    op: OpType, result: str, left: str, right: str, mod: str, red: str
) -> Optional[str]:
    """
    Render an operation `op` (add, sub, neg, ...) into a C string.

    The operation will use `left` (optional) and `right` operands, be over `mod` modulus,
    use the `red` reduction context and leave the result in `result`. All of these need to
    be valid C variable names.

    :param op: The operation type.
    :param result: The variable name to store the result in.
    :param left: The left operand variable name (if any).
    :param right: The right operand variable name (if any).
    :param mod: The modulus variable name.
    :param red: The reduction context variable name.
    :return: The rendered C source code as a string, or None if the operation is not supported.
    """
    if op == OpType.Add:
        return "bn_red_add(&{}, &{}, &{}, &{}, &{});".format(
            left, right, mod, red, result
        )
    elif op == OpType.Sub:
        return "bn_red_sub(&{}, &{}, &{}, &{}, &{});".format(
            left, right, mod, red, result
        )
    elif op == OpType.Neg:
        return "bn_red_neg(&{}, &{}, &{}, &{});".format(right, mod, red, result)
    elif op == OpType.Mult:
        return "bn_red_mul(&{}, &{}, &{}, &{}, &{});".format(
            left, right, mod, red, result
        )
    elif op == OpType.Div or op == OpType.Inv:
        return "bn_red_div(&{}, &{}, &{}, &{}, &{});".format(
            left, right, mod, red, result
        )
    elif op == OpType.Sqr:
        return "bn_red_sqr(&{}, &{}, &{}, &{});".format(left, mod, red, result)
    elif op == OpType.Pow:
        return "bn_red_pow(&{}, &{}, &{}, &{}, &{});".format(
            left, right, mod, red, result
        )
    elif op == OpType.Id:
        return "bn_copy(&{}, &{});".format(left, result)
    else:
        print(op, result, left, right, mod)
        return None


env.globals["render_op"] = render_op


def render_defs(model: CurveModel, coords: CoordinateModel) -> str:
    """
    Render the defs.h file with definitions of the curve and point structures.

    These change depending on the number (and name) of curve parameters and number
    (and name) of point coordinates.

    :param model: The curve model to render.
    :param coords: The coordinate model to render.
    :return: The rendered C source code as a string.
    """
    return env.get_template("defs.h").render(
        params=model.parameter_names, variables=coords.variables
    )


def render_curve_impl(model: CurveModel) -> str:
    """
    Render the curve.c file with basic curve operations.

    These change depending on the number (and name) of curve parameters.

    :param model: The curve model to render.
    :return: The rendered C source code as a string.
    """
    return env.get_template("curve.c").render(params=model.parameter_names)


def transform_ops(
    ops: List[CodeOp],
    parameters: List[str],
    outputs: Set[str],
    renames: Mapping[str, str] = None,
) -> MutableMapping[Any, Any]:
    """
    Transform a list of CodeOps, parameters, outputs and renames into a mapping
    that will be used by the ops template macros to render the ops.

    This tracks allocations and frees, also creates a mapping of constants
    to variable names.

    Useful when you have a list of operations and want to render them,
    such as when executing a formula or coordinate transformation.

    :param ops: The list of operations to transform.
    :param parameters: The list of parameter names that are inputs to the operations.
    :param outputs: The set of output names that should not be freed.
    :param renames: Optional mapping of variable names to renamed versions.
    :return: A mapping with keys:
        - allocations: List of variable names that need to be allocated.
        - initializations: Mapping of variable names to (constant, encode) tuples for initialization.
        - const_mapping: Mapping of (constant, encode) tuples to variable names.
        - operations: List of (op, result, left, right) tuples for the operations
        - frees: List of variable names that need to be freed.
        - returns: Mapping of output variable names to renamed versions.
    """

    def rename(name: str):
        if renames is not None and name not in outputs:
            return renames.get(name, name)
        return name

    allocations: List[str] = []
    initializations = {}
    const_mapping = {}
    operations = []
    frees = []
    # Go over the ops, track allocations needed for intermediates and constants.
    # There are two kinds of constants, encoded and not-encoded. The encoded
    # ones are default, the non-encoded ones are only in the exponents, where
    # you don't want to encode using the reduction object (i.e. Montgomery form).
    # Also constructs a mapping from raw constants to their variable names.
    for op in ops:
        if op.result not in allocations:
            allocations.append(op.result)
            frees.append(op.result)
        for param in op.parameters:
            if param not in allocations and param not in parameters:
                raise ValueError("Should be allocated or parameter: {}".format(param))
        for const in op.constants:
            if op.operator == OpType.Pow:
                name = "cu" + str(const)
                encode = False
            else:
                name = "c" + str(const)
                encode = True
            if name not in allocations:
                allocations.append(name)
                initializations[name] = (const, encode)
                const_mapping[(const, encode)] = name
                frees.append(name)
        operations.append((op.operator, op.result, rename(op.left), rename(op.right)))
    mapped = []
    # Go over the operations and map constants to their variable names,
    # make sure the encoded/non-encoded version is used where appropriate.
    for op in operations:
        o2 = op[2]
        if (o2, True) in const_mapping:
            o2 = const_mapping[(o2, True)]
        o3 = op[3]
        o3_enc = op[0] != OpType.Pow
        if (o3, o3_enc) in const_mapping:
            o3 = const_mapping[(o3, o3_enc)]
        mapped.append((op[0], op[1], o2, o3))
    returns = {}
    # Handle renames in the returns.
    if renames:
        for r_from, r_to in renames.items():
            if r_from in outputs:
                returns[r_from] = r_to

    return dict(
        allocations=allocations,
        initializations=initializations,
        const_mapping=const_mapping,
        operations=mapped,
        frees=frees,
        returns=returns,
    )


def render_coords_impl(
    coords: CoordinateModel, accumulation_order: Optional[AccumulationOrder]
) -> str:
    """
    Render the point.c file with coordinate operations for a given curve model.

    :param coords: The coordinate model containing variables and satisfying equations.
    :param accumulation_order: The accumulation order for scalar multiplication, if any.
    :return: Rendered C source code as a string.
    """
    ops = []
    for s in coords.satisfying:
        try:
            ops.append(CodeOp(s))
        except Exception:
            pass
    renames = {"x": "out_x", "y": "out_y"}
    for variable in coords.variables:
        renames[variable] = "point->{}".format(variable)
    for param in coords.curve_model.parameter_names:
        renames[param] = "curve->{}".format(param)
    namespace = transform_ops(
        ops,
        coords.curve_model.parameter_names,
        coords.curve_model.coordinate_names,
        renames,
    )
    returns = namespace["returns"]
    namespace["returns"] = {}
    frees = namespace["frees"]
    namespace["frees"] = {}

    return env.get_template("point.c").render(
        variables=coords.variables,
        **namespace,
        to_affine_rets=returns,
        to_affine_frees=frees,
        accumulation_order=accumulation_order,
    )


def render_formulas_impl(formulas: Set[Formula]) -> str:
    """
    Render the formulas.c file with formula dispatch functions.

    :param formulas: The set of formulas to render.
    :return: The rendered C source code as a string.
    """
    names = {formula.shortname for formula in formulas}
    return env.get_template("formulas.c").render(names=names)


def render_formula_impl(formula: Formula, short_circuit: bool = False) -> str:
    """
    Render a single formula into its own C file.

    :param formula: The formula to render.
    :param short_circuit: Whether to short-circuit on zero inputs.
    :return: The rendered C source code as a string.
    """
    template = env.get_template(f"formula_{formula.shortname}.c")
    inputs = ["one", "other", "diff"]
    outputs = ["out_one", "out_other"]
    renames = {}
    for input in formula.inputs:
        var = input[0]
        num = int(input[1:]) - formula.input_index
        renames[input] = "{}->{}".format(inputs[num], var)
    for param in formula.coordinate_model.curve_model.parameter_names:
        renames[param] = "curve->{}".format(param)
    for output in formula.outputs:
        var = output[0]
        num = int(output[1:]) - formula.output_index
        renames[output] = "{}->{}".format(outputs[num], var)
    namespace = transform_ops(
        formula.code,
        formula.coordinate_model.curve_model.parameter_names,
        formula.outputs,
        renames,
    )
    namespace["short_circuit"] = short_circuit
    namespace["formula"] = formula
    return template.render(namespace)


def render_scalarmult_impl(scalarmult: ScalarMultiplier) -> str:
    """
    Render the mult.c file with scalar multiplication implementation.

    :param scalarmult: The scalar multiplication algorithm to render.
    :return: The rendered C source code as a string.
    """
    return env.get_template("mult.c").render(
        scalarmult=scalarmult,
        LTRMultiplier=LTRMultiplier,
        RTLMultiplier=RTLMultiplier,
        CoronMultiplier=CoronMultiplier,
        LadderMultiplier=LadderMultiplier,
        SimpleLadderMultiplier=SimpleLadderMultiplier,
        DifferentialLadderMultiplier=DifferentialLadderMultiplier,
        BinaryNAFMultiplier=BinaryNAFMultiplier,
        WindowNAFMultiplier=WindowNAFMultiplier,
        WindowBoothMultiplier=WindowBoothMultiplier,
        SlidingWindowMultiplier=SlidingWindowMultiplier,
        FixedWindowLTRMultiplier=FixedWindowLTRMultiplier,
        FullPrecompMultiplier=FullPrecompMultiplier,
        BGMWMultiplier=BGMWMultiplier,
        CombMultiplier=CombMultiplier,
    )


def render_action() -> str:
    """
    Render the action.c file with the action macros.

    :return: The rendered C source code as a string.
    """
    return env.get_template("action.c").render()


def render_rand() -> str:
    """
    Render the rand.c file with the random number generation code.

    :return: The rendered C source code as a string.
    """
    return env.get_template("rand.c").render()


def render_main(
    model: CurveModel, coords: CoordinateModel, keygen: bool, ecdh: bool, ecdsa: bool
) -> str:
    """
    Render the main.c file with the main function and high-level operations.

    :param model: The curve model.
    :param coords: The coordinate model.
    :param keygen: Whether to include key generation.
    :param ecdh: Whether to include ECDH.
    :param ecdsa: Whether to include ECDSA.
    :return: The rendered C source code as a string.
    """
    return env.get_template("main.c").render(
        model=model,
        coords=coords,
        curve_variables=coords.variables,
        curve_parameters=model.parameter_names,
        keygen=keygen,
        ecdh=ecdh,
        ecdsa=ecdsa,
    )


def render_makefile(
    platform: Platform,
    hash_type: HashType,
    mod_rand: RandomMod,
    reduction: Reduction,
    mul: Multiplication,
    sqr: Squaring,
    defines: Optional[MutableMapping[str, Any]],
) -> str:
    """
    Render the Makefile with the given configuration options.

    :param platform: The target platform.
    :param hash_type: The hash type to use.
    :param mod_rand: The random sampling method.
    :param reduction: The modular reduction method.
    :param mul: The multiplication method.
    :param sqr: The squaring method.
    :param defines: Optional mapping of additional defines to include.
    :return: The rendered Makefile as a string.
    """
    return env.get_template("Makefile").render(
        platform=str(platform),
        hash_type=str(hash_type),
        mod_rand=str(mod_rand),
        reduction=str(reduction),
        mul=str(mul),
        sqr=str(sqr),
        defines=defines,
    )


def save_render(dir: str, fname: str, rendered: str):
    with open(path.join(dir, fname), "w") as f:
        f.write(rendered)


@public
def render(config: DeviceConfiguration) -> Tuple[str, str, str]:
    """
    Render the `config`dispatching into a temporary directory.

    :param config: The configuration to render.
    :return: The temporary directory, the elf-file name, the hex-file name.
    """
    temp = tempfile.mkdtemp()
    symlinks = [
        "asn1",
        "bn",
        "hal",
        "hash",
        "prng",
        "simpleserial",
        "tommath",
        "fat.h",
        "rand.h",
        "point.h",
        "curve.h",
        "mult.h",
        "formulas.h",
        "action.h",
        "Makefile.inc",
    ]
    for sym in symlinks:
        os.symlink(files("pyecsca.codegen").joinpath(sym), path.join(temp, sym))
    gen_dir = path.join(temp, "gen")
    makedirs(gen_dir, exist_ok=True)

    save_render(
        temp,
        "Makefile",
        render_makefile(
            config.platform,
            config.hash_type,
            config.mod_rand,
            config.red,
            config.mult,
            config.sqr,
            config.defines,
        ),
    )
    save_render(
        temp,
        "main.c",
        render_main(
            config.model, config.coords, config.keygen, config.ecdh, config.ecdsa
        ),
    )
    save_render(gen_dir, "defs.h", render_defs(config.model, config.coords))
    save_render(
        gen_dir,
        "point.c",
        render_coords_impl(
            config.coords, getattr(config.scalarmult, "accumulation_order", None)
        ),
    )
    save_render(gen_dir, "formulas.c", render_formulas_impl(config.formulas))
    for formula in config.formulas:
        save_render(
            gen_dir,
            f"formula_{formula.shortname}.c",
            render_formula_impl(formula, config.scalarmult.short_circuit),
        )
    save_render(gen_dir, "action.c", render_action())
    save_render(gen_dir, "rand.c", render_rand())
    save_render(gen_dir, "curve.c", render_curve_impl(config.model))
    save_render(gen_dir, "mult.c", render_scalarmult_impl(config.scalarmult))
    return (
        temp,
        "pyecsca-codegen-{}.elf".format(str(config.platform)),
        "pyecsca-codegen-{}.hex".format(str(config.platform)),
    )


@public
def build(
    dir: str,
    elf_file: str,
    hex_file: str,
    outdir: str,
    strip: bool = False,
    remove: bool = True,
) -> subprocess.CompletedProcess:
    """
    Build a rendered configuration.

    :param dir: Directory with a rendered implementation.
    :param elf_file: Elf-file name.
    :param hex_file: Hex-file name.
    :param outdir: Output directory to copy the elf and hex files into.
    :param strip: Whether to strip the resulting binary of debug symbols.
    :param remove: Whether to remove the original directory after build.
    :return: The subprocess that ran the build (make).
    """
    res = subprocess.run(["make"], cwd=dir, capture_output=True)
    if res.returncode != 0:
        raise ValueError("Build failed!")
    if strip:
        subprocess.run(["make", "strip"], cwd=dir, capture_output=True)
    full_elf_path = path.join(dir, elf_file)
    full_hex_path = path.join(dir, hex_file)
    makedirs(outdir, exist_ok=True)
    shutil.copy(full_elf_path, outdir)
    shutil.copy(full_hex_path, outdir)
    if remove:
        shutil.rmtree(dir)
    return res


@public
def render_and_build(
    config: DeviceConfiguration, outdir: str, strip: bool = False, remove: bool = True
) -> Tuple[str, str, str, subprocess.CompletedProcess]:
    """
    Render and build a `config` in one go.

    :param config: The configuration to build.
    :param outdir: Output directory to copy the elf and hex files into.
    :param strip: Whether to strip the resulting binary of debug symbols.
    :param remove: Whether to remove the original directory after build.
    :return: The subprocess that ran the build (make).
    """
    dir, elf_file, hex_file = render(config)
    res = build(dir, elf_file, hex_file, outdir, strip, remove)
    return dir, elf_file, hex_file, res
