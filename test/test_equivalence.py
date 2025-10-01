import subprocess
import json
from typing import Generator, Any
from click.testing import CliRunner

import pytest
from importlib import resources
from os.path import join

from pyecsca.codegen.builder import build_impl
from pyecsca.ec.formula import FormulaAction, NegationFormula
from pyecsca.ec.model import CurveModel
from pyecsca.ec.coordinates import CoordinateModel
from pyecsca.sca.target.binary import BinaryTarget
from pyecsca.codegen.client import ImplTarget
from pyecsca.ec.context import DefaultContext, local, Node

from pyecsca.ec.mult import (
    LTRMultiplier,
    RTLMultiplier,
    CoronMultiplier,
    BinaryNAFMultiplier,
    WindowNAFMultiplier,
    SlidingWindowMultiplier,
    AccumulationOrder,
    ProcessingDirection,
    ScalarMultiplier,
    FixedWindowLTRMultiplier,
    FullPrecompMultiplier,
    BGMWMultiplier,
    CombMultiplier,
    ScalarMultiplicationAction,
)


class GDBTarget(ImplTarget, BinaryTarget):
    def __init__(self, model: CurveModel, coords: CoordinateModel, **kwargs):
        super().__init__(model, coords, **kwargs)

    def connect(self):
        with resources.path("test", "gdb_script.py") as gdb_script:
            self.process = subprocess.Popen(
                ["gdb", "-batch", "-x", gdb_script, "--args", *self.binary],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                # stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

    # def disconnect(self):
    #     if self.process is None:
    #         return
    #     if self.process.stdin is not None:
    #         self.process.stdin.close()
    #     if self.process.stdout is not None:
    #         self.process.stdout.close()
    #     if self.process.stderr is not None:
    #         self.process.stderr.close()
    #     self.process.terminate()
    #     self.process.wait()


@pytest.fixture(scope="module")
def target(simple_multiplier, secp128r1) -> Generator[GDBTarget, Any, None]:
    mult_class, mult_kwargs = simple_multiplier
    mult_name = mult_class.__name__
    formulas = ["add-1998-cmo", "dbl-1998-cmo"]
    if NegationFormula in mult_class.requires:
        formulas.append("neg")
    runner = CliRunner()
    with runner.isolated_filesystem() as tmpdir:
        res = runner.invoke(
            build_impl,
            [
                "--platform",
                "HOST",
                "--ecdsa",
                "--ecdh",
                secp128r1.curve.model.shortname,
                secp128r1.curve.coordinate_model.name,
                *formulas,
                f"{mult_name}({','.join(f'{key}={value}' for key, value in mult_kwargs.items())})",
                ".",
            ],
            env={"DEBUG": "1", "CFLAGS": "-g -O0"},
        )
        assert res.exit_code == 0
        target = GDBTarget(
            secp128r1.curve.model,
            secp128r1.curve.coordinate_model,
            binary=join(tmpdir, "pyecsca-codegen-HOST.elf"),
        )
        formula_instances = [
            secp128r1.curve.coordinate_model.formulas[formula] for formula in formulas
        ]
        mult = mult_class(*formula_instances, **mult_kwargs)
        target.mult = mult
        yield target


def parse_trace(captured: str):
    current_function = None
    args = []
    rets = []
    result = []
    for line in captured.split("\n"):
        if ":" not in line:
            func = line.strip()
            if func.startswith("point_"):
                func = func[len("point_") :]
            if func == "set":
                # The sets that happen inside another formula (like add) are a sign of short-circuiting.
                # The Python simulation does not record the short-circuits, so we ignore them here.
                current_function = None
            else:
                if current_function is not None:
                    result.append((current_function, args, rets))
                current_function = func
            args = []
            rets = []
        else:
            name, data = line.split(":", 1)
            name = name.strip()
            value = json.loads(data)
            if "out" in name:
                rets.append(value)
            else:
                args.append(value)
    return result


def parse_ctx(scalarmult: Node):
    result = []
    for node in scalarmult.children:
        action: FormulaAction = node.action
        formula = action.formula
        name = formula.shortname
        args = []
        for point in action.input_points:
            point_value = {k: int(v) for k, v in point.coords.items()}
            args.append(point_value)
        rets = []
        for point in action.output_points:
            point_value = {k: int(v) for k, v in point.coords.items()}
            rets.append(point_value)
        result.append((name, args, rets))
    return result


def make_hashable(trace):
    result = []
    for entry in trace:
        name, args, rets = entry
        args_t = tuple(tuple(arg.items()) for arg in args)
        rets_t = tuple(tuple(ret.items()) for ret in rets)
        result.append((name, args_t, rets_t))
    return tuple(result)


def test_equivalence(target, secp128r1, capfd):
    mult = target.mult
    target.connect()
    target.set_params(secp128r1)
    for _ in range(1):
        priv, pub = target.generate()
        assert secp128r1.curve.is_on_curve(pub)
        with local(DefaultContext()) as ctx:
            mult.init(secp128r1, secp128r1.generator)
            expected = mult.multiply(priv).to_affine()
        captured = capfd.readouterr()
        with capfd.disabled():
            assert pub == expected
            from_codegen = parse_trace(captured.err)
            from_sim = parse_ctx(ctx.actions[0]) + parse_ctx(ctx.actions[1])
            codegen_set = set(make_hashable(from_codegen))
            sim_set = set(make_hashable(from_sim))
            if codegen_set != sim_set:
                print(len(from_codegen), len(from_sim))
                print("In codegen but not in sim:")
                for entry in codegen_set - sim_set:
                    print(entry)
                print("In sim but not in codegen:")
                for entry in sim_set - codegen_set:
                    print(entry)
            assert from_codegen == from_sim

    target.quit()
    target.disconnect()
