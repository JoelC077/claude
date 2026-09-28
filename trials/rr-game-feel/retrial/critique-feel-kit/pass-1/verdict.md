FIRST READ: In the true-size frame the eye goes first to the red knob and the slate console at bottom centre, then to the world tilted by the 0.5 deg roll and the lit yellow lamp. It reads as a physical lever throw, which is on brief.
In the matrix the fail (0.68) sits far above everything, but the five blue rows (0.17 / 0.16 / 0.14 / 0.14 / 0.04) are nearly the same length, so crisis, commit and reward don't separate by tier.

SCORES:
G1 Signal and hierarchy: 4/10. Meets the 4 anchor: the feel matrix and Facts "Outshouts" lines show a routine reward outshouting crises. alert_fare_banked (tier 4, 0.135) beats windows_smash (tier 2, 0.12) and hud_crisis_arrival (tier 2, 0.13). The crisis alert_coal_low (0.17) sits under the commit fired_stamp (0.25), and tiers 3 and 4 fall within 0.02 of each other (0.16 / 0.145 / 0.135). Each event does have a readable main channel: lamp and punch on the lever, FOV on the brake, rattle on coal, stamp on fare. Below 7 because of G1-1, G1-2 and G1-3; G1-4 is the one gap left for 8.
G2 Timing and curves: 6/10. Sits between 4 and 7. The lever drag closeup sells resistance: knob = detent x (finger/detent)^1.6, tick at 60%, commit snap at 70%. In fare_banked the stamp landing, ticket punch and first haptic pulse all line up at about 0.4 s. The crate kick settles in about 0.2 s with one overshoot. Below 7 because on the signature event the channels land about 110 ms apart (G2-1), and the brake FOV takes 1.4 s to return (G2-2).
G3 Comfort and accessibility: 7/10. Meets the 7 anchor: all five events are inside the Facts limits. Flash is 0.12 black vignette against a 0.35 limit, hit-stop is 70 ms against 150, and camera is 5.9 / 3.4 / 4.1 / 0 / 0 px against tier limits of 18 / 18 / 10 / 28 / 10. The lever lamp is exempt as an element lamp. Every reduce-motion (dashed) lane keeps the lamp, alpha or haptic. Below 8 because of G3-1; G3-2 is the one gap left.
G4 Phone read: 7/10. Meets the 7 anchor on the true-size lever frame: the 6% console punch is plain (console at t=0.12 vs t=0.63 in the filmstrip), the 5.9 px roll and kick read, and the knob stays in the bottom-centre thumb zone because the camera moves the world, not the console. The brake's FOV -4 deg is roughly a 7.8% zoom, visible at the screen edge. Below 8 because four of five events have no phone frame (G4-1), and the lever's reduce-motion read is subtle (G4-2).
G5 Style match: 7/10. Meets the 7 anchor: physical on most events. The crate lands as a camera thump, fare_banked slams its stamp from scale 1.8 to 1 with a ticket punch, coal_low rattles its ticket 4.94 px, and the lever panel punches 6% with a ring. hard_brake is the one generic event (G5-2). Below 8 because the signature snap home uses a stock app curve (G5-1).
G6 Polish and consistency: 6/10. Sits between 4 and 7. The families mostly share forms: tickets all slide and fade, UI punches ring about 2 cycles and settle in 0.3-0.4 s, and camera kicks use one overshoot. But the haptic doesn't match the visual on 2 of 5 events, stacking isn't covered, and the crate ticket is a timing outlier. Below 7 because of G6-1 and G6-2; G6-3 is minor.

ISSUES (ranked by impact, lowest-scoring criteria first; issue format):
[G1-1] G1 · alert_fare_banked row, feel matrix + Facts   impact: high   blocks-8: yes
  Problem: A tier-4 reward at 0.135 outshouts windows_smash (tier 2, 0.12), hud_crisis_arrival (tier 2, 0.13) and alert_risky_route (tier 3, 0.10). Its bar is the same length as hard_brake's (0.14).
  Fix: alert_fare_banked haptic 0.52 -> 0.30 as a single pulse at the stamp (drop the second pulse at about 0.5 s). Ticket punch scale 4% -> 3%. Stamp scale 1.8 -> 1.5. Target loudness <= 0.09.
  Done when: the matrix shows fare_banked <= 0.10, and Facts list "Outshouts: no higher-tier event" for it.
[G1-2] G1 · crisis tier vs commit tier, feel matrix   impact: high   blocks-8: yes
  Problem: alert_coal_low (tier 2) at 0.17 is below fired_stamp (tier 3) at 0.25 and only 0.015 above lever_commit. lever_commit (0.16) and hard_brake (0.145) both outshout windows_smash (0.12) and hud_crisis_arrival (0.13).
  Fix: alert_coal_low haptic 0.5 -> 0.8, ticket x_px punch 4.94 -> 8 px (8% -> 12%), gauge punch peak 0.0749 -> 0.12, for a target of >= 0.28. Raise windows_smash and hud_crisis_arrival to >= 0.28 in their pass.
  Done when: every tier-2 row in the matrix is >= 0.28, above every tier-3 row, and no event in this pass lists a tier-2 event under Outshouts.
