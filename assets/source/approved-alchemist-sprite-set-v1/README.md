# Approved Alchemist sprite-set handoff V1

This directory is the inert, source-controlled handoff for every Alchemist hero animation approved through the sprite-art pipeline. It contains packaging inputs and their exact provenance; it contains no CAM, mod package, dist output, game file, or deployment artifact.

The copied payload is intentionally narrow:

- Walk V4: 64 canonical indexed TILE-v3 body payloads.
- Stand V5: 8 native Soft-B RGBA body frames.
- Attack V10: 64 native Soft-B forward-thrust frames.
- Cast V20/V6: 48 native Soft-B potion-throw keys.
- Special V31/V7: 56 native Soft-B single-drink keys.
- Death V36: 32 native Soft-B fall-and-reach keys.
- Dead: the exact native Gravestone B frame.
- The approved palette, Walk/Stand checkpoints, Warrior action authority, and all render/review provenance needed to trace those inputs.

Review APNGs, GIFs, comparison sheets, high-resolution renders, and control PNGs are deliberately excluded. They are approval media or intermediates, not package sources.

## Import contract

The normal project route remains:

    scripts/Build-AlchemistProbe.ps1 -ApprovedSpriteTestSet
      -> src/build_alchemist_probe.py
      -> src/alchemist_art_package.py::write_maindata
      -> src/approved_sprite_bundle.py

The packaging thread should extend that route, not create a second packager.

1. Verify every file against manifest.json and PAYLOAD_SHA256SUMS.txt before reading an asset.
2. Keep AVL1Warrior as the stock mechanism and binary-layout authority. Use authority/warrior-action-authority-v1.json and the copied action provenance rather than guessing frame order from images.
3. Keep Walk exactly byte/decoded-index compatible with the already tested V4 path. For the PNG actions, use the same accepted alpha-128 palette conversion and private SPLT.
4. Generate grounded engine shadows during packaging. Index 247 must form the body-contact seam; 248-250 form the projected bands. Reject a transparent moat, direct magenta/body contact without the seam, mixed visible/control RLE runs, missing bands, or control pixels at an edge.
5. Clone each stock IMAG action descriptor literally. Preserve set headers, direction pointers, count words, per-occurrence metadata, reference flags, attachments, repetitions, and runtime timing. Change only private tile references.
6. Cast and Special require private per-occurrence references. Do not collapse their approved A-F/A-G keys back into the stock shared low-16 TILE aliases.
7. Death uses its approved 112x92 action-wide common canvas and hotspot 62,57 because the custom grounded fall and scattered props do not fit every tight retail per-frame rectangle. Preserve the stock-derived envelope and the stock A-B-C-D plus twelve further D occurrences.
8. Dead uses the one exact 35x33 Gravestone B payload shared through stock Dead set 224.
9. Append the private palette and TILE records only after the complete retail tables, update only the cloned private ALC1 references, and prove every unrelated Warrior word remains unchanged.
10. Expand the approved test manifest and tests to cover every action, then build the existing repository-confined test package. Deployment belongs to the Alchemist project thread and must use its normal DLL launcher/deploy path.

## Approval-specific visual rules

- The dagger stays in the anatomical right hand and uses a conventional forward grip.
- Cast is one clean enemy-directed potion throw; the empty-hand return must not pop the bottle back into view.
- Special is one drink, not repeated forehead bashing: raise once, tilt the head back, drink, lower once, and return naturally. Bottle occlusion behind the head is valid in rear views.
- Death drops the dagger and potions, settles on the ground reaching for the green potion, then transitions to Gravestone B.
- Do not recenter, rescale, mirror whole frames, or add per-direction/per-frame corrective offsets after approval.
- The initial disconnected-shadow failure is a regression test: every grounded body/shadow join must satisfy the pinned seam contract.

manifest.json is the machine-readable authority. The copied provenance retains full stock topology, registration, source hashes, frame metrics, and approval validation.

Run the repository's shared Python launcher from this directory for a read-only verification:

    ..\\..\\..\\..\\.tools\\python.cmd verify_handoff.py
