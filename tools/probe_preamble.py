"""Probe the preamble against the pinned toolchain: does sb_check report what its docstring says?"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scmd_bench.repl import LeanPaths, ReplSession

pre = (Path(__file__).resolve().parents[1] / "scmd_bench/lean/preamble.lean").read_text()
s = ReplSession(LeanPaths.discover())
t = time.time()
r = s.send({"cmd": "import Mathlib"}, timeout_s=900)
print("import", round(time.time() - t, 1), r.ok, r.errors[:2])
r0 = s.run("open Nat.Partrec Option Lean", env=r.env)
r2 = s.run(pre, env=r0.env)
print("preamble", r2.ok, [e.get("data") for e in r2.errors][:3])
env = r2.env
cases = {
 "term": "sb_check N0 theorem t1 (a b : Nat) : a + b = b + a := Nat.add_comm a b",
 "tactic_rw": "sb_check N0 theorem t2 (a b : ℕ) (h : a ≤ b) : a < b + 1 := by\n  exact Nat.lt_succ_of_le h",
 "simp": "sb_check N0 theorem t3 (s : Finset ℕ) : s ∪ s = s := by simp",
 "simp_args": "sb_check N0 theorem t4 (a b : ℕ) : a * b = b * a := by simp [mul_comm]",
 "dot": "sb_check N0 theorem t5 (a b c : ℕ) (h1 : a ≤ b) (h2 : b ≤ c) : a ≤ c := h1.trans h2",
 "open_in": "sb_check N0 theorem t6 (s : Finset ℕ) : s ⊆ s := by\n  open Finset in exact Subset.refl s",
 "two_cmds": "sb_check N0 theorem t7 : True := trivial\ntheorem evil : 1 = 1 := rfl",
 "ns": "namespace Bar\nsb_check N0 theorem Foo.sb_target : 1 + 1 = 2 := rfl\nend Bar",
 "sorry": "sb_check N0 theorem t9 : 1 = 2 := sorry",
 "native": "sb_check N0 theorem t10 : 10 < 20 := by native_decide",
 "aux": "sb_check N0 theorem t11 : 2 = 2 := by\n  have h : 1 = 1 := rfl\n  exact rfl",
 "variable": "section\nvariable {α : Type} [Preorder α]\nsb_check N0 theorem t12 (a : α) : a ≤ a := le_refl a\nend",
 "reserved": "def myf (n : Nat) : Nat := n + 1\nsb_check N0 theorem t13 : myf 1 = 2 := by unfold myf; rfl",
 "opened_none": "section\nopen Nat.Partrec\nopen Lean Elab Command\nend",
 "at": "sb_check N0 theorem t8 (a b : ℕ) : a + b = b + a := @add_comm ℕ _ a b",
}
for k, c in cases.items():
    x = s.run(c, env=env)
    print("==", k, "errors:", [e.get("data")[:100] for e in x.errors])
    for m in x.infos:
        print("   ", m.get("data"))
s.close()
