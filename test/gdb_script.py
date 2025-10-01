import sys
import json

import gdb


def extract_bn(bn):
    data_ptr = bn["dp"]
    used = int(bn["used"])
    bs = int(gdb.lookup_global_symbol("bn_digit_bits").value())
    result = 0
    for i in range(used):
        limb = int((data_ptr + i).dereference())
        result += limb << (i * bs)
    return result


def extract_point(point):
    result = {}
    for field in point.type.fields():
        field_name = field.name
        if len(field_name) != 1:
            continue
        field_value = point[field_name]
        result[field_name] = extract_bn(field_value)
    return result


class TraceFunction(gdb.Breakpoint):
    def stop(self):
        try:
            set_bp.enabled = True
            frame = gdb.newest_frame()
            block = frame.block()
            print(frame.name(), file=sys.stderr)
            out = []
            for sym in block:
                if sym.is_argument:
                    name = sym.name
                    try:
                        value = frame.read_var(name)
                    except Exception as e:
                        value = f"<unavailable: {e}>"
                    deref = value.dereference()
                    if deref.type.name == "point_t":
                        if "out" in name:
                            out.append(deref)
                        else:
                            pt = extract_point(deref)
                            print(f"{name}: {json.dumps(pt)}", file=sys.stderr)
            bp = TraceExit(frame)
            bp.silent = True
            bp.target = out
        except RuntimeError as e:
            pass
        return False  # Continue execution


class TraceExit(gdb.FinishBreakpoint):
    def stop(self):
        set_bp.enabled = False
        for i, point in enumerate(self.target):
            print(f"out_{i}: {json.dumps(extract_point(point))}", file=sys.stderr)
        return False  # Continue execution


def register_bp(name):
    if gdb.lookup_global_symbol(name) is not None:
        bp = TraceFunction(name)
        bp.silent = True
        return bp
    return None


register_bp("point_add")
register_bp("point_dadd")
register_bp("point_dadd")
register_bp("point_ladd")
register_bp("point_dbl")
register_bp("point_neg")
register_bp("point_scl")
register_bp("point_tpl")
set_bp = register_bp("point_set")
set_bp.enabled = False

gdb.execute("run")
# print("\x04", file=sys.stderr)