[G1-3] G1 · lever_commit row, matrix + peak frame   impact: high   blocks-8: yes
  Problem: The owner's signature moment (fork_bet) is 0.16, quieter than fired_stamp (0.25) in its own tier and only 0.02 above the tier-4 fare_banked.
  Fix: lever_commit camera kick 0.805 -> 1.2 deg (about 8.8 px, under the 18 px tier-3 limit). lever_panel punch 6% -> 10%. Hit-stop 70 -> 90 ms. Light the console's yellow bar (#F2C230) together with the lamp. Target 0.26-0.27.
  Done when: lever_commit is the loudest tier-3 row (>= fired_stamp) and stays below every tier-2 row.
[G1-4] G1 · alert_crate_landed camera, closeup kit   impact: med   blocks-8: no
  Problem: A tier-4 crate kicks the camera 0.70 deg (4.1 px), more than hard_brake's 0.699 deg (3.4 px) at tier 3. It also outshouts alert_junction_ahead and fork_countdown_tick (tier 3, 0.02).
  Fix: alert_crate_landed kick 0.70 -> 0.40 deg, roll 0.2 -> 0 deg (about 2.3 px).
  Done when: crate cam px < 3.4 in Facts, with no tier-3 event under its Outshouts.
[G2-1] G2 · lever_commit timeline (camera, lever_panel, flash, haptic lanes)   impact: high   blocks-8: yes
  Problem: The haptic peaks at 1.0 at t=0 and is down to about 0.3 when the camera trough and panel punch peak at about 0.108 s. The lamp peaks at about 0.03 s. During the 70 ms hit-stop the panel and camera are flat, so the freeze holds a neutral pose instead of the impact pose. That puts about 6 frames between the felt hit and the seen hit.
  Fix: Drive lever_panel to its 6% peak and the camera kick to its peak by 33 ms (inside hit-stop), and hold that pose through the hit-stop. Alternatively, delay the haptic peak to the 70 ms release. Either way, all four channels should peak within 2 frames.
  Done when: in the lever_commit timeline the peaks of camera, lever_panel, lamp and haptic sit within 33 ms of each other.
[G2-2] G2 · hard_brake FOV lane, closeup kit   impact: med   blocks-8: no
  Problem: FOV -4 deg holds to about 0.6 s, then eases back over about 1.4 s, stretching the event to 2.1 s. This is a floaty tail, and slow FOV drift adds vection on a phone.
  Fix: hard_brake FOV return 1.4 s -> 0.5 s (Quad Out) ending by 1.1 s. Event length 2.1 -> <= 1.2 s.
  Done when: the FOV lane is back at 0 by 1.1 s and Facts show hard_brake lasts <= 1.2 s.
[G6-1] G6 · haptic lanes of hard_brake and alert_coal_low, closeup kit   impact: high   blocks-8: yes
  Problem: hard_brake's haptic has 4 pulses (about 0.05 / 0.2 / 0.35 / 0.5 s) against a single camera dip with no visual judder. coal_low's haptic (2 pulses) ends by 0.2 s, while the ticket rattle (4.94 px, the main visual) runs from about 0.28 to 0.63 s.
  Fix: For hard_brake, either add a 4-step camera pitch judder of 0.15 deg at the haptic times, or replace the haptic with one 0.6 pulse plus a 0.25 tail decaying over 600 ms. For coal_low, add 0.3 haptic pulses at each rattle peak (about 0.33 s and 0.5 s).
  Done when: every haptic pulse in those two plots sits within 33 ms of a visual peak, and no visual peak is left without haptic.
[G6-2] G6 · kit-wide stacking (not shown in any image or Fact beyond the rumble cap)   impact: med   blocks-8: yes
  Problem: No limiter or cooldown is shown for overlapping events. A crate landing during a hard brake would sum two 0.7 deg pitch-down kicks to about 1.4 deg (about 7-8 px). lever_commit plus hard_brake is unshown too.
  Fix: Clamp the summed camera offset to the tier limit of the loudest active event, add a 0.3 s per-event cooldown on camera kicks, and add an overlap plot (hard_brake plus alert_crate_landed at +0.1 s) to the kit.
  Done when: the kit shows an overlap plot whose combined cam px is <= the higher event's tier limit, and Facts state the limiter rule.
[G6-3] G6 · alert_crate_landed ticket lane, closeup kit   impact: low   blocks-8: no
  Problem: The crate ticket starts at about 0.1 s (after its 0-0.1 s haptic has ended) and slides in over about 150 ms. The coal and fare tickets enter at t=0 in about 80-150 ms. It is the one outlier in the ticket family (exact values not legible at fit x0.86).
  Fix: Start the crate ticket at <= 0.05 s, sharing one ticket-entry tween across all three alerts (same duration, same easing).
  Done when: the ticket x and alpha lanes of all three alerts start within 50 ms of t=0 and end at the same duration.
