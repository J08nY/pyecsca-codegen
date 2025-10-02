#!/usr/bin/env python3
"""
Client script.

Use it to interact with the built implementations (and flash them if necessary).

Examples
========

The following examples use the generated implementation in ``pyecsca-codegen-HOST.elf`` for the host
architecture, which is assumed to use the Short-Weierstrass curve model with projective coordinates.

The first example generates a keypair and exports it.

.. code-block:: shell-session

    $ client --platform HOST --fw ./pyecsca-codegen-HOST.elf shortw projective gen secg/secp128r1
    (162938999268550597445809790209592423458, Point([x=111810799217268384317536017529141796945, y=309320541414531923178173772704935971498] in shortw/affine))
    0.01743340492248535

The following example does ECDH with the target, which first generates a keypair.

.. code-block:: shell-session

    $ client --platform HOST --fw ./pyecsca-codegen-HOST.elf shortw projective ecdh secg/secp128r1 122835813094999453922649270086793500655,326514220558629293368386081113307347349
    Keypair: 162938999268550597445809790209592423458, [x=111810799217268384317536017529141796945, y=309320541414531923178173772704935971498]
    ECDH result: 30567033074c9169e9355a7b348aa7511c3ae605

The following example signs a message ``"something"`` using the target, which first generates a keypair.

.. code-block:: shell-session

    $ client --platform HOST --fw ./pyecsca-codegen-HOST.elf shortw projective ecdsa-sign secg/secp128r1 something
    Keypair: 162938999268550597445809790209592423458, [x=111810799217268384317536017529141796945, y=309320541414531923178173772704935971498]
    Signature: 30250211009dc6d5b03cffe0cbd5e829838ecb59e4021023496ba97cf1d816619fe626de2d07b6

The following example verifies a signature on the message ``"something"`` using the target and the provided public key.

.. code-block:: shell-session

    $ client --platform HOST --fw ./pyecsca-codegen-HOST.elf shortw projective ecdsa-verify secg/secp128r1 111810799217268384317536017529141796945,309320541414531923178173772704935971498 something_else 30250211009dc6d5b03cffe0cbd5e829838ecb59e40210171c895d2d4f27850ff5f2a375ea22b7
    Result: True

.. note::
    The implementation has a PRNG it uses to get randomness. This PRNG starts with a constant state.
    You can use the ``--seed`` option to set a custom state.

"""
import bisect
import re
from binascii import hexlify, unhexlify
from enum import IntFlag
from os import path
from time import time
from typing import Mapping, Union, Optional, Tuple

import chipwhisperer as cw
import click
import numpy as np
from chipwhisperer.capture.api.programmers import STM32FProgrammer, XMEGAProgrammer
from chipwhisperer.capture.targets import SimpleSerial
from rainbow.devices import rainbow_stm32f215
from rainbow import TraceConfig, Print
from public import public

from pyecsca.ec.coordinates import CoordinateModel, AffineCoordinateModel
from pyecsca.ec.mod import mod, Mod
from pyecsca.ec.model import CurveModel
from pyecsca.ec.params import DomainParameters, get_params
from pyecsca.ec.point import Point, InfinityPoint
from pyecsca.sca.target import (Target, SimpleSerialTarget, ChipWhispererTarget, BinaryTarget, Flashable,
                                SimpleSerialMessage as SMessage)
from pyecsca.sca.trace import Trace
from pyecsca.codegen.common import wrap_enum, Platform, get_model, get_coords


@public
class Triggers(IntFlag):
    """
    Actions that the implementation can trigger on.

    Given that this is a bit-flag, multiple choices are
    allowed, in which case the trigger signal will toggle
    onn each action entry/exit.
    """
    add = 1 << 0
    dadd = 1 << 1
    dbl = 1 << 2
    ladd = 1 << 3
    neg = 1 << 4
    scl = 1 << 5
    tpl = 1 << 6
    mult = 1 << 7
    keygen = 1 << 8
    ecdh = 1 << 9
    ecdsa_sign = 1 << 10
    ecdsa_verify = 1 << 11
    coord_map = 1 << 12
    random_mod = 1 << 13


