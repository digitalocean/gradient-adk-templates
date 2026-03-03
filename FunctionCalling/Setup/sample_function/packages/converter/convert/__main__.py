"""
Sample DigitalOcean Serverless Function — Unit Converter

A simple function that converts between common units of measurement.
This is deployed by setup.sh so you can try the agent out of the box.

Supported conversions:
  - Temperature: celsius, fahrenheit, kelvin
  - Distance:    miles, kilometers, meters, feet
  - Weight:      pounds, kilograms, grams, ounces
"""

CONVERSIONS = {
    # Temperature
    ("celsius", "fahrenheit"): lambda v: v * 9 / 5 + 32,
    ("fahrenheit", "celsius"): lambda v: (v - 32) * 5 / 9,
    ("celsius", "kelvin"): lambda v: v + 273.15,
    ("kelvin", "celsius"): lambda v: v - 273.15,
    ("fahrenheit", "kelvin"): lambda v: (v - 32) * 5 / 9 + 273.15,
    ("kelvin", "fahrenheit"): lambda v: (v - 273.15) * 9 / 5 + 32,
    # Distance
    ("miles", "kilometers"): lambda v: v * 1.60934,
    ("kilometers", "miles"): lambda v: v / 1.60934,
    ("meters", "feet"): lambda v: v * 3.28084,
    ("feet", "meters"): lambda v: v / 3.28084,
    ("miles", "meters"): lambda v: v * 1609.34,
    ("meters", "miles"): lambda v: v / 1609.34,
    ("kilometers", "meters"): lambda v: v * 1000,
    ("meters", "kilometers"): lambda v: v / 1000,
    ("miles", "feet"): lambda v: v * 5280,
    ("feet", "miles"): lambda v: v / 5280,
    ("kilometers", "feet"): lambda v: v * 3280.84,
    ("feet", "kilometers"): lambda v: v / 3280.84,
    # Weight
    ("pounds", "kilograms"): lambda v: v * 0.453592,
    ("kilograms", "pounds"): lambda v: v / 0.453592,
    ("grams", "ounces"): lambda v: v * 0.035274,
    ("ounces", "grams"): lambda v: v / 0.035274,
    ("kilograms", "grams"): lambda v: v * 1000,
    ("grams", "kilograms"): lambda v: v / 1000,
    ("pounds", "grams"): lambda v: v * 453.592,
    ("grams", "pounds"): lambda v: v / 453.592,
    ("pounds", "ounces"): lambda v: v * 16,
    ("ounces", "pounds"): lambda v: v / 16,
    ("kilograms", "ounces"): lambda v: v * 35.274,
    ("ounces", "kilograms"): lambda v: v / 35.274,
}


def main(event, context):
    value = event.get("value")
    from_unit = (event.get("from_unit") or "").strip().lower()
    to_unit = (event.get("to_unit") or "").strip().lower()

    # --- Validate inputs ---
    if value is None:
        return {
            "body": {"error": "Missing required parameter: value"},
            "statusCode": 400,
        }

    try:
        value = float(value)
    except (ValueError, TypeError):
        return {
            "body": {"error": f"Invalid value: {value!r} — must be a number"},
            "statusCode": 400,
        }

    if not from_unit or not to_unit:
        return {
            "body": {"error": "Both from_unit and to_unit are required"},
            "statusCode": 400,
        }

    # --- Convert ---
    if from_unit == to_unit:
        result = value
    elif (from_unit, to_unit) in CONVERSIONS:
        result = CONVERSIONS[(from_unit, to_unit)](value)
    else:
        supported = sorted({u for pair in CONVERSIONS for u in pair})
        return {
            "body": {
                "error": f"Unsupported conversion: {from_unit} -> {to_unit}",
                "supported_units": supported,
            },
            "statusCode": 400,
        }

    return {
        "body": {
            "original_value": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "converted_value": round(result, 4),
        }
    }
