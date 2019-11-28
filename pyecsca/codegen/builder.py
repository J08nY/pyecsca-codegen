#!/usr/bin/env python3
import os
import shutil
import subprocess
import tempfile
from ast import operator, Add, Sub, Mult, Div, Pow
from dataclasses import dataclass
from enum import Enum
from os import path
from typing import List, Set, Mapping, Any, Optional, Type, Tuple, MutableMapping

import click
from jinja2 import Environment, PackageLoader
from pkg_resources import resource_filename
from pyecsca.ec.coordinates import CoordinateModel
from pyecsca.ec.formula import (Formula, AdditionFormula, DoublingFormula, TriplingFormula,
                                NegationFormula, ScalingFormula, DifferentialAdditionFormula,
                                LadderFormula)
from pyecsca.ec.model import (CurveModel, ShortWeierstrassModel, MontgomeryModel, EdwardsModel,
                              TwistedEdwardsModel)
from pyecsca.ec.op import CodeOp

env = Environment(
        loader=PackageLoader("pyecsca.codegen")
)


def render_op(op: operator, result: str, left: str, right: str, mod: str) -> Optional[str]:
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

    def __repr__(self):
        return self.value

    @classmethod
    def names(cls):
        return list(e.name for e in cls)


class Platform(EnumDefine):
    HOST = "HOST"
    XMEGA = "CW308_XMEGA"
    STM32F0 = "CW308_STM32F0"
    STM32F3 = "CW308_STM32F3"


class Multiplication(EnumDefine):
    TOOM_COOK = "MUL_TOOM_COOK"
    KARATSUBA = "MUL_KARATSUBA"
    COMBA = "MUL_COMBA"
    BASE = "MUL_BASE"


class Squaring(EnumDefine):
    TOOM_COOK = "SQR_TOOM_COOK"
    KARATSUBA = "SQR_KARATSUBA"
    COMBA = "SQR_COMBA"
    BASE = "SQR_BASE"


class Reduction(EnumDefine):
    BARRETT = "RED_BARRETT"
    MONTGOMERY = "RED_MONTGOMERY"
    BASE = "RED_BASE"


class HashType(EnumDefine):
    NONE = "HASH_NONE"
    SHA1 = "HASH_SHA1"
    SHA224 = "HASH_SHA224"
    SHA256 = "HASH_SHA256"
    SHA384 = "HASH_SHA384"
    SHA512 = "HASH_SHA512"


class ScalarMultAlgo(EnumDefine):
    NONE = "MULT_NONE"
    DOUBLE_AND_ADD = "MULT_DOUBLE_AND_ADD"


class RandomMod(EnumDefine):
    SAMPLE = "MOD_RAND_SAMPLE"
    REDUCE = "MOD_RAND_REDUCE"


@dataclass
class Configuration(object):
    platform: Platform
    hash_type: HashType
    mult_algo: ScalarMultAlgo
    mod_rand: RandomMod
    mult: Multiplication  # TODO: Use this
    sqr: Squaring  # TODO: Use this
    red: Reduction  # TODO: Use this
    model: CurveModel
    coords: CoordinateModel
    formulas: List[Formula]


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


def render_formula_impl(formula: Formula) -> str:
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


def render_main(model: CurveModel, coords: CoordinateModel) -> str:
    return env.get_template("main.c").render(curve_variables=coords.variables,
                                             curve_parameters=model.parameter_names)


def render_makefile(platform: Platform, hash_type: HashType, mult_algo: ScalarMultAlgo,
                    mod_rand: RandomMod) -> str:
    return env.get_template("Makefile").render(platform=str(platform), hash_type=str(hash_type),
                                               mult_algo=str(mult_algo), mod_rand=str(mod_rand))


def save_render(dir: str, fname: str, rendered: str):
    with open(path.join(dir, fname), "w") as f:
        f.write(rendered)


def render(config: Configuration) -> Tuple[str, str]:
    temp = tempfile.mkdtemp()
    symlinks = ["asn1", "bn", "hal", "hash", "mult", "prng", "simpleserial", "tommath", "fat.h",
                "point.h", "curve.h", "Makefile.inc"]
    for sym in symlinks:
        os.symlink(resource_filename("pyecsca.codegen", sym), path.join(temp, sym))
    gen_dir = path.join(temp, "gen")
    os.mkdir(gen_dir)
    save_render(temp, "Makefile",
                render_makefile(config.platform, config.hash_type, config.mult_algo,
                                config.mod_rand))
    save_render(temp, "main.c", render_main(config.model, config.coords))
    save_render(gen_dir, "defs.h", render_defs(config.model, config.coords))
    point_render = render_coords_impl(config.coords)
    for formula in config.formulas:
        point_render += "\n"
        point_render += render_formula_impl(formula)
    save_render(gen_dir, "point.c", point_render)
    save_render(gen_dir, "curve.c", render_curve_impl(config.model))
    return temp, "pyecsca-codegen-{}.elf".format(str(config.platform))


def get_model(ctx: click.Context, param, value: str) -> CurveModel:
    classes = {
        "shortw": ShortWeierstrassModel,
        "montgom": MontgomeryModel,
        "edwards": EdwardsModel,
        "twisted": TwistedEdwardsModel
    }
    if value not in classes:
        raise click.BadParameter("Cannot create CurveModel from '{}'.".format(value))
    model = classes[value]()
    ctx.meta["model"] = model
    return model


