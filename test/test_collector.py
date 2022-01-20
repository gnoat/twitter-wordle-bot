import pytest
import sys
import os
import collector
from collections import Counter


def test_process_results(get_results):
    expected_graph = '''⬜⬜⬜🟩⬜⬜⬜
⬜⬜⬜🟩🟨⬜⬜
⬜⬜🟨🟩🟨⬜⬜
⬜⬜🟨🟩🟨⬜⬜
⬜⬜🟨🟩🟨🟨⬜
⬜🟨🟨🟩🟨🟨🟥
1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣❌'''

    raw_results, graph, med, avg, std = collector.process_results(get_results)
    assert med == 4
    assert avg == 4.22
    assert std == 1.27
    assert raw_results == Counter({'4': 58, '5': 46, '3': 37, '6': 24, '2': 14, 'X': 6, '1': 2})
    assert graph == expected_graph
    print(graph)