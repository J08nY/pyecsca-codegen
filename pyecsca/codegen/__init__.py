import os
import tempfile
from ast import operator, Add, Sub, Mult, Div, Pow
from enum import Enum
from os import path
from typing import List, Set, Mapping

from jinja2 import Environment, PackageLoader
from pkg_resources import resource_filename
from pyecsca.ec.coordinates import CoordinateModel
from pyecsca.ec.formula import (Formula, AdditionFormula, DoublingFormula, TriplingFormula,
                                NegationFormula, ScalingFormula, DifferentialAdditionFormula,
                                LadderFormula)
from pyecsca.ec.model import CurveModel, ShortWeierstrassModel
from pyecsca.ec.op import CodeOp

env = Environment(
        loader=PackageLoader("pyecsca.codegen")
)


def render_op(op: operator, result: str, left: str, right: str, mod: str):
    if isinstance(op, Add):
        return "bn_mod_add(&{}, &{}, &{}, &{});".format(left, right, mod, result)
    elif isinstance(op, Sub):
        return "bn_mod_sub(&{}, &{}, &{}, &{});".format(left, right, mod, result)
    elif isinstance(op, Mult):
        return "bn_mod_mul(&{}, &{}, &{}, &{});".format(left, right, mod, result)
    elif isinstance(op, Div):
        return "bn_mod_div(&{}, &{}, &{}, &{});".format(left, right, mod, result)
    elif isinstance(op, Pow) and right == 2:
        return "bn_mod_sqr(&{}, &{}, &{});".format(left, mod, result)
    elif isinstance(op, Pow):
        return "bn_mod_pow(&{}, &{}, &{}, &{});".format(left, right, mod, result)
    else:
        print(op, result, left, right, mod)


env.globals["render_op"] = render_op


class EnumDefine(Enum):
    def __str__(self):
        return self.value


class Platform(EnumDefine):
    HOST = "HOST"
    XMEGA = "CW308_XMEGA"
    STM32F0 = "CW308_STM32F0"
    STM32F3 = "CW308_STM32F3"


class HashType(EnumDefine):
    NONE = "HASH_NONE"
    SHA1 = "HASH_SHA1"
    SHA224 = "HASH_SHA224"
    SHA256 = "HASH_SHA256"
    SHA384 = "HASH_SHA384"
    SHA512 = "HASH_SHA512"


class MultAlgo(EnumDefine):
    NONE = "MULT_NONE"
    DOUBLE_AND_ADD = "MULT_DOUBLE_AND_ADD"


class RandomMod(EnumDefine):
    SAMPLE = "MOD_RAND_SAMPLE"
    REDUCE = "MOD_RAND_REDUCE"


def render_defs(model: CurveModel, coords: CoordinateModel):
    return env.get_template("defs.h").render(params=model.parameter_names,
                                             variables=coords.variables)


def render_curve_impl(model: CurveModel):
    return env.get_template("curve.c").render(params=model.parameter_names)


def transform_ops(ops: List[CodeOp], parameters: List[str], outputs: Set[str],
                  renames: Mapping[str, str] = None):
    def rename(name: str):
        if renames is not None and name not in outputs:
            return renames.get(name, name)
        return name

    allocations = []
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
               renames: Mapping[str, str] = None):
    namespace = transform_ops(ops, parameters, outputs, renames)
    return env.get_template("ops.c").render(namespace)


def render_coords_impl(coords: CoordinateModel):
    ops = []
    for s in coords.satisfying:
        try:
            ops.append(CodeOp(s))
        except:
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


def render_formula_impl(formula: Formula):
    if isinstance(formula, AdditionFormula):
        tname = "formula_add.c"
    elif isinstance(formula, DoublingFormula):
        tname = "formula_dbl.c"
    elif isinstance(formula, TriplingFormula):
        tname = "formula_tpl.c"
    elif isinstance(formula, NegationFormula):
        tname = "formula_neg.c"
    elif isinstance(formula, ScalingFormula):
        tname = "formula_scl.c"
    elif isinstance(formula, DifferentialAdditionFormula):
        tname = "formula_dadd.c"
    elif isinstance(formula, LadderFormula):
        tname = "formula_ladd.c"
    else:
        raise ValueError
    template = env.get_template(tname)
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
    return template.render(namespace)


def render_main(model: CurveModel, coords: CoordinateModel):
    return env.get_template("main.c").render(curve_variables=coords.variables,
                                             curve_parameters=model.parameter_names)


def render_makefile(platform: Platform, hash_type: HashType, mult_algo: MultAlgo,
                    mod_rand: RandomMod):
    return env.get_template("Makefile").render(platform=str(platform), hash_type=str(hash_type),
                                               mult_algo=str(mult_algo), mod_rand=str(mod_rand))


def save_render(dir: str, fname: str, render: str):
    with open(path.join(dir, fname), "w") as f:
        f.write(render)


def build(platform: Platform, hash_type: HashType, mult_algo: MultAlgo, mod_rand: RandomMod,
          model: CurveModel, coords: CoordinateModel, *formulas: Formula):
    temp = tempfile.mkdtemp()
    symlinks = ["asn1", "bn", "hal", "hash", "mult", "prng", "simpleserial", "tommath", "fat.h",
                "point.h", "curve.h", "Makefile.inc"]
    for sym in symlinks:
        os.symlink(resource_filename("pyecsca.codegen", sym), path.join(temp, sym))
    gen_dir = path.join(temp, "gen")
    os.mkdir(gen_dir)
    save_render(temp, "Makefile", render_makefile(platform, hash_type, mult_algo, mod_rand))
    save_render(temp, "main.c", render_main(model, coords))
    save_render(gen_dir, "defs.h", render_defs(model, coords))
    point_render = render_coords_impl(coords)
    for formula in formulas:
        point_render += "\n"
        point_render += render_formula_impl(formula)
    save_render(gen_dir, "point.c", point_render)
    save_render(gen_dir, "curve.c", render_curve_impl(model))
    print(temp)


if __name__ == "__main__":
    model = ShortWeierstrassModel()
    coords = model.coordinates["projective"]
    build(Platform.HOST, HashType.SHA1, MultAlgo.DOUBLE_AND_ADD, RandomMod.SAMPLE, model, coords,
          coords.formulas["add-1998-cmo"], coords.formulas["dbl-1998-cmo"])
