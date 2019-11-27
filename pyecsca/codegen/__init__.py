from ast import operator, Add, Sub, Mult, Div, Pow
from typing import List, Set, Mapping

from jinja2 import Environment, PackageLoader
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


env.globals["render_op"] = render_op


def render_curve_definition(model: CurveModel):
    return env.get_template("curve.h").render(params=model.parameter_names)


def render_curve_impl(model: CurveModel):
    return env.get_template("curve.c").render(params=model.parameter_names)


def render_coords_definition(coords: CoordinateModel):
    return env.get_template("coords.h").render(variables=coords.variables)


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
    returns = {}
    if renames:
        for r_from, r_to in renames.items():
            if r_from in outputs:
                returns[r_from] = r_to

    return dict(allocations=allocations,
                initializations=initializations,
                const_mapping=const_mapping, operations=operations,
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
    namespace = transform_ops(ops, coords.curve_model.parameter_names,
                              coords.curve_model.coordinate_names, renames)
    returns = namespace["returns"]
    namespace["returns"] = {}
    frees = namespace["frees"]
    namespace["frees"] = {}

    return env.get_template("coords.c").render(variables=coords.variables, **namespace,
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


if __name__ == "__main__":
    model = ShortWeierstrassModel()
    coords = model.coordinates["projective"]
    print(render_coords_impl(coords))
