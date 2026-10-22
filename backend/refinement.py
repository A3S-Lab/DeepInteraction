import re
from typing import List, Tuple, Optional
from diff import single_change_span

try:
    from segrefine2 import build_filtered_answer, client
    # Check if API key is configured
    if client.api_key:
        SEMANTIC_FILTERING_AVAILABLE = True
    else:
        SEMANTIC_FILTERING_AVAILABLE = False
        print("Warning: OpenAI API key not configured in segrefine2.py, semantic filtering will be disabled")
except ImportError as e:
    SEMANTIC_FILTERING_AVAILABLE = False
    print(f"Warning: segrefine2 not available ({e}), semantic filtering will be disabled")

def improved_split_sentences(text: str) -> List[str]:
    """
    中英文混合分句器：在 。！？；.!?; 处切句，保留标点，不切英文小数点。
    """
    if not text:
        return []

    t = re.sub(r'\s+', ' ', text.strip())
    sentences = re.split(r'(?<=[。！？；])|(?<=[.!?;])(?=\s|$)(?<!\d\.)', t)

    parts = []
    for sent in sentences:
        sent = sent.strip()
        if sent and len(sent) > 1:  # 过滤过短碎片
            parts.append(sent)

    return parts if parts else [text.strip()]

# Fallback semantic filtering when embeddings are not available
def simple_semantic_filter(question: str, text: str, keep_ratio: float = 0.2) -> Tuple[str, List[Tuple[str, float]]]:
    """
    Simple semantic filtering based on keyword matching when embeddings are not available
    """
    # Split text into sentences using improved splitter
    sentences = improved_split_sentences(text)

    if not sentences:
        return text, []

    # Extract keywords from question (simple approach)
    question_words = set(question.lower().split())
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'what', 'how', 'why', 'when', 'where', 'who', 'which', 'calculate', 'find', 'solve'}
    question_words = question_words - stop_words

    # Score sentences based on keyword overlap
    scored_sentences = []
    for i, sentence in enumerate(sentences):
        sentence_words = set(sentence.lower().split())
        overlap = len(question_words.intersection(sentence_words))
        total_words = len(question_words.union(sentence_words))
        similarity = overlap / total_words if total_words > 0 else 0.0
        scored_sentences.append((i, sentence, similarity))

    # Sort all sentences by similarity (highest first)
    sorted_sentences = sorted(scored_sentences, key=lambda x: x[2], reverse=True)

    # Calculate how many sentences to keep (at least 1, at most all sentences)
    k = max(1, int(len(sentences) * keep_ratio))

    # Keep top k sentences by similarity
    kept = sorted_sentences[:k]

    # Restore original order
    kept.sort(key=lambda x: x[0])

    # Join kept sentences
    result_text = ' '.join(s for _, s, _ in kept).strip()
    details = [(s, sc) for _, s, sc in kept]

    return result_text, details

