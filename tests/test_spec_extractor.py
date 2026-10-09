from src.spec_extractor import SpecExtractor

def test_extract_flash_and_sram():
    extractor = SpecExtractor()
    chunks = [{
        "chunk_id": "test_c1",
        "source": "DS_test.pdf",
        "page": 1,
        "text": "The MCU features 512 Kbytes of Flash memory and 128 Kbytes of SRAM."
    }]
    spec = extractor.extract(chunks)
    assert spec.flash_kb is not None
    assert spec.flash_kb.value == 512
    assert spec.flash_kb.source == "DS_test.pdf"
    assert spec.sram_kb is not None
    assert spec.sram_kb.value == 128

def test_extract_voltage_range():
    extractor = SpecExtractor()
    chunks = [{
        "chunk_id": "test_c2",
        "source": "DS_test.pdf",
        "page": 2,
        "text": "Operating from a 1.7 V to 3.6 V application supply and I/Os."
    }]
    spec = extractor.extract(chunks)
    assert spec.voltage_min.value == 1.7
    assert spec.voltage_max.value == 3.6
    assert spec.voltage_min.page == 2

def test_conflict_handling_returns_none():
    extractor = SpecExtractor()
    chunks = [
        {
            "chunk_id": "c1", "source": "f1.pdf", "page": 1,
            "text": "up to 512 Kbytes of Flash"
        },
        {
            "chunk_id": "c2", "source": "f2.pdf", "page": 2,
            "text": "up to 256 Kbytes of Flash"
        }
    ]
    spec = extractor.extract(chunks)
    # Due to conflict (512 vs 256), the value should be UNKNOWN (None)
    assert spec.flash_kb is None

def test_missing_value():
    extractor = SpecExtractor()
    chunks = [{"chunk_id": "c1", "source": "f1.pdf", "page": 1, "text": "MCU with high performance."}]
    spec = extractor.extract(chunks)
    assert spec.flash_kb is None
    assert spec.gpio_count is None

def test_component_identity():
    extractor = SpecExtractor()
    chunks = [{
        "chunk_id": "c1", "source": "DS_stm32f411re.pdf", "page": 1,
        "text": "512 Kbytes of Flash"
    }]
    # We requested STM32F103C8, so it should ignore STM32F411RE chunks
    spec = extractor.extract(chunks, expected_part_number="STM32F103C8")
    assert spec.flash_kb is None

def test_family_level_max_rejection():
    extractor = SpecExtractor()
    chunks = [{
        "chunk_id": "c1", "source": "DS_test_mcu.pdf", "page": 1,
        "text": "The family features up to 512 Kbytes of Flash memory."
    }]
    # Without part number in text, 'up to 512' should be skipped when part number is expected
    spec = extractor.extract(chunks, expected_part_number="TEST_MCU")
    assert spec.flash_kb is None

def test_family_level_max_with_part_number_still_unknown():
    extractor = SpecExtractor()
    chunks = [{
        "chunk_id": "c1", "source": "DS_test_mcu.pdf", "page": 1,
        "text": "The TEST_MCU features up to 512 Kbytes of Flash memory."
    }]
    # Part number is in text, but "up to" means it's a family max, not a specific guarantee
    spec = extractor.extract(chunks, expected_part_number="TEST_MCU")
    assert spec.flash_kb is None

def test_unambiguous_part_specific_memory():
    extractor = SpecExtractor()
    chunks = [{
        "chunk_id": "c1", "source": "DS_test_mcu.pdf", "page": 1,
        "text": "TEST_MCU memory density: 64 Kbytes of Flash memory."
    }]
    # Unambiguous statement specific to the part
    spec = extractor.extract(chunks, expected_part_number="TEST_MCU")
    assert spec.flash_kb is not None
    assert spec.flash_kb.value == 64


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
