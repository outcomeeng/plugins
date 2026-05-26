export default {
  purpose: "Fallback manual-review prompts for auditing-rust.",
  manualChecks: [
    "Prefer crate:: for stable cross-module imports.",
    "Use self:: or super:: only for nearby private modules that move together.",
    "Reject long super:: chains in shared production modules.",
    "Keep test-only helpers out of production code.",
    "Verify unsafe blocks stay narrow and have precise SAFETY comments.",
  ],
};
