#!/usr/bin/env python3
"""
Builder script.

Use it to render and build ECC implementations.

Examples
========

To list available implementation choices use the ``list`` subcommand.

.. code-block:: shell

    builder list

To go deeper and examine the coordinates for a given curve model, e.g. the Short-Weierstrass one, use:

.. code-block:: shell

    builder list shortw

To list formulas for a given coordinate system and curve model, e.g. projective on Short-Weierstrass curves, use:

.. code-block:: shell

   builder list shortw projective

The following example builds an implementation for the HOST architecture,
using the short-Weierstrass curve model, projective coordinates, ``add-2007-bl`` and ``dbl-2007-bl``
formulas with the left-to-right double-and-add scalar multiplier. Furthermore, it uses Barrett modular
reduction.

.. code-block:: shell

    builder build --platform HOST --red BARRETT -v shortw projective add-2007-bl dbl-2007-bl "ltr()" .

The following uses different formulas with the comb multiplier and specifies its width.

.. code-block:: shell

    builder build --platform HOST --red BARRETT -v shortw projective add-1998-cmo dbl-1998-cmo "comb(width=5)" .
"""
import re
import shutil
import subprocess
from copy import copy
from os import path
from typing import List, Optional, Tuple, Type, MutableMapping, Any

import click
from public import public
from pyecsca.ec.configuration import (Multiplication, Squaring, Reduction, HashType, RandomMod,
                                      Inversion)
from pyecsca.ec.coordinates import CoordinateModel
from pyecsca.ec.formula import Formula, AdditionFormula
from pyecsca.ec.model import CurveModel
from pyecsca.ec.mult import ScalarMultiplier, AccumulationOrder, ProcessingDirection

from pyecsca.codegen.render import render
from pyecsca.codegen.common import Platform, DeviceConfiguration, MULTIPLIERS, wrap_enum, get_model, get_coords


def get_formula(ctx: click.Context, param, value: Optional[Tuple[str]]) -> List[Formula]:
    if not value:
        return []
    ctx.ensure_object(dict)
    coords = ctx.obj["coords"]
    result = []
    for formula in value:
        if formula not in coords.formulas:
            raise click.BadParameter(
                "Formula '{}' is not a formula in '{}'.".format(formula, coords))
        result.append(coords.formulas[formula])
    if len(set(formula.__class__ for formula in result)) != len(result):
        raise click.BadParameter("Duplicate formula types.")
    ctx.obj["formulas"] = copy(result)
    return result


def get_multiplier(ctx: click.Context, param, value: Optional[str]) -> Optional[ScalarMultiplier]:
    if value is None:
        return None
    res = re.match(
        r"(?P<name>[a-zA-Z\-]+)\((?P<args>([a-zA-Z_]+ *= *[a-zA-Z0-9.]+, ?)*?([a-zA-Z_]+ *= *[a-zA-Z0-9.]+)*)\)",
        value)
    if not res:
        raise click.BadParameter("Couldn't parse multiplier spec: {}.".format(value))
    name = res.group("name")
    args = res.group("args")
    mult_class: Type[ScalarMultiplier] = None
    for mult_def in MULTIPLIERS:
        if name in mult_def["name"]:
            mult_class = mult_def["class"]
            break
    if mult_class is None:
        raise click.BadParameter("Unknown multiplier: {}.".format(name))
    ctx.ensure_object(dict)
    formulas = ctx.obj["formulas"]
    classes = set(formula.__class__ for formula in formulas)
    if not all(
            any(issubclass(cls, required) for cls in classes) for required in mult_class.requires):
        raise click.BadParameter(
            "Multiplier {} requires formulas: {}, got {}.".format(mult_class.__name__,
                                                                  mult_class.requires, classes))
    globs = dict(globals())
    globs["AccumulationOrder"] = AccumulationOrder
    globs["ProcessingDirection"] = ProcessingDirection
    kwargs = eval("dict(" + args + ")", globs)
    required = set(
        filter(lambda formula: any(isinstance(formula, cls) for cls in mult_class.requires),
               formulas))
    optional = set(
        filter(lambda formula: any(isinstance(formula, cls) for cls in mult_class.optionals),
               formulas))
    for formula in required.union(optional):
        kwargs[formula.shortname] = formula
    mult = mult_class(**kwargs)
    return mult


def get_define(ctx: click.Context, param, values: Optional[List[str]]) -> Optional[MutableMapping[str, Any]]:
    if values is None:
        return None
    res = {}
    for val in values:
        try:
            k, v = val.split("=")
        except:
            k = val
            v = 1
        res[k] = v
    return res


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option()
@public
def main():
    """
    A tool for building ECC implementations on devices.
    """
    pass


@main.command("build")
@click.option("--platform", envvar="PLATFORM", required=True,
              type=click.Choice(Platform.names()),
              callback=wrap_enum(Platform),
              help="The platform to build for.")
@click.option("--hash", envvar="HASH_TYPE", default="SHA1", show_default=True,
              type=click.Choice(HashType.names()),
              callback=wrap_enum(HashType),
              help="The hash algorithm to use (in ECDH and ECDSA).")
@click.option("--rand", envvar="MOD_RAND", default="SAMPLE", show_default=True,
              type=click.Choice(RandomMod.names()),
              callback=wrap_enum(RandomMod),
              help="The random sampling method to use (for uniform sampling modulo order).")
@click.option("--mul", envvar="MUL", default="BASE", show_default=True,
              type=click.Choice(Multiplication.names()),
              callback=wrap_enum(Multiplication),
              help="Multiplication algorithm to use.")
