from typing import List, Any
from src.schemas import RequirementSpec, ComponentSpec, ConstraintResult, CompatibilityResult
from langsmith import traceable

class CompatibilityEngine:
    @traceable(run_type="chain", name="evaluate_compatibility")
    def evaluate(self, req: RequirementSpec, comp: ComponentSpec) -> CompatibilityResult:
        results: List[ConstraintResult] = []
        all_evidence = []
        
        # 1. Voltage Constraint
        if req.voltage_min is not None or req.voltage_max is not None:
            c_min = comp.voltage_min.value if comp.voltage_min else None
            c_max = comp.voltage_max.value if comp.voltage_max else None
            
            req_min = req.voltage_min if req.voltage_min is not None else float('-inf')
            req_max = req.voltage_max if req.voltage_max is not None else float('inf')
            
            if c_min is None or c_max is None:
                results.append(ConstraintResult(
                    constraint="voltage",
                    required_value=f"{req_min} - {req_max}",
                    actual_value="UNKNOWN",
                    status="UNKNOWN",
                    reason="Missing voltage evidence in component",
                    evidence=None
                ))
            else:
                # Valid overlap: comp.min <= req.max AND comp.max >= req.min
                if c_min <= req_max and c_max >= req_min:
                    results.append(ConstraintResult(
                        constraint="voltage",
                        required_value=f"{req_min} - {req_max}",
                        actual_value=f"{c_min} - {c_max}",
                        status="PASS",
                        reason="Voltage ranges overlap",
                        evidence=comp.voltage_max or comp.voltage_min
                    ))
                    if comp.voltage_max: all_evidence.append(comp.voltage_max)
                    if comp.voltage_min: all_evidence.append(comp.voltage_min)
                else:
                    results.append(ConstraintResult(
                        constraint="voltage",
                        required_value=f"{req_min} - {req_max}",
                        actual_value=f"{c_min} - {c_max}",
                        status="FAIL",
                        reason="Voltage ranges do not overlap",
                        evidence=comp.voltage_max or comp.voltage_min
                    ))
                    if comp.voltage_max: all_evidence.append(comp.voltage_max)
                    if comp.voltage_min: all_evidence.append(comp.voltage_min)
                    
        # 2. Flash Constraint
        if req.min_flash_kb is not None:
            if not comp.flash_kb:
                results.append(ConstraintResult(
                    constraint="flash_kb", required_value=req.min_flash_kb, actual_value="UNKNOWN",
                    status="UNKNOWN", reason="Missing Flash memory evidence", evidence=None
                ))
            else:
                c_flash = comp.flash_kb.value
                status = "PASS" if c_flash >= req.min_flash_kb else "FAIL"
                results.append(ConstraintResult(
                    constraint="flash_kb", required_value=req.min_flash_kb, actual_value=c_flash,
                    status=status, reason=f"Component flash is {c_flash} KB", evidence=comp.flash_kb
                ))
                all_evidence.append(comp.flash_kb)

        # 3. SRAM Constraint
        if req.min_sram_kb is not None:
            if not comp.sram_kb:
                results.append(ConstraintResult(
                    constraint="sram_kb", required_value=req.min_sram_kb, actual_value="UNKNOWN",
                    status="UNKNOWN", reason="Missing SRAM evidence", evidence=None
                ))
            else:
                c_sram = comp.sram_kb.value
                status = "PASS" if c_sram >= req.min_sram_kb else "FAIL"
                results.append(ConstraintResult(
                    constraint="sram_kb", required_value=req.min_sram_kb, actual_value=c_sram,
                    status=status, reason=f"Component SRAM is {c_sram} KB", evidence=comp.sram_kb
                ))
                all_evidence.append(comp.sram_kb)
                
        # 4. GPIO Constraint
        if req.min_gpio is not None:
            if not comp.gpio_count:
                results.append(ConstraintResult(
                    constraint="gpio_count", required_value=req.min_gpio, actual_value="UNKNOWN",
                    status="UNKNOWN", reason="Missing GPIO evidence", evidence=None
                ))
            else:
                c_gpio = comp.gpio_count.value
                status = "PASS" if c_gpio >= req.min_gpio else "FAIL"
                results.append(ConstraintResult(
                    constraint="gpio_count", required_value=req.min_gpio, actual_value=c_gpio,
                    status=status, reason=f"Component GPIO is {c_gpio}", evidence=comp.gpio_count
                ))
                all_evidence.append(comp.gpio_count)
                
        # 5. Frequency Constraint
        if req.frequency_min_mhz is not None or req.frequency_max_mhz is not None:
            if not comp.frequency_mhz:
                results.append(ConstraintResult(
                    constraint="frequency_mhz", required_value=f"{req.frequency_min_mhz}-{req.frequency_max_mhz}",
                    actual_value="UNKNOWN", status="UNKNOWN", reason="Missing Frequency evidence", evidence=None
                ))
            else:
                c_freq = comp.frequency_mhz.value
                req_min = req.frequency_min_mhz if req.frequency_min_mhz is not None else float('-inf')
                req_max = req.frequency_max_mhz if req.frequency_max_mhz is not None else float('inf')
                
                if req_min <= c_freq <= req_max:
                    status = "PASS"
                else:
                    status = "FAIL"
                results.append(ConstraintResult(
                    constraint="frequency_mhz", required_value=f"{req_min}-{req_max}", actual_value=c_freq,
                    status=status, reason=f"Component Frequency is {c_freq} MHz", evidence=comp.frequency_mhz
                ))
                all_evidence.append(comp.frequency_mhz)
                
        # 6. Interfaces
        if req.interfaces:
            if not comp.interfaces:
                results.append(ConstraintResult(
                    constraint="interfaces", required_value=req.interfaces, actual_value="UNKNOWN",
                    status="UNKNOWN", reason="Missing Interfaces evidence", evidence=None
                ))
            else:
                # Assuming component interfaces is a list of Evidence objects
                c_ifaces = [ev.value.upper() for ev in comp.interfaces]
                req_ifaces = [i.upper() for i in req.interfaces]
                missing = [i for i in req_ifaces if i not in c_ifaces]
                if missing:
                    results.append(ConstraintResult(
                        constraint="interfaces", required_value=req.interfaces, actual_value=c_ifaces,
                        status="FAIL", reason=f"Missing required interfaces: {missing}", evidence=comp.interfaces[0] if comp.interfaces else None
                    ))
                else:
                    results.append(ConstraintResult(
                        constraint="interfaces", required_value=req.interfaces, actual_value=c_ifaces,
                        status="PASS", reason="All required interfaces supported", evidence=comp.interfaces[0] if comp.interfaces else None
                    ))
                all_evidence.extend(comp.interfaces)
                
        # 7. Package
        if req.package:
            req_pkg = req.package.replace("-", "").replace(" ", "").upper()
            if not comp.packages:
                results.append(ConstraintResult(
                    constraint="package", required_value=req_pkg, actual_value="UNKNOWN",
                    status="UNKNOWN", reason="Missing Package evidence", evidence=None
                ))
            else:
                c_pkgs = [ev.value.replace("-", "").replace(" ", "").upper() for ev in comp.packages]
                if req_pkg in c_pkgs:
                    results.append(ConstraintResult(
                        constraint="package", required_value=req_pkg, actual_value=c_pkgs,
                        status="PASS", reason="Matching package found", evidence=comp.packages[0]
                    ))
                else:
                    results.append(ConstraintResult(
                        constraint="package", required_value=req_pkg, actual_value=c_pkgs,
                        status="FAIL", reason=f"Package {req_pkg} not found in {c_pkgs}", evidence=comp.packages[0]
                    ))
                all_evidence.extend(comp.packages)
                
        # Overall Decision
        # Hard FAIL has highest priority. 
        # IF any required constraint == FAIL -> INCOMPATIBLE
        # ELSE IF any required constraint == UNKNOWN -> INSUFFICIENT_EVIDENCE
        # ELSE IF all required constraints == PASS -> POTENTIAL_MATCH
        has_fail = any(res.status == "FAIL" for res in results)
        has_unknown = any(res.status == "UNKNOWN" for res in results)
        
        if has_fail:
            overall_status = "INCOMPATIBLE"
            summary = "One or more hard constraints failed."
        elif has_unknown:
            overall_status = "INSUFFICIENT_EVIDENCE"
            summary = "One or more required constraints lack evidence."
        elif len(results) == 0:
            overall_status = "POTENTIAL_MATCH"  # Empty spec -> match everything? Let's say POTENTIAL_MATCH
            summary = "No constraints provided."
        else:
            overall_status = "POTENTIAL_MATCH"
            summary = "All required constraints passed."
            
        return CompatibilityResult(
            part_number=comp.part_number,
            overall_status=overall_status,
            constraint_results=results,
            summary=summary,
            evidence=all_evidence
        )