class RefinementProcessor:
    """
    Refinement based on Tracking Changes
    Implements Emphasis Pruning Removing and NumericalMask
    """

    def __init__(self):
        # 强调词和短语的模式
        self.emphasis_patterns = [
            r'\b(?:very|really|extremely|absolutely|totally|completely|utterly|quite|so|too|much|way|far|highly|deeply|greatly|significantly|substantially|considerably|remarkably|exceptionally|unusually|particularly|especially|notably|strikingly|dramatically|markedly|noticeably|appreciably|distinctly|decidedly|definitely|positively|certainly|surely|undoubtedly|clearly|obviously|evidently|plainly|manifestly|patently|apparently|seemingly|ostensibly)\b',
            r'\b(?:important|key|crucial|essential|vital|critical|fundamental|basic|core|primary|main|major|chief|principal|leading|foremost|paramount|supreme|utmost|extreme|ultimate|absolute|complete|total|full|entire|whole|comprehensive|thorough|exhaustive|inclusive|all-encompassing)\b',
            r'\b(?:must|should|need|have to|got to|required|obligatory|mandatory|compulsory|imperative|essential|indispensable|necessary|requisite|prerequisite)\b',
            r'\b(?:always|never|ever|constantly|continuously|perpetually|endlessly|eternally|forever|ceaselessly|incessantly|persistently|steadily|consistently|regularly|routinely|habitually|invariably|uniformly|universally|generally|typically|usually|normally|ordinarily|commonly|customarily|traditionally)\b',
            r'\b(?:best|worst|better|worse|good|bad|great|terrible|excellent|awful|perfect|horrible|ideal|wonderful|fabulous|fantastic|amazing|incredible|unbelievable|astonishing|stunning|phenomenal|extraordinary|remarkable|marvelous|superb|splendid|magnificent|brilliant|outstanding|exceptional|super|ultra|mega|hyper|ultra-modern|state-of-the-art)\b'
        ]

        # 词界避免掩掉变量下标（G1、x2）；单位长优先避免被单字符截断；°[CF]? 完整消费 25°C
        self.numerical_patterns = [
            r'(?<![A-Za-z\d])\d+(?:\.\d+)?\s*(?:km/h|mph|km|kg|mm|cm|lb|oz|℃|℉|°[CF]?|N|m|g|%)',
            r'(?<![A-Za-z\d])\d+(?:\.\d+)?\s*(?:million|billion|trillion|thousand|hundred)',
            r'(?<![A-Za-z])\d+(?:\.\d+)?',
        ]

    def emphasis_pruning_removing(self, text: str, threshold: float = 0.3) -> str:
        """
        删除强调性内容，如重复句子、强调词等

        Args:
            text: 输入文本
            threshold: 相似度阈值，用于判断是否为重复内容

        Returns:
            精简后的文本
        """
        if not text:
            return text

        # 分割成句子
        sentences = self._split_sentences(text)
        if len(sentences) <= 1:
            return text

        # 计算句子之间的相似度，移除高度相似的句子
        kept_sentences = []
        for i, sentence in enumerate(sentences):
            is_duplicate = False

            # 检查与已保留句子的相似度
            for kept in kept_sentences:
                similarity = self._calculate_sentence_similarity(sentence, kept)
                if similarity > threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                # 移除句子中的强调词
                cleaned_sentence = self._remove_emphasis_words(sentence)
                if cleaned_sentence.strip():  # 只保留非空的句子
                    kept_sentences.append(cleaned_sentence)

        return ' '.join(kept_sentences)

    def numerical_mask(self, text: str, mask_token: str = "[NUM]") -> str:
        """
        对数值进行遮罩处理

        Args:
            text: 输入文本
            mask_token: 遮罩标记

        Returns:
            遮罩后的文本
        """
        if not text:
            return text

        masked_text = text
        for pattern in self.numerical_patterns:
            masked_text = re.sub(pattern, mask_token, masked_text, flags=re.IGNORECASE)

        return masked_text

    def apply_refinement(self, original_text: str, edited_text: str, question: str) -> Tuple[str, dict]:
        """
        应用完整的精简流程：Emphasis Pruning Removing + NumericalMask + Semantic Filtering

        Args:
            original_text: 原始文本
            edited_text: 编辑后的文本
            question: 问题文本（必需，用于语义相似度计算）

        Returns:
            Tuple[str, dict]: (精简后的文本, 处理信息)
        """
        if not question:
            raise ValueError("question parameter is required for semantic filtering")

        # 首先计算文本差异
        (old_prefix, old_change, old_suffix,
         new_prefix, new_change, new_suffix,
         idx_old_prefix, idx_old_change, idx_old_suffix,
         idx_new_prefix, idx_new_change, idx_new_suffix) = single_change_span(original_text, edited_text)

        # 对编辑后的文本进行精简
        refined_text = edited_text

        # 1. Emphasis Pruning Removing
        refined_text = self.emphasis_pruning_removing(refined_text)

        # 2. 语义相关性过滤（基于完整的语义信息进行过滤）
        semantic_details = []
        if SEMANTIC_FILTERING_AVAILABLE:
            try:
                # 使用segrefine2.py的build_filtered_answer进行语义精简
                # 精简掉20%，保留80%最相关的句子（keep_ratio=0.8）
                refined_text, semantic_details = build_filtered_answer(
                    question, refined_text,
                    keep_ratio=0.8,  # 精简掉20%，保留80%
                    min_similarity=0.3,
                    max_sentences=None
                )
            except Exception as e:
                print(f"Warning: Semantic filtering failed: {e}, falling back to simple filtering")
                # 如果语义过滤失败，使用简单的关键词匹配
                refined_text, semantic_details = simple_semantic_filter(question, refined_text, keep_ratio=0.8)
        else:
            print("Warning: Semantic filtering not available, using simple keyword-based filtering")
            # 使用简单的关键词匹配作为fallback
            refined_text, semantic_details = simple_semantic_filter(question, refined_text, keep_ratio=0.8)

        # 3. NumericalMask (最后遮罩数值，保持语义完整性)
        if self._contains_numbers(refined_text):
            refined_text = self.numerical_mask(refined_text)

        processing_info = {
            'original_length': len(original_text),
            'edited_length': len(edited_text),
            'refined_length': len(refined_text),
            'emphasis_pruned': True,
            'numerical_masked': self._contains_numbers(edited_text),
            'semantic_filtered': SEMANTIC_FILTERING_AVAILABLE,
            'semantic_kept_sentences': len(semantic_details) if semantic_details else 0,
            'keep_ratio': 0.8
        }

        return refined_text, processing_info

    def _split_sentences(self, text: str) -> List[str]:
        """分割句子"""
        if not text:
            return []
        # 使用简单的句子分割
        t = re.sub(r'\s+', ' ', text.strip())
        t = re.sub(r'([。！？；.!?;])', r'\1\n', t)
        parts = [p.strip() for p in t.split('\n') if p.strip()]
        return parts if parts else [text.strip()]

    def _remove_emphasis_words(self, sentence: str) -> str:
        """移除句子中的强调词和冗余短语"""
        cleaned = sentence

        # 移除强调词
        for pattern in self.emphasis_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # 移除中文和英文科学文本中的冗余短语
        redundant_phrases = [
            # 中文冗余短语
            r'首先，我们需要',
            r'接下来，考虑',
            r'因此，当.*时',
            r'这意味着.*因为',
            r'综上所述',
            r'我们可以看出',
            r'根据.*可以得到',
            r'由.*可知',
            r'所以我们有',
            r'显然',
            r'容易看出',
            r'不难发现',
            r'也就是说',
            r'即',
            r'也就是',
            r'由于.*，.*',
            r'因为.*，.*所以',
            r'在这种情况下',
            r'在这个例子中',
            r'这是.*的',
            r'它.*是.*的',
            # 英文冗余短语
            r'First, we need to',
            r'First, we must',
            r'Next, let us',
            r'Therefore, when.*then',
            r'This means that.*because',
            r'In conclusion',
            r'We can see that',
            r'According to.*we have',
            r'So we have',
            r'Obviously',
            r'It is easy to see',
            r'It is not difficult to see',
            r'That is to say',
            r'i\.e\.',
            r'that is',
            r'Since.*we have',
            r'Because.*therefore',
            r'In this case',
            r'In this example',
            r'This is.*of',
            r'It is.*of',
            r'As we can see',
            r'Clearly',
            r'Let us consider',
            r'Now, let us'
        ]

        for phrase in redundant_phrases:
            cleaned = re.sub(phrase, '', cleaned, flags=re.IGNORECASE)

        # 清理多余的空格和标点
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'([。！？；，,!;])\s*([。！？；，,!;])', r'\2', cleaned)
        cleaned = re.sub(r'\s*([。！？；，,!;])\s*', r'\1', cleaned)
        cleaned = re.sub(r'^[\s，,、。！？；!;]+', '', cleaned)  # 短语删除后残留的句首标点

        return cleaned

    def _calculate_sentence_similarity(self, sent1: str, sent2: str) -> float:
        """计算两个句子之间的相似度（简化版本）"""
        if not sent1 or not sent2:
            return 0.0

        # 使用简单的词重叠相似度
        words1 = set(re.findall(r'\b\w+\b', sent1.lower()))
        words2 = set(re.findall(r'\b\w+\b', sent2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _contains_numbers(self, text: str) -> bool:
        """检查文本是否包含数值"""
        for pattern in self.numerical_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False


# 便捷函数
def apply_emphasis_pruning(text: str, threshold: float = 0.3) -> str:
    """应用强调性内容删除"""
    processor = RefinementProcessor()
    return processor.emphasis_pruning_removing(text, threshold)

def apply_numerical_mask(text: str, mask_token: str = "[NUM]") -> str:
    """应用数值遮罩"""
    processor = RefinementProcessor()
    return processor.numerical_mask(text, mask_token)

def apply_full_refinement(original_text: str, edited_text: str, question: str = "") -> Tuple[str, dict]:
    """应用完整的精简流程"""
    processor = RefinementProcessor()
    return processor.apply_refinement(original_text, edited_text, question)


if __name__ == "__main__":
    # 示例使用
    processor = RefinementProcessor()

    # 测试强调性内容删除
    test_text = "This is very important. This is extremely crucial. We must always do this."
    pruned = processor.emphasis_pruning_removing(test_text)
    print("Original:", test_text)
    print("Pruned:", pruned)

    # 测试数值遮罩
    numerical_text = "The temperature is 25°C and it weighs 15.5 kg with 1000 units."
    masked = processor.numerical_mask(numerical_text)
    print("Original:", numerical_text)
    print("Masked:", masked)