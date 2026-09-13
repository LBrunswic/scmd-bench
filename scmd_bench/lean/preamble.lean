/-!
scmd-bench preamble -- two metaprograms, re-established in every item's file-prefix environment.

Neither is a tactic and neither can prove anything. They expose the elaborator's own view of a
submission so grading reads constants and syntax trees rather than source text:

* `sb_check <nonce> <command>` elaborates ONE command (the harness-assembled `theorem`) and logs
  every constant the source NAMES, with its defining module, plus where the command ended.

The nonce is chosen per grading session and never shown to a model. Without it a submission could
print a forged report line (`trace "SB_CITED ..."`) and have it read as the harness's own.

No `import` here: a prefix environment already carries its file's imports, and every mathlib file
transitively imports `Lean`. The harness sends this block after the prefix.
-/

open Lean Elab Command in
/--
`sb_check nonce cmd` elaborates `cmd` and reports, for every identifier the SOURCE of `cmd`
writes that elaborated to a global constant:

    SB_<nonce>_CITED <line> <col> <constant> <module-or-"_"> <private:0|1> <kind:t|d> <ident-text>

then, for the declaration the command wrote (if it now exists): `SB_<nonce>_DECL <constant>`, its
axioms (`SB_<nonce>_AXIOM <name>` after an always-logged count) and the constants of its proof term
(`SB_<nonce>_USES`), and finally `SB_<nonce>_END <line> <col>` for the command's own tail
position.

DECL gives the harness the declaration's exact full name (a `theorem Foo.sb_target` written inside
`namespace Bar` is `Bar.Foo.sb_target`); its absence means nothing was declared.

`kind` is `t` when the constant's type is a proposition (a theorem, however Lean stores it) and
`d` for anything else (definition, structure, projection, instance).

WHAT "NAMES" MEANS, PRECISELY
A `TermInfo` node whose expression is a constant and whose syntax is an identifier with ORIGINAL
source info. That excludes three things on purpose:
  * constants a tactic reached on its own (`simp`'s default set, instances, `decide`'s kernel
    terms): their syntax is synthetic, and the benchmark reports that reach as `outside_base`
    rather than forbidding it -- the default simp set alone is 97,393 lemmas;
  * binders and local hypotheses (`isBinder`, or an fvar expression);
  * generalized field notation `h.trans`: the node's identifier text is `h.trans`, which does not
    spell the constant `Eq.trans`. The harness compares the text against the constant (last
    components) and treats a non-spelling as reach, not citation -- the same rule LeanDLLM's
    corpus labels were extracted under, so gold proofs and submissions are judged alike.

