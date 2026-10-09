with open('tests/test_spec_extractor.py', 'a') as f:
    f.write('''
def test_disambiguation_multiple_parts_in_chunk():
    extractor = SpecExtractor()
    chunks = [{
        "chunk_id": "c1", "source": "DS_stm32f103.pdf", "page": 1,
        "text": "The STM32F103x8 features 64 Kbytes of Flash. The STM32F103xB features 128 Kbytes of Flash."
    }]
    # We should NOT skip the chunk just because multiple parts are mentioned or target is not exactly mentioned.
    # The extraction logic will see a conflict (64 vs 128) and safely return None (UNKNOWN).
    spec = extractor.extract(chunks, expected_part_number="STM32F103C8")
    assert spec.flash_kb is None

def test_disambiguation_target_not_mentioned():
    extractor = SpecExtractor()
    chunks = [{
        "chunk_id": "c1", "source": "DS_stm32f103.pdf", "page": 1,
        "text": "The STM32F103x8 features 64 Kbytes of Flash."
    }]
    # It should extract this because the chunk is from the correct family document.
    spec = extractor.extract(chunks, expected_part_number="STM32F103C8")
    assert spec.flash_kb is not None
    assert spec.flash_kb.value == 64
''')
