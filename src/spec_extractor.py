import re
from typing import List, Dict, Any, Optional
from src.schemas import ComponentSpec, Evidence
from langsmith import traceable

class SpecExtractor:
    def __init__(self):
        pass
        
    def _create_evidence(self, field: str, value: Any, chunk: Dict[str, Any], text_match: str) -> Evidence:
        return Evidence(
            field=field,
            value=value,
            source=chunk["source"],
            page=chunk["page"],
            chunk_id=chunk["chunk_id"],
            confidence=0.9, # Heuristic confidence
            evidence_text=text_match
        )
        
    @traceable(run_type="chain", name="extract_specifications")
    def extract(self, chunks: List[Dict[str, Any]], expected_part_number: Optional[str] = None) -> ComponentSpec:
        spec = ComponentSpec()
        
        extracted_flash = []
        extracted_sram = []
        extracted_gpio = []
        extracted_voltage = []
        
        # Filter chunks by component identity if requested
        valid_chunks = chunks
        if expected_part_number:
            target_str = expected_part_number.lower().replace('-', '')
            base_match = re.search(r'(stm32[a-z][0-9]{3}|esp32[a-z0-9]*)', target_str)
            if base_match:
                base_part = base_match.group(1)
                valid_chunks = [c for c in chunks if base_part in c["source"].lower().replace('-', '')]
            else:
                valid_chunks = chunks
            
        for chunk in valid_chunks:
            text = chunk["text"].lower()
            original_text = chunk["text"]
            
            # Flash extraction
            flash_matches = re.finditer(r'(\d+)\s*(?:kbytes|kb|mbytes|mb)\s*(?:of\s*)?flash', text)
            for m in flash_matches:
                val = int(m.group(1))
                if 'mb' in m.group(0):
                    val *= 1024
                
                # Reject generic family-level maximums
                start_idx = max(0, m.start() - 15)
                if 'up to' in text[start_idx:m.start()]:
                    continue
                        
                evidence = self._create_evidence("flash_kb", val, chunk, original_text[m.start():m.end()])
                extracted_flash.append(evidence)
                
            # SRAM extraction
            sram_matches = re.finditer(r'(\d+)\s*(?:kbytes|kb|mbytes|mb)\s*(?:of\s*)?sram', text)
            for m in sram_matches:
                val = int(m.group(1))
                if 'mb' in m.group(0):
                    val *= 1024
                    
                start_idx = max(0, m.start() - 15)
                if 'up to' in text[start_idx:m.start()]:
                    continue
                        
                evidence = self._create_evidence("sram_kb", val, chunk, original_text[m.start():m.end()])
                extracted_sram.append(evidence)
                
            # GPIO extraction
            gpio_matches = re.finditer(r'(\d+)\s*(?:fast\s*)?i/os', text)
            for m in gpio_matches:
                val = int(m.group(1))
                
                start_idx = max(0, m.start() - 15)
                if 'up to' in text[start_idx:m.start()]:
                    continue
                        
                evidence = self._create_evidence("gpio_count", val, chunk, original_text[m.start():m.end()])
                extracted_gpio.append(evidence)
                
            # Voltage extraction
            # e.g., "1.7 V to 3.6 V application supply and I/Os"
            volt_matches = re.finditer(r'(\d+\.?\d*)\s*v\s*(?:to|-)\s*(\d+\.?\d*)\s*v', text)
            for m in volt_matches:
                vmin, vmax = float(m.group(1)), float(m.group(2))
                # Store max for simplicity, or we can just pick the first valid range
                evidence_max = self._create_evidence("voltage_max", vmax, chunk, original_text[m.start():m.end()])
                evidence_min = self._create_evidence("voltage_min", vmin, chunk, original_text[m.start():m.end()])
                extracted_voltage.append((evidence_min, evidence_max))

        # Conflict resolution logic:
        # If we found multiple differing values, we mark as UNKNOWN (None).
        # If all found values match, we assign it.
        
        if extracted_flash:
            unique_vals = set(e.value for e in extracted_flash)
            if len(unique_vals) == 1:
                spec.flash_kb = extracted_flash[0]
            else:
                # Conflict found, mark UNKNOWN (None)
                spec.flash_kb = None
                
        if extracted_sram:
            unique_vals = set(e.value for e in extracted_sram)
            if len(unique_vals) == 1:
                spec.sram_kb = extracted_sram[0]
            else:
                spec.sram_kb = None
                
        if extracted_gpio:
            unique_vals = set(e.value for e in extracted_gpio)
            if len(unique_vals) == 1:
                spec.gpio_count = extracted_gpio[0]
            else:
                spec.gpio_count = None
                
        if extracted_voltage:
            unique_vmins = set(v[0].value for v in extracted_voltage)
            unique_vmaxs = set(v[1].value for v in extracted_voltage)
            if len(unique_vmins) == 1 and len(unique_vmaxs) == 1:
                spec.voltage_min = extracted_voltage[0][0]
                spec.voltage_max = extracted_voltage[0][1]
            else:
                spec.voltage_min = None
                spec.voltage_max = None
                
        return spec
