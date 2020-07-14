import os
import shutil
import subprocess
import tempfile
from _ast import Pow
from os import path
from os import mkdir
from typing import Optional, List, Set, Mapping, MutableMapping, Any, Tuple

from jinja2 import Environment, PackageLoader
from pkg_resources import resource_filename
from public import public
from pyecsca.ec.configuration import HashType, RandomMod, Reduction, Multiplication, Squaring
from pyecsca.ec.coordinates import CoordinateModel
from pyecsca.ec.formula import (Formula)
from pyecsca.ec.model import CurveModel
from pyecsca.ec.mult import (ScalarMultiplier, LTRMultiplier, RTLMultiplier, CoronMultiplier,
                             LadderMultiplier, SimpleLadderMultiplier, DifferentialLadderMultiplier,
                             BinaryNAFMultiplier)
from pyecsca.ec.op import OpType, CodeOp

from pyecsca.codegen.common import Platform, DeviceConfiguration

env = Environment(
        loader=PackageLoader("pyecsca.codegen")
)

env.globals["isinstance"] = isinstance


def render_op(op: OpType, result: str, left: str, right: str, mod: str, red: str) -> Optional[str]:
    if op == OpType.Add:
        return "bn_red_add(&{}, &{}, &{}, &{}, &{});".format(left, right, mod, red, result)
    elif op == OpType.Sub:
        return "bn_red_sub(&{}, &{}, &{}, &{}, &{});".format(left, right, mod, red, result)
    elif op == OpType.Neg:
        return "bn_red_neg(&{}, &{}, &{}, &{});".format(right, mod, red, result)
    elif op == OpType.Mult:
        return "bn_red_mul(&{}, &{}, &{}, &{}, &{});".format(left, right, mod, red, result)
    elif op == OpType.Div or op == OpType.Inv:
        return "bn_red_div(&{}, &{}, &{}, &{}, &{});".format(left, right, mod, red, result)
    elif op == OpType.Sqr:
        return "bn_red_sqr(&{}, &{}, &{}, &{});".format(left, mod, red, result)
    elif op == OpType.Pow:
        return "bn_red_pow(&{}, &{}, &{}, &{}, &{});".format(left, right, mod, red, result)
    elif op == OpType.Id:
        return "bn_copy(&{}, &{});".format(left, result)
    else:
        print(op, result, left, right, mod)
        return None


env.globals["render_op"] = render_op


def render_defs(model: CurveModel, coords: CoordinateModel) -> str:
    return env.get_template("defs.h").render(params=model.parameter_names,
                                             variables=coords.variables)


def render_curve_impl(model: CurveModel) -> str:
    return env.get_template("curve.c").render(params=model.parameter_names)


def transform_ops(ops: List[CodeOp], parameters: List[str], outputs: Set[str],
                  renames: Mapping[str, str] = None) -> MutableMapping[Any, Any]:
    def rename(name: str):
        if renames is not None and name not in outputs:
            return renames.get(name, name)
        return name

    allocations: List[str] = []
    initializations = {}
    const_mapping = {}
    operations = []
    frees = []
    for op in ops:
        if op.result not in allocations:
            allocations.append(op.result)
            frees.append(op.result)
        for param in op.parameters:
            if param not in allocations and param not in parameters:
                raise ValueError("Should be allocated or parameter: {}".format(param))
        for const in op.constants:
            name = "c" + str(const)
            if name not in allocations:
                allocations.append(name)
                initializations[name] = const
                const_mapping[const] = name
                frees.append(name)
        operations.append((op.operator, op.result, rename(op.left), rename(op.right)))
    mapped = []
    for op in operations:
        o2 = op[2]
        if o2 in const_mapping:
            o2 = const_mapping[o2]
        o3 = op[3]
        if o3 in const_mapping and not (isinstance(op[0], Pow) and o3 == 2):
            o3 = const_mapping[o3]
        mapped.append((op[0], op[1], o2, o3))
    returns = {}
    if renames:
        for r_from, r_to in renames.items():
            if r_from in outputs:
                returns[r_from] = r_to

    return dict(allocations=allocations,
                initializations=initializations,
                const_mapping=const_mapping, operations=mapped,
                frees=frees, returns=returns)


def render_ops(ops: List[CodeOp], parameters: List[str], outputs: Set[str],
               renames: Mapping[str, str] = None) -> str:
    namespace = transform_ops(ops, parameters, outputs, renames)
    return env.get_template("ops.c").render(namespace)


def render_coords_impl(coords: CoordinateModel) -> str:
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
    namespace = transform_ops(ops, coords.curve_model.parameter_names,
                              coords.curve_model.coordinate_names, renames)
    returns = namespace["returns"]
    namespace["returns"] = {}
    frees = namespace["frees"]
    namespace["frees"] = {}

    return env.get_template("point.c").render(variables=coords.variables, **namespace,
                                              to_affine_rets=returns, to_affine_frees=frees)


def render_formulas_impl(formulas: Set[Formula]) -> str:
    names = {formula.shortname for formula in formulas}
    return env.get_template("formulas.c").render(names=names)