@click.option("--sqr", envvar="SQR", default="BASE", show_default=True,
              type=click.Choice(Squaring.names()),
              callback=wrap_enum(Squaring),
              help="Squaring algorithm to use.")
@click.option("--red", envvar="RED", default="BASE", show_default=True,
              type=click.Choice(Reduction.names()),
              callback=wrap_enum(Reduction),
              help="Modular reduction algorithm to use.")
@click.option("--inv", envvar="INV", default="GCD", show_default=True,
              type=click.Choice(Inversion.names()),
              callback=wrap_enum(Inversion),
              help="Modular inversion algorithm to use.")
@click.option("--keygen/--no-keygen", help="Whether to enable keygen.", is_flag=True, default=True,
              show_default=True)
@click.option("--ecdh/--no-ecdh", help="Whether to enable ECDH.", is_flag=True, default=True,
              show_default=True)
@click.option("--ecdsa/--no-ecdsa", help="Whether to enable ECDSA.", is_flag=True, default=True,
              show_default=True)
@click.option("-D", "--define", help="Set a custom C define.", multiple=True,
              type=str, callback=get_define)
@click.option("--strip", help="Whether to strip the binary or not.", is_flag=True)
@click.option("--remove/--no-remove", help="Whether to remove the dir.", is_flag=True, default=True,
              show_default=True)
@click.option("-v", "--verbose", count=True)
@click.argument("model", required=True,
                type=click.Choice(["shortw", "montgom", "edwards", "twisted"]),
                callback=get_model)
@click.argument("coords", required=True,
                callback=get_coords)
@click.argument("formulas", required=True, nargs=-1,
                callback=get_formula)
@click.argument("scalarmult", required=True,
                callback=get_multiplier)
@click.argument("outdir")
@click.pass_context
@public
def build_impl(ctx, platform, hash, rand, mul, sqr, red, inv, keygen, ecdh, ecdsa, define, strip, remove,
               verbose, model, coords, formulas, scalarmult, outdir):
    """This command builds an ECC implementation.

    \b
    MODEL: The curve model to use.
    COORDS: The coordinate model to use.
    FORMULAS: The formulas to use.
    SCALARMULT: The scalar multiplication algorithm to use.
    OUTDIR: The output directory for files with the built impl.
    """
    ctx.ensure_object(dict)
    formulas = ctx.obj["formulas"]
    if ecdsa and not any(isinstance(formula, AdditionFormula) for formula in formulas):
        raise click.BadParameter("ECDSA needs an addition formula. None was supplied.")

    click.echo("[ ] Rendering...")
    config = DeviceConfiguration(model, coords, formulas, scalarmult, hash, rand, mul, sqr, red,
                                 inv, platform, keygen, ecdh, ecdsa, define)
    dir, elf_file, hex_file = render(config)
    click.echo("[*] Rendered.")

    click.echo("[ ] Building...")
    result = subprocess.run(["make"], cwd=dir, capture_output=not verbose)
    if result.returncode != 0:
        click.echo("[x] Build failed.")
        shutil.rmtree(dir)
    else:
        click.echo("[*] Built.")

        if strip:
            subprocess.run(["make", "strip"], cwd=dir, capture_output=not verbose)
        full_elf_path = path.join(dir, elf_file)
        full_hex_path = path.join(dir, hex_file)
        shutil.copy(full_elf_path, outdir)
        shutil.copy(full_hex_path, outdir)
        click.echo(elf_file)
        click.echo(hex_file)
        if remove:
            shutil.rmtree(dir)
        else:
            click.echo(dir)


@main.command("list")
@click.argument("model",
                type=click.Choice(["shortw", "montgom", "edwards", "twisted"]),
                callback=get_model, required=False)
@click.argument("coords", required=False,
                callback=get_coords)
@click.argument("formulas", required=False, nargs=-1,
                callback=get_formula)
@public
def list_impl(model: Optional[CurveModel], coords: Optional[CoordinateModel],
              formulas: Optional[Tuple[Formula]]):
    """This command lists possible choices for an ECC implementation.
    If no arguments are provided the argument lists other implementation options,
    such as modular reduction algorithms, build platforms and so on.

    \b
    MODEL: The curve model to list.
    COORDS: The coordinate model to list.
    FORMULAS: The formulas to list.
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
        types: MutableMapping[Type, List] = {}
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
    if not model:
        click.echo(
            click.wrap_text("Platform:\n\t" + ", ".join(Platform.names()),
                            subsequent_indent="\t"))
        click.echo(
            click.wrap_text("Hash type:\n\t" + ", ".join(HashType.names()),
                            subsequent_indent="\t"))
        click.echo(click.wrap_text("Modular Random:\n\t" + ", ".join(RandomMod.names()),
                                   subsequent_indent="\t"))
        click.echo(click.wrap_text("Multiplication:\n\t" + ", ".join(Multiplication.names()),
                                   subsequent_indent="\t"))
        click.echo(
            click.wrap_text("Squaring:\n\t" + ", ".join(Squaring.names()),
                            subsequent_indent="\t"))
        click.echo(click.wrap_text("Modular Reduction:\n\t" + ", ".join(Reduction.names()),
                                   subsequent_indent="\t"))
        click.echo(click.wrap_text(
            "Scalar multplier:\n\t" + ", ".join(map(lambda m: m["name"][-1], MULTIPLIERS)),
            subsequent_indent="\t"))
        click.echo(click.wrap_text("Curve Model:\n\t" + ", ".join(["shortw", "montgom", "edwards", "twisted"])))


if __name__ == "__main__":
    main(obj={})