[G3-1] G3 · sustained rumble, Facts   impact: high   blocks-8: yes
  Problem: Rumble is 1.66 px at max speed and 2.89 px capped at redline, which is 96% of the 3 px limit. The player feels it for much of a 12-minute trip; that is not "barely there".
  Fix: speed-at-max rumble 1.66 -> 0.8 px, redline rumble 1.66 -> 1.2 px, combined cap 2.89 -> 1.8 px.
  Done when: Facts show speed rumble <= 1.0 px and a combined cap <= 2.0 px.
[G3-2] G3 · hard_brake flash lane, reduce-motion (dashed)   impact: med   blocks-8: no
  Problem: With camera and FOV removed, the dashed vignette peaks at about 2/3 of the full one (about 0.08 vs 0.12, read at fit x0.86; I can't get a finer read) and later (about 0.25 s vs 0.05 s). That weakens the one visual left for reduce-motion players.
  Fix: Keep the hard_brake reduce-motion vignette at the full 0.12 peak (or 0.16), reached by 0.05 s. Keep the haptic at 0.6.
  Done when: the dashed and solid flash lanes in the hard_brake plot have the same or a higher peak at the same time.
[G4-1] G4 · contact sheet: true-size phone frames   impact: high   blocks-8: yes
  Problem: Only lever_commit has an 844x390 peak frame. For hard_brake, crate, coal_low and fare_banked there is nothing at phone size to show that the tickets, halo, stamp and gauge punch read in the first 150 ms or don't cover the lever, gauges or ticket stack.
  Fix: Add true-size peak frames with the HUD in place: hard_brake at about 0.15 s, alert_crate_landed at about 0.05 s and 0.25 s, alert_coal_low at about 0.35 s (rattle plus halo), alert_fare_banked at about 0.4 s (stamp landed).
  Done when: the contact sheet shows those frames at 1:1, with no effect covering the lever, gauge or tickets.
[G4-2] G4 · lever_commit reduce motion, closeup kit + peak frame   impact: med   blocks-8: no
  Problem: Under reduce motion the signature's visuals are a lever_panel punch of 1.77% (about 5-6 px across a roughly 315 px console, under 3 px per edge) and a lamp about 20 px across. That is subtle at phone size.
  Fix: lever_commit reduce-motion punch 1.77% -> 4%, and light the full yellow bar (#F2C230) with the lamp for 0.3 s.
  Done when: the reduce-motion lever_panel lane peaks >= 0.04, and a reduce-motion peak frame shows the lit bar.
[G5-1] G5 · lever snap home, drag closeup   impact: high   blocks-8: yes
  Problem: After commit the knob uses a stock Penner Back Out 0.18 s, peaking about 1.03 (a 3% overshoot). That is an app bounce, not a heavy lever hitting its stop, on the signature moment.
  Fix: Snap home as Quad In 0.06 s into the stop, then a damped spring with 2 visible bounces (first overshoot 8%, damping ratio 0.5), total <= 0.25 s.
  Done when: the snap-home plot shows an accelerating approach and 2 decaying bounces, the first >= 1.06, settled by 0.25 s.
[G5-2] G5 · hard_brake, closeup kit   impact: med   blocks-8: no
  Problem: UI punch is 0%, and the brake is a #000000 vignette plus FOV squeeze, which is a serious, cinematic read. Nothing in the HUD reacts slapstick to a hard brake.
  Fix: Add a HUD lurch: the ticket stack and gauge translate 12 px toward the direction of travel, then return with Back Out 0.3 s, in time with the camera dip at about 0.05 s.
  Done when: the hard_brake plot has a HUD-translate lane peaking at <= 0.08 s that returns by 0.4 s.
[G5-3] G5 · lever knob colour, true-size peak frame   impact: low   blocks-8: no
  Problem: The knob is red (about #F0604F), which breaks "red only for the danger signal". This is mock colour, but it is visible.
  Fix: Change the knob fill to hazard yellow #F2C230 with an ink-black outline, or mustard.
  Done when: no red appears in the lever_commit frame outside a danger signal.

OVERALL: 4 (G1)
NEEDS OWNER: Should alert_junction_ahead and fork_countdown_tick stay at tier 3 with loudness 0.02, below the tier-4 crate at 0.036? The alternative is moving them to tier 5 (a tiering call). Otherwise none.
KEEP: (1) the lever drag model: finger^1.6 resistance, tick at 60%, commit snap at 70%, with haptic 1.0. (2) fare_banked's stamp, ticket punch and haptic all landing together at about 0.4 s. (3) reduce-motion lanes that drop camera and FOV but keep the lamp, alpha and haptic.