def get_coords(ctx: click.Context, param, value: Optional[str]) -> Optional[CoordinateModel]:
    if value is None:
        return None
    model = ctx.meta["model"]
    if value not in model.coordinates:
        raise click.BadParameter(
                "Coordinate model '{}' is not a model in '{}'.".format(value,
                                                                       model.__class__.__name__))
    coords = model.coordinates[value]
    ctx.meta["coords"] = coords
    return coords


def get_formula(ctx: click.Context, param, value: Optional[Tuple[str]]) -> List[Formula]:
    if not value:
        return []
    coords = ctx.meta["coords"]
    result = []
    for formula in value:
        if formula not in coords.formulas:
            raise click.BadParameter(
                    "Formula '{}' is not a formula in '{}'.".format(formula, coords))
        result.append(coords.formulas[formula])
    return result


def wrap_enum(enum_class: Type[EnumDefine]):
    def callback(ctx, param, value):
        try:
            res = getattr(enum_class, value)
            return res
        except Exception:
            raise click.BadParameter(
                    "Cannot create {} enum from {}.".format(enum_class.__name__, value))

    return callback


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option()
def main():
    pass


@main.command()
@click.option("--platform", envvar="PLATFORM", required=True,
              type=click.Choice(Platform.names()),
              callback=wrap_enum(Platform),
              help="The platform to build for.")
@click.option("--hash", envvar="HASH_TYPE", default="SHA1", show_default=True,
              type=click.Choice(HashType.names()),
              callback=wrap_enum(HashType),
              help="The hash algorithm to use (in ECDH and ECDSA).")
@click.option("--mult", envvar="MULT_ALGO", required=True,
              type=click.Choice(ScalarMultAlgo.names()),
              callback=wrap_enum(ScalarMultAlgo),
              help="The scalar multiplication algorithm to use.")
@click.option("--rand", envvar="MOD_RAND", default="SAMPLE", show_default=True,
              type=click.Choice(RandomMod.names()),
              callback=wrap_enum(RandomMod),
              help="The random sampling method to use (for uniform sampling modulo order).")
@click.option("--mul", envvar="MUL", default="BASE", show_default=True,
              type=click.Choice(Multiplication.names()),
              callback=wrap_enum(Multiplication),
              help="Multiplier to use.")
@click.option("--sqr", envvar="SQR", default="BASE", show_default=True,
              type=click.Choice(Squaring.names()),
              callback=wrap_enum(Squaring),
              help="Squaring algorithm to use.")
@click.option("--red", envvar="RED", default="BASE", show_default=True,
              type=click.Choice(Reduction.names()),
              callback=wrap_enum(Reduction),
              help="Modular reduction algorithm to use.")
@click.option("--strip", help="Whether to strip the binary or not.", is_flag=True)
@click.option("--remove/--no-remove", help="Whether to remove the dir.", is_flag=True, default=True)
@click.argument("model", required=True,
                type=click.Choice(["shortw", "montgom", "edwards", "twisted"]),
                callback=get_model)
@click.argument("coords", required=True,
                callback=get_coords)
@click.argument("formulas", required=True, nargs=-1,
                callback=get_formula)
@click.argument("outfile")
def build(platform, hash, mult, rand, mul, sqr, red, strip, remove, model, coords, formulas, outfile):
    """This command builds an ECC implementation.

    \b
    MODEL: The curve model to use.
    COORDS: The coordinate model to use.
    FORMULAS: The formulas to use.
    OUTFILE: The output binary file with the built impl.
    """
    config = Configuration(platform, hash, mult, rand, mul, sqr, red, model, coords, formulas)
    dir, file = render(config)

    full_path = path.join(dir, file)
    res = subprocess.run(["make"], cwd=dir, capture_output=True)
    click.echo(res.stdout.decode())
    if strip:
        click.echo(path.getsize(full_path))
        subprocess.run(["strip", file], cwd=dir)
        click.echo(path.getsize(full_path))
    shutil.copy(full_path, outfile)
    if remove:
        shutil.rmtree(dir)
    else:
        click.echo(dir)


@main.command()
@click.argument("model",
                type=click.Choice(["shortw", "montgom", "edwards", "twisted"]),
                callback=get_model)
@click.argument("coords", required=False,
                callback=get_coords)
@click.argument("formulas", required=False, nargs=-1,
                callback=get_formula)
def list(model: Optional[CurveModel], coords: Optional[CoordinateModel],
         formulas: Optional[Tuple[Formula]]):
    """This command lists possible choices for an ECC implementation.

    \b
    MODEL: The curve model to use.
    COORDS: The coordinate model to use.
    FORMULAS: The formulas to use.
    """
    if formulas:
        for formula in formulas:
            click.echo(formula)
            click.echo("\t{}".format(formula.meta))
            for op in formula.code:
                click.echo("\t{}".format(op))
        return
    if not formulas and coords:
        click.echo(coords)
        types = {}
        for val in coords.formulas.values():
            category = types.setdefault(val.__class__, [])
            category.append(val)
        for cls, category in types.items():
            click.echo(cls.__name__)
            for form in category:
                click.echo("\t {}: {}".format(form.name, form.meta))
        return
    if not coords and model:
        click.echo(model)
        for coord in model.coordinates.values():
            click.echo(
                    "{}: {}, [{}]".format(coord.name, coord.full_name, ",".join(coord.variables)))
        return


if __name__ == "__main__":
    main()
