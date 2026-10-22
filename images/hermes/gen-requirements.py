from importlib.metadata import requires
from packaging.requirements import Requirement

skip = {"browser-harness", "cryptography", "pynacl", "pillow-heif"}
lines = []
for raw in requires("hermes-agent") or []:
    req = Requirement(raw)
    if req.marker and not req.marker.evaluate({"extra": ""}):
        continue
    if req.name.lower() in skip:
        continue
    lines.append(str(req))

with open("/tmp/hermes-reqs.txt", "w") as fh:
    fh.write("\n".join(lines) + "\n")
print(f"wrote {len(lines)} top-level requirements")