def render_formula_impl(formula: Formula, short_circuit: bool = False) -> str:
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
    namespace = transform_ops(formula.code, formula.coordinate_model.curve_model.parameter_names,
                              formula.outputs, renames)
    namespace["short_circuit"] = short_circuit
    namespace["formula"] = formula
    return template.render(namespace)


def render_scalarmult_impl(scalarmult: ScalarMultiplier) -> str:
    return env.get_template("mult.c").render(scalarmult=scalarmult, LTRMultiplier=LTRMultiplier,
                                             RTLMultiplier=RTLMultiplier,
                                             CoronMultiplier=CoronMultiplier,
                                             LadderMultiplier=LadderMultiplier,
                                             SimpleLadderMultiplier=SimpleLadderMultiplier,
                                             DifferentialLadderMultiplier=DifferentialLadderMultiplier,
                                             BinaryNAFMultiplier=BinaryNAFMultiplier)


def render_action() -> str:
    return env.get_template("action.c").render()


def render_rand() -> str:
    return env.get_template("rand.c").render()

def render_main(model: CurveModel, coords: CoordinateModel, keygen: bool, ecdh: bool,
                ecdsa: bool) -> str:
    return env.get_template("main.c").render(model=model, coords=coords,
                                             curve_variables=coords.variables,
                                             curve_parameters=model.parameter_names,
                                             keygen=keygen, ecdh=ecdh, ecdsa=ecdsa)


def render_makefile(platform: Platform, hash_type: HashType, mod_rand: RandomMod,
                    reduction: Reduction, mul: Multiplication, sqr: Squaring) -> str:
    return env.get_template("Makefile").render(platform=str(platform), hash_type=str(hash_type),
                                               mod_rand=str(mod_rand), reduction=str(reduction),
                                               mul=str(mul), sqr=str(sqr))


def save_render(dir: str, fname: str, rendered: str):
    with open(path.join(dir, fname), "w") as f:
        f.write(rendered)


@public
def render(config: DeviceConfiguration) -> Tuple[str, str, str]:
    """

    :param config:
    :return:
    """
    temp = tempfile.mkdtemp()
    symlinks = ["asn1", "bn", "hal", "hash", "mult", "prng", "simpleserial", "tommath", "fat.h",
                "rand.h", "point.h", "curve.h", "mult.h", "formulas.h", "action.h", "Makefile.inc"]
    for sym in symlinks:
        os.symlink(resource_filename("pyecsca.codegen", sym), path.join(temp, sym))
    gen_dir = path.join(temp, "gen")
    os.mkdir(gen_dir)

    save_render(temp, "Makefile",
                render_makefile(config.platform, config.hash_type, config.mod_rand, config.red, config.mult, config.sqr))
    save_render(temp, "main.c",
                render_main(config.model, config.coords, config.keygen, config.ecdh, config.ecdsa))
    save_render(gen_dir, "defs.h", render_defs(config.model, config.coords))
    save_render(gen_dir, "point.c", render_coords_impl(config.coords))
    save_render(gen_dir, "formulas.c", render_formulas_impl(config.formulas))
    for formula in config.formulas:
        save_render(gen_dir, f"formula_{formula.shortname}.c",
                    render_formula_impl(formula, config.scalarmult.short_circuit))
    save_render(gen_dir, "action.c", render_action())
    save_render(gen_dir, "rand.c", render_rand())
    save_render(gen_dir, "curve.c", render_curve_impl(config.model))
    save_render(gen_dir, "mult.c", render_scalarmult_impl(config.scalarmult))
    return temp, "pyecsca-codegen-{}.elf".format(
            str(config.platform)), "pyecsca-codegen-{}.hex".format(str(config.platform))


@public
def build(dir: str, elf_file: str, hex_file: str, outdir: str, strip: bool = False,
          remove: bool = True) -> subprocess.CompletedProcess:
    """

    :param dir:
    :param elf_file:
    :param hex_file:
    :param outdir:
    :param strip:
    :param remove:
    :return:
    """
    res = subprocess.run(["make"], cwd=dir, capture_output=True)
    if res.returncode != 0:
        raise ValueError("Build failed!")
    if strip:
        subprocess.run(["make", "strip"], cwd=dir)
    full_elf_path = path.join(dir, elf_file)
    full_hex_path = path.join(dir, hex_file)
    mkdir(outdir)
    shutil.copy(full_elf_path, outdir)
    shutil.copy(full_hex_path, outdir)
    if remove:
        shutil.rmtree(dir)
    return res


@public
def render_and_build(config: DeviceConfiguration, outdir: str, strip: bool = False,
                     remove: bool = True) -> Tuple[str, str, str, subprocess.CompletedProcess]:
    """

    :param config:
    :param outdir:
    :param strip:
    :param remove:
    :return:
    """
    dir, elf_file, hex_file = render(config)
    res = build(dir, elf_file, hex_file, outdir, strip, remove)
    return dir, elf_file, hex_file, res
