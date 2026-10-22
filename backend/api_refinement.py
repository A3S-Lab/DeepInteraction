#!/usr/bin/env python3
"""
Deep Interaction API: Text Refinement and Emphasis
API for processing original and edited text to generate refined output with emphasis

Input:
- original_text: Original CoT response (e.g., "ABCDEF")
- edited_text: User-edited version (e.g., "ABCGH")
- question: Optional question for semantic filtering

Output:
- Refined text with emphasis markers (e.g., "abc*GH*")
"""

import json
import sys
from typing import Dict, Any, Optional
from diff import single_change_span
from refinement import apply_full_refinement, RefinementProcessor

class DeepInteractionAPI:
    """API for Deep Interaction text refinement and emphasis"""

    def __init__(self):
        self.refinement_processor = RefinementProcessor()

    def process_text(self,
                    original_text: str,
                    edited_text: str,
                    question: str,
                    emphasis_marker: str = "*") -> Dict[str, Any]:
        """
        Process original and edited text to generate refined output with emphasis

        Args:
            original_text: Original CoT response
            edited_text: User-edited version
            question: Optional question for semantic filtering
            emphasis_marker: Character to use for emphasis markers (default: "*")

        Returns:
            Dict containing:
            - refined_text: Full refined text
            - emphasized_text: Text with emphasis markers around changed parts
            - changes_detected: Details about detected changes
            - processing_stats: Refinement processing statistics
        """

        # 1. Detect text differences
        (old_prefix, old_change, old_suffix,
         new_prefix, new_change, new_suffix,
         idx_old_prefix, idx_old_change, idx_old_suffix,
         idx_new_prefix, idx_new_change, idx_new_suffix) = single_change_span(original_text, edited_text)

        # 2. Apply refinement to the edited text
        refined_text, processing_stats = self.refinement_processor.apply_refinement(
            original_text, edited_text, question or ""
        )

        # 3. Generate emphasized text
        emphasized_text = self._generate_emphasized_text(
            refined_text, new_change, emphasis_marker
        )

        # 4. Prepare change detection details
        changes_detected = {
            "old_change": old_change.strip(),
            "new_change": new_change.strip(),
            "change_start_pos": idx_new_change[0],
            "change_end_pos": idx_new_change[1],
            "has_changes": len(new_change.strip()) > 0
        }

        return {
            "refined_text": refined_text.strip(),
            "emphasized_text": emphasized_text.strip(),
            "changes_detected": changes_detected,
            "processing_stats": processing_stats
        }

    def _generate_emphasized_text(self,
                                 refined_text: str,
                                 new_change: str,
                                 emphasis_marker: str = "*") -> str:
        """
        Generate text with emphasis markers around the changed parts

        Args:
            refined_text: The refined text
            new_change: The detected change from user edit
            emphasis_marker: Marker character for emphasis

        Returns:
            Text with emphasis markers around changed parts
        """

        if not new_change.strip():
            return refined_text

        # Find the changed part in the refined text
        # Since refinement may have modified the text, we need to find
        # the most similar part to the original change
        change_clean = new_change.strip()

        # Simple approach: look for the change as a substring
        if change_clean in refined_text:
            start_idx = refined_text.find(change_clean)
            end_idx = start_idx + len(change_clean)
            emphasized = (
                refined_text[:start_idx] +
                emphasis_marker + change_clean + emphasis_marker +
                refined_text[end_idx:]
            )
            return emphasized

        # If direct substring match fails, try to find the longest common substring
        # between the change and refined text
        emphasized = self._find_and_emphasize_similar_parts(refined_text, change_clean, emphasis_marker)

        return emphasized

    def _find_and_emphasize_similar_parts(self,
                                        refined_text: str,
                                        change: str,
                                        emphasis_marker: str) -> str:
        """
        Find similar parts between change and refined text and emphasize them
        """
        # Split both texts into words for comparison
        refined_words = refined_text.split()
        change_words = change.split()

        # Find the best matching subsequence
        best_match_start = -1
        best_match_length = 0

        for i in range(len(refined_words)):
            for j in range(len(change_words)):
                k = 0
                while (i + k < len(refined_words) and
                       j + k < len(change_words) and
                       refined_words[i + k] == change_words[j + k]):
                    k += 1

                if k > best_match_length:
                    best_match_length = k
                    best_match_start = i

        if best_match_length > 0:
            # Reconstruct text with emphasis
            result_parts = []
            current_pos = 0

            for i, word in enumerate(refined_words):
                if i == best_match_start:
                    result_parts.append(emphasis_marker)
                result_parts.append(word)
                if i == best_match_start + best_match_length - 1:
                    result_parts.append(emphasis_marker)
                if i < len(refined_words) - 1:
                    result_parts.append(" ")

            return "".join(result_parts)

        # Fallback: return original text if no good match found
        return refined_text

def main():
    """Command line interface for the API"""

    if len(sys.argv) < 4:
        print("Usage: python api_refinement.py <original_text> <edited_text> <question>")
        print("Example: python api_refinement.py 'ABCDEF' 'ABCGH' 'What is the answer?'")
        sys.exit(1)

    original_text = sys.argv[1]
    edited_text = sys.argv[2]
    question = sys.argv[3]

    # Initialize API
    api = DeepInteractionAPI()

    # Process text
    result = api.process_text(original_text, edited_text, question)

    # Output as JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()