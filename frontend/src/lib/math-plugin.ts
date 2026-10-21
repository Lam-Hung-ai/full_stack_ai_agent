import { createMathPlugin } from "@streamdown/math";

/**
 * `@streamdown/math`'s default `math` export leaves `singleDollarTextMath`
 * off (remark-math's own default is `true`), so single-$ inline math like
 * "the max is $P_{max}$" never gets recognized as math at all — it falls
 * through to plain text instead of KaTeX, while $$...$$ block math still
 * renders fine. Models write single-$ inline math far more often than block
 * math, so leaving this off makes most inline formulas show up as raw LaTeX
 * source. Enable it explicitly; a single module-level instance keeps the
 * plugin object reference stable across renders.
 */
export const mathPlugin = createMathPlugin({ singleDollarTextMath: true });
