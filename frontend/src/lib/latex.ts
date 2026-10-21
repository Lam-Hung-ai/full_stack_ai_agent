import { isWithinCodeBlock, type RemendHandler } from "remend";

/**
 * Models inconsistently emit LaTeX math as \(...\) / \[...\] instead of the
 * $...$ / $$...$$ delimiters remark-math (and therefore KaTeX rendering)
 * actually recognizes. remend tracks \(...\)/\[...\] internally (so its own
 * bold/italic/code completions don't corrupt math spans written that way),
 * but it never rewrites them into $...$ for rendering — remark-math only
 * ever parses $ delimiters. Converting is on us.
 *
 * Registered as a remend handler (via `remend={{ handlers: [latexDelimiterHandler] }}`
 * on Streamdown) rather than called manually before rendering, so every
 * consumer of Streamdown gets it automatically and it runs in the same
 * pass as remend's own incomplete-markdown completions.
 *
 * Skips matches inside fenced code blocks (e.g. a LaTeX syntax example shown
 * in a ``` block) using remend's own code-fence detector, so a literal
 * \(...\) shown as sample code isn't rewritten into rendered math.
 */
export const latexDelimiterHandler: RemendHandler = {
  name: "latex-delimiters",
  // Lower than remend's built-in handlers' default (100) so backslash
  // delimiters are normalized to $ before anything else inspects math spans.
  priority: 10,
  handle(text) {
    const rewrite = (input: string, pattern: RegExp, format: (expr: string) => string) =>
      input.replace(pattern, (match: string, expr: string, offset: number) =>
        isWithinCodeBlock(input, offset) ? match : format(expr),
      );

    let result = text;
    result = rewrite(result, /\\\[([\s\S]*?)\\\]/g, (expr) => `$$${expr}$$`);
    result = rewrite(result, /\\\(([\s\S]*?)\\\)/g, (expr) => `$${expr}$`);
    return result;
  },
};
