from jinja2 import Environment, PackageLoader
from pyecsca.ec.model import CurveModel, ShortWeierstrassModel
from pyecsca.ec.coordinates import CoordinateModel

env = Environment(
        loader=PackageLoader("pyecsca.codegen")
)


def get_curve_definition(model: CurveModel):
    return env.get_template("curve.h").render(params=model.parameter_names)

def get_curve_impl(model: CurveModel):
    return env.get_template("curve.c").render(params=model.parameter_names)

def get_coords_definition(coords: CoordinateModel):
    return env.get_template("coords.h").render(variables=coords.variables)

def get_coords_impl(coords: CoordinateModel):
    print(coords.satisfying)
    return env.get_template("coords.c").render(variables=coords.variables)

if __name__ == "__main__":
    model = ShortWeierstrassModel()
    s = get_curve_definition(model)

    s = get_curve_impl(model)

    coords = model.coordinates["projective"]

    s = get_coords_definition(coords)

    s = get_coords_impl(coords)