def encode_scalar(val: Union[int, Mod]) -> bytes:
    """
    Encode a scalar value (int or Mod) into bytes,
    such that the implementation can load them.
    """
    if isinstance(val, int):
        return val.to_bytes((val.bit_length() + 7) // 8, "big")
    elif isinstance(val, Mod):
        return encode_scalar(int(val))
    return bytes()


def encode_point(point: Point) -> Mapping:
    """
    Encode point coordinates.
    """
    if isinstance(point, InfinityPoint):
        return {"n": bytes([1])}
    return {var: encode_scalar(value) for var, value in point.coords.items()}


def encode_data(name: Optional[str], structure: Union[Mapping, bytes]) -> bytes:
    """
    Encode `structure` into the format used by the implementation command
    parsing (see <docs/commands.rst>) and give it a `name`.

    The format uses a tree of name-length-value nodes that is serialized
    one after another (and can be easily parsed out recursively). This function
    expects the `structure` to be either:
      - bytes, in which case this is a leaf node and the function will just
      create the name-length-value entry encoding.
      - Mapping, in which case this function will recursively encode the
      entries in the mapping.
    """
    if isinstance(structure, bytes):
        if name is None:
            raise ValueError
        header = bytes([ord(name)]) + bytes([len(structure)])
        return header + structure
    data = bytes()
    for k, v in structure.items():
        data += encode_data(k, v)
    if name is not None:
        return bytes([ord(name) | 0x80]) + bytes([len(data)]) + data
    return data


def decode_data(data: bytes) -> Mapping:
    """
    Decode the `data` in the format used by the implementation command
    parsing.

    The format uses a tree of name-length-value nodes, this tree is
    deserialized and turned into a Mapping by this function. However,
    as the format does not hold any information about the data type
    (only its name, length and value) this function does not decode
    the byte values (i.e. decoding an encoding of a scalar will
    result in a Mapping with bytes on the output, not an int or a Mod).
    """
    result = {}
    parsed = 0
    while parsed < len(data):
        name = data[parsed]
        length = data[parsed + 1]
        if name & 0x80:
            sub = decode_data(data[parsed + 2: parsed + 2 + length])
            result[chr(name & 0x7f)] = sub
            parsed += length + 2
        else:
            result[chr(name)] = data[parsed + 2: parsed + 2 + length]
            parsed += length + 2
    return result


@public
def cmd_init_prng(seed: bytes) -> str:
    """Build the init PRNG command."""
    return "i" + hexlify(seed).decode()


@public
def cmd_set_params(params: DomainParameters) -> str:
    """Build the set parameters command."""
    data = {
        "p": encode_scalar(params.curve.prime),
        "n": encode_scalar(params.order),
        "h": encode_scalar(params.cofactor)
    }
    for param, value in params.curve.parameters.items():
        data[param] = encode_scalar(value)
    data["g"] = encode_point(params.generator.to_affine())
    data["i"] = encode_point(params.curve.neutral)
    return "c" + hexlify(encode_data(None, data)).decode()


@public
def cmd_generate() -> str:
    """Build the generate keypair command."""
    return "g"


@public
def cmd_set_privkey(privkey: int) -> str:
    """Build the set private key command."""
    return "s" + hexlify(encode_data(None, {"s": encode_scalar(privkey)})).decode()


@public
def cmd_set_pubkey(pubkey: Point) -> str:
    """Build the set public key command."""
    return "w" + hexlify(encode_data(None, {"w": encode_point(pubkey.to_affine())})).decode()


@public
def cmd_scalar_mult(scalar: int, point: Point) -> str:
    """Build the scalar multiplication command."""
    return "m" + hexlify(encode_data(None, {"s": encode_scalar(scalar),
                                            "w": encode_point(point.to_affine())})).decode()


@public
def cmd_ecdh(pubkey: Point) -> str:
    """Build the ECDH command."""
    return "e" + hexlify(encode_data(None, {"w": encode_point(pubkey.to_affine())})).decode()


@public
def cmd_ecdsa_sign(data: bytes) -> str:
    """Build the ECDSA sign command."""
    return "a" + hexlify(encode_data(None, {"d": data})).decode()


@public
def cmd_ecdsa_verify(data: bytes, sig: bytes) -> str:
    """Build the ECDSA verify command."""
    return "r" + hexlify(encode_data(None, {"d": data, "s": sig})).decode()


@public
def cmd_set_trigger(actions: Triggers) -> str:
    """Build the set trigger command."""
    vector_bytes = actions.to_bytes(4, "little")
    return "t" + hexlify(vector_bytes).decode()


@public
def cmd_debug() -> str:
    """Build the debug command."""
    return "d"


@public
class EmulatorTarget(Target):
    """
    An emulator-based target, using the rainbow emulator.

    This target will load the binary in an emulator and run the commands
    by calling the corresponding functions in the binary. It will also
    hook the ``simpleserial_put`` function to get the output data from
    the implementation.

    Note that this target does not support triggers, as the rainbow
    emulator does not support GPIOs.
    """
    emulator: rainbow_stm32f215
    """The rainbow emulator instance."""
    result: list
    """The result of the last command."""
    model: CurveModel
    """The curve model."""
    coords: CoordinateModel
    """The coordinate model."""
    seed: Optional[bytes]
    """The PRNG seed, if any."""
    params: Optional[DomainParameters]
    """The domain parameters, if any."""
    privkey: Optional[int]
    """The private key, if any."""
    pubkey: Optional[Point]
    """The public key, if any."""
    trace: list
    """The trace collected during the emulation."""


    def __init__(self, model: CurveModel, coords: CoordinateModel, print_config: Print = Print(0),
                 trace_config: TraceConfig = TraceConfig(), allow_breakpoints: bool = False):
        super().__init__()
        self.emulator = rainbow_stm32f215(print_config=print_config, trace_config=trace_config,
                                          allow_stubs=True, allow_breakpoints=allow_breakpoints)
        self.result = []
        self.trace = []
        self.model = model
        self.coords = coords
        self.seed = None
        self.params = None
        self.privkey = None
        self.pubkey = None
        self._funcs = []
        self._addrs = []

    def __emulate(self, command: str, function: str) -> None:
        data = unhexlify(command[1:])
        length = len(data)
        data_adress = 0xDEAD0000
        self.emulator[data_adress] = data
        self.emulator['r0'] = data_adress
        self.emulator['r1'] = length
        self.emulator.start(self.emulator.functions[function] | 1, 0)
        self.trace.extend(self.emulator.trace)
        self.emulator.reset()

    def connect(self, **kwargs) -> None:
        self.emulator.load(kwargs["binary"])
        self.emulator.setup()
        self.emulator.start(self.emulator.functions['init_implementation'] | 1, 0)
        self.emulator.reset()
        # Compute the function map from the emulator.
        addr_map = [(addr, name) for name, addr in self.emulator.functions.items()]
        addr_map.sort()
        self._addrs = [addr - 1 for addr, name in addr_map]
        self._funcs = [name for addr, name in addr_map]

    def set_params(self, params: DomainParameters) -> None:
        command = cmd_set_params(params)
        self.__emulate(command, 'cmd_set_params')
        self.params = params

    def __scalar_mult_hook(self, emulator) -> None:
        point_length = emulator['r1'] // len(self.coords.variables)
        res_adress = emulator['r2']
        self.result.append({var: mod(int.from_bytes(emulator[res_adress + i * point_length:
                                                             res_adress + (i + 1) * point_length], 'big'),
                                     self.params.curve.prime)
                            for i, var in enumerate(self.coords.variables)})

    def scalar_mult(self, scalar: int, point: Point) -> Point:
        self.result = []
        self.emulator.hook_bypass("simpleserial_put", self.__scalar_mult_hook)
        command = cmd_scalar_mult(scalar, point)
        self.__emulate(command, 'cmd_scalar_mult')
        return Point(self.coords, **self.result[0])

    def init_prng(self, seed: bytes) -> None:
        command = cmd_init_prng(seed)
        self.__emulate(command, 'cmd_init_prng')
        self.seed = seed

    def __generate_hook(self, emulator) -> None:
        key_length = emulator['r1']
        key_bytes = emulator[emulator['r2']: emulator['r2'] + key_length]
        self.result.append(key_length)
        self.result.append(key_bytes)

    def generate(self) -> Tuple[int, Point]:
        self.result = []
        self.emulator.hook_bypass("simpleserial_put", self.__generate_hook)
        command = cmd_generate()
        self.__emulate(command, 'cmd_generate')
        priv = int.from_bytes(self.result[1], 'big')
        pub_x = int.from_bytes(self.result[3][0:self.result[2] // 2], 'big')
        pub_y = int.from_bytes(self.result[3][self.result[2] // 2:self.result[2]], 'big')
        return priv, Point(AffineCoordinateModel(self.model), x=mod(pub_x, self.params.curve.prime),
                           y=mod(pub_y, self.params.curve.prime))

    def set_privkey(self, privkey: int) -> None:
        command = cmd_set_privkey(privkey)
        self.__emulate(command, 'cmd_set_privkey')
        self.privkey = privkey

    def set_pubkey(self, pubkey: Point) -> None:
        command = cmd_set_pubkey(pubkey)
        self.__emulate(command, 'cmd_set_pubkey')
        self.pubkey = pubkey

    def __ec_hook(self, simulator) -> None:
        self.result.append(simulator[simulator['r2']:simulator['r2'] + simulator['r1']])

    def ecdh(self, other_pubkey: Point) -> bytes:
        self.result = []
        self.emulator.hook_bypass("simpleserial_put", self.__ec_hook)
        command = cmd_ecdh(other_pubkey)
        self.__emulate(command, 'cmd_ecdh')
        shared_secret = self.result[0]
        return shared_secret

    def ecdsa_sign(self, data: bytes) -> bytes:
        self.result = []
        self.emulator.hook_bypass("simpleserial_put", self.__ec_hook)
        command = cmd_ecdsa_sign(data)
        self.__emulate(command, 'cmd_ecdsa_sign')
        signature = self.result[0]
        return signature

    def ecdsa_verify(self, data: bytes, signature: bytes) -> bool:
        self.result = []
        self.emulator.hook_bypass("simpleserial_put", self.__ec_hook)
        command = cmd_ecdsa_verify(data, signature)
        self.__emulate(command, 'cmd_ecdsa_verify')
        return bool(int.from_bytes(self.result[0], 'big'))

    def transform_trace(self, filter_malloc: bool = True, save_instructions: bool = False) -> Trace:
        """Transform the collected trace into a :py:class:`pyecsca.sca.trace.Trace` object."""
        samples = []
        instructions = []
        inside_malloc = False
        # Get the trace but filter out known non-CT malloc functions.
        for event in self.trace:
            sample = event.get("register", 0)
            instruction = event.get("instruction", None)
            if instruction is None or not filter_malloc:
                samples.append(sample)
                continue
            addr = int(instruction.split(" ")[1], 16)
            func = self._funcs[bisect.bisect(self._addrs, addr) - 1]
            if func == "__malloc_lock":
                inside_malloc = True
            if func == "__malloc_unlock":
                inside_malloc = False
            if not inside_malloc and func not in ("free", "_free_r",
                                                  "calloc", "_calloc_r",
                                                  "realloc", "_realloc_r",
                                                  "malloc", "_malloc_r",
                                                  "__malloc_lock", "__malloc_unlock",
                                                  "_sbrk_r", "_sbrk",
                                                  "__udivmoddi4", "__aeabi_uldivmod"):
                samples.append(sample)
                if save_instructions:
                    instructions.append(instruction)
        return Trace(np.array(samples, dtype=np.int32), meta={"instructions": instructions})

    def set_trigger(self):
        pass

    def debug(self) -> Tuple[str, str]:
        return self.model.shortname, self.coords.name

    def quit(self):
        pass

    def disconnect(self):
        self.emulator.start(self.emulator.functions['deinit'] | 1, 0)
        self.emulator.reset()


@public
class ImplTarget(SimpleSerialTarget):
    """
    A target that is based on an implementation built by pyecsca-codegen.

    This is an abstract class that uses the send_cmd method on the
    :py:class:`pyecsca.sca.target.simpleserial.SimpleSerialTarget`
    class to send commands to the target. That class in turn requires one to
    implement the read/write/connect/disconnect methods that communicate with the
    target somehow. See :py:class:`DeviceTarget` that uses
    :py:class:`pyecsca.sca.target.chipwhisperer.ChipWhispererTarget` for thar purpose,
    or :py:class:`HostTarget` that uses :py:class:`pyecsca.sca.target.binary.BinaryTarget`.
    """
    model: CurveModel
    """The curve model."""
    coords: CoordinateModel
    """The coordinate model."""
    seed: Optional[bytes]
    """The PRNG seed, if any."""
    params: Optional[DomainParameters]
    """The domain parameters, if any."""
    privkey: Optional[int]
    """The private key, if any."""
    pubkey: Optional[Point]
    """The public key, if any."""
    trigger: Optional[Triggers]
    """The trigger actions, if any."""
    timeout: int
    """The command timeout, in milliseconds."""

    def __init__(self, model: CurveModel, coords: CoordinateModel, **kwargs):
        super().__init__(**kwargs)
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
        else:
            self.timeout = 1000
        self.model = model
        self.coords = coords
        self.seed = None
        self.params = None
        self.privkey = None
        self.pubkey = None
        self.trigger = None

    def init_prng(self, seed: bytes) -> None:
        """
        Init the PRNG using the `seed`.

        """
        self.send_cmd(SMessage.from_raw(cmd_init_prng(seed)), self.timeout)
        self.seed = seed

    def set_params(self, params: DomainParameters) -> None:
        """
        Set the domain parameters on the target.
        """
        self.send_cmd(SMessage.from_raw(cmd_set_params(params)), self.timeout)
        self.params = params

    def generate(self) -> Tuple[int, Point]:
        """
        Generate a keypair on the target and set it (and export it).

        Requires that domain parameters are set up.
        """
        resp = self.send_cmd(SMessage.from_raw(cmd_generate()), self.timeout)
        priv = resp["s"].data
        pub = resp["w"].data
        self.privkey = int(priv, 16)
        pub_len = len(pub)
        x = int(pub[:pub_len // 2], 16)
        y = int(pub[pub_len // 2:], 16)
        self.pubkey = Point(AffineCoordinateModel(self.model), x=mod(x, self.params.curve.prime),
                            y=mod(y, self.params.curve.prime))
        return self.privkey, self.pubkey

    def set_privkey(self, privkey: int) -> None:
        """
        Set the private key on the target.
        """
        self.send_cmd(SMessage.from_raw(cmd_set_privkey(privkey)), self.timeout)
        self.privkey = privkey

    def set_pubkey(self, pubkey: Point) -> None:
        """
        Set the public key on the target.
        """
        self.send_cmd(SMessage.from_raw(cmd_set_pubkey(pubkey)), self.timeout)
        self.pubkey = pubkey

    def scalar_mult(self, scalar: int, point: Point) -> Point:
        """
        Run scalar multiplication on the target and export the result.

        Requires that domain parameters are set up.
        """
        resp = self.send_cmd(SMessage.from_raw(cmd_scalar_mult(scalar, point)), self.timeout)
        result = resp["w"]
        plen = ((self.params.curve.prime.bit_length() + 7) // 8) * 2
        params = {var: mod(int(result.data[i * plen:(i + 1) * plen], 16), self.params.curve.prime)
                  for
                  i, var in enumerate(self.coords.variables)}
        return Point(self.coords, **params)

    def ecdh(self, other_pubkey: Point) -> bytes:
        """
        Do ECDH with the target.

        Requires that domain parameters are set up, as well as a private key.
        """
        resp = self.send_cmd(SMessage.from_raw(cmd_ecdh(other_pubkey)), self.timeout)
        result = resp["r"]
        return unhexlify(result.data)

    def ecdsa_sign(self, data: bytes) -> bytes:
        """
        Sign a message on the target.

        Requires that domain parameters are set up, as well as a private key.
        """
        resp = self.send_cmd(SMessage.from_raw(cmd_ecdsa_sign(data)), self.timeout)
        signature = resp["s"]
        return unhexlify(signature.data)

    def ecdsa_verify(self, data: bytes, signature: bytes) -> bool:
        """
        Verify a signature on the target.

        Requires that domain parameters are set up, as well as a public key.
        """
        resp = self.send_cmd(SMessage.from_raw(cmd_ecdsa_verify(data, signature)), self.timeout)
        result = resp["v"]
        return unhexlify(result.data)[0] == 1

    def debug(self) -> Tuple[str, str]:
        """
        Run the debug command on the target.

        Returns the curve model and coordinate model names.
        """
        resp = self.send_cmd(SMessage.from_raw(cmd_debug()), self.timeout)["d"]
        model, coords = unhexlify(resp.data).decode().split(",")
        return model, coords

    def set_trigger(self, actions: Triggers) -> None:
        """
        Setup the trigger on the target.

        .. note::

            The triggers are not exclusive, and you can set to trigger on multiple actions.
            However, note that they toggle the trigger signal. For example, if you set up
            triggers on scalar multiplication and addition (``Triggers.mult | Triggers.add``)
            the trigger signal will go high once scalar multiplication starts, then go low
            during each addition operation and finally go low for good after scalar multiplication
            ends.
        """
        self.send_cmd(SMessage.from_raw(cmd_set_trigger(actions)), self.timeout)
        self.trigger = actions

    def quit(self):
        """Turn off the target."""
        self.write(b"x\n")

    def disconnect(self):
        super().disconnect()


@public
class DeviceTarget(ImplTarget, ChipWhispererTarget):  # pragma: no cover
    """
    A ChipWhisperer-based device target.
    """

    def __init__(self, model: CurveModel, coords: CoordinateModel, platform: Platform, **kwargs):
        scope = cw.scope()
        scope.default_setup()
        target = SimpleSerial()
        if platform in (Platform.STM32F0, Platform.STM32F3):
            programmer = STM32FProgrammer
        elif platform == Platform.XMEGA:
            programmer = XMEGAProgrammer
        else:
            raise ValueError
        super().__init__(model, coords, target=target, scope=scope, programmer=programmer, **kwargs)


@public
class HostTarget(ImplTarget, BinaryTarget):
    """
    A host-based target, will just run the binary on your machine and communicate
    with it via stdin/stdout.
    """

    def __init__(self, model: CurveModel, coords: CoordinateModel, **kwargs):
        super().__init__(model, coords, **kwargs)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--platform", envvar="PLATFORM", required=True,
              type=click.Choice(Platform.names()),
              callback=wrap_enum(Platform),
              help="The target platform to use.")
@click.option("--fw",
              help="The firmware. Either a .hex file for a device platform or .elf for HOST platform.",
              required=True)
@click.option("--timeout", type=int, default=15000)
@click.option("--seed", type=str, help="Set the PRNG seed (hex string).")
@click.argument("model", required=True,
                type=click.Choice(["shortw", "montgom", "edwards", "twisted"]),
                callback=get_model)
@click.argument("coords", required=True,
                callback=get_coords)
@click.version_option()
@click.pass_context
@public
def main(ctx, platform, fw, timeout, seed, model, coords):
    """
    A tool for communicating with built and flashed ECC implementations.
    """
    ctx.ensure_object(dict)
    ctx.obj["fw"] = fw
    ctx.obj["seed"] = seed
    if platform != Platform.HOST:
        ctx.obj["target"] = DeviceTarget(model, coords, platform, timeout=timeout)
    else:
        if fw is None or not path.isfile(fw):
            click.secho("Binary is required if the target is the host.", fg="red", err=True)
            raise click.Abort
        ctx.obj["target"] = HostTarget(model, coords, binary=fw, timeout=timeout)


def get_curve(ctx: click.Context, param, value: Optional[str]) -> DomainParameters:
    if value is None:
        return None
    ctx.ensure_object(dict)
    category, name = value.split("/")
    curve = get_params(category, name, ctx.obj["coords"].name)
    ctx.obj["params"] = curve
    return curve


@main.command("gen")
@click.argument("curve", required=True, callback=get_curve)
@click.pass_context
@public
def generate(ctx: click.Context, curve):
    """Generate a keypair on a curve."""
    ctx.ensure_object(dict)
    target: ImplTarget = ctx.obj["target"]
    if isinstance(target, Flashable):
        target.flash(ctx.obj["fw"])
    target.connect()
    if seed := ctx.obj["seed"]:
        target.init_prng(bytes.fromhex(seed))
    target.set_params(curve)
    start = time()
    click.echo(target.generate())
    click.echo(time() - start)
    target.quit()
    target.disconnect()


def get_pubkey(ctx: click.Context, param, value: Optional[str]) -> Point:
    if value is None:
        return None
    ctx.ensure_object(dict)
    curve: DomainParameters = ctx.obj["params"]
    if re.match("^04([0-9a-fA-F]{2})+$", value):
        value = value[2:]
        plen = len(value) // 2
        x = int(value[:plen], 16)
        y = int(value[plen:], 16)
    elif re.match("^[0-9]+,[0-9]+$", value):
        xs, ys = value.split(",")
        x = int(xs)
        y = int(ys)
    else:
        raise click.BadParameter("Couldn't parse pubkey: {}.".format(value))
    x = mod(x, curve.curve.prime)
    y = mod(y, curve.curve.prime)
    return Point(AffineCoordinateModel(curve.curve.model), x=x, y=y)


@main.command("ecdh")
@click.argument("curve", required=True, callback=get_curve)
@click.argument("pubkey", required=True, callback=get_pubkey)
@click.pass_context
@public
def ecdh(ctx: click.Context, curve, pubkey):
    """Perform ECDH with a given public key."""
    ctx.ensure_object(dict)
    target: ImplTarget = ctx.obj["target"]
    if isinstance(target, Flashable):
        target.flash(ctx.obj["fw"])
    target.connect()
    if seed := ctx.obj["seed"]:
        target.init_prng(bytes.fromhex(seed))
    target.set_params(curve)
    priv, pub = target.generate()
    click.echo(f"Keypair: {priv}, {pub}")
    click.echo(f"ECDH result: {hexlify(target.ecdh(pubkey)).decode()}")
    target.quit()
    target.disconnect()


@main.command("ecdsa-sign")
@click.argument("curve", required=True, callback=get_curve)
@click.argument("data", required=True, type=str)
@click.pass_context
@public
def ecdsa_sign(ctx: click.Context, curve, data):
    """Sign data using ECDSA."""
    ctx.ensure_object(dict)
    target: ImplTarget = ctx.obj["target"]
    if isinstance(target, Flashable):
        target.flash(ctx.obj["fw"])
    target.connect()
    if seed := ctx.obj["seed"]:
        target.init_prng(bytes.fromhex(seed))
    target.set_params(curve)
    priv, pub = target.generate()
    click.echo(f"Keypair: {priv}, {pub}")
    click.echo(f"Signature: {hexlify(target.ecdsa_sign(data.encode())).decode()}")
    target.quit()
    target.disconnect()


@main.command("ecdsa-verify")
@click.argument("curve", required=True, callback=get_curve)
@click.argument("pubkey", required=True, callback=get_pubkey)
@click.argument("data", required=True, type=str)
@click.argument("signature", required=True, type=str)
@click.pass_context
@public
def ecdsa_verify(ctx: click.Context, curve, pubkey, data, signature):
    """
    Verify data using ECDSA.
    """
    ctx.ensure_object(dict)
    target: ImplTarget = ctx.obj["target"]
    if isinstance(target, Flashable):
        target.flash(ctx.obj["fw"])
    target.connect()
    if seed := ctx.obj["seed"]:
        target.init_prng(bytes.fromhex(seed))
    target.set_params(curve)
    target.set_pubkey(pubkey)
    res = target.ecdsa_verify(data.encode(), unhexlify(signature))
    click.echo(f"Result: {res}")
    target.quit()
    target.disconnect()


if __name__ == "__main__":
    main(obj={})
