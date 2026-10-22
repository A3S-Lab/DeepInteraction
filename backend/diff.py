from difflib import SequenceMatcher
from typing import Tuple

def single_change_span(
    old: str,
    new: str,
) -> Tuple[
    str, str, str,   # 1-3: old_prefix, old_change, old_suffix
    str, str, str,   # 4-6: new_prefix, new_change, new_suffix
    Tuple[int, int], # 7: 原文_修改前_索引
    Tuple[int, int], # 8: 原文_修改_索引
    Tuple[int, int], # 9: 原文_之后_索引
    Tuple[int, int], # 10: 新文_修改前_索引
    Tuple[int, int], # 11: 新文_修改_索引
    Tuple[int, int], # 12: 新文_之后_索引
]:
    """
    计算两段文本的“修改前内容”“修改内容”“修改内容之后”，并返回 12 个值（见返回值顺序）。
    索引为半开区间：[start, end)，从 0 开始计数。
    """
    sm = SequenceMatcher(a=old, b=new, autojunk=False)
    opcodes = sm.get_opcodes()

    # 初始化前缀/后缀边界
    prefix_old_start = 0
    prefix_old_end = 0
    prefix_new_start = 0
    prefix_new_end = 0

    suffix_old_start = len(old)
    suffix_old_end = len(old)
    suffix_new_start = len(new)
    suffix_new_end = len(new)

    # 找前缀 equal
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            if i1 == prefix_old_end == 0 and j1 == prefix_new_end == 0:
                prefix_old_end = i2
                prefix_new_end = j2
            else:
                break
        else:
            break

    # 找后缀 equal
    for tag, i1, i2, j1, j2 in reversed(opcodes):
        if tag == 'equal':
            if i2 == suffix_old_start == len(old) and j2 == suffix_new_start == len(new):
                suffix_old_start = i1
                suffix_new_start = j1
            else:
                break
        else:
            break

    # 防止前后缀重叠（例如完全相同的情况）
    if prefix_old_end > suffix_old_start or prefix_new_end > suffix_new_start:
        prefix_old_end = suffix_old_start = len(old)
        prefix_new_end = suffix_new_start = len(new)

    # 中间（修改）区
    old_change_start, old_change_end = prefix_old_end, suffix_old_start
    new_change_start, new_change_end = prefix_new_end, suffix_new_start

    # 切片
    old_prefix = old[prefix_old_start:prefix_old_end]
    old_change = old[old_change_start:old_change_end]
    old_suffix = old[suffix_old_start:suffix_old_end]

    new_prefix = new[prefix_new_start:prefix_new_end]
    new_change = new[new_change_start:new_change_end]
    new_suffix = new[suffix_new_start:suffix_new_end]

    return (
        old_prefix,
        old_change,
        old_suffix,
        new_prefix,
        new_change,
        new_suffix,
        (prefix_old_start, prefix_old_end),
        (old_change_start, old_change_end),
        (suffix_old_start, suffix_old_end),
        (prefix_new_start, prefix_new_end),
        (new_change_start, new_change_end),
        (suffix_new_start, suffix_new_end),
    )

if __name__ == "__main__":
    old_text = "You are a beautiful girl and everyoneaaaa likes you very much"
    new_text = "You are a very beautiful boy, everyone likes you very much"

    (
        old_prefix, old_change, old_suffix,
        new_prefix, new_change, new_suffix,
        idx_old_prefix, idx_old_change, idx_old_suffix,
        idx_new_prefix, idx_new_change, idx_new_suffix,
    ) = single_change_span(old_text, new_text)

    print("修改前内容:", old_prefix)
    print("修改内容（原文区段）:", old_change)
    print("修改内容之后:", old_suffix)
    print("新文本_修改内容:", new_change)
    print("原文_修改前_索引:", idx_old_prefix)
    print("原文_修改_索引:", idx_old_change)
    print("原文_之后_索引:", idx_old_suffix)
    print("新文_修改前_索引:", idx_new_prefix)
    print("新文_修改_索引:", idx_new_change)
    print("新文_之后_索引:", idx_new_suffix)