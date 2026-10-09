import pytest
from src.requirement_parser import RequirementParser

def test_empty_input():
    parser = RequirementParser()
    req = parser.parse("")
    assert req.min_flash_kb is None
    assert req.voltage_min is None

def test_complete_requirement():
    parser = RequirementParser()
    text = "I need a 3.3V MCU with at least 128KB Flash, 32KB SRAM, at least 30 GPIO, LQFP-48 package, and SPI and I2C."
    req = parser.parse(text)
    assert req.voltage_min == 3.3
    assert req.min_flash_kb == 128
    assert req.min_sram_kb == 32
    assert req.min_gpio == 30
    assert req.package == "LQFP48"
    assert "SPI" in req.interfaces
    assert "I2C" in req.interfaces

def test_flash_mb_normalization():
    parser = RequirementParser()
    req = parser.parse("Requires 1 MB Flash")
    assert req.min_flash_kb == 1024

def test_contradictory_requirement():
    parser = RequirementParser()
    with pytest.raises(ValueError, match="Contradictory"):
        parser.parse("minimum Flash 128 KB but maximum Flash 64 KB")

def test_partial_requirement():
    parser = RequirementParser()
    req = parser.parse("Looking for Wi-Fi and Bluetooth")
    assert "Wi-Fi" in req.connectivity
    assert "Bluetooth" in req.connectivity
    assert req.min_flash_kb is None

def test_frequency_normalization():
    parser = RequirementParser()
    req = parser.parse("at least 80 MHz")
    assert req.frequency_min_mhz == 80.0
