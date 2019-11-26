from ast import operator, Add, Sub, Mult, Div, Pow
from typing import List

from jinja2 import Environment, PackageLoader
from pyecsca.ec.coordinates import CoordinateModel
from pyecsca.ec.model import CurveModel, ShortWeierstrassModel, MontgomeryModel
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

env.globals["render_op"] = render_op


def get_curve_definition(model: CurveModel):
    return env.get_template("curve.h").render(params=model.parameter_names)


def get_curve_impl(model: CurveModel):
    return env.get_template("curve.c").render(params=model.parameter_names)


def get_coords_definition(coords: CoordinateModel):
    return env.get_template("coords.h").render(variables=coords.variables)


def transform_ops(ops: List[CodeOp], parameters: List[str], outputs: List[str]):
    allocations = []
    initializations = {}
    const_mapping = {}
    operations = []
    frees = []
    for op in ops:
        if op.result not in allocations and op.result not in outputs:
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
        operations.append((op.operator, op.result, op.left, op.right))
    return env.get_template("ops.c").render(allocations=allocations,
                                            initializations=initializations,
                                            const_mapping=const_mapping, operations=operations,
                                            frees=frees)


def get_coords_impl(coords: CoordinateModel):
    ops = []
    for s in coords.satisfying:
        try:
            ops.append(CodeOp(s))
        except:
            pass
    transform_ops(ops, coords.curve_model.parameter_names, coords.curve_model.coordinate_names)
    return env.get_template("coords.c").render(variables=coords.variables)


if __name__ == "__main__":
    model = ShortWeierstrassModel()
    s = get_curve_definition(model)

    s = get_curve_impl(model)

    coords = model.coordinates["projective"]

    s = get_coords_definition(coords)

    s = get_coords_impl(coords)

    mont = MontgomeryModel()
    mcoords = mont.coordinates["xz"]
    dbl = mcoords.formulas["dbl-1987-m"]
    t = transform_ops(dbl.code, mont.parameter_names, dbl.outputs)
    print(t)
