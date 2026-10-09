import re
from typing import List
from src.schemas import RequirementSpec

from langsmith import traceable

class RequirementParser:
    @traceable(run_type="parser", name="parse_requirements")
    def parse(self, text: str) -> RequirementSpec:
        if not text or not text.strip():
            return RequirementSpec()

        text_lower = text.lower()
        req = RequirementSpec()

        # Parse Part Number
        part_match = re.search(r'(stm32[a-z0-9]+|esp32[a-z0-9\-]*)', text_lower)
        if part_match:
            req.part_number = part_match.group(1).upper()

        # Parse Flash
        flash_matches = re.findall(r'(\d+)\s*(kb|mb)\s*flash', text_lower)
        if flash_matches:
            val, unit = flash_matches[0]
            val = int(val)
            if unit == 'mb':
                val *= 1024
            req.min_flash_kb = val

        # Parse SRAM
        sram_matches = re.findall(r'(\d+)\s*(kb|mb)\s*sram', text_lower)
        if sram_matches:
            val, unit = sram_matches[0]
            val = int(val)
            if unit == 'mb':
                val *= 1024
            req.min_sram_kb = val

        # Parse Voltage
        voltage_matches = re.findall(r'(\d+\.?\d*)\s*v', text_lower)
        if voltage_matches:
            val = float(voltage_matches[0])
            req.voltage_min = val
            req.voltage_max = val

        # Parse GPIO
        gpio_matches = re.findall(r'(?:at least |>|=)?\s*(\d+)\s*gpio', text_lower)
        if gpio_matches:
            req.min_gpio = int(gpio_matches[0])

        # Parse Frequency
        freq_matches = re.findall(r'(\d+)\s*mhz', text_lower)
        if freq_matches:
            req.frequency_min_mhz = float(freq_matches[0])

        # Parse Package
        package_match = re.search(r'(lqfp-?\d+|qfn-?\d+|bga-?\d+)', text_lower)
        if package_match:
            pkg = package_match.group(1).replace('-', '').upper()
            req.package = pkg

        # Parse Interfaces
        interfaces = []
        for iface in ['spi', 'i2c', 'i²c', 'uart', 'can']:
            if iface in text_lower:
                normalized = 'I2C' if iface == 'i²c' else iface.upper()
                if normalized not in interfaces:
                    interfaces.append(normalized)
        req.interfaces = interfaces

        # Parse Connectivity
        connectivity = []
        if 'wi-fi' in text_lower or 'wifi' in text_lower:
            connectivity.append('Wi-Fi')
        if 'bluetooth' in text_lower or 'ble' in text_lower:
            connectivity.append('Bluetooth')
        req.connectivity = connectivity

        # Contradiction Handling
        # If text says "minimum flash X but maximum flash Y" where X > Y
        min_flash_m = re.search(r'minimum flash (\d+)\s*(kb|mb)', text_lower)
        max_flash_m = re.search(r'maximum flash (\d+)\s*(kb|mb)', text_lower)
        if min_flash_m and max_flash_m:
            min_f = int(min_flash_m.group(1)) * (1024 if min_flash_m.group(2) == 'mb' else 1)
            max_f = int(max_flash_m.group(1)) * (1024 if max_flash_m.group(2) == 'mb' else 1)
            if min_f > max_f:
                raise ValueError(f"Contradictory requirements: min flash {min_f}KB > max flash {max_f}KB")

        return req
