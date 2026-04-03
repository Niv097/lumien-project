from typing import Dict, Any, List
import re

class EnrichmentService:
    @staticmethod
    def identify_bank_from_ifsc(ifsc: str) -> str:
        # Mock logic: Extract bank code from IFSC (first 4 chars)
        if ifsc:
            return ifsc[:4].upper()
        return None

    @staticmethod
    def identify_bank_from_upi(vpa: str) -> str:
        # Mock logic: Identify bank from UPI handle
        vpa_map = {
            "okhdfcbank": "HDFC",
            "okicici": "ICICI",
            "oksbi": "SBI",
            "apl": "AXIS",
            "ybl": "YESB"
        }
        if "@" in vpa:
            handle = vpa.split("@")[1].lower()
            return vpa_map.get(handle)
        return None

    @staticmethod
    def calculate_confidence(signals: List[Dict[str, Any]]) -> float:
        # Scoring logic
        score = 0.0
        for signal in signals:
            if signal["type"] == "IFSC_MATCH":
                score += 0.6
            elif signal["type"] == "UPI_HANDLE_MATCH":
                score += 0.4
            elif signal["type"] == "BIN_MATCH":
                score += 0.5
            elif signal["type"] == "HISTORICAL_MATCH":
                score += 0.2
        
        return min(score, 1.0) * 100

    def enrich_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        signals = []
        target_bank = None
        
        # Check IFSC
        ifsc = case_data.get("ifsc")
        bank_from_ifsc = self.identify_bank_from_ifsc(ifsc)
        if bank_from_ifsc:
            target_bank = bank_from_ifsc
            signals.append({"type": "IFSC_MATCH", "value": bank_from_ifsc})
            
        # Check UPI
        vpa = case_data.get("vpa")
        bank_from_vpa = self.identify_bank_from_upi(vpa)
        if bank_from_vpa:
            if not target_bank:
                target_bank = bank_from_vpa
            signals.append({"type": "UPI_HANDLE_MATCH", "value": bank_from_vpa})
            
        confidence = self.calculate_confidence(signals)
        
        return {
            "target_bank": target_bank,
            "confidence": confidence,
            "signals": signals,
            "can_auto_route": confidence >= 80,
            "needs_review": confidence < 50
        }

enrichment_service = EnrichmentService()