The END line exists because `cmd` is parsed as ONE command. A submission that closes the proof and
starts a second declaration (`... \n theorem evil ...`) is a different command stream, and the
harness detects it by the END position falling short of the submitted text.
WHY EVERY NAME BELOW IS WRITTEN FROM THE ROOT, AND WHY THERE IS NO `a[i]`
This block is re-elaborated INSIDE each item's file prefix, under whatever that file has opened. A
file that opens `Nat.Partrec` makes the pattern `none` ambiguous with `Partrec.none` (measured:
the preamble failed to elaborate in `Mathlib.Computability.Partrec`'s prefix), and any opened
namespace can shadow a short name the same way. So PATTERNS (which admit no overload resolution) and types are `_root_`-qualified, and locals
carry an `sb` prefix no file defines. Index notation is avoided for the same reason: a file that
opens `AddMonoidAlgebra` parses `x[i]` as the monoid-algebra notation `R[M]`. Functions stay short under `open Lean Elab Command`: an
application is elaborated against its expected type, which disambiguates an overload.
-/
elab "sb_check " sbNonce:ident sbCmd:command : command => do
  let sbTag := sbNonce.getId.toString
  let sbBefore := (← getInfoState).trees.size
  let sbEnvBefore ← getEnv
  withEnableInfoTree true <| elabCommand sbCmd
  let sbTrees := (← getInfoState).trees
  let sbEnv ← getEnv
  let sbFm ← getFileMap
  let mut sbSeen : _root_.Std.HashSet _root_.String := {}
  for sbT in sbTrees.toList.drop sbBefore do
    let sbHits := sbT.collectNodesBottomUp fun _ sbInfo _ sbAcc =>
      match sbInfo with
      | _root_.Lean.Elab.Info.ofTermInfo sbTi =>
        match sbTi.expr.consumeMData with
        | _root_.Lean.Expr.const sbC _ =>
          if sbTi.isBinder then sbAcc
          else match sbTi.stx with
            | _root_.Lean.Syntax.ident (_root_.Lean.SourceInfo.original _ sbP _ sbE) sbRaw _ _ =>
              -- The identifier must be text OF THIS COMMAND. A declaration's `variable` binders
              -- carry syntax from the command that declared them, earlier in the file, whose
              -- positions index a different source; read against this command's file map they
              -- land at arbitrary places. So the span must spell the identifier here.
              if _root_.String.Pos.Raw.extract sbFm.source sbP sbE == sbRaw.toString then
                (sbC, sbP, sbRaw.toString) :: sbAcc
              else sbAcc
            | _ => sbAcc
        | _ => sbAcc
      | _ => sbAcc
    for (sbC, sbP, sbRaw) in sbHits do
      let sbPos := sbFm.toPosition sbP
      let sbMod := match sbEnv.getModuleIdxFor? sbC with
        | _root_.Option.some sbIdx => (sbEnv.header.moduleNames.getD sbIdx.toNat .anonymous).toString
        | _root_.Option.none => "_"
      let sbPriv := if isPrivateName sbC then "1" else "0"
      -- A PREMISE IS A PROOF OF A PROPOSITION, decided by the constant's TYPE. Not by
      -- `ConstantInfo.thmInfo`: under Lean's module system an imported theorem can arrive as a
      -- different constructor (its body is not exported), and `SemiconjBy.neg_left_iff` read as a
      -- definition -- measured, which let a proof name it freely.
      let sbKind ← match sbEnv.find? sbC with
        | _root_.Option.some sbCi => do
          let sbIsProp ← liftTermElabM <| _root_.Lean.Meta.isProp sbCi.type
          -- A projection onto a Prop FIELD of a structure or class (`Category.assoc`,
          -- `SMulCommClass.smul_comm`) is a law of the structure the statement already mentions,
          -- not a lemma: it is `d`. The corpus's dependency labels never list them either, so
          -- charging them would reject correct gold proofs (measured: 7 of the first 101 dev
          -- candidates).
          pure (if sbIsProp && !(sbEnv.isProjectionFn sbC) then "t" else "d")
        | _root_.Option.none => pure "d"
      let sbLine := s!"SB_{sbTag}_CITED {sbPos.line} {sbPos.column} {sbC} {sbMod} {sbPriv} {sbKind} {sbRaw}"
      unless sbSeen.contains sbLine do
        sbSeen := sbSeen.insert sbLine
        logInfo sbLine
  -- THE DECLARED CONSTANT, RESOLVED FROM THE COMMAND'S OWN `declId` IN THE COMMAND'S SCOPE.
  -- Not `Environment.contains (namespace ++ written)`: mathlib v4.31.0 files are `module`s, where a
  -- declaration outside `public section` is PRIVATE and its constant is the mangled
  -- `_private.<Module>.0.<name>` -- measured, `contains` said false for a gold proof that `#check`
  -- found. Resolution applies the same rules the source did. The axioms and the proof term's
  -- constants are read here too, by constant, because a private name cannot be written back as
  -- an identifier in a follow-up command.
  match sbCmd.raw.find? (·.isOfKind ``Lean.Parser.Command.declId) with
  | _root_.Option.some sbId =>
    let sbWritten := (sbId.getArg 0).getId
    let sbNs ← getCurrNamespace
    let sbFull := if sbWritten.getRoot == `_root_ then sbWritten.replacePrefix `_root_ .anonymous
      else sbNs ++ sbWritten
    let sbEnvNow ← getEnv
    -- Direct lookup first (public, then module-private mangling); scope resolution as a fallback.
    -- Resolution alone failed on a correct proof whose written name was ambiguous in scope.
    let sbDirect := [sbFull, mkPrivateName sbEnvNow sbFull].find? (fun n => sbEnvNow.contains n)
    try
      let sbDecl ← match sbDirect with
        | _root_.Option.some n => pure n
        | _root_.Option.none => liftCoreM <| realizeGlobalConstNoOverload (sbId.getArg 0)
      logInfo s!"SB_{sbTag}_DECL {sbDecl}"
      let sbAx ← collectAxioms sbDecl
      logInfo s!"SB_{sbTag}_AXIOMS_N {sbAx.size}"
      for sbX in sbAx do
        logInfo s!"SB_{sbTag}_AXIOM {sbX}"
      let sbVal : _root_.Option _root_.Lean.Expr := match (← getEnv).find? sbDecl with
        | _root_.Option.some (_root_.Lean.ConstantInfo.thmInfo sbV) => _root_.Option.some sbV.value
        | _root_.Option.some (_root_.Lean.ConstantInfo.defnInfo sbV) => _root_.Option.some sbV.value
        | _ => _root_.Option.none
      let sbUsed := (sbVal.map (·.getUsedConstants)).getD #[]
      logInfo s!"SB_{sbTag}_USES_N {sbUsed.size}"
      for sbN in sbUsed do
        logInfo s!"SB_{sbTag}_USES {sbN}"
    catch _ => pure ()
  | _root_.Option.none => pure ()
  match sbCmd.raw.getTailPos? with
  | _root_.Option.some sbP =>
    let sbPos := sbFm.toPosition sbP
    logInfo s!"SB_{sbTag}_END {sbPos.line} {sbPos.column}"
  | _root_.Option.none => logInfo s!"SB_{sbTag}_END 0 0"
