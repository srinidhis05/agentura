/**
 * Format skill output for display.
 *
 * Handles the common case where output is `{ raw_output: "```json\n{...}\n```" }`
 * by stripping markdown fences and pretty-printing the inner JSON.
 */
export function formatOutput(output: unknown): string {
  if (output == null) return "";
  if (typeof output === "string") return extractAndFormat(output);

  // Check for { raw_output: "..." } wrapper
  if (
    typeof output === "object" &&
    "raw_output" in (output as Record<string, unknown>)
  ) {
    const raw = (output as Record<string, unknown>).raw_output;
    if (typeof raw === "string") {
      return extractAndFormat(raw);
    }
  }

  return JSON.stringify(output, null, 2);
}

/** Strip markdown code fences and try to pretty-print JSON. */
function extractAndFormat(text: string): string {
  let cleaned = text.trim();

  // Strip ```json ... ``` or ``` ... ``` fences
  const fenceMatch = cleaned.match(/^```(?:json|jsonc)?\s*\n([\s\S]*?)\n```$/);
  if (fenceMatch) {
    cleaned = fenceMatch[1].trim();
  }

  // Try to parse as JSON and pretty-print
  try {
    const parsed = JSON.parse(cleaned);
    return JSON.stringify(parsed, null, 2);
  } catch {
    // Not valid JSON — return the cleaned text as-is
    return cleaned;
  }
}
