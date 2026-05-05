import re
import random
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CATEGORY_KEYWORDS = {
    "Stationery": [
        "paper", "pen", "pencil", "stapler", "marker", "highlighter",
        "notebook", "notepad", "envelope", "file", "folder", "binder",
        "clip", "eraser", "tape", "glue", "ruler", "scissor", "whiteboard",
        "chalk", "ink", "stamp"
    ],
    "IT Supply": [
        "laptop", "computer", "desktop", "monitor", "keyboard", "mouse",
        "usb", "cable", "charger", "adapter", "toner", "cartridge",
        "printer", "scanner", "router", "modem", "headphone", "webcam",
        "ssd", "hard drive", "ram", "processor", "hub", "dock", "tablet",
        "motor", "driver", "wheel", "robot", "encoder", "battery", "sensor",
        "arduino", "raspberry", "microcontroller", "servo", "actuator",
        "electronic", "circuit", "transistor", "resistor", "capacitor"
    ],
    "Furniture": [
        "chair", "table", "desk", "cabinet", "shelf", "bookcase",
        "sofa", "couch", "bench", "stool", "cupboard", "drawer",
        "rack", "stand", "pedestal", "wardrobe"
    ],
    "Hygiene": [
        "sanitizer", "soap", "tissue", "hand wash", "disinfectant",
        "mask", "glove", "wipe", "towel", "napkin", "detergent",
        "cleaner", "shampoo", "gel", "spray", "antiseptic", "bleach"
    ],
    "Logistics": [
        "shipping", "courier", "delivery", "freight", "transport",
        "bluedart", "delhivery", "fedex", "dhl", "logistics", "dispatch",
        "handling", "packaging", "postage"
    ]
}


def get_category(item_name: str) -> str:
    if not item_name:
        return "General"
    name_lower = item_name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name_lower:
                return category
    return "General"


def clean_number(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^\d.]", "", str(value))
    try:
        return float(cleaned)
    except:
        return 0.0


def parse_textract_response(raw_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    parsed_items = []
    line_items = raw_response.get("line_items", [])

    if not line_items:
        logger.warning("No line items found in OCR response")
        return parsed_items

    for idx, item in enumerate(line_items, start=1):
        try:
            item_name = (
                item.get("item_name") or
                item.get("ITEM") or
                item.get("description") or
                item.get("DESCRIPTION") or
                item.get("name") or
                "Unknown Item"
            )

            quantity = clean_number(
                item.get("quantity") or
                item.get("QUANTITY") or
                item.get("qty") or
                1
            )
            if quantity == 0:
                quantity = 1

            unit_rate = clean_number(
                item.get("unit_price") or
                item.get("UNIT_PRICE") or
                item.get("unit_rate") or
                item.get("rate") or
                item.get("RATE") or
                0
            )

            raw_amount = clean_number(
                item.get("amount") or
                item.get("AMOUNT") or
                item.get("total") or
                item.get("total_amount") or
                0
            )

            gst_percent = clean_number(
                item.get("tax") or
                item.get("TAX") or
                item.get("gst") or
                item.get("gst_percent") or
                item.get("igst") or
                18
            )

            unit = (
                item.get("unit") or
                item.get("UNIT") or
                "Pcs"
            )

            hsn_code = str(
                item.get("hsn_code") or
                item.get("HSN") or
                item.get("hsn") or
                ""
            )

            # Fix unit_rate if it looks wrong
            if unit_rate > 0 and quantity > 0:
                calculated_base = unit_rate * quantity
                gst_amount = calculated_base * (gst_percent / 100)
                total_with_gst = calculated_base + gst_amount

                if raw_amount > 0:
                    diff = abs(total_with_gst - raw_amount) / raw_amount
                    if diff > 0.1:
                        derived_rate = raw_amount / quantity
                        if abs(derived_rate - unit_rate) / max(unit_rate, 1) > 0.1:
                            unit_rate = derived_rate

            base_amount = unit_rate * quantity
            gst_amount = base_amount * (gst_percent / 100)
            total_amount = round(base_amount + gst_amount, 2)

            if raw_amount > 0 and total_amount == 0:
                total_amount = raw_amount

            category = get_category(str(item_name))

            filled = sum([
                bool(item_name and item_name != "Unknown Item"),
                bool(quantity),
                bool(unit_rate),
                bool(total_amount),
                bool(hsn_code)
            ])
            confidence = round(0.80 + (filled / 5) * 0.19, 2)

            parsed_items.append({
                "item_name": str(item_name).strip(),
                "category": category,
                "hsn_code": hsn_code,
                "quantity": quantity,
                "unit": str(unit).strip(),
                "unit_rate": round(unit_rate, 2),
                "gst_percent": gst_percent,
                "total_amount": total_amount,
                "confidence_score": confidence,
            })

        except Exception as e:
            logger.warning(f"Error parsing item {idx}: {str(e)}")
            continue

    logger.info(f"Successfully parsed {len(parsed_items)} line items")
    return parsed_items


class Parser:
    @staticmethod
    def parse_textract_response(raw_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        return parse_textract_response(raw_response)

    @staticmethod
    def parse_line_items(raw_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        return parse_textract_response(raw_response)


def parse_line_items(raw_response: Dict[str, Any]) -> Dict[str, Any]:
    items = parse_textract_response(raw_response)
    total_amount = sum(i.get("total_amount", 0) for i in items)
    return {
        "items": items,
        "total_amount": total_amount,
        "item_count": len(items),
        "header": raw_response.get("header", {})
    }